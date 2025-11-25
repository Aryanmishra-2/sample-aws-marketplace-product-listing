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

export default function AIAnalysisPage() {
  const router = useRouter();
  const {
    isAuthenticated,
    productContext,
    setAnalysisResult,
    setCurrentStep,
    analysisResult,
  } = useStore();

  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [analysisComplete, setAnalysisComplete] = useState(false);

  useEffect(() => {
    if (!isAuthenticated || !productContext) {
      router.push('/');
      return;
    }

    // Check if analysis already exists
    if (analysisResult) {
      setAnalysisComplete(true);
      setProgress(100);
      setStatus('Analysis complete!');
    } else {
      // Start analysis automatically
      startAnalysis();
    }
  }, [isAuthenticated, productContext, analysisResult, router]);

  const startAnalysis = async () => {
    setLoading(true);
    setError('');

    try {
      // Step 1: Analyze product
      setStatus('Understanding your product...');
      setProgress(20);

      const analysisResponse = await axios.post('/api/analyze-product', {
        product_context: productContext,
      });

      if (!analysisResponse.data.success) {
        throw new Error(analysisResponse.data.error || 'Analysis failed');
      }

      setProgress(40);

      // Step 2: Generate content
      setStatus('Generating listing content...');

      const contentResponse = await axios.post('/api/generate-content', {
        analysis: analysisResponse.data.analysis,
        product_context: productContext,
      });

      if (!contentResponse.data.success) {
        throw new Error(contentResponse.data.error || 'Content generation failed');
      }

      setProgress(60);

      // Step 3: Suggest pricing
      setStatus('Analyzing pricing model...');

      const pricingResponse = await axios.post('/api/suggest-pricing', {
        analysis: analysisResponse.data.analysis,
      });

      if (!pricingResponse.data.success) {
        throw new Error(pricingResponse.data.error || 'Pricing suggestion failed');
      }

      setProgress(100);
      setStatus('Analysis complete!');

      // Store results
      const result = {
        title: contentResponse.data.content.product_title,
        short_description: contentResponse.data.content.short_description,
        long_description: contentResponse.data.content.long_description,
        highlights: contentResponse.data.content.highlights,
        categories: contentResponse.data.content.categories,
        search_keywords: contentResponse.data.content.search_keywords,
        pricing_model: pricingResponse.data.pricing.recommended_model,
        pricing_dimensions: pricingResponse.data.pricing.suggested_dimensions,
        support_description: 'Professional support available via email and documentation',
        features: analysisResponse.data.analysis.key_features || [],
      };

      setAnalysisResult(result);
      setAnalysisComplete(true);
    } catch (err: any) {
      console.error('Analysis error:', err);
      setError(err.response?.data?.error || err.message || 'Failed to analyze product');
      setProgress(0);
      setStatus('');
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = () => {
    setCurrentStep('review_suggestions');
    router.push('/review-suggestions');
  };

  const handleBack = () => {
    setCurrentStep('gather_context');
    router.push('/product-info');
  };

  const handleReanalyze = () => {
    setAnalysisComplete(false);
    setProgress(0);
    setStatus('');
    setError('');
    startAnalysis();
  };

  if (!isAuthenticated || !productContext) {
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
              description="Our AI is analyzing your product to generate marketplace listing content"
            >
              Analyzing Your Product
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
                  <Button onClick={handleReanalyze}>
                    Retry Analysis
                  </Button>
                }
              >
                {error}
              </Alert>
            )}

            {analysisComplete && !error && (
              <Alert type="success" header="Analysis Complete!">
                Your product has been analyzed successfully. Review the AI-generated suggestions
                on the next screen.
              </Alert>
            )}

            <Container
              header={
                <Header variant="h2">Product Information Provided</Header>
              }
            >
              <SpaceBetween size="s">
                {productContext.product_urls && productContext.product_urls.length > 0 && (
                  <Box>
                    <Box variant="awsui-key-label">Website:</Box>
                    <Box>{productContext.product_urls[0]}</Box>
                  </Box>
                )}
                {productContext.documentation_url && (
                  <Box>
                    <Box variant="awsui-key-label">Documentation:</Box>
                    <Box>{productContext.documentation_url}</Box>
                  </Box>
                )}
                {productContext.product_description && (
                  <Box>
                    <Box variant="awsui-key-label">Description:</Box>
                    <Box>{productContext.product_description.substring(0, 200)}...</Box>
                  </Box>
                )}
              </SpaceBetween>
            </Container>

            <Container
              header={
                <Header variant="h2">Analysis Progress</Header>
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
                  label="Analysis progress"
                  description={status}
                  status={error ? 'error' : loading ? 'in-progress' : 'success'}
                />

                {!loading && !error && analysisComplete && (
                  <Box variant="p" textAlign="center" color="text-status-success">
                    ✓ AI analysis complete! Your listing content is ready for review.
                  </Box>
                )}

                {loading && (
                  <Box variant="p" textAlign="center">
                    This may take 30-60 seconds. Please wait...
                  </Box>
                )}
              </SpaceBetween>
            </Container>

            {analysisComplete && !error && (
              <Container>
                <SpaceBetween size="m" direction="horizontal">
                  <Button onClick={handleBack}>
                    ← Back
                  </Button>
                  <Button onClick={handleReanalyze}>
                    Re-analyze
                  </Button>
                  <Button variant="primary" onClick={handleContinue}>
                    Review Suggestions →
                  </Button>
                </SpaceBetween>
              </Container>
            )}

            {!analysisComplete && !loading && error && (
              <Container>
                <SpaceBetween size="m" direction="horizontal">
                  <Button onClick={handleBack}>
                    ← Back to Product Info
                  </Button>
                  <Button variant="primary" onClick={handleReanalyze}>
                    Retry Analysis
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
