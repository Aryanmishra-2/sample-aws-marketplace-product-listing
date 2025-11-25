'use client';

import { useState, useEffect } from 'react';
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
  ContentLayout,
  BreadcrumbGroup,
  Textarea,
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';

export default function ProductInfoPage() {
  const router = useRouter();
  const { isAuthenticated, setProductContext, setCurrentStep, productContext } = useStore();
  
  const [websiteUrl, setWebsiteUrl] = useState(productContext?.product_urls?.[0] || '');
  const [docsUrl, setDocsUrl] = useState(productContext?.documentation_url || '');
  const [pricingUrl, setPricingUrl] = useState('');
  const [description, setDescription] = useState(productContext?.product_description || '');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  const handleContinue = () => {
    if (!websiteUrl) {
      setError('Please provide at least your product website URL');
      return;
    }

    // Store context
    setProductContext({
      product_name: '',
      product_description: description,
      product_urls: [websiteUrl, pricingUrl].filter(Boolean),
      documentation_url: docsUrl || undefined,
      additional_context: undefined,
    });

    setCurrentStep('analyze_product');
    router.push('/ai-analysis');
  };

  const handleBack = () => {
    setCurrentStep('welcome');
    router.push('/welcome');
  };

  if (!isAuthenticated) {
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
              description="Provide your product information so our AI can analyze it and create your marketplace listing"
            >
              Product Information
            </Header>
          }
        >
          <SpaceBetween size="l">
            {error && (
              <Alert type="error" dismissible onDismiss={() => setError('')}>
                {error}
              </Alert>
            )}

            <Container
              header={
                <Header
                  variant="h2"
                  description="Enter URLs and information about your product"
                >
                  Product URLs
                </Header>
              }
            >
              <form onSubmit={(e) => { e.preventDefault(); handleContinue(); }}>
                <Form
                  actions={
                    <SpaceBetween direction="horizontal" size="xs">
                      <Button onClick={handleBack}>
                        Back
                      </Button>
                      <Button variant="primary" onClick={handleContinue}>
                        Continue →
                      </Button>
                    </SpaceBetween>
                  }
                >
                  <SpaceBetween size="l">
                    <FormField
                      label="Product Website"
                      description="Main product website or landing page"
                      constraintText="Required"
                    >
                      <Input
                        value={websiteUrl}
                        onChange={({ detail }) => setWebsiteUrl(detail.value)}
                        placeholder="https://yourproduct.com"
                        type="url"
                      />
                    </FormField>

                    <FormField
                      label="Documentation URL"
                      description="Technical documentation or user guides"
                    >
                      <Input
                        value={docsUrl}
                        onChange={({ detail }) => setDocsUrl(detail.value)}
                        placeholder="https://docs.yourproduct.com"
                        type="url"
                      />
                    </FormField>

                    <FormField
                      label="Pricing Page"
                      description="Your existing pricing page if available"
                    >
                      <Input
                        value={pricingUrl}
                        onChange={({ detail }) => setPricingUrl(detail.value)}
                        placeholder="https://yourproduct.com/pricing"
                        type="url"
                      />
                    </FormField>

                    <FormField
                      label="Product Description"
                      description="Brief description of your product (optional, helps AI generate better content)"
                    >
                      <Textarea
                        value={description}
                        onChange={({ detail }) => setDescription(detail.value)}
                        placeholder="Describe your product, its key features, and target audience..."
                        rows={6}
                      />
                    </FormField>
                  </SpaceBetween>
                </Form>
              </form>
            </Container>
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}
