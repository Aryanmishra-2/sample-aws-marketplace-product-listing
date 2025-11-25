'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  AppLayout,
  Container,
  Header,
  SpaceBetween,
  Button,
  Alert,
  Box,
  ColumnLayout,
  ContentLayout,
  BreadcrumbGroup,
  Checkbox,
  Link,
  StatusIndicator,
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';
import GlobalHeader from '@/components/GlobalHeader';

export default function SellerRegistrationPage() {
  const router = useRouter();
  const { isAuthenticated, sellerStatus } = useStore();
  
  const [taxInfoConfirmed, setTaxInfoConfirmed] = useState(false);
  const [paymentInfoConfirmed, setPaymentInfoConfirmed] = useState(false);
  const [accountStatusConfirmed, setAccountStatusConfirmed] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated || !sellerStatus) {
    return null;
  }

  const status = sellerStatus.seller_status;
  const productsCount = sellerStatus.owned_products?.length || 0;
  const allConfirmed = taxInfoConfirmed && paymentInfoConfirmed && accountStatusConfirmed;

  // SCENARIO 1: Seller with existing products
  if (status === 'APPROVED' && productsCount > 0) {
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
                { text: 'Seller Registration', href: '/seller-registration' },
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
                  description="Your seller account is fully configured and ready"
                >
                  Seller Profile Complete
                </Header>
              }
            >
              <SpaceBetween size="l">
                <Alert type="success" header="✅ Seller Profile Complete!">
                  Your account has {productsCount} existing product{productsCount > 1 ? 's' : ''}. 
                  This confirms your seller profile is fully configured.
                </Alert>

                <Container>
                  <SpaceBetween size="m">
                    <Box variant="h3">Your seller account is ready to:</Box>
                    <ul style={{ marginLeft: '20px' }}>
                      <li>Create new product listings</li>
                      <li>Manage existing products</li>
                      <li>View sales and reports</li>
                    </ul>
                  </SpaceBetween>
                </Container>

                <Container>
                  <SpaceBetween size="m">
                    <Header variant="h2">Ready to Create a New Product?</Header>
                    <Button
                      variant="primary"
                      onClick={() => router.push('/welcome')}
                    >
                      📦 Create New Product Listing
                    </Button>
                  </SpaceBetween>
                </Container>

                <Container>
                  <SpaceBetween size="s">
                    <Box variant="h3">Manage Existing Products</Box>
                    <Link
                      external
                      href="https://aws.amazon.com/marketplace/management/products"
                    >
                      AWS Marketplace Management Portal
                    </Link>
                  </SpaceBetween>
                </Container>
              </SpaceBetween>
            </ContentLayout>
          }
        />
      </>
    );
  }

  // SCENARIO 2: Seller registered but no products
  if (status === 'APPROVED' && productsCount === 0) {
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
                { text: 'Seller Registration', href: '/seller-registration' },
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
                  description="Complete your seller profile before creating products"
                >
                  Seller Profile Validation
                </Header>
              }
            >
              <SpaceBetween size="l">
                <Alert type="success" header="🎉 Seller Registration: APPROVED">
                  Your account is registered as an AWS Marketplace seller!
                </Alert>

                <Alert type="warning" header="⚠️ Profile Validation Required">
                  Before creating products, you must complete your seller profile in the AWS portal.
                  AWS Marketplace requires complete tax and payment information before you can list products.
                </Alert>

                <Container>
                  <SpaceBetween size="m">
                    <Header variant="h2">Complete These Steps in AWS Portal</Header>
                    <Box>
                      <ol style={{ marginLeft: '20px' }}>
                        <li>
                          <Box fontWeight="bold">Open AWS Marketplace Seller Settings:</Box>
                          <Link
                            external
                            href="https://aws.amazon.com/marketplace/management/seller-settings/account"
                          >
                            AWS Marketplace Seller Settings
                          </Link>
                        </li>
                        <li>
                          <Box fontWeight="bold">Verify Tax Information:</Box>
                          <ul style={{ marginLeft: '20px', marginTop: '8px' }}>
                            <li>Check that your W-9 (US) or W-8 (International) form is submitted</li>
                            <li>Ensure your business name and EIN/Tax ID are correct</li>
                            <li>Verify your business address is up to date</li>
                          </ul>
                        </li>
                        <li>
                          <Box fontWeight="bold">Verify Payment Information:</Box>
                          <ul style={{ marginLeft: '20px', marginTop: '8px' }}>
                            <li>Confirm your bank account details are configured</li>
                            <li>Check that your routing number and account number are correct</li>
                            <li>Ensure disbursement method is selected</li>
                          </ul>
                        </li>
                        <li>
                          <Box fontWeight="bold">Verify Account Status:</Box>
                          <ul style={{ marginLeft: '20px', marginTop: '8px' }}>
                            <li>Check that the portal shows "Account status: Publish paid and free products"</li>
                            <li>This confirms you can publish both free and paid products</li>
                          </ul>
                        </li>
                        <li>
                          <Box fontWeight="bold">Return here and confirm completion below</Box>
                        </li>
                      </ol>
                    </Box>
                  </SpaceBetween>
                </Container>

                <Container header={<Header variant="h2">Validation Checklist</Header>}>
                  <SpaceBetween size="m">
                    <ColumnLayout columns={3}>
                      <div>
                        <Box variant="h4">📋 Tax Information</Box>
                        <Checkbox
                          checked={taxInfoConfirmed}
                          onChange={({ detail }) => setTaxInfoConfirmed(detail.checked)}
                        >
                          Tax information complete
                        </Checkbox>
                        <Box fontSize="body-s" color="text-body-secondary" padding={{ top: 'xs' }}>
                          Check this ONLY after verifying your tax information in AWS Marketplace Seller Settings
                        </Box>
                      </div>
                      <div>
                        <Box variant="h4">💳 Payment Information</Box>
                        <Checkbox
                          checked={paymentInfoConfirmed}
                          onChange={({ detail }) => setPaymentInfoConfirmed(detail.checked)}
                        >
                          Payment information complete
                        </Checkbox>
                        <Box fontSize="body-s" color="text-body-secondary" padding={{ top: 'xs' }}>
                          Check this ONLY after verifying your banking/payment information
                        </Box>
                      </div>
                      <div>
                        <Box variant="h4">✅ Account Status</Box>
                        <Checkbox
                          checked={accountStatusConfirmed}
                          onChange={({ detail }) => setAccountStatusConfirmed(detail.checked)}
                        >
                          Can publish paid/free products
                        </Checkbox>
                        <Box fontSize="body-s" color="text-body-secondary" padding={{ top: 'xs' }}>
                          Check this ONLY if portal shows "Publish paid and free products"
                        </Box>
                      </div>
                    </ColumnLayout>

                    {allConfirmed ? (
                      <Alert type="success" header="✅ Validation Complete!">
                        <SpaceBetween size="s">
                          <Box>Your seller profile is ready. You have confirmed that:</Box>
                          <ul style={{ marginLeft: '20px' }}>
                            <li>Tax information is complete</li>
                            <li>Payment information is complete</li>
                            <li>Account status allows publishing paid and free products</li>
                          </ul>
                          <Box>You can now proceed to create product listings.</Box>
                          <Button
                            variant="primary"
                            onClick={() => router.push('/welcome')}
                          >
                            📦 Create Product Listing
                          </Button>
                        </SpaceBetween>
                      </Alert>
                    ) : (
                      <Alert type="error" header="❌ Validation Incomplete">
                        <SpaceBetween size="s">
                          <Box>Please complete validation for:</Box>
                          <ul style={{ marginLeft: '20px' }}>
                            {!taxInfoConfirmed && <li>Tax Information</li>}
                            {!paymentInfoConfirmed && <li>Payment Information</li>}
                            {!accountStatusConfirmed && <li>Account Status (Publish paid/free products)</li>}
                          </ul>
                          <Box>You must confirm all three items before creating products.</Box>
                        </SpaceBetween>
                      </Alert>
                    )}
                  </SpaceBetween>
                </Container>
              </SpaceBetween>
            </ContentLayout>
          }
        />
      </>
    );
  }

  // SCENARIO 3: Not registered
  if (status === 'NOT_REGISTERED') {
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
                { text: 'Seller Registration', href: '/seller-registration' },
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
                  description="Register your account as an AWS Marketplace seller"
                >
                  Seller Registration Required
                </Header>
              }
            >
              <SpaceBetween size="l">
                <Alert type="warning" header="📝 Seller Registration: NOT REGISTERED">
                  Your account is not yet registered as an AWS Marketplace seller.
                </Alert>

                <Container>
                  <SpaceBetween size="m">
                    <Header variant="h2">To become an AWS Marketplace seller, you need to:</Header>
                    <ol style={{ marginLeft: '20px' }}>
                      <li>🏢 Create your Business Profile in the AWS Marketplace Management Portal</li>
                      <li>📋 Complete Tax Information (W-9 or W-8 form)</li>
                      <li>💳 Set up Payment Information (Bank account details)</li>
                      <li>✅ Submit for AWS Review (2-3 business days)</li>
                    </ol>
                  </SpaceBetween>
                </Container>

                <Container header={<Header variant="h2">🚀 Get Started with Seller Registration</Header>}>
                  <SpaceBetween size="m">
                    <Box>
                      Click the button below to create your seller profile. This will take you to the AWS Marketplace 
                      Seller Registration portal where you can:
                    </Box>
                    <ul style={{ marginLeft: '20px' }}>
                      <li>Register your business information</li>
                      <li>Complete required tax forms</li>
                      <li>Set up payment and disbursement methods</li>
                      <li>Submit your application for AWS review</li>
                    </ul>
                    <Box color="text-body-secondary">Estimated time: 15-20 minutes</Box>
                    <Button
                      variant="primary"
                      iconAlign="right"
                      iconName="external"
                      href="https://aws.amazon.com/marketplace/management/seller-settings/register"
                      target="_blank"
                    >
                      🏢 Create Business Profile
                    </Button>
                  </SpaceBetween>
                </Container>

                <Alert type="info" header="💡 After Completing Registration">
                  <ul style={{ marginLeft: '20px' }}>
                    <li>Return to the home page</li>
                    <li>Click "🔄 Re-validate Credentials" to refresh your seller status</li>
                    <li>Once approved, you can create product listings</li>
                  </ul>
                </Alert>
              </SpaceBetween>
            </ContentLayout>
          }
        />
      </>
    );
  }

  // PENDING or other status
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
              { text: 'Seller Registration', href: '/seller-registration' },
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
              <Header variant="h1">
                Seller Registration Status
              </Header>
            }
          >
            <SpaceBetween size="l">
              {status === 'PENDING' ? (
                <Alert type="warning" header="⏳ Seller Registration: PENDING">
                  Your seller registration is currently under review by AWS.
                  Estimated completion: 2-3 business days.
                </Alert>
              ) : (
                <Alert type="warning" header={`❓ Seller Registration: ${status}`}>
                  Status unclear. Manual verification may be required.
                </Alert>
              )}

              <Container>
                <SpaceBetween size="m">
                  <Box>Please check your AWS Marketplace Management Portal for more details.</Box>
                  <Button
                    iconAlign="right"
                    iconName="external"
                    href="https://aws.amazon.com/marketplace/management/seller-settings/account"
                    target="_blank"
                  >
                    Open AWS Marketplace Portal
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
