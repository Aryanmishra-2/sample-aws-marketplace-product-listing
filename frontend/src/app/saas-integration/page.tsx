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
}

const DEPLOYMENT_STAGES: DeploymentStage[] = [
  { name: 'Validating Parameters', description: 'Checking deployment configuration', status: 'pending' },
  { name: 'Creating Stack', description: 'Initiating CloudFormation stack creation', status: 'pending' },
  { name: 'Creating IAM Roles', description: 'Setting up IAM roles and policies', status: 'pending' },
  { name: 'Creating DynamoDB Tables', description: 'Creating subscription and metering tables', status: 'pending' },
  { name: 'Creating Lambda Functions', description: 'Deploying metering Lambda function', status: 'pending' },
  { name: 'Creating API Gateway', description: 'Setting up fulfillment API', status: 'pending' },
  { name: 'Creating SNS Topic', description: 'Configuring notification topic', status: 'pending' },
  { name: 'Finalizing Stack', description: 'Completing stack creation', status: 'pending' },
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
  const [deploymentStages, setDeploymentStages] = useState<DeploymentStage[]>(DEPLOYMENT_STAGES);
  const [currentStageIndex, setCurrentStageIndex] = useState(-1);
  const [deploymentProgress, setDeploymentProgress] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime, setStartTime] = useState<number | null>(null);

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

  const updateStageStatus = (index: number, status: DeploymentStage['status'], message?: string) => {
    setDeploymentStages(prev => {
      const newStages = [...prev];
      newStages[index] = {
        ...newStages[index],
        status,
        message,
      };
      return newStages;
    });
  };

  const handleDeploy = async () => {
    if (!email || !stackName || !accessKey || !secretKey) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError('');
    setStartTime(Date.now());
    setDeploymentStages(DEPLOYMENT_STAGES.map(s => ({ ...s, status: 'pending' as const })));

    try {
      for (let i = 0; i < DEPLOYMENT_STAGES.length; i++) {
        setCurrentStageIndex(i);
        updateStageStatus(i, 'in-progress');
        setDeploymentProgress((i / DEPLOYMENT_STAGES.length) * 90);

        await new Promise((resolve) => setTimeout(resolve, 600));
        
        updateStageStatus(i, 'completed', '✓ Complete');
      }

      setDeploymentProgress(95);

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

      setDeploymentProgress(100);
      setSuccess(true);
      setDeployedStackId(response.data.stack_id);
      setStackId(response.data.stack_id);
    } catch (err: any) {
      console.error('Deployment error:', err);
      setError(err.response?.data?.error || err.message || 'Failed to deploy SaaS integration');
      if (currentStageIndex >= 0 && currentStageIndex < deploymentStages.length) {
        updateStageStatus(currentStageIndex, 'error', '✗ Failed');
      }
    } finally {
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
                        <Box>📧 Check your email to confirm SNS subscription.</Box>
                        <Box color="text-body-secondary">Time: {formatTime(elapsedTime)}</Box>
                      </SpaceBetween>
                    </Alert>
                  )}

                  {loading && (
                    <Container header={<Header variant="h2" description={`Elapsed: ${formatTime(elapsedTime)}`}>Deployment Progress</Header>}>
                      <SpaceBetween size="l">
                        <Box textAlign="center"><Spinner size="large" /></Box>
                        <ProgressBar value={deploymentProgress} label="CloudFormation deployment" description={currentStageIndex >= 0 && currentStageIndex < deploymentStages.length ? deploymentStages[currentStageIndex].name : 'Initializing...'} status="in-progress" additionalInfo={`${Math.round(deploymentProgress)}%`} />
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
                        <Box variant="p" textAlign="center" color="text-body-secondary">Deploying CloudFormation stack... This may take 3-5 minutes.</Box>
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
