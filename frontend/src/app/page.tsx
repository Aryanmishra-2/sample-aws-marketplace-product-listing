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
  const [permissions, setPermissions] = useState<any>(null);
  const [canProceed, setCanProceed] = useState(true);
  const [marketplaceProducts, setMarketplaceProducts] = useState<any[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);

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
        
        // List marketplace products with intelligent status
        setLoadingProducts(true);
        try {
          const productsResponse = await axios.post('/api/list-marketplace-products', {
            aws_access_key_id: accessKey,
            aws_secret_access_key: secretKey,
            aws_session_token: sessionToken || undefined,
          });
          
          if (productsResponse.data.success) {
            setMarketplaceProducts(productsResponse.data.products || []);
          }
        } catch (productErr) {
          console.error('Failed to list marketplace products:', productErr);
        } finally {
          setLoadingProducts(false);
        }
        
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
        
        // Don't auto-navigate - let user review products and permissions first
        setCurrentStep('welcome');
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
              <Alert type="success" header="✓ Credentials Validated Successfully">
                <SpaceBetween size="s">
                  <ColumnLayout columns={2} variant="text-grid">
                    <div>
                      <Box variant="awsui-key-label">AWS Account ID</Box>
                      <Box fontWeight="bold" fontSize="heading-m">{sellerStatus.account_id}</Box>
                    </div>
                    <div>
                      <Box variant="awsui-key-label">Organization</Box>
                      <Box>
                        <Badge color={
                          useStore.getState().accountInfo?.region_type === 'AWS_INDIA' ? 'green' :
                          useStore.getState().accountInfo?.region_type === 'AWS_INC' ? 'blue' : 'grey'
                        }>
                          {useStore.getState().accountInfo?.organization || 'Unknown'}
                        </Badge>
                      </Box>
                    </div>
                  </ColumnLayout>
                  <ColumnLayout columns={2} variant="text-grid">
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
                  </ColumnLayout>
                </SpaceBetween>
              </Alert>
            )}

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

            {marketplaceProducts.length > 0 && (
              <Container
                header={
                  <Header
                    variant="h2"
                    description="Your AWS Marketplace products with intelligent status detection and guided workflows"
                    counter={`(${marketplaceProducts.length})`}
                  >
                    Marketplace Products
                  </Header>
                }
              >
                <Table
                  columnDefinitions={[
                    {
                      id: 'name',
                      header: 'Product Name',
                      cell: (item: any) => (
                        <Box>
                          <Box fontWeight="bold">{item.product_name}</Box>
                          <Box fontSize="body-s" color="text-body-secondary">
                            {item.product_id.substring(0, 24)}...
                          </Box>
                        </Box>
                      ),
                    },
                    {
                      id: 'type',
                      header: 'Type',
                      cell: (item: any) => <Badge>{item.product_type}</Badge>,
                    },
                    {
                      id: 'visibility',
                      header: 'Visibility',
                      cell: (item: any) => {
                        const color = 
                          item.visibility === 'PUBLIC' ? 'green' :
                          item.visibility === 'LIMITED' ? 'blue' :
                          item.visibility === 'DRAFT' ? 'grey' : 'red';
                        return <Badge color={color}>{item.visibility}</Badge>;
                      },
                    },
                    {
                      id: 'saas_status',
                      header: 'SaaS Integration',
                      cell: (item: any) => {
                        if (!item.needs_saas_integration) {
                          return <Box color="text-body-secondary">N/A</Box>;
                        }
                        const status = item.saas_integration_status;
                        if (status === 'COMPLETED') {
                          return <StatusIndicator type="success">Completed</StatusIndicator>;
                        } else if (status === 'REQUIRED') {
                          return <StatusIndicator type="warning">Required</StatusIndicator>;
                        } else if (status === 'PENDING') {
                          return <StatusIndicator type="info">Pending</StatusIndicator>;
                        }
                        return <Box color="text-body-secondary">Not Required</Box>;
                      },
                    },
                    {
                      id: 'recommendations',
                      header: 'Recommendations',
                      cell: (item: any) => (
                        <Box>
                          {item.recommendations.map((rec: string, idx: number) => (
                            <Box key={idx} fontSize="body-s" color="text-body-secondary">
                              • {rec}
                            </Box>
                          ))}
                        </Box>
                      ),
                    },
                    {
                      id: 'actions',
                      header: 'Actions',
                      cell: (item: any) => (
                        <SpaceBetween size="xs">
                          {item.allowed_actions.includes('edit') && (
                            <Button
                              variant="primary"
                              onClick={() => {
                                useStore.getState().setProductId(item.product_id);
                                useStore.getState().setCurrentStep('create_listing');
                                router.push('/create-listing');
                              }}
                            >
                              Edit Draft
                            </Button>
                          )}
                          {item.allowed_actions.includes('continue_listing') && (
                            <Button
                              variant="primary"
                              onClick={() => {
                                useStore.getState().setProductId(item.product_id);
                                useStore.getState().setCurrentStep('review_suggestions');
                                router.push('/review-suggestions');
                              }}
                            >
                              Continue Listing
                            </Button>
                          )}
                          {item.allowed_actions.includes('deploy_saas') && (
                            <Button
                              variant="primary"
                              onClick={() => {
                                useStore.getState().setProductId(item.product_id);
                                useStore.getState().setCurrentStep('saas_deployment');
                                router.push('/saas-integration');
                              }}
                            >
                              Deploy SaaS
                            </Button>
                          )}
                          {item.allowed_actions.includes('view') && !item.is_editable && (
                            <Button
                              onClick={() => {
                                useStore.getState().setProductId(item.product_id);
                                router.push('/listing-success');
                              }}
                            >
                              View Details
                            </Button>
                          )}
                        </SpaceBetween>
                      ),
                    },
                  ]}
                  items={marketplaceProducts}
                  loading={loadingProducts}
                  loadingText="Loading marketplace products..."
                  empty={
                    <Box textAlign="center" color="inherit">
                      <b>No products found</b>
                      <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                        No marketplace products found in this account.
                      </Box>
                      <Button
                        variant="primary"
                        onClick={() => {
                          useStore.getState().setCurrentStep('welcome');
                          router.push('/welcome');
                        }}
                      >
                        Create New Product
                      </Button>
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

            {sellerStatus && canProceed && (
              <Container>
                <SpaceBetween size="m">
                  <Header variant="h3">Ready to Continue?</Header>
                  <Box>
                    {marketplaceProducts.length > 0 ? (
                      <Box>
                        You have {marketplaceProducts.length} existing product{marketplaceProducts.length > 1 ? 's' : ''}. 
                        Select a product above to continue, or create a new one.
                      </Box>
                    ) : (
                      <Box>
                        No existing products found. Let's create your first AWS Marketplace listing!
                      </Box>
                    )}
                  </Box>
                  <Button
                    variant="primary"
                    onClick={() => router.push('/welcome')}
                  >
                    {marketplaceProducts.length > 0 ? 'Create New Product' : 'Get Started'} →
                  </Button>
                </SpaceBetween>
              </Container>
            )}

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
