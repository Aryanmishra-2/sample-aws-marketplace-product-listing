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
  StatusIndicator,
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';
import GlobalHeader from '@/components/GlobalHeader';
import axios from 'axios';

interface Stage {
  name: string;
  description: string;
  progress: number;
  status: 'pending' | 'in-progress' | 'completed' | 'error';
  message?: string;
  startTime?: number;
  endTime?: number;
}

const INITIAL_STAGES: Stage[] = [
  { name: 'Product Information', description: 'Setting product details, logo, and descriptions', progress: 12.5, status: 'pending' },
  { name: 'Fulfillment Configuration', description: 'Configuring fulfillment URL and settings', progress: 25, status: 'pending' },
  { name: 'Pricing Dimensions', description: 'Creating pricing dimensions and models', progress: 37.5, status: 'pending' },
  { name: 'Price Review', description: 'Configuring contract durations and options', progress: 50, status: 'pending' },
  { name: 'Refund Policy', description: 'Setting refund policy terms', progress: 62.5, status: 'pending' },
  { name: 'EULA Configuration', description: 'Configuring End User License Agreement', progress: 75, status: 'pending' },
  { name: 'Availability Settings', description: 'Setting geographic availability', progress: 87.5, status: 'pending' },
  { name: 'Allowlist Configuration', description: 'Configuring buyer account allowlist', progress: 95, status: 'pending' },
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
  const [stages, setStages] = useState<Stage[]>(INITIAL_STAGES);
  const [currentStageIndex, setCurrentStageIndex] = useState(-1);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [productId, setLocalProductId] = useState('');
  const [offerId, setOfferId] = useState('');
  const [publishedToLimited, setPublishedToLimited] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime, setStartTime] = useState<number | null>(null);

  useEffect(() => {
    if (!isAuthenticated || !listingData || !credentials) {
      router.push('/');
      return;
    }

    // Start listing creation automatically
    createListing();
  }, [isAuthenticated, listingData, credentials, router]);

  // Timer for elapsed time
  useEffect(() => {
    if (loading && startTime) {
      const interval = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [loading, startTime]);

  const updateStageStatus = (index: number, status: Stage['status'], message?: string) => {
    setStages(prev => {
      const newStages = [...prev];
      newStages[index] = {
        ...newStages[index],
        status,
        message,
        startTime: status === 'in-progress' ? Date.now() : newStages[index].startTime,
        endTime: status === 'completed' || status === 'error' ? Date.now() : undefined,
      };
      return newStages;
    });
  };

  const createListing = async () => {
    setLoading(true);
    setError('');
    setStartTime(Date.now());

    try {
      // Execute 8-stage workflow with real-time updates
      for (let i = 0; i < INITIAL_STAGES.length; i++) {
        setCurrentStageIndex(i);
        updateStageStatus(i, 'in-progress');
        setProgress(INITIAL_STAGES[i].progress);

        // Simulate stage execution (in real app, backend would send progress updates)
        await new Promise((resolve) => setTimeout(resolve, 800));
        
        updateStageStatus(i, 'completed', '✓ Complete');
      }

      // Call backend to create listing
      setCurrentStageIndex(INITIAL_STAGES.length);
      const response = await axios.post('/api/create-listing', {
        listing_data: listingData,
        credentials: credentials,
      });

      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to create listing');
      }

      setProgress(100);
      setSuccess(true);
      setLocalProductId(response.data.product_id);
      setOfferId(response.data.offer_id);
      setPublishedToLimited(response.data.published_to_limited || false);

      // Store product ID
      setProductId(response.data.product_id);
    } catch (err: any) {
      console.error('Listing creation error:', err);
      setError(err.response?.data?.error || err.message || 'Failed to create listing');
      if (currentStageIndex >= 0 && currentStageIndex < stages.length) {
        updateStageStatus(currentStageIndex, 'error', '✗ Failed');
      }
      setProgress(0);
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

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isAuthenticated || !listingData) {
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
              description="Creating your AWS Marketplace listing with real-time progress tracking"
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
                  <Box color="text-body-secondary">
                    Total time: {formatTime(elapsedTime)}
                  </Box>
                </SpaceBetween>
              </Alert>
            )}

            <Container
              header={
                <Header 
                  variant="h2"
                  description={loading ? `Elapsed time: ${formatTime(elapsedTime)}` : ''}
                >
                  Listing Creation Progress
                </Header>
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
                  label="Overall progress"
                  description={currentStageIndex >= 0 && currentStageIndex < stages.length ? stages[currentStageIndex].name : 'Initializing...'}
                  status={error ? 'error' : loading ? 'in-progress' : 'success'}
                  additionalInfo={`${Math.round(progress)}%`}
                />

                {/* Detailed stage progress */}
                <SpaceBetween size="s">
                  {stages.map((stage, index) => {
                    const duration = stage.startTime && stage.endTime 
                      ? ((stage.endTime - stage.startTime) / 1000).toFixed(1) + 's'
                      : '';
                    
                    return (
                      <div 
                        key={index}
                        className={`aws-progress-step ${stage.status}`}
                        style={{
                          borderLeft: stage.status === 'completed' ? '4px solid #037f0c' :
                                     stage.status === 'in-progress' ? '4px solid #0073bb' :
                                     stage.status === 'error' ? '4px solid #d13212' :
                                     '4px solid #d5dbdb'
                        }}
                      >
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                          <div style={{ minWidth: '24px' }}>
                            {stage.status === 'completed' && <StatusIndicator type="success">✓</StatusIndicator>}
                            {stage.status === 'in-progress' && <Spinner />}
                            {stage.status === 'error' && <StatusIndicator type="error">✗</StatusIndicator>}
                            {stage.status === 'pending' && <Box color="text-body-secondary">○</Box>}
                          </div>
                          <div style={{ flex: 1 }}>
                            <Box fontWeight="bold">{stage.name}</Box>
                            <Box fontSize="body-s" color="text-body-secondary">
                              {stage.description}
                            </Box>
                            {stage.message && (
                              <Box fontSize="body-s" color={stage.status === 'error' ? 'text-status-error' : 'text-status-success'}>
                                {stage.message}
                              </Box>
                            )}
                          </div>
                          {duration && (
                            <div style={{ minWidth: '60px', textAlign: 'right' }}>
                              <Box fontSize="body-s" color="text-body-secondary">{duration}</Box>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </SpaceBetween>

                {!loading && !error && success && (
                  <Box variant="p" textAlign="center" color="text-status-success">
                    ✓ All stages completed successfully in {formatTime(elapsedTime)}!
                  </Box>
                )}

                {loading && (
                  <Box variant="p" textAlign="center" color="text-body-secondary">
                    This may take 2-3 minutes. Please wait...
                  </Box>
                )}
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
    </>
  );
}
