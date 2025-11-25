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
  ContentLayout,
  BreadcrumbGroup,
  ProgressBar,
  Box,
  Spinner,
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';
import axios from 'axios';

const STAGES = [
  { name: 'Product Information', progress: 12.5 },
  { name: 'Fulfillment', progress: 25 },
  { name: 'Pricing Dimensions', progress: 37.5 },
  { name: 'Price Review', progress: 50 },
  { name: 'Refund Policy', progress: 62.5 },
  { name: 'EULA', progress: 75 },
  { name: 'Availability', progress: 87.5 },
  { name: 'Allowlist', progress: 95 },
];

export default function CreateListingPage() {
  const router = useRouter();
  const {
    isAuthenticated,
    listingData,
    setProductId,
    setCurrentStep,
    credentials,
  } = useStore();

  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [productId, setLocalProductId] = useState('');
  const [offerId, setOfferId] = useState('');
  const [publishedToLimited, setPublishedToLimited] = useState(false);

  useEffect(() => {
    if (!isAuthenticated || !listingData || !credentials) {
      router.push('/');
      return;
    }

    // Start listing creation automatically
    createListing();
  }, [isAuthenticated, listingData, credentials, router]);

  const createListing = async () => {
    setLoading(true);
    setError('');

    try {
      // Execute 8-stage workflow
      for (let i = 0; i < STAGES.length; i++) {
        setCurrentStage(STAGES[i].name);
        setProgress(STAGES[i].progress);

        // Simulate stage execution (in real app, this would call backend)
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }

      // Call backend to create listing
      const response = await axios.post('/api/create-listing', {
        listing_data: listingData,
        credentials: credentials,
      });

      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to create listing');
      }

      setProgress(100);
      setCurrentStage('Complete!');
      setSuccess(true);
      setLocalProductId(response.data.product_id);
      setOfferId(response.data.offer_id);
      setPublishedToLimited(response.data.published_to_limited || false);

      // Store product ID
      setProductId(response.data.product_id);
    } catch (err: any) {
      console.error('Listing creation error:', err);
      setError(err.response?.data?.error || err.message || 'Failed to create listing');
      setProgress(0);
      setCurrentStage('');
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = () => {
    setCurrentStep('saas_deployment');
    router.push('/listing-success');
  };

  const handleBack = () => {
    setCurrentStep('review_suggestions');
    router.push('/review-suggestions');
  };

  if (!isAuthenticated || !listingData) {
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
            { text: 'Product Information', href: '/product-info' },
            { text: 'AI Analysis', href: '/ai-analysis' },
            { text: 'Review Suggestions', href: '/review-suggestions' },
            { text: 'Create Listing', href: '/create-listing' },
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
              description="Creating your AWS Marketplace listing"
            >
              {success ? 'Listing Created Successfully!' : 'Creating Your Listing...'}
            </Header>
          }
        >
          <SpaceBetween size="l">
            {error && (
              <Alert
                type="error"
                dismissible
                onDismiss={() => setError('')}
                action={
                  <Button onClick={createListing}>
                    Retry
                  </Button>
                }
              >
                {error}
              </Alert>
            )}

            {success && (
              <Alert type="success" header="Listing Created Successfully!">
                <SpaceBetween size="s">
                  <Box>Your AWS Marketplace listing has been created successfully!</Box>
                  {productId && <Box>Product ID: <strong>{productId}</strong></Box>}
                  {offerId && <Box>Offer ID: <strong>{offerId}</strong></Box>}
                  {publishedToLimited && (
                    <Box color="text-status-success">
                      ✓ Published to Limited stage - ready for testing!
                    </Box>
                  )}
                </SpaceBetween>
              </Alert>
            )}

            <Container
              header={
                <Header variant="h2">Listing Creation Progress</Header>
              }
            >
              <SpaceBetween size="l">
                {loading && (
                  <Box textAlign="center">
                    <Spinner size="large" />
                  </Box>
                )}

                <ProgressBar
                  value={progress}
                  label="Creation progress"
                  description={currentStage}
                  status={error ? 'error' : loading ? 'in-progress' : 'success'}
                />

                {!loading && !error && success && (
                  <Box variant="p" textAlign="center" color="text-status-success">
                    ✓ All stages completed successfully!
                  </Box>
                )}

                {loading && (
                  <Box variant="p" textAlign="center">
                    This may take 2-3 minutes. Please wait...
                  </Box>
                )}

                {/* Show stages */}
                <SpaceBetween size="xs">
                  {STAGES.map((stage, index) => (
                    <Box key={index}>
                      <SpaceBetween size="xxs" direction="horizontal">
                        <Box>
                          {progress >= stage.progress ? '✓' : index === STAGES.findIndex(s => s.name === currentStage) ? '⟳' : '○'}
                        </Box>
                        <Box
                          color={
                            progress >= stage.progress
                              ? 'text-status-success'
                              : index === STAGES.findIndex(s => s.name === currentStage)
                              ? 'text-status-info'
                              : 'text-body-secondary'
                          }
                        >
                          {stage.name}
                        </Box>
                      </SpaceBetween>
                    </Box>
                  ))}
                </SpaceBetween>
              </SpaceBetween>
            </Container>

            {success && (
              <Container>
                <SpaceBetween size="m" direction="horizontal">
                  <Button onClick={handleBack}>
                    ← Back
                  </Button>
                  <Button variant="primary" onClick={handleContinue}>
                    View Results →
                  </Button>
                </SpaceBetween>
              </Container>
            )}

            {!success && !loading && error && (
              <Container>
                <SpaceBetween size="m" direction="horizontal">
                  <Button onClick={handleBack}>
                    ← Back to Review
                  </Button>
                  <Button variant="primary" onClick={createListing}>
                    Retry Creation
                  </Button>
                </SpaceBetween>
              </Container>
            )}
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}
