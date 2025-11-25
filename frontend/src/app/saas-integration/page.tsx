'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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
import GlobalHeader from '@/components/GlobalHeader';
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
  const { isAuthenticated, productId, credentials, setStackId, setCurrentStep } = useStore();

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

    setStackName(`marketplace-saas-${productId.substring(0, 8)}`);

    if (credentials) {
      setAccessKey(credentials.aws_access_key_id || '');
      setSecretKey(credentials.aws_secret_access_key || '');
      setSessionToken(credentials.aws_session_token || '');
    }
  }, [isAuthenticated, productId, credentials, router]);

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
      const pollInterval = setInterval(async () => {
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
            }
          } else {
            // Handle API error
            console.error('Stack status check failed:', response.data.error);
            if (response.data.stack_status === 'NOT_FOUND') {
              // Stack might not be created yet, continue polling
              setCfStatus('CREATING...');
            }
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
    
    // Track which resources have been seen
    const seenResources = new Set<string>();
    
    events.forEach(event => {
      const resourceType = event.resource_type;
      const status = event.status;
      const logicalId = event.logical_id;
      
      seenResources.add(resourceType);
      
      // Find matching stage
      const stageIndex = newStages.findIndex(s => s.resourceType === resourceType);
      if (stageIndex >= 0) {
        if (status.includes('COMPLETE')) {
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

    // Calculate progress
    const completed = newStages.filter(s => s.status === 'completed').length;
    const inProgress = newStages.filter(s => s.status === 'in-progress').length;
    const progress = ((completed + (inProgress * 0.5)) / newStages.length) * 100;
    
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
    setDeployedStackName(stackName);

    try {
      const response = await axios.post('/api/deploy-saas', {
        product_id: productId,
        email,
        stack_name: stackName,
        region: region.value,
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
      
      // Polling will continue via useEffect
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
    <>
      <GlobalHeader />
      <AppLayout
        navigationHide
        toolsHide
        breadcrumbs={
          <BreadcrumbGroup
            items={[
              { text: 'Home', href: '/' },
              { text: 'Welcome', href: '/welcome' },
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
                    <Alert type="success" header="Deployment Successful!">
                      <SpaceBetween size="s">
                        <Box>SaaS integration infrastructure deployed successfully!</Box>
                        <Box><strong>Stack ID:</strong> {deployedStackId}</Box>
                        <Box><strong>Stack Name:</strong> {deployedStackName}</Box>
                        <Box>📧 Check your email to confirm SNS subscription.</Box>
                        <Box color="text-body-secondary">Time: {formatTime(elapsedTime)}</Box>
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
    </>
  );
}
