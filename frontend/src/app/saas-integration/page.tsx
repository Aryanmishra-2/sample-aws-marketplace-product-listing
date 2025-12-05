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
  }, [isAuthenticated, productId, credentials, router, urlProductId, storeProductId, setProductId]);

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

  const handleDeploy = async () => {
    if (!email || !stackName || !accessKey || !secretKey) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError('');
    setStartTime(Date.now());
    setDeploymentStages(INITIAL_STAGES.map(s => ({ ...s, status: 'pending' as const })));
    
    // The backend uses this stack name format: saas-integration-{product_id}
    const actualStackName = `saas-integration-${productId}`;
    setDeployedStackName(actualStackName);

    try {
      // Get pricing model from listingData (ui_pricing_model has the full value)
      const pricingModel = listingData?.ui_pricing_model || listingData?.pricing_model || 'Usage';
      
      const response = await axios.post('/api/deploy-saas', {
        product_id: productId,
        email,
        stack_name: stackName,
        region: region.value,
        pricing_model: pricingModel,
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
      }
      
      // Otherwise, polling will continue via useEffect
    } catch (err: any) {
      console.error('Deployment error:', err);
      setError(err.response?.data?.error || err.message || 'Failed to deploy SaaS integration');
      setLoading(false);
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
                    {success && <Button variant="primary" onClick={() => router.push('/')}>Continue →</Button>}
                    {!success && <Button variant="primary" onClick={handleDeploy} loading={loading} disabled={loading}>Deploy Stack 🚀</Button>}
                  </SpaceBetween>
                }
              >
                <SpaceBetween size="l">
                  {error && <Alert type="error" dismissible onDismiss={() => setError('')}>{error}</Alert>}

                  {success && (
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
                          <li>
                            <Box fontWeight="bold">Confirm SNS Subscription</Box>
                            <Box fontSize="body-s" color="text-body-secondary">
                              📧 Check your email ({email}) and confirm the SNS subscription to receive marketplace notifications
                            </Box>
                          </li>
                          <li>
                            <Box fontWeight="bold">Test the Integration</Box>
                            <Box fontSize="body-s" color="text-body-secondary">
                              Test the buyer experience by subscribing to your product from a test account
                            </Box>
                          </li>
                        </ol>
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
