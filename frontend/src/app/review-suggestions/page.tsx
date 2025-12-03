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
  Select,
  Multiselect,
  Checkbox,
  ColumnLayout,
} from '@cloudscape-design/components';
import { useStore } from '@/lib/store';
import WorkflowNav from '@/components/WorkflowNav';
import DimensionManager from '@/components/DimensionManager';

const AWS_CATEGORY_GROUPS = [
  {
    label: 'AI Agents & Tools',
    options: [
      { label: 'AI Security', value: 'AI Security' },
      { label: 'Content Creation', value: 'Content Creation' },
      { label: 'Customer Experience Personalization', value: 'Customer Experience Personalization' },
      { label: 'Customer Support', value: 'Customer Support' },
      { label: 'Data Analysis', value: 'Data Analysis' },
      { label: 'Finance & Accounting', value: 'Finance & Accounting' },
      { label: 'IT Support', value: 'IT Support' },
      { label: 'Legal & Compliance', value: 'Legal & Compliance' },
      { label: 'Observability', value: 'Observability' },
      { label: 'Procurement & Supply Chain', value: 'Procurement & Supply Chain' },
      { label: 'Quality Assurance', value: 'Quality Assurance' },
      { label: 'Research', value: 'Research' },
      { label: 'Sales & Marketing', value: 'Sales & Marketing' },
      { label: 'Scheduling & Coordination', value: 'Scheduling & Coordination' },
      { label: 'Software Development', value: 'Software Development' },
    ],
  },
  {
    label: 'Infrastructure Software',
    options: [
      { label: 'Backup & Recovery', value: 'Backup & Recovery' },
      { label: 'Data Analytics', value: 'Data Analytics' },
      { label: 'Data Integration', value: 'Data Integration' },
      { label: 'Data Preparation', value: 'Data Preparation' },
      { label: 'ELT/ETL', value: 'ELT/ETL' },
      { label: 'Streaming Solutions', value: 'Streaming Solutions' },
      { label: 'Databases', value: 'Databases' },
      { label: 'Data Warehouses', value: 'Data Warehouses' },
      { label: 'Analytic Platforms', value: 'Analytic Platforms' },
      { label: 'Data Catalogs', value: 'Data Catalogs' },
      { label: 'Master Data Management', value: 'Master Data Management' },
      { label: 'Masking/Tokenization', value: 'Masking/Tokenization' },
      { label: 'Business Intelligence & Advanced Analytics', value: 'Business Intelligence & Advanced Analytics' },
      { label: 'High Performance Computing', value: 'High Performance Computing' },
      { label: 'Migration', value: 'Migration' },
      { label: 'Network Infrastructure', value: 'Network Infrastructure' },
      { label: 'Operating Systems', value: 'Operating Systems' },
      { label: 'Security', value: 'Security' },
      { label: 'Storage', value: 'Storage' },
    ],
  },
  {
    label: 'DevOps',
    options: [
      { label: 'Agile Lifecycle Management', value: 'Agile Lifecycle Management' },
      { label: 'Application Development', value: 'Application Development' },
      { label: 'Application Servers', value: 'Application Servers' },
      { label: 'Application Stacks', value: 'Application Stacks' },
      { label: 'Continuous Integration and Continuous Delivery', value: 'Continuous Integration and Continuous Delivery' },
      { label: 'Infrastructure as Code', value: 'Infrastructure as Code' },
      { label: 'Issue & Bug Tracking', value: 'Issue & Bug Tracking' },
      { label: 'Monitoring', value: 'Monitoring' },
      { label: 'Log Analysis', value: 'Log Analysis' },
      { label: 'Source Control', value: 'Source Control' },
      { label: 'Testing', value: 'Testing' },
    ],
  },
  {
    label: 'Business Applications',
    options: [
      { label: 'Blockchain', value: 'Blockchain' },
      { label: 'Collaboration & Productivity', value: 'Collaboration & Productivity' },
      { label: 'Contact Center', value: 'Contact Center' },
      { label: 'Content Management', value: 'Content Management' },
      { label: 'CRM', value: 'CRM' },
      { label: 'eCommerce', value: 'eCommerce' },
      { label: 'eLearning', value: 'eLearning' },
      { label: 'Human Resources', value: 'Human Resources' },
      { label: 'IT Business Management', value: 'IT Business Management' },
      { label: 'Project Management', value: 'Project Management' },
    ],
  },
  {
    label: 'IoT',
    options: [
      { label: 'Analytics', value: 'Analytics' },
      { label: 'Applications', value: 'Applications' },
      { label: 'Device Connectivity', value: 'Device Connectivity' },
      { label: 'Device Management', value: 'Device Management' },
      { label: 'Device Security', value: 'Device Security' },
      { label: 'Industrial IoT', value: 'Industrial IoT' },
      { label: 'Smart Home & City', value: 'Smart Home & City' },
    ],
  },
  {
    label: 'Industries',
    options: [
      { label: 'Education & Research', value: 'Education & Research' },
      { label: 'Financial Services', value: 'Financial Services' },
      { label: 'Healthcare & Life Sciences', value: 'Healthcare & Life Sciences' },
      { label: 'Media & Entertainment', value: 'Media & Entertainment' },
      { label: 'Industrial', value: 'Industrial' },
      { label: 'Energy', value: 'Energy' },
      { label: 'Automotive', value: 'Automotive' },
    ],
  },
  {
    label: 'Data',
    options: [
      { label: 'Financial Services Data', value: 'Financial Services Data' },
      { label: 'Retail, Location & Marketing Data', value: 'Retail, Location & Marketing Data' },
      { label: 'Public Sector Data', value: 'Public Sector Data' },
      { label: 'Healthcare & Life Sciences Data', value: 'Healthcare & Life Sciences Data' },
      { label: 'Resources Data', value: 'Resources Data' },
      { label: 'Media & Entertainment Data', value: 'Media & Entertainment Data' },
      { label: 'Telecommunications Data', value: 'Telecommunications Data' },
      { label: 'Environmental Data', value: 'Environmental Data' },
      { label: 'Automotive Data', value: 'Automotive Data' },
      { label: 'Manufacturing Data', value: 'Manufacturing Data' },
      { label: 'Gaming Data', value: 'Gaming Data' },
    ],
  },
  {
    label: 'Professional Services',
    options: [
      { label: 'Assessments', value: 'Assessments' },
      { label: 'Implementation', value: 'Implementation' },
      { label: 'Managed Services', value: 'Managed Services' },
      { label: 'Premium Support', value: 'Premium Support' },
      { label: 'Training', value: 'Training' },
    ],
  },
  {
    label: 'Machine Learning',
    options: [
      { label: 'Human Review Services', value: 'Human Review Services' },
      { label: 'ML Solutions', value: 'ML Solutions' },
      { label: 'Data Labeling Services', value: 'Data Labeling Services' },
      { label: 'Computer Vision', value: 'Computer Vision' },
      { label: 'Natural Language Processing', value: 'Natural Language Processing' },
      { label: 'Speech Recognition', value: 'Speech Recognition' },
      { label: 'Generative AI', value: 'Generative AI' },
      { label: 'Sentiment Analysis', value: 'Sentiment Analysis' },
      { label: 'Text to Speech', value: 'Text to Speech' },
      { label: 'Translation', value: 'Translation' },
      { label: 'Object Detection', value: 'Object Detection' },
      { label: 'Anomaly Detection', value: 'Anomaly Detection' },
      { label: 'Time-series Forecasting', value: 'Time-series Forecasting' },
    ],
  },
  {
    label: 'Cloud Operations',
    options: [
      { label: 'Cloud Governance', value: 'Cloud Governance' },
      { label: 'Cloud Financial Management', value: 'Cloud Financial Management' },
      { label: 'Monitoring and Observability', value: 'Monitoring and Observability' },
      { label: 'Compliance and Auditing', value: 'Compliance and Auditing' },
      { label: 'Operations Management', value: 'Operations Management' },
      { label: 'AIOps', value: 'AIOps' },
    ],
  },
];

