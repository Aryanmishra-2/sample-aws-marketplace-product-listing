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
  Box,
  ContentLayout,
  BreadcrumbGroup,
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';

export default function WelcomePage() {
  const router = useRouter();
  const { sellerStatus, isAuthenticated, setCurrentStep } = useStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  const handleStartListing = () => {
    setCurrentStep('gather_context');
    router.push('/product-info');
  };

  const handleBackToCredentials = () => {
    setCurrentStep('credentials');
    router.push('/');
  };

  if (!isAuthenticated) {
    return null;
  }

  const isApproved = sellerStatus?.seller_status === 'APPROVED';
  const isPending = sellerStatus?.seller_status === 'PENDING';
  const isNotRegistered = sellerStatus?.seller_status === 'NOT_REGISTERED';

  return (
    <AppLayout
      navigationHide
      toolsHide
      breadcrumbs={
        <BreadcrumbGroup
          items={[
            { text: 'Home', href: '/' },
            { text: 'Welcome', href: '/welcome' },
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
              description="Your AWS Marketplace journey starts here"
            >
              Welcome to AWS Marketplace Seller Portal
            </Header>
          }
        >
          <SpaceBetween size="l">
            {isApproved && (
              <Alert type="success" header="Seller Status: APPROVED">
                Your account is registered as an AWS Marketplace seller! You can now create
                product listings.
                {sellerStatus.owned_products && sellerStatus.owned_products.length > 0 && (
                  <Box margin={{ top: 's' }}>
                    You currently have {sellerStatus.owned_products.length} product(s) in your
                    account.
                  </Box>
                )}
              </Alert>
            )}

            {isPending && (
              <Alert type="warning" header="Seller Registration: PENDING">
                Your seller registration is currently under review by AWS. Estimated completion:
                2-3 business days.
              </Alert>
            )}

            {isNotRegistered && (
              <Alert type="info" header="Seller Registration: NOT REGISTERED">
                <SpaceBetween size="m">
                  <Box>Your account is not yet registered as an AWS Marketplace seller.</Box>
                  <Box variant="h4">To become an AWS Marketplace seller, you need to:</Box>
                  <ul>
                    <li>Create your Business Profile in the AWS Marketplace Management Portal</li>
                    <li>Complete Tax Information (W-9 or W-8 form)</li>
                    <li>Set up Payment Information (Bank account details)</li>
                    <li>Submit for AWS Review (2-3 business days)</li>
                  </ul>
                  <Button
                    variant="primary"
                    href="https://aws.amazon.com/marketplace/management/seller-settings/register"
                    target="_blank"
                    iconAlign="right"
                    iconName="external"
                  >
                    Create Business Profile
                  </Button>
                </SpaceBetween>
              </Alert>
            )}

            <Container
              header={
                <Header variant="h2">Complete End-to-End Solution</Header>
              }
            >
              <SpaceBetween size="m">
                <Box variant="h3">This comprehensive workflow will:</Box>
                
                <Box>
                  <Box variant="h4">Step 1: Seller Registration 🏢</Box>
                  <ul>
                    <li>Check your current seller status</li>
                    <li>Guide you through AWS Marketplace seller registration</li>
                    <li>Handle business profile, tax information, and banking setup</li>
                  </ul>
                </Box>

                <Box>
                  <Box variant="h4">Step 2: Listing Creation 🛍️</Box>
                  <ul>
                    <li>Analyze your product documentation</li>
                    <li>Generate all required listing content automatically</li>
                    <li>Select optimal pricing models and dimensions</li>
                    <li>Create and publish your marketplace listing</li>
                  </ul>
                </Box>

                <Box>
                  <Box variant="h4">Step 3: SaaS Integration (Optional) 🔧</Box>
                  <ul>
                    <li>Deploy serverless infrastructure</li>
                    <li>Configure fulfillment and metering</li>
                    <li>Test buyer experience</li>
                    <li>Submit for public visibility</li>
                  </ul>
                </Box>
              </SpaceBetween>
            </Container>

            <Container>
              <SpaceBetween size="m" direction="horizontal">
                <Button onClick={handleBackToCredentials}>
                  Back to Credentials
                </Button>
                {isApproved && (
                  <Button variant="primary" onClick={handleStartListing}>
                    Start AI-Guided Creation →
                  </Button>
                )}
              </SpaceBetween>
            </Container>
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}
