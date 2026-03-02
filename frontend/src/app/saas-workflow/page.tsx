'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  AppLayout,
  Container,
  Header,
  SpaceBetween,
  Button,
  Alert,
  ContentLayout,
  BreadcrumbGroup,
  Box,
  Spinner,
  StatusIndicator,
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';
import WorkflowNav from '@/components/WorkflowNav';
import axios from 'axios';

export default function SaaSWorkflowPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, productId: storeProductId, credentials } = useStore();
  
  const urlProductId = searchParams.get('productId');
  const productId = urlProductId || storeProductId;
  const stackName = searchParams.get('stackName') || `saas-integration-${productId}`;
  const pricingModelParam = searchParams.get('pricingModel');

  const [accessKey, setAccessKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [sessionToken, setSessionToken] = useState('');
  const [email, setEmail] = useState('');
  const [region, setRegion] = useState('us-east-1');
  const [pricingModel, setPricingModel] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [currentStep, setCurrentStep] = useState(0); // 0: SNS, 1: Buyer Experience, 2: Complete
  const [buyerSteps, setBuyerSteps] = useState<any[]>([]);
  const [meteringSteps, setMeteringSteps] = useState<any[]>([]);
  const [showFinalGuide, setShowFinalGuide] = useState(false);

  useEffect(() => {
    if (!isAuthenticated || !productId) {
      router.push('/');
      return;
    }

    if (credentials) {
      setAccessKey(credentials.aws_access_key_id || '');
      setSecretKey(credentials.aws_secret_access_key || '');
      setSessionToken(credentials.aws_session_token || '');
    }

    // Initialize pricing model from URL or localStorage
    if (pricingModelParam) {
      console.log('[WORKFLOW] Using pricing model from URL:', pricingModelParam);
      setPricingModel(pricingModelParam);
    } else {
      // Try to get from localStorage
      try {
        const listingData = localStorage.getItem(`listing_data_${productId}`);
        if (listingData) {
          const parsed = JSON.parse(listingData);
          if (parsed.pricing_model) {
            console.log('[WORKFLOW] Using pricing model from localStorage:', parsed.pricing_model);
            setPricingModel(parsed.pricing_model);
          }
        }
      } catch (e) {
        console.error('[WORKFLOW] Failed to read pricing model from localStorage:', e);
      }
    }

    // Fetch buyer experience steps
    fetchBuyerSteps();
  }, [isAuthenticated, productId, credentials, router, pricingModelParam]);

  const fetchBuyerSteps = async () => {
    try {
      const response = await axios.post('/api/buyer-experience-guide', {});
      console.log('[WORKFLOW DEBUG] Buyer steps response:', response.data);
      if (response.data.success && response.data.guide?.steps) {
        // Transform steps to include icons and colors
        const transformedSteps = response.data.guide.steps.map((step: any, index: number) => ({
          ...step,
          icon: ['🌐', '✅', '📝', '🛒', '⚙️', '💳', '👤', '📝', '🎉'][index] || '📋',
          color: ['#0073bb', '#037f0c', '#ff9900', '#ec7211', '#232f3e', '#16191f', '#0073bb', '#037f0c', '#ff9900'][index] || '#545b64'
        }));
        console.log('[WORKFLOW DEBUG] Transformed buyer steps:', transformedSteps);
        setBuyerSteps(transformedSteps);
      }
    } catch (err) {
      console.error('Failed to fetch buyer steps:', err);
    }
  };

  const handleSnsComplete = () => {
    setCurrentStep(1);
  };

  const handleBuyerExperienceComplete = () => {
    setCurrentStep(2);
  };



  const handleCompleteTesting = async () => {
    setLoading(true);
    setError('');
    setShowFinalGuide(false); // Reset
    setMeteringSteps([]); // Clear previous steps
    
    try {
      console.log('[WORKFLOW DEBUG] Complete Testing with pricing model:', pricingModel);
      console.log('[WORKFLOW DEBUG] Product ID:', productId);
      console.log('[WORKFLOW DEBUG] Stack Name:', stackName);
      
      // Use pricing model from state (already loaded from URL or localStorage)
      let currentPricingModel = pricingModel;
      
      // If still not available, try localStorage one more time
      if (!currentPricingModel) {
        console.log('[WORKFLOW DEBUG] Pricing model not in state, checking localStorage...');
        try {
          const listingData = localStorage.getItem(`listing_data_${productId}`);
          if (listingData) {
            const parsed = JSON.parse(listingData);
            currentPricingModel = parsed.pricing_model;
            console.log('[WORKFLOW DEBUG] Found pricing model in localStorage:', currentPricingModel);
            setPricingModel(currentPricingModel);
          }
        } catch (e) {
          console.error('[WORKFLOW DEBUG] Failed to read from localStorage:', e);
        }
      }
      
      // Last resort: fetch from CloudFormation stack
      if (!currentPricingModel) {
        console.log('[WORKFLOW DEBUG] Fetching pricing model from CloudFormation stack...');
        const stackResponse = await axios.post('/api/get-stack-parameters', {
          stack_name: stackName,
          region: region,
          credentials: {
            aws_access_key_id: accessKey,
            aws_secret_access_key: secretKey,
            aws_session_token: sessionToken || undefined,
          }
        });
        
        console.log('[WORKFLOW DEBUG] Stack parameters response:', stackResponse.data);
        
        if (stackResponse.data.success) {
          currentPricingModel = stackResponse.data.pricing_model;
          setPricingModel(currentPricingModel);
          console.log('[WORKFLOW DEBUG] Fetched pricing model:', currentPricingModel);
        } else {
          throw new Error('Failed to fetch pricing model from stack');
        }
      }
      
      console.log('[WORKFLOW DEBUG] Using pricing model:', currentPricingModel);
      
      // Route based on pricing model
      if (currentPricingModel === 'contracts') {
        // Contract-based -> Public Visibility
        console.log('[WORKFLOW DEBUG] Contract-based pricing - fetching public visibility guide');
        const visibilityResponse = await axios.post('/api/public-visibility-guide', {});
        console.log('[WORKFLOW DEBUG] Visibility response:', visibilityResponse.data);
        
        if (visibilityResponse.data.success) {
          // For contract-based pricing, navigate to public visibility page
          router.push(`/public-visibility?productId=${productId}&stackName=${stackName}&pricingModel=${currentPricingModel}`);
        }
      } else if (currentPricingModel === 'subscriptions' || currentPricingModel === 'contracts_with_subscription') {
        // Usage-based or hybrid -> Run Metering Agent
        console.log('[WORKFLOW DEBUG] Usage-based pricing - running metering agent...');
        console.log('[WORKFLOW DEBUG] Calling /api/run-metering with product_id:', productId);
        console.log('[WORKFLOW DEBUG] [DEBUG] Product ID:', productId);
        console.log('[WORKFLOW DEBUG] [DEBUG] Has credentials:', {
          accessKey: !!accessKey,
          secretKey: !!secretKey,
          sessionToken: !!sessionToken
        });
        
        // Try to get pricing dimensions from localStorage (from create listing process)
        let storedPricingDimensions = null;
        try {
          const listingData = localStorage.getItem(`listing_data_${productId}`);
          if (listingData) {
            const parsed = JSON.parse(listingData);
            storedPricingDimensions = parsed.pricing_dimensions;
            console.log('[WORKFLOW DEBUG] Found stored pricing dimensions:', storedPricingDimensions);
          }
        } catch (e) {
          console.log('[WORKFLOW DEBUG] No stored pricing dimensions found');
        }

        const meteringResponse = await axios.post('/api/run-metering', {
          product_id: productId,
          credentials: {
            aws_access_key_id: accessKey,
            aws_secret_access_key: secretKey,
            aws_session_token: sessionToken || undefined,
          },
          pricing_dimensions: storedPricingDimensions || undefined
        });
        
        console.log('[WORKFLOW DEBUG] Metering response:', meteringResponse.data);
        console.log('[WORKFLOW DEBUG] [DEBUG] Response success:', meteringResponse.data.success);
        console.log('[WORKFLOW DEBUG] [DEBUG] Response error:', meteringResponse.data.error);
        console.log('[WORKFLOW DEBUG] Metering steps:', meteringResponse.data.steps);
        console.log('[WORKFLOW DEBUG] [DEBUG] Steps count:', meteringResponse.data.steps?.length);
        
        if (meteringResponse.data.steps && meteringResponse.data.steps.length > 0) {
          setMeteringSteps(meteringResponse.data.steps);
          setShowFinalGuide(true);
          
          // Metering successful - user can proceed to public visibility when ready
        } else {
          console.error('[WORKFLOW ERROR] No metering steps returned');
        }
        
        if (!meteringResponse.data.success) {
          setError(meteringResponse.data.error || 'Metering agent failed');
        }
      } else {
        setError('Unable to determine pricing model: ' + currentPricingModel);
      }
    } catch (err: any) {
      console.error('[WORKFLOW ERROR] Failed to complete testing:', err);
      console.error('[WORKFLOW ERROR] Error details:', err.response?.data);
      setError(err.response?.data?.error || err.message || 'Failed to complete testing workflow');
    } finally {
      setLoading(false);
    }
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
            { text: 'SaaS Integration', href: '/saas-integration' },
            { text: 'Workflow', href: '/saas-workflow' },
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
              description="Complete the SaaS integration workflow"
            >
              SaaS Integration Workflow
            </Header>
          }
        >
          <SpaceBetween size="l">
            {error && <Alert type="error" dismissible onDismiss={() => setError('')}>{error}</Alert>}

            {/* Step 1: SNS Confirmation */}
            {currentStep === 0 && (
              <Container
                header={
                  <Header
                    variant="h2"
                    description="Step 1 of 3: Enable marketplace notifications"
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
                      { icon: '📬', title: 'Open your email inbox', desc: 'Check the email address you provided during deployment' },
                      { icon: '🔍', title: 'Find the AWS Notification email', desc: 'Look for "AWS Notification - Subscription Confirmation"' },
                      { icon: '✅', title: 'Click "Confirm subscription"', desc: 'This will open a browser page confirming your subscription' },
                    ].map((step, index) => (
                      <Container key={index}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                          <div style={{ fontSize: '36px', minWidth: '56px', textAlign: 'center' }}>{step.icon}</div>
                          <div style={{ flex: 1 }}>
                            <Box variant="h3" color="text-label">{step.title}</Box>
                            <Box fontSize="body-m" color="text-body-secondary" padding={{ top: 'xs' }}>{step.desc}</Box>
                          </div>
                        </div>
                      </Container>
                    ))}
                  </SpaceBetween>

                  <Box textAlign="center">
                    <Button variant="primary" onClick={handleSnsComplete}>
                      SNS Confirmed - Continue to Buyer Experience →
                    </Button>
                  </Box>
                </SpaceBetween>
              </Container>
            )}

            {/* Step 2: Buyer Experience */}
            {currentStep === 1 && (
              <Container
                header={
                  <Header
                    variant="h2"
                    description="Step 2 of 3: Test the customer purchase flow"
                  >
                    🛒 Buyer Experience Testing
                  </Header>
                }
              >
                <SpaceBetween size="l">
                  <Alert type="info">
                    <Box fontWeight="bold">Test your product as a customer would experience it</Box>
                  </Alert>

                  {buyerSteps.length === 0 && (
                    <Alert 
                      type="warning"
                      action={
                        <Button onClick={fetchBuyerSteps}>Retry</Button>
                      }
                    >
                      <Box>Loading buyer experience steps... If steps don't appear, click Retry.</Box>
                    </Alert>
                  )}

                  {buyerSteps.length > 0 && (
                    <SpaceBetween size="m">
                      {buyerSteps.map((step: any, index: number) => (
                        <Container key={index}>
                          <SpaceBetween size="m">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                              <div style={{ fontSize: '36px', minWidth: '56px', textAlign: 'center' }}>{step.icon}</div>
                              <div style={{ flex: 1 }}>
                                <Box variant="h3" color="text-label">Step {step.step}: {step.title}</Box>
                                <Box fontSize="body-m" color="text-body-secondary" padding={{ top: 'xs' }}>{step.description}</Box>
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
                                {step.step}
                              </div>
                            </div>
                            {step.actions && step.actions.length > 0 && (
                              <Box padding={{ left: 'xxl' }}>
                                <SpaceBetween size="xs">
                                  {step.actions.map((action: string, actionIndex: number) => (
                                    <Box key={actionIndex} fontSize="body-s" color="text-body-secondary">
                                      • {action}
                                    </Box>
                                  ))}
                                </SpaceBetween>
                              </Box>
                            )}
                            {step.expected && step.expected.length > 0 && (
                              <Box padding={{ left: 'xxl' }}>
                                <Box fontWeight="bold" fontSize="body-s" padding={{ bottom: 'xs' }}>Expected Results:</Box>
                                <SpaceBetween size="xs">
                                  {step.expected.map((result: string, resultIndex: number) => (
                                    <Box key={resultIndex} fontSize="body-s" color="text-status-success">
                                      ✓ {result}
                                    </Box>
                                  ))}
                                </SpaceBetween>
                              </Box>
                            )}
                          </SpaceBetween>
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
                    <Button variant="primary" onClick={handleBuyerExperienceComplete}>
                      Buyer Experience Complete - Proceed to Final Step →
                    </Button>
                  </Box>
                </SpaceBetween>
              </Container>
            )}

            {/* Step 3: Complete Testing */}
            {currentStep === 2 && !showFinalGuide && (
              <Container
                header={
                  <Header
                    variant="h2"
                    description="Step 3 of 3: Finalize your integration"
                  >
                    ✅ Complete Testing
                  </Header>
                }
              >
                <SpaceBetween size="l">
                  {!loading && (
                    <>
                      <Alert type="success">
                        <Box fontWeight="bold">You've completed the buyer experience testing!</Box>
                      </Alert>

                      <Box>
                        Click below to proceed to the final configuration step based on your pricing model.
                      </Box>
                    </>
                  )}

                  {loading && (
                    <Alert type="info">
                      <SpaceBetween size="m" alignItems="center">
                        <Box textAlign="center">
                          <Spinner size="large" />
                        </Box>
                        <Box textAlign="center" fontWeight="bold">
                          Processing metering workflow...
                        </Box>
                        <Box textAlign="center" fontSize="body-s" color="text-body-secondary">
                          This may take a minute. The metering agent is checking entitlements, creating records, and triggering Lambda functions.
                        </Box>
                      </SpaceBetween>
                    </Alert>
                  )}

                  <Box textAlign="center">
                    <Button 
                      variant="primary" 
                      onClick={handleCompleteTesting}
                      loading={loading}
                      disabled={loading}
                    >
                      {loading ? 'Processing...' : 'Complete Testing - View Final Steps →'}
                    </Button>
                  </Box>
                </SpaceBetween>
              </Container>
            )}

            {/* Final Guide: Metering or Public Visibility */}
            {showFinalGuide && meteringSteps.length > 0 && (
              <Container
                header={
                  <Header
                    variant="h2"
                    description="Metering agent execution progress with detailed substeps"
                    actions={
                      <Button variant="primary" onClick={() => router.push('/')}>
                        Finish →
                      </Button>
                    }
                  >
                    📊 Metering Workflow
                  </Header>
                }
              >
                <SpaceBetween size="l">
                  <Alert type="success">
                    <Box fontWeight="bold">Metering Agent with Strands Framework</Box>
                    <Box fontSize="body-s" padding={{ top: 'xs' }}>
                      The MeteringAgent uses the strands framework to orchestrate the metering workflow with detailed step-by-step progress tracking.
                    </Box>
                  </Alert>

                  {meteringSteps.map((step: any, index: number) => (
                    <Container key={index}>
                      <SpaceBetween size="m">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                          <div style={{ fontSize: '32px', minWidth: '48px', textAlign: 'center' }}>
                            {step.status === 'completed' && '✅'}
                            {step.status === 'failed' && '❌'}
                            {step.status === 'warning' && '⚠️'}
                            {step.status === 'skipped' && '⊘'}
                            {step.status === 'in_progress' && '⏳'}
                          </div>
                          <div style={{ flex: 1 }}>
                            <Box variant="h3" color="text-label">
                              Step {step.step}: {step.name}
                            </Box>
                            {step.status === 'completed' && (
                              <StatusIndicator type="success">Completed</StatusIndicator>
                            )}
                            {step.status === 'failed' && (
                              <StatusIndicator type="error">Failed</StatusIndicator>
                            )}
                            {step.status === 'warning' && (
                              <StatusIndicator type="warning">Warning</StatusIndicator>
                            )}
                            {step.status === 'skipped' && (
                              <StatusIndicator type="info">Skipped</StatusIndicator>
                            )}
                            {step.status === 'in_progress' && (
                              <StatusIndicator type="in-progress">In Progress</StatusIndicator>
                            )}
                          </div>
                        </div>
                        
                        {/* Display substeps if available */}
                        {step.substeps && step.substeps.length > 0 && (
                          <Box padding={{ left: 'xxl' }}>
                            <Box fontWeight="bold" fontSize="body-s" padding={{ bottom: 'xs' }}>Substeps:</Box>
                            <SpaceBetween size="xs">
                              {step.substeps.map((substep: any, subIndex: number) => (
                                <div key={subIndex} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <div style={{ fontSize: '16px', minWidth: '24px' }}>
                                    {substep.status === 'completed' && '✓'}
                                    {substep.status === 'failed' && '✗'}
                                    {substep.status === 'in_progress' && '⏳'}
                                    {substep.status === 'pending' && '○'}
                                  </div>
                                  <Box 
                                    fontSize="body-s" 
                                    color={
                                      substep.status === 'completed' ? 'text-status-success' :
                                      substep.status === 'failed' ? 'text-status-error' :
                                      substep.status === 'in_progress' ? 'text-status-info' :
                                      'text-body-secondary'
                                    }
                                  >
                                    {substep.name}
                                  </Box>
                                </div>
                              ))}
                            </SpaceBetween>
                          </Box>
                        )}
                        
                        {step.message && (
                          <Alert type="info">
                            <Box fontSize="body-s">{step.message}</Box>
                          </Alert>
                        )}
                        
                        {step.reason && (
                          <Alert type="info">
                            <Box fontSize="body-s"><strong>Reason:</strong> {step.reason}</Box>
                          </Alert>
                        )}
                        
                        {step.error && (
                          <Alert type="error">
                            <Box fontSize="body-s">{step.error}</Box>
                          </Alert>
                        )}
                        
                        {/* Display key details */}
                        {(step.customer_identifier || step.pricing_model || step.usage_dimensions) && (
                          <Box padding={{ left: 'xxl' }}>
                            <Box fontWeight="bold" fontSize="body-s" padding={{ bottom: 'xs' }}>Details:</Box>
                            <SpaceBetween size="xxs">
                              {step.customer_identifier && (
                                <Box fontSize="body-s" color="text-body-secondary">
                                  • Customer: {step.customer_identifier}
                                </Box>
                              )}
                              {step.pricing_model && (
                                <Box fontSize="body-s" color="text-body-secondary">
                                  • Pricing Model: {step.pricing_model}
                                </Box>
                              )}
                              {step.timestamp && (
                                <Box fontSize="body-s" color="text-body-secondary">
                                  • Timestamp: {step.timestamp}
                                </Box>
                              )}
                              {step.subscribers_table && (
                                <Box fontSize="body-s" color="text-body-secondary">
                                  • Subscribers Table: {step.subscribers_table}
                                </Box>
                              )}
                              {step.metering_table && (
                                <Box fontSize="body-s" color="text-body-secondary">
                                  • Metering Table: {step.metering_table}
                                </Box>
                              )}
                              {step.usage_dimensions && (
                                <Box fontSize="body-s" color="text-body-secondary">
                                  • Usage Dimensions: {Array.isArray(step.usage_dimensions) ? step.usage_dimensions.join(', ') : step.usage_dimensions}
                                </Box>
                              )}
                            </SpaceBetween>
                          </Box>
                        )}
                        
                        {step.lambda_function && (
                          <Box padding={{ left: 'xxl' }}>
                            <Box fontSize="body-s" color="text-body-secondary">
                              <strong>Lambda Function:</strong> {step.lambda_function}
                            </Box>
                            {step.lambda_result && (
                              <Box fontSize="body-s" color="text-body-secondary" padding={{ top: 'xxs' }}>
                                <strong>Status:</strong> {step.lambda_result.status || 'N/A'}
                              </Box>
                            )}
                          </Box>
                        )}
                      </SpaceBetween>
                    </Container>
                  ))}
                </SpaceBetween>

                {/* Add button to proceed to public visibility after successful metering */}
                {meteringSteps.some((step: any) => step.status === 'completed') && (
                  <Container>
                    <SpaceBetween size="m">
                      <Alert type="success">
                        <Box fontWeight="bold">Metering Integration Complete!</Box>
                        <Box fontSize="body-s" padding={{ top: 'xs' }}>
                          Your SaaS integration and metering are working correctly. You can now proceed to make your product publicly available on AWS Marketplace.
                        </Box>
                      </Alert>
                      
                      <Box textAlign="center">
                        <Button 
                          variant="primary"
                          onClick={() => {
                            router.push(`/public-visibility?productId=${productId}&stackName=${stackName}&pricingModel=${pricingModel}`);
                          }}
                        >
                          Proceed to Public Visibility Steps →
                        </Button>
                      </Box>
                    </SpaceBetween>
                  </Container>
                )}
              </Container>
            )}


          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}
