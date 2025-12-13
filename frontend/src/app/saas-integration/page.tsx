'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  AppLayout,
  Container,
  Header,
  SpaceBetween,
  Form,
  FormField,
  Input,
  Button,
  Alert,
  ContentLayout,
  BreadcrumbGroup,
  Select,
  Box,
  ExpandableSection,
  ProgressBar,
  StatusIndicator,
  Spinner,
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';
import WorkflowNav from '@/components/WorkflowNav';
import axios from 'axios';

interface DeploymentStage {
  name: string;
  description: string;
  status: 'pending' | 'in-progress' | 'completed' | 'error';
  message?: string;
  resourceType?: string;
}

const INITIAL_STAGES: DeploymentStage[] = [
  { name: 'Stack Creation', description: 'Initiating CloudFormation stack', status: 'pending', resourceType: 'AWS::CloudFormation::Stack' },
  { name: 'IAM Roles', description: 'Creating IAM roles and policies', status: 'pending', resourceType: 'AWS::IAM::Role' },
  { name: 'DynamoDB Tables', description: 'Creating subscription and metering tables', status: 'pending', resourceType: 'AWS::DynamoDB::Table' },
  { name: 'Lambda Functions', description: 'Deploying metering Lambda', status: 'pending', resourceType: 'AWS::Lambda::Function' },
  { name: 'API Gateway', description: 'Setting up fulfillment API', status: 'pending', resourceType: 'AWS::ApiGateway::RestApi' },
  { name: 'SNS Topic', description: 'Configuring notifications', status: 'pending', resourceType: 'AWS::SNS::Topic' },
];

