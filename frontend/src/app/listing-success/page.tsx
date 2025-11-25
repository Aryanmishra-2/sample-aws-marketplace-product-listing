'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
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
  ColumnLayout,
  Link,
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';
import GlobalHeader from '@/components/GlobalHeader';

export default function ListingSuccessPage() {
  const router = useRouter();
  const { isAuthenticated, productId, setCurrentStep } = useStore();

  useEffect(() => {
    if (!isAuthenticated || !productId) {
      router.push('/');
    }
  }, [isAuthenticated, productId, router]);

  const handleDeploySaaS = () => {
    setCurrentStep('saas_deployment');
    router.push('/saas-integration');
  };

  const handleCreateAnother = () => {
    setCurrentStep('gather_context');
    router.push('/product-info');
  };

  const handleGoHome = () => {
    setCurrentStep('credentials');
    router.push('/');
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
              description="Your AWS Marketplace listing has been created successfully"
            >
              🎉 Listing Created Successfully!
            </Header>
          }
        >
          <SpaceBetween size="l">
            <Alert type="success" header="Your listing is ready!">
              <SpaceBetween size="s">
                <Box>
                  Your AWS Marketplace listing has been created with all configurations complete.
                </Box>
                <Box>
                  <strong>Product ID:</strong> {productId}
                </Box>
              </SpaceBetween>
            </Alert>

            <Container
              header={
                <Header variant="h2">What's Been Completed</Header>
              }
            >
              <SpaceBetween size="s">
                <Box>✅ Product information</Box>
                <Box>✅ Fulfillment configuration</Box>
                <Box>✅ Pricing and dimensions</Box>
                <Box>✅ Support terms</Box>
                <Box>✅ EULA</Box>
                <Box>✅ Geographic availability</Box>
              </SpaceBetween>
            </Container>

            <Container
              header={
                <Header variant="h2">Next Steps</Header>
              }
            >
              <SpaceBetween size="m">
                <Box variant="h3">Option 1: Deploy SaaS Integration (Recommended)</Box>
                <Box>
                  Deploy the complete serverless infrastructure for your AWS Marketplace SaaS
                  integration using CloudFormation. This includes:
                </Box>
                <ul>
                  <li>DynamoDB tables for subscriptions and metering</li>
                  <li>Lambda functions for usage metering</li>
                  <li>API Gateway for fulfillment</li>
                  <li>SNS topics for notifications</li>
                  <li>IAM roles and policies</li>
                </ul>
                <Button variant="primary" onClick={handleDeploySaaS}>
                  Deploy SaaS Integration →
                </Button>

                <Box variant="h3">Option 2: Manual Configuration</Box>
                <Box>
                  Configure your listing manually through the AWS Marketplace Management Portal:
                </Box>
                <ol>
                  <li>
                    Go to{' '}
                    <Link
                      external
                      href="https://aws.amazon.com/marketplace/management/products"
                    >
                      AWS Marketplace Management Portal
                    </Link>
                  </li>
                  <li>Find your product using the Product ID above</li>
                  <li>Complete any additional configurations</li>
                  <li>Test your listing in Limited stage</li>
                  <li>Submit for public visibility when ready</li>
                </ol>
              </SpaceBetween>
            </Container>

            <Container
              header={
                <Header variant="h2">Testing Your Listing</Header>
              }
            >
              <SpaceBetween size="m">
                <Box variant="h3">Limited Stage Testing</Box>
                <Box>
                  Your listing is now in Limited stage, which means:
                </Box>
                <ul>
                  <li>Only your AWS account can see and subscribe to it</li>
                  <li>You can test the complete subscription flow</li>
                  <li>Verify fulfillment URL integration</li>
                  <li>Test metering and entitlement (if applicable)</li>
                </ul>

                <Box variant="h3">How to Test</Box>
                <ol>
                  <li>
                    Go to{' '}
                    <Link external href="https://aws.amazon.com/marketplace">
                      AWS Marketplace
                    </Link>
                  </li>
                  <li>Search for your product title or use the Product ID</li>
                  <li>Click "Continue to Subscribe"</li>
                  <li>Accept terms and click "Set Up Your Account"</li>
                  <li>You'll be redirected to your fulfillment URL</li>
                </ol>
              </SpaceBetween>
            </Container>

            <Container
              header={
                <Header variant="h2">Going Public</Header>
              }
            >
              <SpaceBetween size="m">
                <Box>When you're ready to make your listing publicly available:</Box>
                <ol>
                  <li>Update pricing from test values to production prices</li>
                  <li>
                    Go to{' '}
                    <Link
                      external
                      href="https://aws.amazon.com/marketplace/management/products"
                    >
                      AWS Marketplace Management Portal
                    </Link>
                  </li>
                  <li>Find your product and click "Update visibility"</li>
                  <li>Select "Public" and submit for AWS review</li>
                  <li>AWS reviews your listing (typically 1-2 weeks)</li>
                  <li>Once approved, your listing is publicly available!</li>
                </ol>
              </SpaceBetween>
            </Container>

            <Container
              header={
                <Header variant="h2">Resources</Header>
              }
            >
              <ColumnLayout columns={2} variant="text-grid">
                <div>
                  <Box variant="h4">Documentation</Box>
                  <SpaceBetween size="xs">
                    <Link
                      external
                      href="https://docs.aws.amazon.com/marketplace/latest/userguide/saas-guidelines.html"
                    >
                      SaaS Product Guidelines
                    </Link>
                    <Link
                      external
                      href="https://docs.aws.amazon.com/marketplace/latest/userguide/saas-prepare.html"
                    >
                      Testing Your Product
                    </Link>
                    <Link
                      external
                      href="https://docs.aws.amazon.com/marketplace/latest/userguide/what-is-marketplace.html"
                    >
                      Seller Guide
                    </Link>
                  </SpaceBetween>
                </div>
                <div>
                  <Box variant="h4">Support</Box>
                  <SpaceBetween size="xs">
                    <Link
                      external
                      href="https://aws.amazon.com/marketplace/management/contact-us/"
                    >
                      Seller Support
                    </Link>
                    <Link
                      external
                      href="https://aws.amazon.com/marketplace/management/products"
                    >
                      Management Portal
                    </Link>
                    <Link
                      external
                      href="https://aws.amazon.com/marketplace/management/seller-settings/account"
                    >
                      Seller Settings
                    </Link>
                  </SpaceBetween>
                </div>
              </ColumnLayout>
            </Container>

            <Container>
              <SpaceBetween size="m" direction="horizontal">
                <Button onClick={handleGoHome}>
                  ← Back to Home
                </Button>
                <Button onClick={handleCreateAnother}>
                  Create Another Listing
                </Button>
                <Button variant="primary" onClick={handleDeploySaaS}>
                  Deploy SaaS Integration →
                </Button>
              </SpaceBetween>
            </Container>
          </SpaceBetween>
        </ContentLayout>
      }
      />
    </>
  );
}
