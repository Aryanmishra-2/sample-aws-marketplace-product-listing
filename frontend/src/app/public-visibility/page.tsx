// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
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
  Spinner,
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';
import WorkflowNav from '@/components/WorkflowNav';
import axios from 'axios';

export default function PublicVisibilityPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, credentials } = useStore();
  
  const productId = searchParams.get('productId');
  const stackName = searchParams.get('stackName');
  const pricingModel = searchParams.get('pricingModel');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [visibilitySteps, setVisibilitySteps] = useState<any[]>([]);

  useEffect(() => {
    if (!isAuthenticated || !productId) {
      router.push('/');
      return;
    }

    // Load public visibility guide
    loadPublicVisibilityGuide();
  }, [isAuthenticated, productId, router]);

  const loadPublicVisibilityGuide = async () => {
    try {
      setLoading(true);
      console.log('[PUBLIC VISIBILITY] Loading public visibility guide...');
      
      const response = await axios.post('/api/public-visibility-guide', {});
      
      console.log('[PUBLIC VISIBILITY] Guide response:', response.data);
      
      if (response.data.success && response.data.guide?.steps) {
        setVisibilitySteps(response.data.guide.steps);
      } else {
        setError(response.data.error || 'Failed to load public visibility guide');
      }
    } catch (err: any) {
      console.error('[PUBLIC VISIBILITY] Error loading guide:', err);
      setError(err.response?.data?.error || err.message || 'Failed to load public visibility guide');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated || !productId) {
    return null;
  }

  return (
    <AppLayout
      navigation={<WorkflowNav />}
      toolsHide
      breadcrumbs={
        <BreadcrumbGroup
          items={[
            { text: 'Home', href: '/' },
            { text: 'SaaS Workflow', href: `/saas-workflow?productId=${productId}&stackName=${stackName}` },
            { text: 'Public Visibility', href: '#' },
          ]}
          onFollow={(e) => {
            e.preventDefault();
            if (e.detail.href !== '#') {
              router.push(e.detail.href);
            }
          }}
        />
      }
      content={
        <ContentLayout
          header={
            <Header
              variant="h1"
              description="Make your product publicly available to all AWS customers"
              actions={
                <Button variant="primary" onClick={() => router.push('/')}>
                  Finish →
                </Button>
              }
            >
              🌐 Public Visibility Guide
            </Header>
          }
        >
          <SpaceBetween size="l">
            {loading && (
              <Container>
                <SpaceBetween size="m" alignItems="center">
                  <Box textAlign="center">
                    <Spinner size="large" />
                  </Box>
                  <Box textAlign="center" fontWeight="bold">
                    Loading public visibility guide...
                  </Box>
                </SpaceBetween>
              </Container>
            )}

            {error && (
              <Alert type="error" header="Error Loading Guide">
                {error}
              </Alert>
            )}

            {!loading && !error && visibilitySteps.length > 0 && (
              <>
                <Alert type="success">
                  <Box fontWeight="bold">Metering Integration Complete!</Box>
                  <Box fontSize="body-s" padding={{ top: 'xs' }}>
                    Your SaaS integration and metering are working correctly. Follow the steps below to make your product publicly available on AWS Marketplace.
                  </Box>
                </Alert>

                <SpaceBetween size="m">
                  {visibilitySteps.map((step: any, index: number) => (
                    <Container key={index}>
                      <SpaceBetween size="m">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                          <div 
                            style={{ 
                              fontSize: '32px', 
                              minWidth: '48px', 
                              textAlign: 'center',
                              color: step.color || '#0073bb'
                            }}
                          >
                            {step.icon || '📋'}
                          </div>
                          <div style={{ flex: 1 }}>
                            <Box variant="h3" color="text-label">
                              Step {step.step}: {step.title}
                            </Box>
                            <Box fontSize="body-m" color="text-body-secondary" padding={{ top: 'xs' }}>
                              {step.description}
                            </Box>
                          </div>
                        </div>
                        
                        {step.actions && step.actions.length > 0 && (
                          <Box padding={{ left: 'xxl' }}>
                            <Box fontWeight="bold" fontSize="body-s" padding={{ bottom: 'xs' }}>Actions to Take:</Box>
                            <SpaceBetween size="xs">
                              {step.actions.map((action: string, actionIndex: number) => (
                                <Box key={actionIndex} fontSize="body-s" color="text-body-secondary">
                                  • {action}
                                </Box>
                              ))}
                            </SpaceBetween>
                          </Box>
                        )}
                        
                        {step.expected && step.expected.length > 0 && (
                          <Box padding={{ left: 'xxl' }}>
                            <Box fontWeight="bold" fontSize="body-s" padding={{ bottom: 'xs' }}>Expected Results:</Box>
                            <SpaceBetween size="xs">
                              {step.expected.map((result: string, resultIndex: number) => (
                                <Box key={resultIndex} fontSize="body-s" color="text-status-success">
                                  ✓ {result}
                                </Box>
                              ))}
                            </SpaceBetween>
                          </Box>
                        )}
                      </SpaceBetween>
                    </Container>
                  ))}
                </SpaceBetween>

                <Alert type="info">
                  <SpaceBetween size="xs">
                    <Box fontWeight="bold">Important Notes:</Box>
                    <Box fontSize="body-s">
                      • AWS Marketplace review typically takes 1-3 business days<br/>
                      • You'll receive email notifications about the review status<br/>
                      • Once approved, your product will be publicly searchable<br/>
                      • Make sure your support documentation is complete before submitting
                    </Box>
                  </SpaceBetween>
                </Alert>

                <Container>
                  <SpaceBetween size="m">
                    <Box variant="h3">Next Steps</Box>
                    <Box fontSize="body-m">
                      Follow the steps above to submit your public visibility request through the AWS Marketplace Management Portal. 
                      Once approved, your product will be available to all AWS customers.
                    </Box>
                    <Box textAlign="center">
                      <Button 
                        variant="primary" 
                        iconAlign="right"
                        iconName="external"
                        onClick={() => {
                          window.open('https://aws.amazon.com/marketplace/management/products', '_blank');
                        }}
                      >
                        Open AWS Marketplace Management Portal
                      </Button>
                    </Box>
                  </SpaceBetween>
                </Container>
              </>
            )}
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}