export default function SaaSIntegrationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, productId: storeProductId, credentials, setStackId, setCurrentStep, setProductId, listingData } = useStore();
  
  // Get productId from URL or store
  const urlProductId = searchParams.get('productId');
  const productId = urlProductId || storeProductId;

  const [email, setEmail] = useState('');
  const [stackName, setStackName] = useState('');
  const [region, setRegion] = useState<any>({ label: 'us-east-1', value: 'us-east-1' });
  const [accessKey, setAccessKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [sessionToken, setSessionToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [deployedStackId, setDeployedStackId] = useState('');
  const [deployedStackName, setDeployedStackName] = useState('');
  const [deploymentStages, setDeploymentStages] = useState<DeploymentStage[]>(INITIAL_STAGES);
  const [deploymentProgress, setDeploymentProgress] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [cfStatus, setCfStatus] = useState('');
  const [cfEvents, setCfEvents] = useState<any[]>([]);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [existingStackId, setExistingStackId] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [showSnsConfirmation, setShowSnsConfirmation] = useState(false);
  const [showBuyerExperience, setShowBuyerExperience] = useState(false);
  const [buyerSteps, setBuyerSteps] = useState<any[]>([]);
  const [showMeteringGuide, setShowMeteringGuide] = useState(false);
  const [meteringSteps, setMeteringSteps] = useState<any[]>([]);
  const [showVisibilityGuide, setShowVisibilityGuide] = useState(false);
  const [visibilitySteps, setVisibilitySteps] = useState<any[]>([]);
  const [currentSubStep, setCurrentSubStep] = useState(0); // Track current sub-step (0-3)
  const [pricingModel, setPricingModel] = useState<any>(null); // Pricing model selection

  useEffect(() => {
    if (!isAuthenticated || !productId) {
      router.push('/');
      return;
    }

    // If productId came from URL, store it
    if (urlProductId && urlProductId !== storeProductId) {
      setProductId(urlProductId);
    }

    setStackName(`marketplace-saas-${productId.substring(0, 8)}`);

    if (credentials) {
      setAccessKey(credentials.aws_access_key_id || '');
      setSecretKey(credentials.aws_secret_access_key || '');
      setSessionToken(credentials.aws_session_token || '');
    }

    // Check if coming from "Continue" button (stack already exists)
    const skipDeployment = searchParams.get('skipDeployment');
    if (skipDeployment === 'true') {
      // Stack already exists, redirect to workflow page
      const stackName = `saas-integration-${productId}`;
      router.push(`/saas-workflow?productId=${productId}&stackName=${stackName}`);
    }
  }, [isAuthenticated, productId, credentials, router, urlProductId, storeProductId, setProductId, searchParams]);

  useEffect(() => {
    if (loading && startTime) {
      const interval = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [loading, startTime]);

  // Poll CloudFormation status
  useEffect(() => {
    if (loading && deployedStackName) {
      let pollCount = 0;
      const maxPolls = 200; // ~10 minutes at 3s intervals
      
      const pollInterval = setInterval(async () => {
        pollCount++;
        
        try {
          const response = await axios.post('/api/get-stack-status', {
            stack_name: deployedStackName,
            region: region.value,
            credentials: {
              aws_access_key_id: accessKey,
              aws_secret_access_key: secretKey,
              aws_session_token: sessionToken || undefined,
            },
          });

          if (response.data.success) {
            const status = response.data.stack_status;
            const events = response.data.events || [];
            const statusReason = response.data.stack_status_reason || '';
            
            setCfStatus(status);
            setCfEvents(events);

            // Update stages based on events
            updateStagesFromEvents(events, status);

            // Check if deployment is complete
            if (status === 'CREATE_COMPLETE') {
              setDeploymentProgress(100);
              setSuccess(true);
              setLoading(false);
              setCurrentSubStep(0); // Stack Deployment complete
              clearInterval(pollInterval);
            } else if (status.includes('FAILED') || status.includes('ROLLBACK')) {
              // Mark all in-progress stages as error
              const failedStages = deploymentStages.map(stage => {
                if (stage.status === 'in-progress' || stage.status === 'pending') {
                  return { ...stage, status: 'error' as const, message: '✗ Failed' };
                }
                return stage;
              });
              setDeploymentStages(failedStages);
              
              const reason = statusReason || 'Deployment failed';
              setError(`CloudFormation deployment failed: ${reason}`);
              setLoading(false);
              clearInterval(pollInterval);
            } else if (status === 'CREATE_IN_PROGRESS') {
              // Show some progress while creating
              const baseProgress = Math.min(pollCount * 2, 30); // Slow initial progress
              setDeploymentProgress(prev => Math.max(prev, baseProgress));
            }
          } else {
            // Handle API error
            console.error('Stack status check failed:', response.data.error);
            if (response.data.stack_status === 'NOT_FOUND') {
              // Stack might not be created yet, show initializing progress
              setCfStatus('Initializing stack...');
              // Show slow progress while waiting for stack to appear
              const initProgress = Math.min(pollCount, 10);
              setDeploymentProgress(initProgress);
              
              // Mark first stage as in-progress
              setDeploymentStages(prev => prev.map((stage, idx) => 
                idx === 0 ? { ...stage, status: 'in-progress' as const, message: 'Initializing...' } : stage
              ));
            }
          }
          
          // Timeout protection
          if (pollCount >= maxPolls) {
            setError('Deployment timed out. Please check AWS CloudFormation console for status.');
            setLoading(false);
            clearInterval(pollInterval);
          }
        } catch (err: any) {
          console.error('Failed to poll stack status:', err);
          // Don't stop polling on network errors, just log
        }
      }, 3000); // Poll every 3 seconds

      return () => clearInterval(pollInterval);
    }
  }, [loading, deployedStackName, region, accessKey, secretKey, sessionToken]);

  const updateStagesFromEvents = (events: any[], stackStatus: string) => {
    const newStages = [...deploymentStages];
    
    // If stack is complete, mark all stages as complete
    if (stackStatus === 'CREATE_COMPLETE') {
      newStages.forEach((stage, idx) => {
        newStages[idx].status = 'completed';
        newStages[idx].message = '✓ Complete';
      });
      setDeploymentProgress(100);
      setDeploymentStages(newStages);
      return;
    }
    
    // Track which resources have been seen
    const seenResources = new Set<string>();
    
    events.forEach(event => {
      const resourceType = event.resource_type;
      const status = event.status;
      
      seenResources.add(resourceType);
      
      // Find matching stage by resource type
      const stageIndex = newStages.findIndex(s => s.resourceType === resourceType);
      if (stageIndex >= 0) {
        if (status.includes('COMPLETE') && !status.includes('ROLLBACK')) {
          newStages[stageIndex].status = 'completed';
          newStages[stageIndex].message = '✓ Complete';
        } else if (status.includes('IN_PROGRESS')) {
          newStages[stageIndex].status = 'in-progress';
          newStages[stageIndex].message = 'Creating...';
        } else if (status.includes('FAILED')) {
          newStages[stageIndex].status = 'error';
          newStages[stageIndex].message = event.reason || '✗ Failed';
        } else if (status.includes('ROLLBACK')) {
          newStages[stageIndex].status = 'error';
          newStages[stageIndex].message = '✗ Rolled back';
        }
      }
    });

    // If stack is in failed/rollback state, mark all non-completed stages as error
    if (stackStatus.includes('FAILED') || stackStatus.includes('ROLLBACK')) {
      newStages.forEach((stage, idx) => {
        if (stage.status !== 'completed') {
          newStages[idx].status = 'error';
          if (!newStages[idx].message || newStages[idx].message === 'Creating...') {
            newStages[idx].message = '✗ Failed';
          }
        }
      });
    }

    // Calculate progress based on events and stack status
    const completed = newStages.filter(s => s.status === 'completed').length;
    const inProgress = newStages.filter(s => s.status === 'in-progress').length;
    let progress = ((completed + (inProgress * 0.5)) / newStages.length) * 100;
    
    // If we're in CREATE_IN_PROGRESS but no events match our stages, show some progress
    if (stackStatus === 'CREATE_IN_PROGRESS' && progress === 0) {
      progress = Math.min(events.length * 5, 50); // Show progress based on event count
    }
    
    setDeploymentProgress(Math.min(progress, 95)); // Cap at 95% until fully complete
    setDeploymentStages(newStages);
  };

  const checkStackExists = async () => {
    const actualStackName = `saas-integration-${productId}`;
    
    try {
      const response = await axios.post('/api/check-stack-exists', {
        stack_name: actualStackName,
        region: region.value,
        credentials: {
          aws_access_key_id: accessKey,
          aws_secret_access_key: secretKey,
          aws_session_token: sessionToken || undefined,
        },
      });
      
      return response.data;
    } catch (err) {
      console.error('Error checking stack:', err);
      return { exists: false };
    }
  };

  const handleDeleteStack = async () => {
    setDeleting(true);
    setError('');
    setShowDeleteConfirm(false);
    
    try {
      // Initiate deletion (non-blocking)
      const response = await axios.post('/api/delete-stack', {
        stack_name: existingStackId,
        region: region.value,
        credentials: {
          aws_access_key_id: accessKey,
          aws_secret_access_key: secretKey,
          aws_session_token: sessionToken || undefined,
        },
      });
      
      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to initiate stack deletion');
      }

      // Poll for deletion completion
      const stackNameToCheck = response.data.stack_name || existingStackId;
      let deleteComplete = false;
      let pollCount = 0;
      const maxPolls = 120; // 10 minutes at 5s intervals
      
      while (!deleteComplete && pollCount < maxPolls) {
        await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
        pollCount++;
        
        try {
          const statusResponse = await axios.post('/api/get-stack-status', {
            stack_name: stackNameToCheck,
            region: region.value,
            credentials: {
              aws_access_key_id: accessKey,
              aws_secret_access_key: secretKey,
              aws_session_token: sessionToken || undefined,
            },
          });
          
          const status = statusResponse.data.stack_status;
          
          if (status === 'DELETE_COMPLETE' || status === 'NOT_FOUND') {
            deleteComplete = true;
            console.log('[DEBUG] Stack deleted successfully');
          } else if (status === 'DELETE_FAILED') {
            throw new Error('Stack deletion failed');
          } else {
            console.log(`[DEBUG] Deletion in progress: ${status} (${pollCount * 5}s elapsed)`);
          }
        } catch (err: any) {
          // If stack not found, deletion is complete
          if (err.response?.data?.stack_status === 'NOT_FOUND') {
            deleteComplete = true;
            console.log('[DEBUG] Stack deleted successfully (not found)');
          } else {
            console.error('[DEBUG] Error checking deletion status:', err);
          }
        }
      }
      
      if (!deleteComplete) {
        throw new Error('Stack deletion timed out after 10 minutes');
      }
      
      setDeleting(false);
      
      // Now proceed with deployment
      await deployStack();
      
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Failed to delete stack');
      setDeleting(false);
      setShowDeleteConfirm(true); // Show confirmation again on error
    }
  };

  const deployStack = async () => {
    setLoading(true);
    setError('');
    setStartTime(Date.now());
    setDeploymentStages(INITIAL_STAGES.map(s => ({ ...s, status: 'pending' as const })));
    
    const actualStackName = `saas-integration-${productId}`;
    setDeployedStackName(actualStackName);

    try {
      // Pass pricing model to backend for CloudFormation deployment
      console.log('[FRONTEND DEBUG] Deploying with pricing model:', pricingModel);
      console.log('[FRONTEND DEBUG] Pricing model value being sent:', pricingModel?.value);
      
      // Try to get pricing dimensions from stored listing data
      let storedPricingDimensions = null;
      
      // First try: Get from store
      if (listingData?.pricing_dimensions) {
        storedPricingDimensions = listingData.pricing_dimensions;
        console.log('[FRONTEND DEBUG] Using pricing dimensions from store listing data:', storedPricingDimensions);
      } else {
        // Second try: Get from localStorage (from create listing process)
        console.log('[FRONTEND DEBUG] No pricing dimensions in store, trying localStorage...');
        try {
          const storedListingData = localStorage.getItem(`listing_data_${productId}`);
          if (storedListingData) {
            const parsed = JSON.parse(storedListingData);
            storedPricingDimensions = parsed.pricing_dimensions;
            console.log('[FRONTEND DEBUG] Found pricing dimensions in localStorage:', storedPricingDimensions);
          } else {
            console.log('[FRONTEND DEBUG] No listing data found in localStorage for product:', productId);
          }
        } catch (e) {
          console.error('[FRONTEND DEBUG] Error reading from localStorage:', e);
        }
      }
      
      if (!storedPricingDimensions) {
        console.log('[FRONTEND DEBUG] ⚠ NO PRICING DIMENSIONS FOUND - will be null in backend request');
      }
      
      const response = await axios.post('/api/deploy-saas', {
        product_id: productId,
        email,
        stack_name: stackName,
        region: region.value,
        pricing_model: pricingModel?.value, // Pass selected pricing model
        pricing_dimensions: storedPricingDimensions, // Pass pricing dimensions if available
        credentials: {
          aws_access_key_id: accessKey,
          aws_secret_access_key: secretKey,
          aws_session_token: sessionToken || undefined,
        },
      });

      if (!response.data.success) {
        throw new Error(response.data.error || 'Deployment failed');
      }

      setDeployedStackId(response.data.stack_id);
      setStackId(response.data.stack_id);
      
      // Update stack name from response if provided (backend knows the actual name)
      if (response.data.stack_name) {
        setDeployedStackName(response.data.stack_name);
      }
      
      // If stack already exists and is complete, show success immediately
      if (response.data.status === 'CREATE_COMPLETE') {
        setDeploymentProgress(100);
        setSuccess(true);
        setLoading(false);
        setCfStatus('CREATE_COMPLETE');
        // Mark all stages as completed
        setDeploymentStages(INITIAL_STAGES.map(s => ({ ...s, status: 'completed' as const, message: '✓ Complete' })));
        setCurrentSubStep(0); // Stack Deployment complete
      }
      
      // Otherwise, polling will continue via useEffect
    } catch (err: any) {
      console.error('Deployment error:', err);
      setError(err.response?.data?.error || err.message || 'Failed to deploy SaaS integration');
      setLoading(false);
    }
  };

  const handleDeploy = async () => {
    if (!email || !stackName || !accessKey || !secretKey) {
      setError('Please fill in all required fields');
      return;
    }

    if (!pricingModel) {
      setError('Please select a pricing model');
      return;
    }

    // Check if stack already exists
    const stackCheck = await checkStackExists();
    
    if (stackCheck.exists) {
      setExistingStackId(stackCheck.stack_name);
      setShowDeleteConfirm(true);
    } else {
      // Stack doesn't exist, proceed with deployment
      await deployStack();
    }
  };

  const handleBack = () => {
    router.push('/listing-success');
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isAuthenticated || !productId) {
    return null;
  }

  const handleSubStepNavigation = (subStepIndex: number) => {
    // Only allow navigation to completed or current sub-steps
    if (subStepIndex <= currentSubStep) {
      setCurrentSubStep(subStepIndex);
      
      // Update UI state based on sub-step
      if (subStepIndex === 0) {
        // Stack Deployment - show deployment section
        setShowSnsConfirmation(false);
        setShowBuyerExperience(false);
        setShowMeteringGuide(false);
        setShowVisibilityGuide(false);
      } else if (subStepIndex === 1) {
        // SNS Confirmation
        setShowSnsConfirmation(true);
        setShowBuyerExperience(false);
        setShowMeteringGuide(false);
        setShowVisibilityGuide(false);
      } else if (subStepIndex === 2) {
        // Buyer Experience
        setShowSnsConfirmation(false);
        setShowBuyerExperience(true);
        setShowMeteringGuide(false);
        setShowVisibilityGuide(false);
      } else if (subStepIndex === 3) {
        // Testing Complete - show metering or visibility guide
        setShowSnsConfirmation(false);
        setShowBuyerExperience(false);
        // Keep current guide visible (metering or visibility)
      }
    }
  };

  return (
    <AppLayout
        navigation={<WorkflowNav />}
        toolsHide
        breadcrumbs={
          <BreadcrumbGroup
            items={[
              { text: 'Home', href: '/' },
              { text: 'Success', href: '/listing-success' },
              { text: 'SaaS Integration', href: '/saas-integration' },
            ]}
            onFollow={(e) => {
              e.preventDefault();
              router.push(e.detail.href);
            }}
          />
        }
        content={
          <ContentLayout
            header={
              <Header
                variant="h1"
                description="Deploy serverless infrastructure for your AWS Marketplace SaaS integration"
              >
                Deploy SaaS Integration
              </Header>
            }
          >
            <form onSubmit={(e) => { e.preventDefault(); handleDeploy(); }}>
              <Form
                actions={
                  <SpaceBetween direction="horizontal" size="xs">
                    <Button onClick={handleBack}>← Back</Button>
                    {success && !showSnsConfirmation && <Button variant="primary" onClick={() => { 
                      router.push(`/saas-workflow?productId=${productId}&stackName=${deployedStackName}&pricingModel=${pricingModel?.value || ''}`);
                    }}>Continue to Workflow →</Button>}
                    {!success && <Button variant="primary" onClick={handleDeploy} loading={loading} disabled={loading}>Deploy Stack 🚀</Button>}
                  </SpaceBetween>
                }
              >
                <SpaceBetween size="l">
                  {!success && !loading && !showDeleteConfirm && !deleting && (
                    <Alert type="info" header="📋 Complete SaaS Integration Workflow">
                      <SpaceBetween size="m">
                        <Box>
                          After deploying the CloudFormation stack, you'll complete the following steps to fully integrate your SaaS product with AWS Marketplace:
                        </Box>
                        
                        <Container>
                          <SpaceBetween size="s">
                            <Box variant="h4">Step 1: Deploy Infrastructure (5-10 minutes)</Box>
                            <Box fontSize="body-s" color="text-body-secondary">
                              CloudFormation will create DynamoDB tables, Lambda functions, API Gateway, SNS topics, and IAM roles for your SaaS integration.
                            </Box>
                          </SpaceBetween>
                        </Container>

                        <Container>
                          <SpaceBetween size="s">
                            <Box variant="h4">Step 2: Confirm SNS Subscription</Box>
                            <Box fontSize="body-s" color="text-body-secondary">
                              You'll receive an email to confirm your SNS subscription. This enables notifications for marketplace events like new subscriptions and entitlement changes.
                            </Box>
                          </SpaceBetween>
                        </Container>

                        <Container>
                          <SpaceBetween size="s">
                            <Box variant="h4">Step 3: Test Buyer Experience</Box>
                            <Box fontSize="body-s" color="text-body-secondary">
                              Simulate the complete buyer journey by purchasing your product on AWS Marketplace, registering, and verifying the integration works end-to-end.
                            </Box>
                          </SpaceBetween>
                        </Container>

                        <Container>
                          <SpaceBetween size="s">
                            <Box variant="h4">Step 4: Complete Testing (Pricing-Based)</Box>
                            <Box fontSize="body-s" color="text-body-secondary">
                              Based on your pricing model, you'll either:
                            </Box>
                            <ul style={{ marginLeft: '20px', marginTop: '8px' }}>
                              <li>
                                <Box fontSize="body-s">
                                  <strong>Usage-Based Pricing:</strong> Configure metering to track customer usage and bill accordingly
                                </Box>
                              </li>
                              <li>
                                <Box fontSize="body-s">
                                  <strong>Contract-Based Pricing:</strong> Submit a public visibility request to make your product publicly available
                                </Box>
                              </li>
                            </ul>
                          </SpaceBetween>
                        </Container>

                        <Box color="text-status-info" fontSize="body-s">
                          ℹ️ Total time: 15-30 minutes including deployment and testing
                        </Box>
                      </SpaceBetween>
                    </Alert>
                  )}

                  {error && <Alert type="error" dismissible onDismiss={() => setError('')}>{error}</Alert>}

                  {showDeleteConfirm && !deleting && (
                    <Alert
                      type="warning"
                      header="⚠️ Stack Already Exists"
                      action={
                        <SpaceBetween direction="horizontal" size="xs">
                          <Button onClick={() => router.push('/seller-registration')} disabled={deleting}>Cancel</Button>
                          <Button variant="primary" onClick={handleDeleteStack} loading={deleting}>Delete and Redeploy</Button>
                          <Button 
                            variant="normal" 
                            onClick={async () => {
                              try {
                                // Skip deletion, go directly to SNS confirmation workflow
                                setShowDeleteConfirm(false);
                                setSuccess(true);
                                setDeployedStackName(`saas-integration-${productId}`);
                                
                                // Try to retrieve pricing dimensions from existing stack
                                console.log('[SAAS-INTEGRATION] Retrieving pricing dimensions from existing stack...');
                                try {
                                  const stackResponse = await axios.post('/api/get-stack-parameters', {
                                    stack_name: `saas-integration-${productId}`,
                                    region: region.value,
                                    credentials: {
                                      aws_access_key_id: accessKey,
                                      aws_secret_access_key: secretKey,
                                      aws_session_token: sessionToken || undefined,
                                    }
                                  });
                                  
                                  if (stackResponse.data.success && stackResponse.data.pricing_dimensions) {
                                    // Store pricing dimensions for later use in metering
                                    const pricingDimensions = stackResponse.data.pricing_dimensions;
                                    console.log('[SAAS-INTEGRATION] Retrieved pricing dimensions:', pricingDimensions);
                                    
                                    // Store in localStorage for metering workflow
                                    const listingData = {
                                      pricing_dimensions: pricingDimensions,
                                      pricing_model: stackResponse.data.pricing_model,
                                      retrieved_from: 'existing_stack',
                                      timestamp: new Date().toISOString()
                                    };
                                    localStorage.setItem(`listing_data_${productId}`, JSON.stringify(listingData));
                                    console.log('[SAAS-INTEGRATION] Stored pricing dimensions for metering workflow');
                                  } else {
                                    console.log('[SAAS-INTEGRATION] No pricing dimensions found in existing stack');
                                  }
                                } catch (stackErr) {
                                  console.error('[SAAS-INTEGRATION] Failed to retrieve pricing dimensions from stack:', stackErr);
                                  // Continue anyway - metering will use defaults
                                }
                                
                                setCurrentSubStep(1);
                                setShowSnsConfirmation(true);
                              } catch (err) {
                                console.error('[SAAS-INTEGRATION] Error using existing stack:', err);
                                setError('Failed to use existing stack. Please try again.');
                              }
                            }}
                          >
                            Use Existing Stack →
                          </Button>
                        </SpaceBetween>
                      }
                    >
                      <SpaceBetween size="s">
                        <Box>A CloudFormation stack with this product ID already exists:</Box>
                        <Box fontWeight="bold">{existingStackId}</Box>
                        <Box>Choose an option:</Box>
                        <ul style={{ marginLeft: '20px', marginTop: '8px' }}>
                          <li>
                            <Box fontWeight="bold">Delete and Redeploy</Box>
                            <Box fontSize="body-s" color="text-body-secondary">
                              Delete the existing stack and deploy a fresh one (10-20 minutes)
                            </Box>
                          </li>
                          <li style={{ marginTop: '8px' }}>
                            <Box fontWeight="bold">Use Existing Stack</Box>
                            <Box fontSize="body-s" color="text-body-secondary">
                              Keep the existing stack and proceed to SNS confirmation and buyer experience workflow (instant)
                            </Box>
                          </li>
                        </ul>
                        <Box color="text-status-warning" fontSize="body-s">
                          ⚠️ Warning: "Delete and Redeploy" will delete all existing resources including DynamoDB tables, Lambda functions, and API Gateway endpoints.
                        </Box>
                      </SpaceBetween>
                    </Alert>
                  )}

                  {deleting && (
                    <Alert type="info" header="🗑️ Deleting Existing Stack">
                      <SpaceBetween size="m">
                        <Box textAlign="center"><Spinner size="large" /></Box>
                        <Box>Deleting CloudFormation stack: <strong>{existingStackId}</strong></Box>
                        <Box fontSize="body-s" color="text-body-secondary">
                          This may take 5-10 minutes. The stack and all its resources (DynamoDB tables, Lambda functions, API Gateway, etc.) are being removed.
                        </Box>
                        <Box fontSize="body-s" color="text-status-info">
                          ℹ️ Once deletion is complete, a new stack will be deployed automatically.
                        </Box>
                      </SpaceBetween>
                    </Alert>
                  )}

                  {success && !showSnsConfirmation && (
                    <Alert type="success" header="✅ Deployment Successful!">
                      <SpaceBetween size="m">
                        <Box>SaaS integration infrastructure deployed successfully!</Box>
                        <Box><strong>Stack ID:</strong> {deployedStackId}</Box>
                        <Box><strong>Stack Name:</strong> {deployedStackName}</Box>
                        <Box color="text-body-secondary">Time: {formatTime(elapsedTime)}</Box>
                        
                        <Box variant="h4">Next Steps:</Box>
                        <ol style={{ marginLeft: '20px' }}>
                          <li>
                            <Box fontWeight="bold">Get the Fulfillment URL from CloudFormation Outputs</Box>
                            <Box fontSize="body-s" color="text-body-secondary">
                              Open the CloudFormation stack in AWS Console and copy the "AWSMarketplaceFulfillmentURL" from the Outputs tab
                            </Box>
                            <Button
                              iconAlign="right"
                              iconName="external"
                              onClick={() => {
                                window.open(`https://console.aws.amazon.com/cloudformation/home?region=${region.value}#/stacks/outputs?stackId=${encodeURIComponent(deployedStackId)}`, '_blank');
                              }}
                            >
                              View Stack Outputs
                            </Button>
                          </li>
                          <li>
                            <Box fontWeight="bold">Update Product with Fulfillment URL</Box>
                            <Box fontSize="body-s" color="text-body-secondary">
                              Go to AWS Marketplace Management Portal and update your product's fulfillment URL
                            </Box>
                            <Button
                              iconAlign="right"
                              iconName="external"
                              onClick={() => {
                                window.open(`https://aws.amazon.com/marketplace/management/products/${productId}`, '_blank');
                              }}
                            >
                              Open Product in Console
                            </Button>
                          </li>
                        </ol>
                      </SpaceBetween>
                    </Alert>
                  )}

                  {showSnsConfirmation && !showBuyerExperience && (
                    <Container
                      header={
                        <Header
                          variant="h2"
                          description="Step 2 of 4: Enable marketplace notifications"
                        >
                          📧 Confirm Amazon SNS Subscription
                        </Header>
                      }
                    >
                      <SpaceBetween size="l">
                        <Alert type="info">
                          <Box>
                            To receive email notifications at <strong style={{ color: '#0073bb' }}>{email}</strong>, you need to confirm the SNS subscription.
                          </Box>
                        </Alert>

                        <SpaceBetween size="m">
                          {[
                            {
                              icon: '📬',
                              title: 'Open your email inbox',
                              description: `Check the email address: ${email}`,
                              color: '#0073bb'
                            },
                            {
                              icon: '🔍',
                              title: 'Find the confirmation email',
                              description: 'Subject: "AWS Notification - Subscription Confirmation"',
                              color: '#0073bb'
                            },
                            {
                              icon: '✅',
                              title: 'Click "Confirm subscription"',
                              description: 'This link will open in your browser to confirm the subscription',
                              color: '#037f0c'
                            }
                          ].map((step, index) => (
                            <Container key={index}>
                              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                                <div style={{
                                  fontSize: '32px',
                                  minWidth: '48px',
                                  textAlign: 'center',
                                  lineHeight: '1'
                                }}>
                                  {step.icon}
                                </div>
                                <div style={{ flex: 1 }}>
                                  <Box variant="h3" color="text-label">
                                    Step {index + 1}: {step.title}
                                  </Box>
                                  <Box fontSize="body-m" color="text-body-secondary" padding={{ top: 'xs' }}>
                                    {step.description}
                                  </Box>
                                </div>
                                <div style={{
                                  width: '32px',
                                  height: '32px',
                                  borderRadius: '50%',
                                  backgroundColor: step.color,
                                  color: 'white',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontSize: '16px',
                                  fontWeight: 'bold'
                                }}>
                                  {index + 1}
                                </div>
                              </div>
                            </Container>
                          ))}
                        </SpaceBetween>

                        <Alert type="success">
                          <SpaceBetween size="xs">
                            <Box fontWeight="bold">What happens after confirmation?</Box>
                            <Box fontSize="body-s">
                              ✓ You'll receive emails for new buyer registrations<br/>
                              ✓ Get notified about entitlement changes<br/>
                              ✓ Stay updated on subscription events
                            </Box>
                          </SpaceBetween>
                        </Alert>

                        <Box textAlign="center">
                          <Button 
                            variant="primary" 
                            onClick={() => {
                              setShowBuyerExperience(true);
                              setCurrentSubStep(2);
                            }}
                          >
                            I've Confirmed - Continue to Buyer Experience →
                          </Button>
                        </Box>
                      </SpaceBetween>
                    </Container>
                  )}

                  {showBuyerExperience && (
                    <Container
                      header={
                        <Header
                          variant="h2"
                          description="Step 3 of 4: Simulate the complete buyer journey"
                          actions={
                        <Button variant="primary" onClick={async () => {
                          setLoading(true);
                          setError('');
                          
                          try {
                            // Run buyer experience and automatically route to next step
                            const response = await axios.post('/api/run-buyer-experience', {
                              product_id: productId,
                              credentials: {
                                aws_access_key_id: accessKey,
                                aws_secret_access_key: secretKey,
                                aws_session_token: sessionToken || undefined,
                              }
                            });
                            
                            if (response.data.success) {
                              const pricingModel = response.data.pricing_model;
                              const nextStep = response.data.next_step;
                              
                              // Show appropriate guide based on routing
                              if (nextStep === 'metering') {
                                // Usage-based or Contract-with-consumption - show metering guide
                                const meteringResponse = await axios.post('/api/metering-guide', {});
                                if (meteringResponse.data.success) {
                                  setMeteringSteps(meteringResponse.data.steps);
                                  setShowMeteringGuide(true);
                                  setCurrentSubStep(3); // Move to Testing Complete
                                }
                              } else if (nextStep === 'public_visibility') {
                                // Contract-based - show public visibility guide
                                const visibilityResponse = await axios.post('/api/public-visibility-guide', {});
                                if (visibilityResponse.data.success) {
                                  setVisibilitySteps(visibilityResponse.data.steps);
                                  setShowVisibilityGuide(true);
                                  setCurrentSubStep(3); // Move to Testing Complete
                                }
                              }
                            } else {
                              setError(response.data.error || 'Buyer experience simulation failed');
                            }
                          } catch (err: any) {
                            console.error('Failed to run buyer experience:', err);
                            setError(err.response?.data?.error || 'Failed to complete buyer experience');
                          } finally {
                            setLoading(false);
                          }
                        }}>
                          Complete Testing →
                        </Button>
                          }
                        >
                          🛒 Test Buyer Experience
                        </Header>
                      }
                    >
                      <SpaceBetween size="l">
                        <Alert type="info">
                          <Box>
                            Now let's test your SaaS integration by simulating the buyer experience. Follow these steps to ensure everything works correctly.
                          </Box>
                        </Alert>
                        
                        {buyerSteps.length > 0 ? (
                          buyerSteps.map((step, index) => (
                            <Container key={index} header={<Header variant="h3">Step {step.step}: {step.title}</Header>}>
                              <SpaceBetween size="s">
                                <Box>{step.description}</Box>
                                <Box variant="h4">Actions:</Box>
                                <ul style={{ marginLeft: '20px' }}>
                                  {step.actions?.map((action: string, idx: number) => (
                                    <li key={idx}><Box fontSize="body-s">{action}</Box></li>
                                  ))}
                                </ul>
                                {step.expected && (
                                  <>
                                    <Box variant="h4">Expected Outcomes:</Box>
                                    <ul style={{ marginLeft: '20px' }}>
                                      {step.expected.map((outcome: string, idx: number) => (
                                        <li key={idx}><Box fontSize="body-s" color="text-status-success">✓ {outcome}</Box></li>
                                      ))}
                                    </ul>
                                  </>
                                )}
                              </SpaceBetween>
                            </Container>
                          ))
                        ) : (
                          <SpaceBetween size="m">
                            {[
                              { icon: '🏢', title: 'Open SaaS product page', desc: 'Navigate to AWS Marketplace Management Portal and select your product', color: '#0073bb' },
                              { icon: '✓', title: 'Validate fulfillment URL', desc: 'In Request Log tab, verify last request status is "Succeeded"', color: '#037f0c' },
                              { icon: '👁️', title: 'View on Marketplace', desc: 'Select "View on AWS Marketplace"', color: '#0073bb' },
                              { icon: '🛍️', title: 'Start purchase', desc: 'Select "View purchase options"', color: '#0073bb' },
                              { icon: '⚙️', title: 'Configure contract', desc: '1 month duration, No renewal, quantity 1', color: '#ff9900' },
                              { icon: '💳', title: 'Create contract', desc: 'Select "Create contract" then "Pay now"', color: '#ff9900' },
                              { icon: '📝', title: 'Register account', desc: 'Fill registration form and select "Register"', color: '#0073bb' },
                              { icon: '🎉', title: 'Verify success', desc: 'Blue banner appears + email notification received', color: '#037f0c' }
                            ].map((step, index) => (
                              <Container key={index}>
                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                                  <div style={{
                                    fontSize: '36px',
                                    minWidth: '56px',
                                    textAlign: 'center',
                                    lineHeight: '1'
                                  }}>
                                    {step.icon}
                                  </div>
                                  <div style={{ flex: 1 }}>
                                    <Box variant="h3" color="text-label">
                                      Step {index + 1}: {step.title}
                                    </Box>
                                    <Box fontSize="body-m" color="text-body-secondary" padding={{ top: 'xs' }}>
                                      {step.desc}
                                    </Box>
                                  </div>
                                  <div style={{
                                    width: '36px',
                                    height: '36px',
                                    borderRadius: '50%',
                                    backgroundColor: step.color,
                                    color: 'white',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '18px',
                                    fontWeight: 'bold'
                                  }}>
                                    {index + 1}
                                  </div>
                                </div>
                              </Container>
                            ))}
                          </SpaceBetween>
                        )}
                        
                        <Alert type="success">
                          <SpaceBetween size="xs">
                            <Box fontWeight="bold">Expected Results:</Box>
                            <Box fontSize="body-s">
                              ✓ Blue banner confirms successful registration<br/>
                              ✓ Email notification with subscription details<br/>
                              ✓ Customer record created in DynamoDB
                            </Box>
                          </SpaceBetween>
                        </Alert>

                        <Box textAlign="center">
                          <Button 
                            variant="primary"
                            formAction="none"
                            onClick={async (e) => {
                              e.preventDefault(); // Prevent form submission
                              setLoading(true);
                              setError('');
                              
                              try {
                                console.log('[FRONTEND DEBUG] Complete Testing clicked');
                                console.log('[FRONTEND DEBUG] Current pricing model:', pricingModel?.value);
                                
                                // If pricing model is not available (e.g., used Continue button), fetch from CloudFormation
                                let currentPricingModel = pricingModel?.value;
                                
                                if (!currentPricingModel) {
                                  console.log('[FRONTEND DEBUG] Pricing model not available, fetching from CloudFormation stack...');
                                  try {
                                    const stackResponse = await axios.post('/api/get-stack-parameters', {
                                      stack_name: `saas-integration-${productId}`,
                                      region: region.value,
                                      credentials: {
                                        aws_access_key_id: accessKey,
                                        aws_secret_access_key: secretKey,
                                        aws_session_token: sessionToken || undefined,
                                      }
                                    });
                                    
                                    if (stackResponse.data.success) {
                                      currentPricingModel = stackResponse.data.pricing_model;
                                      console.log('[FRONTEND DEBUG] Fetched pricing model from stack:', currentPricingModel);
                                    }
                                  } catch (stackErr) {
                                    console.error('[FRONTEND DEBUG] Failed to fetch pricing model from stack:', stackErr);
                                  }
                                }
                                
                                // Route based on pricing model
                                console.log('[FRONTEND DEBUG] Routing based on pricing model:', currentPricingModel);
                                
                                if (currentPricingModel === 'contracts') {
                                  // Contract-based pricing -> Public Visibility
                                  console.log('[FRONTEND DEBUG] Contract-based pricing detected, showing public visibility guide');
                                  const visibilityResponse = await axios.post('/api/public-visibility-guide', {});
                                  if (visibilityResponse.data.success) {
                                    setVisibilitySteps(visibilityResponse.data.steps);
                                    setShowVisibilityGuide(true);
                                    setCurrentSubStep(3);
                                  }
                                } else if (currentPricingModel === 'subscriptions' || currentPricingModel === 'contracts_with_subscription') {
                                  // Usage-based or hybrid -> Metering
                                  console.log('[FRONTEND DEBUG] Usage-based pricing detected, showing metering guide');
                                  const meteringResponse = await axios.post('/api/metering-guide', {});
                                  if (meteringResponse.data.success) {
                                    setMeteringSteps(meteringResponse.data.steps);
                                    setShowMeteringGuide(true);
                                    setCurrentSubStep(3);
                                  }
                                } else {
                                  setError('Unable to determine pricing model. Please redeploy the stack.');
                                }
                              } catch (err: any) {
                                console.error('Failed to complete testing:', err);
                                setError(err.response?.data?.error || 'Failed to complete testing workflow');
                              } finally {
                                setLoading(false);
                              }
                            }}
                          >
                            Complete Testing - Proceed to Final Step →
                          </Button>
                        </Box>
                      </SpaceBetween>
                    </Container>
                  )}

                  {showMeteringGuide && (
                    <Alert 
                      type="info" 
                      header="📊 Metering Setup Guide"
                      action={
                        <Button variant="primary" onClick={() => router.push('/')}>
                          Finish →
                        </Button>
                      }
                    >
                      <SpaceBetween size="m">
                        <Box>
                          Your product uses usage-based pricing, which requires metering setup to track customer usage and bill accordingly.
                        </Box>
                        
                        {meteringSteps.map((step, index) => (
                          <Container key={index} header={<Header variant="h3">Step {step.step}: {step.title}</Header>}>
                            <SpaceBetween size="s">
                              <Box>{step.description}</Box>
                              <Box variant="h4">Actions:</Box>
                              <ul style={{ marginLeft: '20px' }}>
                                {step.actions?.map((action: string, idx: number) => (
                                  <li key={idx}><Box fontSize="body-s">{action}</Box></li>
                                ))}
                              </ul>
                              {step.expected && (
                                <>
                                  <Box variant="h4">Expected Outcomes:</Box>
                                  <ul style={{ marginLeft: '20px' }}>
                                    {step.expected.map((outcome: string, idx: number) => (
                                      <li key={idx}><Box fontSize="body-s" color="text-status-success">✓ {outcome}</Box></li>
                                    ))}
                                  </ul>
                                </>
                              )}
                            </SpaceBetween>
                          </Container>
                        ))}
                      </SpaceBetween>
                    </Alert>
                  )}

                  {showVisibilityGuide && (
                    <Alert 
                      type="info" 
                      header="🌐 Public Visibility Request Guide"
                      action={
                        <Button variant="primary" onClick={() => router.push('/')}>
                          Finish →
                        </Button>
                      }
                    >
                      <SpaceBetween size="m">
                        <Box>
                          Your product uses contract-based pricing. Follow these steps to request public visibility for your product.
                        </Box>
                        
                        {visibilitySteps.map((step, index) => (
                          <Container key={index} header={<Header variant="h3">Step {step.step}: {step.title}</Header>}>
                            <SpaceBetween size="s">
                              <Box>{step.description}</Box>
                              <Box variant="h4">Actions:</Box>
                              <ul style={{ marginLeft: '20px' }}>
                                {step.actions?.map((action: string, idx: number) => (
                                  <li key={idx}><Box fontSize="body-s">{action}</Box></li>
                                ))}
                              </ul>
                              {step.expected && (
                                <>
                                  <Box variant="h4">What to Expect:</Box>
                                  <ul style={{ marginLeft: '20px' }}>
                                    {step.expected.map((outcome: string, idx: number) => (
                                      <li key={idx}><Box fontSize="body-s" color="text-status-info">ℹ️ {outcome}</Box></li>
                                    ))}
                                  </ul>
                                </>
                              )}
                            </SpaceBetween>
                          </Container>
                        ))}
                      </SpaceBetween>
                    </Alert>
                  )}

                  {loading && (
                    <Container header={<Header variant="h2" description={`Elapsed: ${formatTime(elapsedTime)} | Status: ${cfStatus || 'Starting...'}`}>CloudFormation Deployment</Header>}>
                      <SpaceBetween size="l">
                        <Box textAlign="center"><Spinner size="large" /></Box>
                        <ProgressBar value={deploymentProgress} label="Deployment progress" description={cfStatus || 'Initializing CloudFormation...'} status="in-progress" additionalInfo={`${Math.round(deploymentProgress)}%`} />
                        
                        <SpaceBetween size="s">
                          {deploymentStages.map((stage, index) => (
                            <div key={index} className={`aws-progress-step ${stage.status}`} style={{ borderLeft: stage.status === 'completed' ? '4px solid #037f0c' : stage.status === 'in-progress' ? '4px solid #0073bb' : stage.status === 'error' ? '4px solid #d13212' : '4px solid #d5dbdb' }}>
                              <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                                <div style={{ minWidth: '24px' }}>
                                  {stage.status === 'completed' && <StatusIndicator type="success">✓</StatusIndicator>}
                                  {stage.status === 'in-progress' && <Spinner />}
                                  {stage.status === 'error' && <StatusIndicator type="error">✗</StatusIndicator>}
                                  {stage.status === 'pending' && <Box color="text-body-secondary">○</Box>}
                                </div>
                                <div style={{ flex: 1 }}>
                                  <Box fontWeight="bold">{stage.name}</Box>
                                  <Box fontSize="body-s" color="text-body-secondary">{stage.description}</Box>
                                  {stage.message && <Box fontSize="body-s" color={stage.status === 'error' ? 'text-status-error' : 'text-status-success'}>{stage.message}</Box>}
                                </div>
                              </div>
                            </div>
                          ))}
                        </SpaceBetween>

                        {cfEvents.length > 0 && (
                          <ExpandableSection headerText="Recent CloudFormation Events" variant="container">
                            <SpaceBetween size="xs">
                              {cfEvents.map((event, idx) => (
                                <Box key={idx} fontSize="body-s">
                                  <Box color={event.status.includes('FAILED') ? 'text-status-error' : event.status.includes('COMPLETE') ? 'text-status-success' : 'text-body-secondary'}>
                                    [{event.timestamp?.substring(11, 19)}] {event.logical_id}: {event.status}
                                    {event.reason && <Box color="text-status-error"> - {event.reason}</Box>}
                                  </Box>
                                </Box>
                              ))}
                            </SpaceBetween>
                          </ExpandableSection>
                        )}

                        <Box variant="p" textAlign="center" color="text-body-secondary">
                          Deploying CloudFormation stack... This may take 3-5 minutes.
                        </Box>
                      </SpaceBetween>
                    </Container>
                  )}

                  {!loading && (
                    <>
                      <Container header={<Header variant="h2">Product Information</Header>}>
                        <Box><Box variant="awsui-key-label">Product ID:</Box><Box>{productId}</Box></Box>
                      </Container>

                      <Container header={<Header variant="h2">Configuration</Header>}>
                        <SpaceBetween size="l">
                          <FormField 
                            label="Pricing Model" 
                            description="Select the pricing model for your SaaS product"
                            constraintText="Required"
                          >
                            <Select 
                              selectedOption={pricingModel} 
                              onChange={({ detail }) => setPricingModel(detail.selectedOption)} 
                              options={[
                                { label: 'Usage-based (Subscriptions)', value: 'subscriptions', description: 'Pay-as-you-go pricing model' },
                                { label: 'Contract-based (Contracts)', value: 'contracts', description: 'Fixed-term contract pricing' },
                                { label: 'Contract with Consumption', value: 'contracts_with_subscription', description: 'Hybrid pricing model' }
                              ]} 
                              placeholder="Select pricing model"
                              disabled={loading || success} 
                            />
                          </FormField>
                          <FormField label="Email for SNS Notifications" description="Receives AWS Marketplace notifications" constraintText="Required">
                            <Input value={email} onChange={({ detail }) => setEmail(detail.value)} placeholder="admin@yourcompany.com" type="email" disabled={loading || success} />
                          </FormField>
                          <FormField label="CloudFormation Stack Name" constraintText="Required">
                            <Input value={stackName} onChange={({ detail }) => setStackName(detail.value)} disabled={loading || success} />
                          </FormField>
                          <FormField label="AWS Region" description="Infrastructure deployment region">
                            <Select selectedOption={region} onChange={({ detail }) => setRegion(detail.selectedOption)} options={[{ label: 'us-east-1', value: 'us-east-1' }, { label: 'us-west-2', value: 'us-west-2' }, { label: 'eu-west-1', value: 'eu-west-1' }]} disabled={loading || success} />
                          </FormField>
                        </SpaceBetween>
                      </Container>

                      <Container header={<Header variant="h2">AWS Credentials</Header>}>
                        <SpaceBetween size="l">
                          <FormField label="AWS Access Key ID" constraintText="Required">
                            <Input value={accessKey} onChange={({ detail }) => setAccessKey(detail.value)} type="password" disabled={loading || success} />
                          </FormField>
                          <FormField label="AWS Secret Access Key" constraintText="Required">
                            <Input value={secretKey} onChange={({ detail }) => setSecretKey(detail.value)} type="password" disabled={loading || success} />
                          </FormField>
                          <FormField label="AWS Session Token" description="Optional for temporary credentials">
                            <Input value={sessionToken} onChange={({ detail }) => setSessionToken(detail.value)} type="password" disabled={loading || success} />
                          </FormField>
                        </SpaceBetween>
                      </Container>

                      <ExpandableSection headerText="Infrastructure Components" variant="container">
                        <SpaceBetween size="s">
                          <Box>CloudFormation will deploy:</Box>
                          <ul style={{ marginLeft: '20px' }}>
                            <li>🗄 DynamoDB tables for subscriptions and metering</li>
                            <li>λ Lambda function for usage metering</li>
                            <li>🔗 API Gateway for fulfillment</li>
                            <li>📧 SNS topic for notifications</li>
                            <li>🔐 IAM roles and policies</li>
                          </ul>
                        </SpaceBetween>
                      </ExpandableSection>
                    </>
                  )}
                </SpaceBetween>
              </Form>
            </form>
          </ContentLayout>
        }
      />
  );
}
