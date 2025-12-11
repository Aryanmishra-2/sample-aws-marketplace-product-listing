'use client';

import { useStore } from '@/lib/store';

const WORKFLOW_STEPS = [
  { key: 'credentials', label: 'Credentials', progress: 0 },
  { key: 'welcome', label: 'Welcome', progress: 10 },
  { key: 'gather_context', label: 'Product Info', progress: 20 },
  { key: 'analyze_product', label: 'AI Analysis', progress: 35 },
  { key: 'review_suggestions', label: 'Review', progress: 50 },
  { key: 'create_listing', label: 'Create Listing', progress: 65 },
  { key: 'saas_deployment', label: 'SaaS Deploy', progress: 80 },
  { key: 'workflow_orchestrator', label: 'Complete', progress: 100 },
];

export default function ProgressBar() {
  const { accountInfo, currentStep } = useStore();

  if (!accountInfo) {
    return null;
  }

  const currentStepData = WORKFLOW_STEPS.find(s => s.key === currentStep) || WORKFLOW_STEPS[0];
  const progressValue = currentStepData.progress;

  return (
    <div
      style={{
        backgroundColor: 'white',
        padding: '16px 20px',
        borderBottom: '1px solid #d5dbdb',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.05)',
      }}
    >
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#232f3e' }}>
            {currentStepData.label}
          </div>
          <div style={{ fontSize: '12px', color: '#545b64' }}>
            Step {WORKFLOW_STEPS.findIndex(s => s.key === currentStep) + 1} of {WORKFLOW_STEPS.length}
          </div>
        </div>
        <div style={{ 
          backgroundColor: '#f2f3f3',
          borderRadius: '4px',
          height: '8px',
          overflow: 'hidden',
          position: 'relative',
          border: '1px solid #d5dbdb'
        }}>
          <div style={{
            background: progressValue === 100 
              ? 'linear-gradient(90deg, #037f0c, #05a30f)' 
              : 'linear-gradient(90deg, #ff9900, #ec7211)',
            height: '100%',
            width: `${progressValue}%`,
            transition: 'width 0.3s ease-in-out',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent)',
              animation: progressValue < 100 ? 'shimmer 2s infinite' : 'none'
            }} />
          </div>
        </div>
        <div style={{ 
          marginTop: '4px',
          fontSize: '12px',
          color: progressValue === 100 ? '#037f0c' : '#ff9900',
          fontWeight: 'bold',
          textAlign: 'right'
        }}>
          {progressValue}% Complete
        </div>
      </div>
    </div>
  );
}
