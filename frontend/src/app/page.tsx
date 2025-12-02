'use client';

import { useState } from 'react';
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
  Box,
  ColumnLayout,
  ContentLayout,
  Table,
  Badge,
  StatusIndicator,
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';
import axios from 'axios';

export default function CredentialsPage() {
  const router = useRouter();
  const { setCredentials, setSellerStatus, setCurrentStep, sellerStatus, setAccountInfo } = useStore();
  
  const [accessKey, setAccessKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [sessionToken, setSessionToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [permissions, setPermissions] = useState<any>(null);
  const [canProceed, setCanProceed] = useState(true);

  const handleValidate = async () => {
    if (!accessKey || !secretKey) {
      setError('Please provide both Access Key ID and Secret Access Key');
      return;
    }

    // Prevent duplicate calls
    if (loading) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Validate credentials
      const validateResponse = await axios.post('/api/validate-credentials', {
        aws_access_key_id: accessKey,
        aws_secret_access_key: secretKey,
        aws_session_token: sessionToken || undefined,
      });

      if (validateResponse.data.success) {
        // Store permissions info
        setPermissions(validateResponse.data.permissions);
        setCanProceed(validateResponse.data.can_proceed);
        
        // Store credentials
        setCredentials(
          {
            aws_access_key_id: accessKey,
            aws_secret_access_key: secretKey,
            aws_session_token: sessionToken || undefined,
            region: 'us-east-1',
          },
          validateResponse.data.session_id || 'session-' + Date.now()
        );

        // Store account info
        setAccountInfo({
          account_id: validateResponse.data.account_id,
          user_arn: validateResponse.data.user_arn,
          user_name: validateResponse.data.user_name || validateResponse.data.user_arn.split('/').pop() || 'Unknown',
          organization: validateResponse.data.organization,
          region_type: validateResponse.data.region_type,
        });

        // Check seller status
        const statusResponse = await axios.post('/api/check-seller-status', {
          aws_access_key_id: accessKey,
          aws_secret_access_key: secretKey,
          aws_session_token: sessionToken || undefined,
        });

        setSellerStatus(statusResponse.data);
        
        // OPTIMIZATION: Auto-redirect based on seller status for faster UX
        // This reduces perceived wait time by immediately routing users
        setCurrentStep('welcome');
        
        // Route based on seller status (immediate redirect)
        if (statusResponse.data.seller_status === 'NOT_REGISTERED') {
          // Not registered - go to registration page immediately
          router.push('/seller-registration');
          return; // Exit early to prevent further processing
        } else if (statusResponse.data.seller_status === 'PENDING') {
          // Pending - go to status page immediately
          router.push('/seller-registration');
          return; // Exit early
        } else if (statusResponse.data.seller_status === 'APPROVED') {
          // Approved - check if they have products (this is fast, uses cached data)
          const hasProducts = statusResponse.data.owned_products && statusResponse.data.owned_products.length > 0;
          
          if (hasProducts) {
            // Has products - go to seller registration page which shows product management
            router.push('/seller-registration');
            return; // Exit early
          } else {
            // No products - go to validation page
            router.push('/seller-registration');
            return; // Exit early
          }
        }
        
        // If we reach here, status is unknown - stay on current page
        // User can manually navigate using buttons
      } else {
        setError(validateResponse.data.error || 'Credential validation failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Failed to validate credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleClearData = () => {
    if (confirm('Are you sure you want to clear all data? This cannot be undone.')) {
      useStore.getState().clearCredentials();
      setAccessKey('');
      setSecretKey('');
      setSessionToken('');
      setError('');
    }
  };

  return (
    <AppLayout
      navigationHide
      toolsHide
      content={
        <ContentLayout
          header={
            <SpaceBetween size="m">
              <Header
                variant="h1"
                description="Enter your AWS credentials to get started with AWS Marketplace seller registration and listing creation"
              >
                Listing Product in AWS Marketplace
              </Header>
            </SpaceBetween>
          }
        >
          <SpaceBetween size="l">
            {permissions && (
              <Container header={<Header variant="h2">IAM Permissions Status</Header>}>
                <SpaceBetween size="m">
                  <ColumnLayout columns={3} variant="text-grid">
                    <div>
                      <Box variant="awsui-key-label">Marketplace Access</Box>
                      <StatusIndicator type={permissions.has_marketplace_full_access ? 'success' : 'warning'}>
                        {permissions.has_marketplace_full_access ? 'Full Access' : 'Limited'}
                      </StatusIndicator>
                    </div>
                    <div>
                      <Box variant="awsui-key-label">Product Management</Box>
                      <StatusIndicator type={permissions.has_marketplace_manage_products ? 'success' : 'error'}>
                        {permissions.has_marketplace_manage_products ? 'Enabled' : 'Missing'}
                      </StatusIndicator>
                    </div>
                    <div>
                      <Box variant="awsui-key-label">Admin Access</Box>
                      <StatusIndicator type={permissions.has_admin_access ? 'success' : 'info'}>
                        {permissions.has_admin_access ? 'Yes' : 'No'}
                      </StatusIndicator>
                    </div>
                  </ColumnLayout>

                  {permissions.recommendations && permissions.recommendations.length > 0 && (
                    <SpaceBetween size="s">
                      <Box variant="h4">Recommendations</Box>
                      {permissions.recommendations.map((rec: any, idx: number) => (
                        <Alert
                          key={idx}
                          type={rec.severity === 'high' ? 'warning' : 'info'}
                          header={rec.title}
                        >
                          <SpaceBetween size="xs">
                            <Box>{rec.message}</Box>
                            <Box><strong>Action:</strong> {rec.action}</Box>
                            {rec.policy_arn && (
                              <Box fontSize="body-s" color="text-body-secondary">
                                Policy ARN: {rec.policy_arn}
                              </Box>
                            )}
                            {rec.required_actions && (
                              <Box>
                                <Box variant="awsui-key-label">Required Permissions:</Box>
                                <ul style={{ marginLeft: '20px', marginTop: '4px' }}>
                                  {rec.required_actions.map((action: string, i: number) => (
                                    <li key={i}><Box fontSize="body-s">{action}</Box></li>
                                  ))}
                                </ul>
                              </Box>
                            )}
                          </SpaceBetween>
                        </Alert>
                      ))}
                    </SpaceBetween>
                  )}

                  {!canProceed && (
                    <Alert type="error" header="Insufficient Permissions">
                      You need additional IAM permissions to use this application. Please contact your AWS administrator to grant the required marketplace permissions.
                    </Alert>
                  )}
                </SpaceBetween>
              </Container>
            )}

            {error && (
              <Alert type="error" dismissible onDismiss={() => setError('')}>
                {error}
              </Alert>
            )}

            <Container
              header={
                <Header
                  variant="h2"
                  description="Your credentials are used to validate your AWS account and check seller registration status"
                >
                  AWS Credentials
                </Header>
              }
            >
              <form onSubmit={(e) => { e.preventDefault(); handleValidate(); }}>
                <Form
                  actions={
                    <SpaceBetween direction="horizontal" size="xs">
                      <Button onClick={handleClearData} disabled={loading}>
                        Clear All Data
                      </Button>
                      <Button
                        variant="primary"
                        loading={loading}
                        onClick={handleValidate}
                      >
                        Validate Credentials
                      </Button>
                    </SpaceBetween>
                  }
                >
                  <SpaceBetween size="l">
                    <FormField
                      label="AWS Access Key ID"
                      description="Your AWS Access Key ID (starts with AKIA)"
                      constraintText="Required"
                    >
                      <Input
                        value={accessKey}
                        onChange={({ detail }) => setAccessKey(detail.value)}
                        placeholder="AKIA..."
                        type="password"
                        disabled={loading}
                      />
                    </FormField>

                    <FormField
                      label="AWS Secret Access Key"
                      description="Your AWS Secret Access Key"
                      constraintText="Required"
                    >
                      <Input
                        value={secretKey}
                        onChange={({ detail }) => setSecretKey(detail.value)}
                        type="password"
                        disabled={loading}
                      />
                    </FormField>

                    <FormField
                      label="AWS Session Token"
                      description="Required only for temporary credentials"
                    >
                      <Input
                        value={sessionToken}
                        onChange={({ detail }) => setSessionToken(detail.value)}
                        type="password"
                        disabled={loading}
                      />
                    </FormField>
                  </SpaceBetween>
                </Form>
              </form>
            </Container>

            {!sellerStatus && (
              <Container>
                <SpaceBetween size="m">
                  <Header variant="h3">What happens next?</Header>
                  <ColumnLayout columns={3} variant="text-grid">
                    <div>
                      <Box variant="h4">1. Validate Account</Box>
                      <Box variant="p">
                        We'll validate your AWS credentials and determine your organization
                        (AWS Inc vs AWS India)
                      </Box>
                    </div>
                    <div>
                      <Box variant="h4">2. Check Status</Box>
                      <Box variant="p">
                        Check your current seller registration status and guide you through
                        the process if needed
                      </Box>
                    </div>
                    <div>
                      <Box variant="h4">3. Create Listing</Box>
                      <Box variant="p">
                        Use AI to analyze your product and create a complete marketplace
                        listing automatically
                      </Box>
                    </div>
                  </ColumnLayout>
                </SpaceBetween>
              </Container>
            )}
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}
