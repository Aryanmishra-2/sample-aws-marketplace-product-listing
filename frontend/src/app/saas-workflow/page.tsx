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
  const [pricingModel, setPricingModel] = useState(pricingModelParam || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [currentStep, setCurrentStep] = useState(0); // 0: SNS, 1: Buyer Experience, 2: Complete
  const [buyerSteps, setBuyerSteps] = useState<any[]>([]);
  const [meteringSteps, setMeteringSteps] = useState<any[]>([]);
  const [visibilitySteps, setVisibilitySteps] = useState<any[]>([]);
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

    // Fetch buyer experience steps
    fetchBuyerSteps();
  }, [isAuthenticated, productId, credentials, router]);

  const fetchBuyerSteps = async () => {
    try {
      const response = await axios.post('/api/buyer-experience-guide', {});
      console.log('[WORKFLOW DEBUG] Buyer steps response:', response.data);
      if (response.data.success) {
        // Transform steps to include icons and colors
        const transformedSteps = response.data.steps.map((step: any, index: number) => ({
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
    
    try {
      console.log('[WORKFLOW DEBUG] Complete Testing with pricing model:', pricingModel);
      
      // If pricing model not available, fetch from stack
      let currentPricingModel = pricingModel;
      
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
        
        if (stackResponse.data.success) {
          currentPricingModel = stackResponse.data.pricing_model;
          setPricingModel(currentPricingModel);
          console.log('[WORKFLOW DEBUG] Fetched pricing model:', currentPricingModel);
        }
      }
      
      // Route based on pricing model
      if (currentPricingModel === 'contracts') {
        // Contract-based -> Public Visibility
        const visibilityResponse = await axios.post('/api/public-visibility-guide', {});
        if (visibilityResponse.data.success) {
          setVisibilitySteps(visibilityResponse.data.steps);
          setShowFinalGuide(true);
        }
      } else if (currentPricingModel === 'subscriptions' || currentPricingModel === 'contracts_with_subscription') {
        // Usage-based or hybrid -> Metering
        const meteringResponse = await axios.post('/api/metering-guide', {});
        if (meteringResponse.data.success) {
          setMeteringSteps(meteringResponse.data.steps);
          setShowFinalGuide(true);
        }
      } else {
        setError('Unable to determine pricing model');
      }
    } catch (err: any) {
      console.error('Failed to complete testing:', err);
      setError(err.response?.data?.error || 'Failed to complete testing workflow');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated || !productId) {
    return null;
  }

  return (
    <AppLayout
      navigation={<WorkflowNav currentSubStep={1} />}
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
                  <Alert type="success">
                    <Box fontWeight="bold">You've completed the buyer experience testing!</Box>
                  </Alert>

                  <Box>
                    Click below to proceed to the final configuration step based on your pricing model.
                  </Box>

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
                    description="Configure metering for usage-based pricing"
                    actions={
                      <Button variant="primary" onClick={() => router.push('/')}>
                        Finish →
                      </Button>
                    }
                  >
                    📊 Metering Setup Guide
                  </Header>
                }
              >
                <SpaceBetween size="l">
                  <Alert type="info">
                    Your product uses usage-based pricing, which requires metering setup to track customer usage and bill accordingly.
                  </Alert>
                  <SpaceBetween size="m">
                    {meteringSteps.map((step: any, index: number) => (
                      <Container key={index}>
                        <SpaceBetween size="m">
                          <Box variant="h3" color="text-label">Step {step.step}: {step.title}</Box>
                          <Box fontSize="body-m" color="text-body-secondary">{step.description}</Box>
                          {step.actions && step.actions.length > 0 && (
                            <SpaceBetween size="xs">
                              {step.actions.map((action: string, actionIndex: number) => (
                                <Box key={actionIndex} fontSize="body-s" color="text-body-secondary">
                                  • {action}
                                </Box>
                              ))}
                            </SpaceBetween>
                          )}
                          {step.expected && step.expected.length > 0 && (
                            <Box>
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
                </SpaceBetween>
              </Container>
            )}

            {showFinalGuide && visibilitySteps.length > 0 && (
              <Container
                header={
                  <Header
                    variant="h2"
                    description="Make your product publicly available"
                    actions={
                      <Button variant="primary" onClick={() => router.push('/')}>
                        Finish →
                      </Button>
                    }
                  >
                    🌐 Public Visibility Request
                  </Header>
                }
              >
                <SpaceBetween size="l">
                  <Alert type="info">
                    Your product uses contract-based pricing. Submit a public visibility request to make your product available to all AWS customers.
                  </Alert>
                  <SpaceBetween size="m">
                    {visibilitySteps.map((step: any, index: number) => (
                      <Container key={index}>
                        <SpaceBetween size="m">
                          <Box variant="h3" color="text-label">Step {step.step}: {step.title}</Box>
                          <Box fontSize="body-m" color="text-body-secondary">{step.description}</Box>
                          {step.actions && step.actions.length > 0 && (
                            <SpaceBetween size="xs">
                              {step.actions.map((action: string, actionIndex: number) => (
                                <Box key={actionIndex} fontSize="body-s" color="text-body-secondary">
                                  • {action}
                                </Box>
                              ))}
                            </SpaceBetween>
                          )}
                          {step.expected && step.expected.length > 0 && (
                            <Box>
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
                </SpaceBetween>
              </Container>
            )}
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}
