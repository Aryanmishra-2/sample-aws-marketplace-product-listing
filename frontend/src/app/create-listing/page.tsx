'use client';

import { useState, useEffect, useRef } from 'react';
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
import WorkflowNav from '@/components/WorkflowNav';
import axios from 'axios';

interface Changeset {
  change_set_id: string;
  change_set_name: string;
  status: string;
  start_time?: string;
  end_time?: string;
  entity_id?: string;
  failure_code?: string;
}

interface Stage {
  name: string;
  status: 'pending' | 'in_progress' | 'complete' | 'failed';
  message?: string;
}

const STAGE_NAMES = [
  'Product & Offer Creation',
  'Product Details',
  'Fulfillment',
  'Pricing',
  'Support Terms',
  'Legal Terms',
  'Availability',
  'Publish to Limited',
];

export default function CreateListingPage() {
  const router = useRouter();
  const { isAuthenticated, listingData, setProductId, setCurrentStep, credentials } = useStore();

  const [loading, setLoading] = useState(false);
  const [stages, setStages] = useState<Stage[]>(STAGE_NAMES.map(name => ({ name, status: 'pending' })));
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [productId, setLocalProductId] = useState('');
  const [offerId, setOfferId] = useState('');
  const [publishedToLimited, setPublishedToLimited] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [sessionStartTime, setSessionStartTime] = useState<Date | null>(null);
  const [completedChangesets, setCompletedChangesets] = useState<Set<string>>(new Set());
  const hasStartedRef = useRef(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const requestSentRef = useRef(false);

  useEffect(() => {
    if (!isAuthenticated || !listingData || !credentials) {
      router.push('/');
      return;
    }
    if (!hasStartedRef.current && !loading && !success) {
      hasStartedRef.current = true;
      startListingCreation();
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [isAuthenticated, listingData, credentials]);

  useEffect(() => {
    if (loading && startTime) {
      const interval = setInterval(() => setElapsedTime(Math.floor((Date.now() - startTime) / 1000)), 1000);
      return () => clearInterval(interval);
    }
  }, [loading, startTime]);

  const startListingCreation = async () => {
    setLoading(true);
    setError('');
    setStartTime(Date.now());
    const sessionStart = new Date();
    setSessionStartTime(sessionStart);
    setCompletedChangesets(new Set());
    
    // Set first stage as in_progress
    setStages(prev => prev.map((s, i) => ({ ...s, status: i === 0 ? 'in_progress' : 'pending' })));

    // Fire off the create_listing request (don't wait for response)
    if (!requestSentRef.current) {
      requestSentRef.current = true;
      axios.post('/api/create-listing-stream', {
        listing_data: listingData,
        credentials,
      }, { timeout: 600000 }).then(response => {
        console.log('[create-listing] Response received:', response.data);
        if (response.data.success) {
          setLocalProductId(response.data.product_id || '');
          setOfferId(response.data.offer_id || '');
          setPublishedToLimited(response.data.published_to_limited || false);
          if (response.data.product_id) setProductId(response.data.product_id);
        }
      }).catch(err => {
        console.log('[create-listing] Request error (expected timeout):', err.message);
      });
    }

    // Start polling for changesets
    startPolling(sessionStart);
  };

  const startPolling = (sessionStart: Date) => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    const pollChangesets = async () => {
      try {
        const response = await axios.post('/api/list-changesets', { credentials, max_results: 20 });
        
        if (!response.data.success) {
          console.log('[poll] API error:', response.data.error);
          return;
        }

        const changesets: Changeset[] = response.data.changesets;
        
        // Filter to changesets started after our session began (with 1 min buffer)
        const sessionStartWithBuffer = new Date(sessionStart.getTime() - 60000);
        const relevantChangesets = changesets.filter(cs => {
          if (!cs.start_time) return false;
          const csTime = new Date(cs.start_time);
          return csTime >= sessionStartWithBuffer;
        });

        console.log('[poll] Found', relevantChangesets.length, 'relevant changesets');

        // Count completed changesets
        const newCompleted = new Set(completedChangesets);
        let foundProductId = '';
        let foundOfferId = '';
        let hasReleasedToLimited = false;

        for (const cs of relevantChangesets) {
          // Extract entity IDs
          if (cs.entity_id) {
            if (cs.entity_id.startsWith('prod-')) foundProductId = cs.entity_id.split('@')[0];
            if (cs.entity_id.startsWith('offer-')) foundOfferId = cs.entity_id.split('@')[0];
          }

          if (cs.status === 'SUCCEEDED') {
            newCompleted.add(cs.change_set_id);
            
            // Check for Release to Limited
            if (cs.change_set_name?.includes('Release') && cs.change_set_name?.includes('Limited')) {
              hasReleasedToLimited = true;
            }
          }
        }

        setCompletedChangesets(newCompleted);

        // Update product/offer IDs
        if (foundProductId && !productId) {
          setLocalProductId(foundProductId);
          setProductId(foundProductId);
        }
        if (foundOfferId && !offerId) {
          setOfferId(foundOfferId);
        }

        // Update stages based on completed count
        // The orchestration runs ~10 changesets total
        const completedCount = newCompleted.size;
        console.log('[poll] Completed changesets:', completedCount);

        const newStages = STAGE_NAMES.map((name, idx) => {
          // Map stage index to expected changeset count
          // Stage 0: 1 changeset (CreateProduct)
          // Stage 1: 2 changesets (UpdateInfo)
          // Stage 2: 3 changesets (Fulfillment)
          // Stage 3: 4 changesets (Pricing)
          // Stage 4: 5 changesets (Support)
          // Stage 5: 6 changesets (Legal)
          // Stage 6: 7 changesets (Availability)
          // Stage 7: 8+ changesets (Release to Limited)
          const requiredCount = idx + 1;
          
          if (completedCount >= requiredCount) {
            return { name, status: 'complete' as const, message: 'Completed' };
          } else if (completedCount === requiredCount - 1) {
            return { name, status: 'in_progress' as const, message: 'Processing...' };
          } else {
            return { name, status: 'pending' as const };
          }
        });

        setStages(newStages);

        // Check if done (Release to Limited completed OR 8+ changesets)
        if (hasReleasedToLimited || completedCount >= 8) {
          console.log('[poll] ✅ All done! Stopping polling.');
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          setStages(STAGE_NAMES.map(name => ({ name, status: 'complete', message: 'Completed' })));
          setSuccess(true);
          setLoading(false);
          setPublishedToLimited(hasReleasedToLimited);
        }

      } catch (err) {
        console.error('[poll] Error:', err);
      }
    };

    // Poll immediately, then every 5 seconds
    // Continue for up to 10 minutes (600 seconds)
    pollChangesets();
    pollingRef.current = setInterval(() => {
      const elapsed = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;
      if (elapsed > 600) {
        console.log('[poll] Timeout after 10 minutes');
        if (pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
        // If we have some progress, show success
        if (completedChangesets.size > 0) {
          setSuccess(true);
        } else {
          setError('Timeout - check AWS Marketplace console');
        }
        setLoading(false);
      } else {
        pollChangesets();
      }
    }, 5000);
  };

  const formatTime = (s: number) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`;

  const getStatusIcon = (status: Stage['status']) => {
    switch (status) {
      case 'complete': return <StatusIndicator type="success">✓</StatusIndicator>;
      case 'in_progress': return <Spinner />;
      case 'failed': return <StatusIndicator type="error">✗</StatusIndicator>;
      default: return <Box color="text-body-secondary">○</Box>;
    }
  };

  const getColor = (status: Stage['status']) => {
    switch (status) {
      case 'complete': return '#037f0c';
      case 'in_progress': return '#0073bb';
      case 'failed': return '#d13212';
      default: return '#d5dbdb';
    }
  };

  const progress = Math.round((stages.filter(s => s.status === 'complete').length / stages.length) * 100);

  if (!isAuthenticated || !listingData) return null;

  return (
    <AppLayout
      navigation={<WorkflowNav />}
      toolsHide
      breadcrumbs={
        <BreadcrumbGroup
          items={[{ text: 'Home', href: '/' }, { text: 'Create Listing', href: '/create-listing' }]}
          onFollow={(e) => { e.preventDefault(); router.push(e.detail.href); }}
        />
      }
      content={
        <ContentLayout header={<Header variant="h1">{success ? 'Listing Created!' : 'Creating Listing...'}</Header>}>
          <SpaceBetween size="l">
            {error && <Alert type="error" dismissible onDismiss={() => setError('')}>{error}</Alert>}

            {success && (
              <Alert type="success" header="Listing Created Successfully!">
                <SpaceBetween size="xs">
                  {productId && <Box>Product ID: <strong>{productId}</strong></Box>}
                  {offerId && <Box>Offer ID: <strong>{offerId}</strong></Box>}
                  {publishedToLimited && <Box color="text-status-success">✓ Published to Limited</Box>}
                  <Box color="text-body-secondary">Time: {formatTime(elapsedTime)}</Box>
                </SpaceBetween>
              </Alert>
            )}

            <Container header={<Header variant="h2">Progress {loading && `(${formatTime(elapsedTime)})`}</Header>}>
              <SpaceBetween size="m">
                {loading && <Box textAlign="center"><Spinner size="large" /></Box>}
                
                <ProgressBar
                  value={progress}
                  status={error ? 'error' : loading ? 'in-progress' : 'success'}
                  additionalInfo={`${progress}%`}
                />

                <SpaceBetween size="xs">
                  {stages.map((stage, idx) => (
                    <div key={idx} style={{ borderLeft: `4px solid ${getColor(stage.status)}`, paddingLeft: 12, paddingTop: 6, paddingBottom: 6 }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <div style={{ minWidth: 24 }}>{getStatusIcon(stage.status)}</div>
                        <div>
                          <Box fontWeight="bold">{stage.name}</Box>
                          {stage.message && <Box fontSize="body-s" color="text-body-secondary">{stage.message}</Box>}
                        </div>
                      </div>
                    </div>
                  ))}
                </SpaceBetween>

                {loading && (
                  <Box textAlign="center" color="text-body-secondary">
                    Polling AWS Marketplace... ({completedChangesets.size} changesets completed)
                  </Box>
                )}
              </SpaceBetween>
            </Container>

            {(success || (!loading && error)) && (
              <Container>
                <SpaceBetween size="m" direction="horizontal">
                  <Button onClick={() => router.push('/review-suggestions')}>← Back</Button>
                  {success && <Button variant="primary" onClick={() => { setCurrentStep('saas_deployment'); router.push('/listing-success'); }}>Continue →</Button>}
                  {error && <Button variant="primary" onClick={() => { hasStartedRef.current = false; requestSentRef.current = false; setSuccess(false); setCompletedChangesets(new Set()); startListingCreation(); }}>Retry</Button>}
                </SpaceBetween>
              </Container>
            )}
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}
