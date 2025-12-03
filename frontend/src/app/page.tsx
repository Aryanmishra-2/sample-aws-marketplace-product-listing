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
        
        // Mark credentials step as complete
        useStore.getState().markStepComplete('credentials');
        
        // OPTIMIZATION: Auto-redirect based on seller status for faster UX
        // This reduces perceived wait time by immediately routing users
        setCurrentStep('seller_registration');
        
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
          <ColumnLayout columns={2} borders="vertical">
            {/* Left Column - Credentials Form */}
            <div>
              <SpaceBetween size="l">
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
                      <ColumnLayout columns={1} variant="text-grid">
                        <div>
                          <Box variant="h4">1. Validate Account</Box>
                          <Box variant="p">Validate AWS credentials and organization</Box>
                        </div>
                        <div>
                          <Box variant="h4">2. Check Status</Box>
                          <Box variant="p">Check seller registration status</Box>
                        </div>
                        <div>
                          <Box variant="h4">3. Create Listing</Box>
                          <Box variant="p">AI-guided listing creation</Box>
                        </div>
                      </ColumnLayout>
                    </SpaceBetween>
                  </Container>
                )}
              </SpaceBetween>
            </div>

            {/* Right Column - Status Display */}
            <div>
              {sellerStatus && permissions && (
                <SpaceBetween size="l">
                  <Container header={<Header variant="h2">Validation Status</Header>}>
                    <SpaceBetween size="m">
                      <div>
                        <Box variant="awsui-key-label">AWS Account ID</Box>
                        <Box fontWeight="bold" fontSize="heading-m">{sellerStatus.account_id}</Box>
                      </div>
                      <div>
                        <Box variant="awsui-key-label">Organization</Box>
                        <Badge color={
                          useStore.getState().accountInfo?.region_type === 'AWS_INDIA' ? 'green' :
                          useStore.getState().accountInfo?.region_type === 'AWS_INC' ? 'blue' : 'grey'
                        }>
                          {useStore.getState().accountInfo?.organization || 'Unknown'}
                        </Badge>
                      </div>
                      <div>
                        <Box variant="awsui-key-label">Seller Status</Box>
                        <Badge color={sellerStatus.seller_status === 'APPROVED' ? 'green' : 'grey'}>
                          {sellerStatus.seller_status}
                        </Badge>
                      </div>
                      {sellerStatus.owned_products && sellerStatus.owned_products.length > 0 && (
                        <div>
                          <Box variant="awsui-key-label">Existing Products</Box>
                          <Box fontWeight="bold">{sellerStatus.owned_products.length}</Box>
                        </div>
                      )}
                    </SpaceBetween>
                  </Container>

                  <Container header={<Header variant="h2">IAM Permissions</Header>}>
                    <SpaceBetween size="m">
                      <div>
                        <Box variant="awsui-key-label">AWSMarketplaceFullAccess Policy</Box>
                        <StatusIndicator type={permissions.has_marketplace_full_access_policy ? 'success' : 'warning'}>
                          {permissions.has_marketplace_full_access_policy ? 'Attached' : 'Not Attached'}
                        </StatusIndicator>
                      </div>
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
                                <Box fontSize="body-s">{rec.message}</Box>
                                <Box fontSize="body-s"><strong>Action:</strong> {rec.action}</Box>
                              </SpaceBetween>
                            </Alert>
                          ))}
                        </SpaceBetween>
                      )}

                      {canProceed && (
                        <Alert type="success" header="✅ Ready to Proceed">
                          All required permissions are in place. You can create product listings.
                        </Alert>
                      )}

                      {!canProceed && (
                        <Alert type="error" header="❌ Insufficient Permissions">
                          Contact your AWS administrator to grant required marketplace permissions.
                        </Alert>
                      )}
                    </SpaceBetween>
                  </Container>
                </SpaceBetween>
              )}

              {!sellerStatus && (
                <Container>
                  <Box textAlign="center" padding={{ vertical: 'xxl' }}>
                    <Box variant="h3" color="text-body-secondary">
                      Enter credentials to see status
                    </Box>
                  </Box>
                </Container>
              )}
            </div>
          </ColumnLayout>
        </ContentLayout>
      }
    />
  );
}
