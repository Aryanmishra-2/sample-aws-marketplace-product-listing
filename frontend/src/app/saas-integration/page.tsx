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
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';
import axios from 'axios';

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

  useEffect(() => {
    if (!isAuthenticated || !productId) {
      router.push('/');
      return;
    }

    // Pre-fill stack name
    setStackName(`marketplace-saas-${productId.substring(0, 8)}`);

    // Pre-fill credentials if available
    if (credentials) {
      setAccessKey(credentials.aws_access_key_id || '');
      setSecretKey(credentials.aws_secret_access_key || '');
      setSessionToken(credentials.aws_session_token || '');
    }
  }, [isAuthenticated, productId, credentials, router]);

  const handleDeploy = async () => {
    if (!email || !stackName || !accessKey || !secretKey) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError('');

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

      setSuccess(true);
      setDeployedStackId(response.data.stack_id);
      setStackId(response.data.stack_id);
    } catch (err: any) {
      console.error('Deployment error:', err);
      setError(err.response?.data?.error || err.message || 'Failed to deploy SaaS integration');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    router.push('/listing-success');
  };

  const handleContinue = () => {
    setCurrentStep('workflow_orchestrator');
    router.push('/workflow-orchestrator');
  };

  if (!isAuthenticated || !productId) {
    return null;
  }

  return (
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
                  <Button onClick={handleBack}>
                    ← Back
                  </Button>
                  {success && (
                    <Button variant="primary" onClick={handleContinue}>
                      Continue to Full Workflow →
                    </Button>
                  )}
                  {!success && (
                    <Button
                      variant="primary"
                      onClick={handleDeploy}
                      loading={loading}
                    >
                      Deploy CloudFormation Stack 🚀
                    </Button>
                  )}
                </SpaceBetween>
              }
            >
              <SpaceBetween size="l">
                {error && (
                  <Alert type="error" dismissible onDismiss={() => setError('')}>
                    {error}
                  </Alert>
                )}

                {success && (
                  <Alert type="success" header="Deployment Successful!">
                    <SpaceBetween size="s">
                      <Box>
                        Your SaaS integration infrastructure has been deployed successfully!
                      </Box>
                      <Box>
                        <strong>Stack ID:</strong> {deployedStackId}
                      </Box>
                      <Box>
                        📧 Check your email to confirm the SNS subscription for marketplace
                        notifications.
                      </Box>
                    </SpaceBetween>
                  </Alert>
                )}

                <Container
                  header={
                    <Header variant="h2">Product Information</Header>
                  }
                >
                  <SpaceBetween size="s">
                    <Box>
                      <Box variant="awsui-key-label">Product ID:</Box>
                      <Box>{productId}</Box>
                    </Box>
                  </SpaceBetween>
                </Container>

                <Container
                  header={
                    <Header variant="h2">Configuration</Header>
                  }
                >
                  <SpaceBetween size="l">
                    <FormField
                      label="Email for SNS Notifications"
                      description="This email will receive AWS Marketplace notifications"
                      constraintText="Required"
                    >
                      <Input
                        value={email}
                        onChange={({ detail }) => setEmail(detail.value)}
                        placeholder="admin@yourcompany.com"
                        type="email"
                        disabled={loading || success}
                      />
                    </FormField>

                    <FormField
                      label="CloudFormation Stack Name"
                      constraintText="Required"
                    >
                      <Input
                        value={stackName}
                        onChange={({ detail }) => setStackName(detail.value)}
                        disabled={loading || success}
                      />
                    </FormField>

                    <FormField
                      label="AWS Region"
                      description="Infrastructure will be deployed in the selected region"
                    >
                      <Select
                        selectedOption={region}
                        onChange={({ detail }) => setRegion(detail.selectedOption)}
                        options={[
                          { label: 'us-east-1', value: 'us-east-1' },
                          { label: 'us-west-2', value: 'us-west-2' },
                          { label: 'eu-west-1', value: 'eu-west-1' },
                        ]}
                        disabled={loading || success}
                      />
                    </FormField>
                  </SpaceBetween>
                </Container>

                <Container
                  header={
                    <Header variant="h2">AWS Credentials</Header>
                  }
                >
                  <SpaceBetween size="l">
                    <FormField
                      label="AWS Access Key ID"
                      constraintText="Required"
                    >
                      <Input
                        value={accessKey}
                        onChange={({ detail }) => setAccessKey(detail.value)}
                        type="password"
                        disabled={loading || success}
                      />
                    </FormField>

                    <FormField
                      label="AWS Secret Access Key"
                      constraintText="Required"
                    >
                      <Input
                        value={secretKey}
                        onChange={({ detail }) => setSecretKey(detail.value)}
                        type="password"
                        disabled={loading || success}
                      />
                    </FormField>

                    <FormField
                      label="AWS Session Token"
                      description="Optional for temporary credentials"
                    >
                      <Input
                        value={sessionToken}
                        onChange={({ detail }) => setSessionToken(detail.value)}
                        type="password"
                        disabled={loading || success}
                      />
                    </FormField>
                  </SpaceBetween>
                </Container>

                <ExpandableSection
                  headerText="Infrastructure Components"
                  variant="container"
                >
                  <SpaceBetween size="s">
                    <Box>CloudFormation will deploy:</Box>
                    <ul>
                      <li>🗄 DynamoDB tables for subscriptions and metering</li>
                      <li>λ Lambda function for usage metering</li>
                      <li>🔗 API Gateway for fulfillment</li>
                      <li>📧 SNS topic for notifications</li>
                      <li>🔐 IAM roles and policies</li>
                    </ul>
                  </SpaceBetween>
                </ExpandableSection>
              </SpaceBetween>
            </Form>
          </form>
        </ContentLayout>
      }
    />
  );
}
