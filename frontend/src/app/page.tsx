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

interface Agent {
  agent_id: string;
  agent_name: string;
  agent_status: string;
  description: string;
  updated_at: string | null;
}

export default function CredentialsPage() {
  const router = useRouter();
  const { setCredentials, setSellerStatus, setCurrentStep, sellerStatus, setAccountInfo } = useStore();
  
  const [accessKey, setAccessKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [sessionToken, setSessionToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loadingAgents, setLoadingAgents] = useState(false);

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

        // Store account info
        setAccountInfo({
          account_id: validateResponse.data.account_id,
          user_arn: validateResponse.data.user_arn,
          user_name: validateResponse.data.user_arn.split('/').pop() || 'Unknown',
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
        
        // List Bedrock agents
        setLoadingAgents(true);
        try {
          const agentsResponse = await axios.post('/api/list-agents', {
            aws_access_key_id: accessKey,
            aws_secret_access_key: secretKey,
            aws_session_token: sessionToken || undefined,
          });
          
          if (agentsResponse.data.success) {
            setAgents(agentsResponse.data.agents || []);
          }
        } catch (agentErr) {
          console.error('Failed to list agents:', agentErr);
        } finally {
          setLoadingAgents(false);
        }
        
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
                  <Box>Account ID: <strong>{sellerStatus.account_id}</strong></Box>
                  <Box>
                    Organization: <Badge color={sellerStatus.account_id ? 'blue' : 'grey'}>
                      {useStore.getState().accountInfo?.organization || 'Unknown'}
                    </Badge>
                  </Box>
                  <Box>Seller Status: <Badge color={sellerStatus.seller_status === 'APPROVED' ? 'green' : 'grey'}>{sellerStatus.seller_status}</Badge></Box>
                  {sellerStatus.owned_products && sellerStatus.owned_products.length > 0 && (
                    <Box>Existing Products: <strong>{sellerStatus.owned_products.length}</strong></Box>
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

            {sellerStatus && sellerStatus.owned_products && sellerStatus.owned_products.length > 0 && (
              <Container
                header={
                  <Header
                    variant="h2"
                    description="Your existing AWS Marketplace products - select one to continue from where you left off"
                    counter={`(${sellerStatus.owned_products.length})`}
                  >
                    Existing Products
                  </Header>
                }
              >
                <Table
                  columnDefinitions={[
                    {
                      id: 'id',
                      header: 'Product ID',
                      cell: (item: any) => (
                        <Box fontWeight="bold">
                          {item.product_id || item.Id || '-'}
                        </Box>
                      ),
                    },
                    {
                      id: 'name',
                      header: 'Product Name',
                      cell: (item: any) => item.product_name || item.Name || '-',
                    },
                    {
                      id: 'type',
                      header: 'Product Type',
                      cell: (item: any) => (
                        <Badge>{item.product_type || item.ProductType || 'SaaS'}</Badge>
                      ),
                    },
                    {
                      id: 'status',
                      header: 'Status',
                      cell: (item: any) => {
                        const status = item.status || item.Status || 'UNKNOWN';
                        const color = status === 'ACTIVE' ? 'green' : 
                                     status === 'DRAFT' ? 'blue' : 'grey';
                        return <Badge color={color}>{status}</Badge>;
                      },
                    },
                    {
                      id: 'actions',
                      header: 'Actions',
                      cell: (item: any) => (
                        <Button
                          variant="primary"
                          onClick={() => {
                            const prodId = item.product_id || item.Id;
                            useStore.getState().setProductId(prodId);
                            useStore.getState().setCurrentStep('review_suggestions');
                            router.push('/review-suggestions');
                          }}
                        >
                          Continue →
                        </Button>
                      ),
                    },
                  ]}
                  items={sellerStatus.owned_products}
                  empty={
                    <Box textAlign="center" color="inherit">
                      <b>No products</b>
                      <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                        No products found in this account.
                      </Box>
                    </Box>
                  }
                />
              </Container>
            )}

            {agents.length > 0 && (
              <Container
                header={
                  <Header
                    variant="h2"
                    description="Bedrock agents found in your AWS account"
                    counter={`(${agents.length})`}
                  >
                    Your Bedrock Agents
                  </Header>
                }
              >
                <Table
                  columnDefinitions={[
                    {
                      id: 'name',
                      header: 'Agent Name',
                      cell: (item: Agent) => item.agent_name || '-',
                    },
                    {
                      id: 'id',
                      header: 'Agent ID',
                      cell: (item: Agent) => (
                        <Box fontSize="body-s" color="text-body-secondary">
                          {item.agent_id}
                        </Box>
                      ),
                    },
                    {
                      id: 'status',
                      header: 'Status',
                      cell: (item: Agent) => {
                        const status = item.agent_status;
                        if (status === 'PREPARED' || status === 'READY') {
                          return <Badge color="green">{status}</Badge>;
                        } else if (status === 'CREATING' || status === 'UPDATING') {
                          return <Badge color="blue">{status}</Badge>;
                        } else if (status === 'FAILED') {
                          return <Badge color="red">{status}</Badge>;
                        }
                        return <Badge>{status}</Badge>;
                      },
                    },
                    {
                      id: 'description',
                      header: 'Description',
                      cell: (item: Agent) => item.description || '-',
                    },
                    {
                      id: 'updated',
                      header: 'Last Updated',
                      cell: (item: Agent) => {
                        if (!item.updated_at) return '-';
                        return new Date(item.updated_at).toLocaleDateString();
                      },
                    },
                  ]}
                  items={agents}
                  loading={loadingAgents}
                  loadingText="Loading agents..."
                  empty={
                    <Box textAlign="center" color="inherit">
                      <b>No agents</b>
                      <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                        No Bedrock agents found in this account.
                      </Box>
                    </Box>
                  }
                />
              </Container>
            )}

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
