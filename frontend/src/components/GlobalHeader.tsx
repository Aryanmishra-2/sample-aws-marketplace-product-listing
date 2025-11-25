'use client';

import { Box, SpaceBetween, ProgressBar, Badge } from '@cloudscape-design/components';
import { useStore } from '@/lib/store';

const WORKFLOW_STEPS = [
  { key: 'credentials', label: 'Credentials', progress: 0 },
  { key: 'welcome', label: 'Welcome', progress: 10 },
  { key: 'gather_context', label: 'Product Info', progress: 25 },
  { key: 'analyze_product', label: 'AI Analysis', progress: 40 },
  { key: 'review_suggestions', label: 'Review', progress: 55 },
  { key: 'create_listing', label: 'Create Listing', progress: 70 },
  { key: 'saas_deployment', label: 'SaaS Deploy', progress: 85 },
  { key: 'workflow_orchestrator', label: 'Complete', progress: 100 },
];

export default function GlobalHeader() {
  const { accountInfo, currentStep, productId, clearCredentials } = useStore();

  if (!accountInfo) {
    return null;
  }

  const handleClearData = () => {
    if (confirm('Are you sure you want to clear all data? This will log you out and cannot be undone.')) {
      clearCredentials();
      window.location.href = '/';
    }
  };

  const handleHome = () => {
    window.location.href = '/';
  };

  const currentStepData = WORKFLOW_STEPS.find(s => s.key === currentStep) || WORKFLOW_STEPS[0];
  const progressValue = currentStepData.progress;

  // Extract user name from ARN
  const userName = accountInfo.user_arn.split('/').pop() || 'Unknown';

  // Determine organization badge color
  const getOrgBadgeColor = () => {
    if (accountInfo.region_type === 'AWS_INC') return 'blue';
    if (accountInfo.region_type === 'AWS_INDIA') return 'green';
    return 'grey';
  };

  return (
    <div
      style={{
        backgroundColor: '#232f3e',
        color: 'white',
        padding: '12px 20px',
        borderBottom: '2px solid #ff9900',
      }}
    >
      <SpaceBetween size="s">
        {/* Account Info Row */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <SpaceBetween size="l" direction="horizontal">
            <div>
              <div style={{ fontSize: '12px', color: '#aab7b8', marginBottom: '4px' }}>
                AWS Account
              </div>
              <div style={{ fontWeight: 'bold', fontSize: '16px', color: 'white' }}>
                {accountInfo.account_id}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '12px', color: '#aab7b8', marginBottom: '4px' }}>
                IAM User
              </div>
              <div style={{ fontWeight: 'bold', fontSize: '16px', color: 'white' }}>
                {userName}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '12px', color: '#aab7b8', marginBottom: '4px' }}>
                Organization
              </div>
              <div style={{ marginTop: '4px' }}>
                <Badge color={getOrgBadgeColor()}>
                  {accountInfo.organization}
                </Badge>
              </div>
            </div>

            {productId && (
              <div>
                <div style={{ fontSize: '12px', color: '#aab7b8', marginBottom: '4px' }}>
                  Product ID
                </div>
                <div style={{ fontWeight: 'bold', fontSize: '16px', color: '#ff9900' }}>
                  {productId.substring(0, 20)}...
                </div>
              </div>
            )}
          </SpaceBetween>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '12px', color: '#aab7b8', textAlign: 'right', marginBottom: '4px' }}>
                Current Step
              </div>
              <div style={{ fontWeight: 'bold', fontSize: '16px', color: '#ff9900' }}>
                {currentStepData.label}
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={handleHome}
                style={{
                  backgroundColor: '#232f3e',
                  color: 'white',
                  border: '1px solid #ff9900',
                  borderRadius: '4px',
                  padding: '8px 16px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                }}
              >
                🏠 Home
              </button>
              <button
                onClick={handleClearData}
                style={{
                  backgroundColor: '#d13212',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '8px 16px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                }}
              >
                🗑️ Clear Data
              </button>
            </div>
          </div>
        </div>

        {/* Progress Bar Row */}
        <div style={{ marginTop: '8px' }}>
          <div style={{ 
            backgroundColor: '#e9ebed',
            borderRadius: '4px',
            height: '8px',
            overflow: 'hidden',
            position: 'relative'
          }}>
            <div style={{
              backgroundColor: progressValue === 100 ? '#037f0c' : '#0073bb',
              height: '100%',
              width: `${progressValue}%`,
              transition: 'width 0.3s ease-in-out',
              boxShadow: progressValue > 0 ? '0 0 8px rgba(0, 115, 187, 0.5)' : 'none'
            }} />
          </div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            marginTop: '4px',
            fontSize: '12px',
            color: '#aab7b8'
          }}>
            <span>Step {WORKFLOW_STEPS.findIndex(s => s.key === currentStep) + 1} of {WORKFLOW_STEPS.length}</span>
            <span style={{ color: progressValue === 100 ? '#037f0c' : '#ff9900', fontWeight: 'bold' }}>{progressValue}%</span>
          </div>
        </div>
      </SpaceBetween>
    </div>
  );
}
