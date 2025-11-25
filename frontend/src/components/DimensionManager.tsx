'use client';

import { useState } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  FormField,
  Input,
  Button,
  Box,
  Alert,
  Select,
  ExpandableSection,
} from '@cloudscape-design/components';

interface Dimension {
  name: string;
  key: string;
  description: string;
  type: 'Entitled' | 'Metered';
}

interface DimensionManagerProps {
  dimensions: Dimension[];
  onChange: (dimensions: Dimension[]) => void;
  pricingModel: 'Contract' | 'Usage' | 'Contract with Consumption';
  suggestedDimensions?: string[];
}

export default function DimensionManager({
  dimensions,
  onChange,
  pricingModel,
  suggestedDimensions = [],
}: DimensionManagerProps) {
  const [dimName, setDimName] = useState('');
  const [dimKey, setDimKey] = useState('');
  const [dimDescription, setDimDescription] = useState('');
  const [dimType, setDimType] = useState<'Entitled' | 'Metered'>('Entitled');
  const [error, setError] = useState('');

  const allowTypeSelection = pricingModel === 'Contract with Consumption';
  const defaultType = pricingModel === 'Usage' ? 'Metered' : 'Entitled';

  const handleAddDimension = () => {
    setError('');

    if (!dimName || !dimKey || !dimDescription) {
      setError('All fields (Name, Key, and Description) are required');
      return;
    }

    // Check for duplicate keys
    if (dimensions.some((d) => d.key === dimKey)) {
      setError('A dimension with this key already exists');
      return;
    }

    const newDimension: Dimension = {
      name: dimName,
      key: dimKey,
      description: dimDescription,
      type: allowTypeSelection ? dimType : defaultType,
    };

    onChange([...dimensions, newDimension]);

    // Clear form
    setDimName('');
    setDimKey('');
    setDimDescription('');
    setDimType('Entitled');
  };

  const handleRemoveDimension = (index: number) => {
    onChange(dimensions.filter((_, i) => i !== index));
  };

  const getTypeLabel = () => {
    if (pricingModel === 'Usage') return 'Metered';
    if (pricingModel === 'Contract') return 'Entitled';
    return dimType;
  };

  return (
    <Container
      header={
        <Header
          variant="h3"
          description="Define what customers will be charged for"
        >
          Pricing Dimensions
        </Header>
      }
    >
      <SpaceBetween size="l">
        {suggestedDimensions.length > 0 && (
          <Alert type="info" header="AI Suggested Dimensions">
            {suggestedDimensions.join(', ')}
          </Alert>
        )}

        {pricingModel === 'Usage' && (
          <Alert type="info">
            Usage-based pricing: Customers pay for what they use (metered dimensions)
          </Alert>
        )}

        {pricingModel === 'Contract' && (
          <Alert type="info">
            Contract-based pricing: Customers pay upfront for entitled dimensions
          </Alert>
        )}

        {pricingModel === 'Contract with Consumption' && (
          <Alert type="info">
            Hybrid pricing: Customers commit to a contract with entitled dimensions, plus pay for
            additional usage beyond their entitlement (metered dimensions)
          </Alert>
        )}

        {/* Show existing dimensions */}
        {dimensions.length > 0 && (
          <Box>
            <Box variant="h4" margin={{ bottom: 's' }}>
              Added Dimensions ({dimensions.length})
            </Box>
            <SpaceBetween size="s">
              {dimensions.map((dim, index) => (
                <Box key={index}>
                  <SpaceBetween size="xs" direction="horizontal">
                    <div style={{ flex: 1 }}>
                      <Box variant="strong">{dim.name}</Box>
                      <Box variant="small" color="text-body-secondary">
                        {dim.key} - {dim.type}
                      </Box>
                      <Box variant="small">{dim.description}</Box>
                    </div>
                    <Button onClick={() => handleRemoveDimension(index)}>
                      Remove
                    </Button>
                  </SpaceBetween>
                </Box>
              ))}
            </SpaceBetween>
          </Box>
        )}

        {/* Add dimension form */}
        <ExpandableSection
          headerText="Add Dimension"
          variant="container"
          defaultExpanded={dimensions.length === 0}
        >
          <SpaceBetween size="m">
            {error && (
              <Alert type="error" dismissible onDismiss={() => setError('')}>
                {error}
              </Alert>
            )}

            <FormField
              label="Dimension Name"
              description="e.g., Active Users"
              constraintText="Required"
            >
              <Input
                value={dimName}
                onChange={({ detail }) => setDimName(detail.value)}
                placeholder="Active Users"
              />
            </FormField>

            <FormField
              label="Dimension Key"
              description="e.g., users (lowercase, no spaces)"
              constraintText="Required"
            >
              <Input
                value={dimKey}
                onChange={({ detail }) => setDimKey(detail.value)}
                placeholder="users"
              />
            </FormField>

            <FormField
              label="Description"
              description="e.g., Number of active users per month"
              constraintText="Required"
            >
              <Input
                value={dimDescription}
                onChange={({ detail }) => setDimDescription(detail.value)}
                placeholder="Number of active users per month"
              />
            </FormField>

            {allowTypeSelection && (
              <FormField
                label="Dimension Type"
                description="Entitled: Included in contract. Metered: Pay-per-use overages."
              >
                <Select
                  selectedOption={{ label: dimType, value: dimType }}
                  onChange={({ detail }) =>
                    setDimType(detail.selectedOption.value as 'Entitled' | 'Metered')
                  }
                  options={[
                    { label: 'Entitled', value: 'Entitled' },
                    { label: 'Metered', value: 'Metered' },
                  ]}
                />
              </FormField>
            )}

            {!allowTypeSelection && (
              <Alert type="info">
                Dimension type: <strong>{getTypeLabel()}</strong> (based on pricing model)
              </Alert>
            )}

            <Button variant="primary" onClick={handleAddDimension}>
              Add Dimension
            </Button>
          </SpaceBetween>
        </ExpandableSection>
      </SpaceBetween>
    </Container>
  );
}
