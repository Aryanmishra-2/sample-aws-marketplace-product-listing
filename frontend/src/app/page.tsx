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
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';
import axios from 'axios';

export default function CredentialsPage() {
  const router = useRouter();
  const { setCredentials, setSellerStatus, setCurrentStep, sellerStatus } = useStore();
  
  const [accessKey, setAccessKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [sessionToken, setSessionToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleValidate = async () => {
    if (!accessKey || !secretKey) {
      setError('Please provide both Access Key ID and Secret Access Key');
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

        // Check seller status
        const statusResponse = await axios.post('/api/check-seller-status', {
          aws_access_key_id: accessKey,
          aws_secret_access_key: secretKey,
          aws_session_token: sessionToken || undefined,
        });

        setSellerStatus(statusResponse.data);
        setCurrentStep('welcome');
        router.push('/welcome');
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
                AWS Marketplace Seller Registration
              </Header>
            </SpaceBetween>
          }
        >
          <SpaceBetween size="l">
            {sellerStatus && (
              <Alert type="success" header="Credentials Validated">
                <SpaceBetween size="xs">
                  <Box>Account ID: {sellerStatus.account_id}</Box>
                  <Box>Seller Status: {sellerStatus.seller_status}</Box>
                  {sellerStatus.owned_products && sellerStatus.owned_products.length > 0 && (
                    <Box>Products: {sellerStatus.owned_products.length}</Box>
                  )}
                </SpaceBetween>
              </Alert>
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
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}