export default function ReviewSuggestionsPage() {
  const router = useRouter();
  const { isAuthenticated, analysisResult, setListingData, setCurrentStep } = useStore();

  // Product Information
  const [productTitle, setProductTitle] = useState('');
  const [logoS3Url, setLogoS3Url] = useState('');
  const [shortDescription, setShortDescription] = useState('');
  const [longDescription, setLongDescription] = useState('');
  const [highlight1, setHighlight1] = useState('');
  const [highlight2, setHighlight2] = useState('');
  const [highlight3, setHighlight3] = useState('');
  const [categories, setCategories] = useState<any[]>([]);
  const [keywords, setKeywords] = useState('');

  // Support Information
  const [supportEmail, setSupportEmail] = useState('');
  const [fulfillmentUrl, setFulfillmentUrl] = useState('');
  const [supportDescription, setSupportDescription] = useState('');

  // Pricing
  const [pricingModel, setPricingModel] = useState<any>({ label: 'Contract', value: 'Contract' });
  const [dimensions, setDimensions] = useState<any[]>([]);
  const [contractDurations, setContractDurations] = useState<any[]>([]);
  const [purchasingOption, setPurchasingOption] = useState<any>({
    label: 'Multiple dimensions per contract',
    value: 'multiple',
  });

  // Refund Policy
  const [refundPolicy, setRefundPolicy] = useState('');

  // EULA
  const [eulaType, setEulaType] = useState<any>({ label: 'SCMP (Standard Contract)', value: 'scmp' });
  const [customEulaUrl, setCustomEulaUrl] = useState('');

  // Availability
  const [availabilityType, setAvailabilityType] = useState<any>({
    label: 'All countries (worldwide)',
    value: 'all',
  });
  const [excludedCountries, setExcludedCountries] = useState('');
  const [allowedCountries, setAllowedCountries] = useState('');

  // Publishing
  const [autoPublish, setAutoPublish] = useState(true);
  const [offerName, setOfferName] = useState('');
  const [offerDescription, setOfferDescription] = useState('');

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated || !analysisResult) {
      router.push('/');
      return;
    }

    // Populate form with AI suggestions
    setProductTitle(analysisResult.title?.substring(0, 72) || '');
    setShortDescription(analysisResult.short_description || '');
    setLongDescription(analysisResult.long_description || '');
    
    if (analysisResult.highlights && analysisResult.highlights.length > 0) {
      setHighlight1(analysisResult.highlights[0] || '');
      setHighlight2(analysisResult.highlights[1] || '');
      setHighlight3(analysisResult.highlights[2] || '');
    }

    if (analysisResult.categories) {
      setCategories(
        analysisResult.categories.map((cat: string) => ({ label: cat, value: cat }))
      );
    }

    if (analysisResult.search_keywords) {
      setKeywords(analysisResult.search_keywords.join(', '));
    }

    setSupportDescription(analysisResult.support_description || 'Professional support available');

    // Set pricing model
    const model = analysisResult.pricing_model || 'Contract';
    setPricingModel({ label: model, value: model });

    // Set default refund policy
    setRefundPolicy(
      `We offer a 30-day money-back guarantee. If you're not satisfied with the product, please contact support within 30 days of purchase to request a full refund.`
    );

    // Set default contract durations
    setContractDurations([
      { label: '12 Months', value: '12' },
    ]);

    // Set offer name/description
    setOfferName(analysisResult.title?.substring(0, 72) || '');
    setOfferDescription(analysisResult.short_description?.substring(0, 200) || '');
  }, [isAuthenticated, analysisResult, router]);

  const validateForm = () => {
    setError('');

    if (!productTitle || productTitle.length < 5 || productTitle.length > 72) {
      setError('Product title must be between 5 and 72 characters');
      return false;
    }

    if (!logoS3Url || !logoS3Url.startsWith('https://') || !logoS3Url.includes('.s3')) {
      setError('Logo S3 URL must be a valid HTTPS S3 URL');
      return false;
    }

    if (!shortDescription || !longDescription || !highlight1) {
      setError('Please fill in all required fields');
      return false;
    }

    if (categories.length === 0 || categories.length > 3) {
      setError('Please select 1-3 categories');
      return false;
    }

    if (!supportEmail || !fulfillmentUrl || !supportDescription) {
      setError('Please fill in all support information');
      return false;
    }

    if (dimensions.length === 0) {
      setError('Please add at least one pricing dimension');
      return false;
    }

    // Validate dimensions based on pricing model
    const dimTypes = new Set(dimensions.map((d: any) => d.type));

    if (pricingModel.value === 'Contract' && !dimTypes.has('Entitled')) {
      setError('Contract model requires at least one Entitled dimension');
      return false;
    }

    if (pricingModel.value === 'Usage' && !dimTypes.has('Metered')) {
      setError('Usage model requires at least one Metered dimension');
      return false;
    }

    if (pricingModel.value === 'Contract with Consumption') {
      if (!dimTypes.has('Entitled') || !dimTypes.has('Metered')) {
        setError('Hybrid model requires at least one Entitled and one Metered dimension');
        return false;
      }
    }

    if (!refundPolicy) {
      setError('Please provide a refund policy');
      return false;
    }

    if (eulaType.value === 'custom' && !customEulaUrl) {
      setError('Please provide Custom EULA S3 URL');
      return false;
    }

    return true;
  };

  const handleCreateListing = () => {
    if (!validateForm()) {
      return;
    }

    const highlights = [highlight1, highlight2, highlight3].filter(Boolean);

    const listingData = {
      title: productTitle,
      logo_s3_url: logoS3Url,
      short_description: shortDescription,
      long_description: longDescription,
      highlights,
      categories: categories.map((c) => c.value),
      search_keywords: keywords.split(',').map((k) => k.trim()).filter(Boolean),
      support_email: supportEmail,
      fulfillment_url: fulfillmentUrl,
      support_description: supportDescription,
      pricing_model: pricingModel.value === 'Contract with Consumption' ? 'Contract' : pricingModel.value,
      ui_pricing_model: pricingModel.value,
      pricing_dimensions: dimensions,
      contract_durations: contractDurations.map((d) => d.label),
      purchasing_option: purchasingOption.value,
      refund_policy: refundPolicy,
      eula_type: eulaType.value,
      custom_eula_url: customEulaUrl || undefined,
      availability_type: availabilityType.value,
      excluded_countries: excludedCountries.split(',').map((c) => c.trim()).filter(Boolean),
      allowed_countries: allowedCountries.split(',').map((c) => c.trim()).filter(Boolean),
      auto_publish_to_limited: autoPublish,
      offer_name: offerName,
      offer_description: offerDescription,
    };

    setListingData(listingData);
    setCurrentStep('create_listing');
    router.push('/create-listing');
  };

  if (!isAuthenticated || !analysisResult) {
    return null;
  }

  return (
    <>
      <AppLayout
        navigation={<WorkflowNav />}
        toolsHide
        breadcrumbs={
        <BreadcrumbGroup
          items={[
            { text: 'Home', href: '/' },
            { text: 'Product Information', href: '/product-info' },
            { text: 'AI Analysis', href: '/ai-analysis' },
            { text: 'Review Suggestions', href: '/review-suggestions' },
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
              description="Review and edit the AI-generated content before creating your listing"
            >
              Review AI-Generated Content
            </Header>
          }
        >
          <form onSubmit={(e) => { e.preventDefault(); handleCreateListing(); }}>
            <Form
              actions={
                <SpaceBetween direction="horizontal" size="xs">
                  <Button onClick={() => router.push('/ai-analysis')}>
                    ← Back
                  </Button>
                  <Button
                    variant="primary"
                    onClick={handleCreateListing}
                    loading={loading}
                  >
                    Create Listing 🚀
                  </Button>
                </SpaceBetween>
              }
            >
              <SpaceBetween size="l">
                {error && (
                  <Alert type="error" dismissible onDismiss={() => setError('')}>
                    {error}
                  </Alert>
                )}

                {/* Product Information */}
                <Container header={<Header variant="h2">Product Information</Header>}>
                  <SpaceBetween size="l">
                    <FormField
                      label="Product Title"
                      description={`${productTitle.length}/72 characters`}
                      constraintText="Required (5-72 characters)"
                    >
                      <Input
                        value={productTitle}
                        onChange={({ detail }) => setProductTitle(detail.value)}
                        placeholder="Your Product Name"
                      />
                    </FormField>

                    <FormField
                      label="Logo S3 URL"
                      description="S3 URL to your product logo (PNG/JPG, min 110x110px)"
                      constraintText="Required"
                    >
                      <Input
                        value={logoS3Url}
                        onChange={({ detail }) => setLogoS3Url(detail.value)}
                        placeholder="https://your-bucket.s3.amazonaws.com/logo.png"
                        type="url"
                      />
                    </FormField>

                    <FormField
                      label="Short Description"
                      description="Brief description for search results (10-500 characters)"
                      constraintText="Required"
                    >
                      <Textarea
                        value={shortDescription}
                        onChange={({ detail }) => setShortDescription(detail.value)}
                        rows={3}
                      />
                    </FormField>

                    <FormField
                      label="Long Description"
                      description="Detailed description with benefits (50-5000 characters)"
                      constraintText="Required"
                    >
                      <Textarea
                        value={longDescription}
                        onChange={({ detail }) => setLongDescription(detail.value)}
                        rows={8}
                      />
                    </FormField>

                    <FormField
                      label="Highlights"
                      description="Key features or benefits (1 required, 2 optional)"
                    >
                      <SpaceBetween size="s">
                        <Input
                          value={highlight1}
                          onChange={({ detail }) => setHighlight1(detail.value)}
                          placeholder="Highlight 1 (required)"
                        />
                        <Input
                          value={highlight2}
                          onChange={({ detail }) => setHighlight2(detail.value)}
                          placeholder="Highlight 2 (optional)"
                        />
                        <Input
                          value={highlight3}
                          onChange={({ detail }) => setHighlight3(detail.value)}
                          placeholder="Highlight 3 (optional)"
                        />
                      </SpaceBetween>
                    </FormField>

                    <ColumnLayout columns={2}>
                      <FormField
                        label="Categories"
                        description="Select 1-3 categories"
                        constraintText="Required"
                      >
                        <Multiselect
                          selectedOptions={categories}
                          onChange={({ detail }) => setCategories([...detail.selectedOptions])}
                          options={AWS_CATEGORY_GROUPS}
                          placeholder="Select categories"
                          filteringType="auto"
                        />
                      </FormField>

                      <FormField
                        label="Search Keywords"
                        description="Comma-separated keywords"
                        constraintText="Required"
                      >
                        <Input
                          value={keywords}
                          onChange={({ detail }) => setKeywords(detail.value)}
                          placeholder="saas, cloud, software"
                        />
                      </FormField>
                    </ColumnLayout>
                  </SpaceBetween>
                </Container>

                {/* Support Information */}
                <Container header={<Header variant="h2">Support Information</Header>}>
                  <SpaceBetween size="l">
                    <ColumnLayout columns={2}>
                      <FormField label="Support Email" constraintText="Required">
                        <Input
                          value={supportEmail}
                          onChange={({ detail }) => setSupportEmail(detail.value)}
                          placeholder="support@example.com"
                          type="email"
                        />
                      </FormField>

                      <FormField label="Fulfillment URL" constraintText="Required">
                        <Input
                          value={fulfillmentUrl}
                          onChange={({ detail }) => setFulfillmentUrl(detail.value)}
                          placeholder="https://yourapp.com/signup"
                          type="url"
                        />
                      </FormField>
                    </ColumnLayout>

                    <FormField
                      label="Support Description"
                      description="Describe your support offerings"
                      constraintText="Required"
                    >
                      <Textarea
                        value={supportDescription}
                        onChange={({ detail }) => setSupportDescription(detail.value)}
                        rows={4}
                      />
                    </FormField>
                  </SpaceBetween>
                </Container>

                {/* Pricing Configuration */}
                <Container header={<Header variant="h2">Pricing Configuration</Header>}>
                  <SpaceBetween size="l">
                    <FormField
                      label="Pricing Model"
                      description="Select the pricing model for your product"
                    >
                      <Select
                        selectedOption={pricingModel}
                        onChange={({ detail }) => setPricingModel(detail.selectedOption)}
                        options={[
                          { label: 'Contract', value: 'Contract' },
                          { label: 'Usage', value: 'Usage' },
                          { label: 'Contract with Consumption', value: 'Contract with Consumption' },
                        ]}
                      />
                    </FormField>

                    <DimensionManager
                      dimensions={dimensions}
                      onChange={setDimensions}
                      pricingModel={pricingModel.value}
                      suggestedDimensions={
                        Array.isArray(analysisResult.pricing_dimensions)
                          ? analysisResult.pricing_dimensions.map((d: any) => typeof d === 'string' ? d : d.name || d)
                          : []
                      }
                    />

                    {(pricingModel.value === 'Contract' || pricingModel.value === 'Contract with Consumption') && (
                      <>
                        <FormField
                          label="Contract Durations"
                          description="Select available contract lengths"
                        >
                          <Multiselect
                            selectedOptions={contractDurations}
                            onChange={({ detail }) => setContractDurations([...detail.selectedOptions])}
                            options={[
                              { label: '1 Month', value: '1' },
                              { label: '3 Months', value: '3' },
                              { label: '6 Months', value: '6' },
                              { label: '12 Months', value: '12' },
                              { label: '24 Months', value: '24' },
                              { label: '36 Months', value: '36' },
                            ]}
                            placeholder="Select durations"
                          />
                        </FormField>

                        <FormField label="Purchasing Options">
                          <Select
                            selectedOption={purchasingOption}
                            onChange={({ detail }) => setPurchasingOption(detail.selectedOption)}
                            options={[
                              { label: 'Multiple dimensions per contract', value: 'multiple' },
                              { label: 'Single dimension per contract', value: 'single' },
                            ]}
                          />
                        </FormField>
                      </>
                    )}
                  </SpaceBetween>
                </Container>

                {/* Refund Policy */}
                <Container header={<Header variant="h2">Refund Policy</Header>}>
                  <FormField
                    label="Refund Policy"
                    description="50-5000 characters"
                    constraintText="Required"
                  >
                    <Textarea
                      value={refundPolicy}
                      onChange={({ detail }) => setRefundPolicy(detail.value)}
                      rows={4}
                    />
                  </FormField>
                </Container>

                {/* EULA Configuration */}
                <Container header={<Header variant="h2">EULA Configuration</Header>}>
                  <SpaceBetween size="l">
                    <FormField label="EULA Type">
                      <Select
                        selectedOption={eulaType}
                        onChange={({ detail }) => setEulaType(detail.selectedOption)}
                        options={[
                          { label: 'SCMP (Standard Contract)', value: 'scmp' },
                          { label: 'Custom EULA', value: 'custom' },
                        ]}
                      />
                    </FormField>

                    {eulaType.value === 'custom' && (
                      <FormField
                        label="Custom EULA S3 URL"
                        constraintText="Required for custom EULA"
                      >
                        <Input
                          value={customEulaUrl}
                          onChange={({ detail }) => setCustomEulaUrl(detail.value)}
                          placeholder="https://your-bucket.s3.amazonaws.com/eula.pdf"
                          type="url"
                        />
                      </FormField>
                    )}
                  </SpaceBetween>
                </Container>

                {/* Geographic Availability */}
                <Container header={<Header variant="h2">Geographic Availability</Header>}>
                  <SpaceBetween size="l">
                    <FormField label="Availability Type">
                      <Select
                        selectedOption={availabilityType}
                        onChange={({ detail }) => setAvailabilityType(detail.selectedOption)}
                        options={[
                          { label: 'All countries (worldwide)', value: 'all' },
                          { label: 'All countries except specific ones', value: 'exclude' },
                          { label: 'Only specific countries', value: 'include' },
                        ]}
                      />
                    </FormField>

                    {availabilityType.value === 'exclude' && (
                      <FormField
                        label="Excluded Country Codes"
                        description="Comma-separated ISO codes (e.g., US, GB, DE)"
                      >
                        <Input
                          value={excludedCountries}
                          onChange={({ detail }) => setExcludedCountries(detail.value)}
                          placeholder="US, GB, DE"
                        />
                      </FormField>
                    )}

                    {availabilityType.value === 'include' && (
                      <FormField
                        label="Allowed Country Codes"
                        description="Comma-separated ISO codes (e.g., US, GB, DE)"
                        constraintText="Required"
                      >
                        <Input
                          value={allowedCountries}
                          onChange={({ detail }) => setAllowedCountries(detail.value)}
                          placeholder="US, GB, DE"
                        />
                      </FormField>
                    )}
                  </SpaceBetween>
                </Container>

                {/* Publishing Options */}
                <Container header={<Header variant="h2">Publishing Options</Header>}>
                  <SpaceBetween size="l">
                    <Checkbox
                      checked={autoPublish}
                      onChange={({ detail }) => setAutoPublish(detail.checked)}
                    >
                      Automatically publish to Limited stage after creation
                    </Checkbox>

                    {autoPublish && (
                      <Alert type="info">
                        Your listing will be published to Limited stage automatically. You can test
                        it immediately with your AWS account.
                      </Alert>
                    )}

                    {autoPublish && (
                      <ColumnLayout columns={2}>
                        <FormField label="Offer Name">
                          <Input
                            value={offerName}
                            onChange={({ detail }) => setOfferName(detail.value)}
                          />
                        </FormField>

                        <FormField label="Offer Description">
                          <Input
                            value={offerDescription}
                            onChange={({ detail }) => setOfferDescription(detail.value)}
                          />
                        </FormField>
                      </ColumnLayout>
                    )}
                  </SpaceBetween>
                </Container>
              </SpaceBetween>
            </Form>
          </form>
        </ContentLayout>
      }
      />
    </>
  );
}
