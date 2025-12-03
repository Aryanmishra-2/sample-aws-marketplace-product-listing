'use client';

import { useStore } from '@/lib/store';
import { useRouter, usePathname } from 'next/navigation';
import { Box, SpaceBetween, StatusIndicator } from '@cloudscape-design/components';
import { useState, useEffect } from 'react';

const WORKFLOW_STAGES = [
  { 
    key: 'credentials', 
    label: 'Credentials', 
    path: '/',
    icon: '🔑',
    description: 'AWS Credentials'
  },
  { 
    key: 'seller_registration', 
    label: 'Seller Registration', 
    path: '/seller-registration',
    icon: '🏢',
    description: 'Seller Profile'
  },
  { 
    key: 'gather_context', 
    label: 'Product Information', 
    path: '/product-info',
    icon: '📝',
    description: 'Product Details'
  },
  { 
    key: 'analyze_product', 
    label: 'AI Analysis', 
    path: '/ai-analysis',
    icon: '🤖',
    description: 'AI Processing'
  },
  { 
    key: 'review_suggestions', 
    label: 'Review Suggestions', 
    path: '/review-suggestions',
    icon: '✏️',
    description: 'Review & Edit'
  },
  { 
    key: 'create_listing', 
    label: 'Create Listing', 
    path: '/create-listing',
    icon: '📦',
    description: 'Publish Product'
  },
  { 
    key: 'saas_deployment', 
    label: 'SaaS Integration', 
    path: '/saas-integration',
    icon: '🔧',
    description: 'Deploy Infrastructure'
  },
];

export default function WorkflowNav() {
  const { accountInfo, currentStep, completedSteps } = useStore();
  const router = useRouter();
  const pathname = usePathname();
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted || !accountInfo) {
    return null;
  }

  const currentStepIndex = WORKFLOW_STAGES.findIndex(s => s.key === currentStep);

  const getStepStatus = (stage: typeof WORKFLOW_STAGES[0], index: number) => {
    if (completedSteps.includes(stage.key as any)) {
      return 'completed';
    }
    if (stage.key === currentStep || pathname === stage.path) {
      return 'current';
    }
    if (index < currentStepIndex) {
      return 'completed';
    }
    return 'pending';
  };

  const handleNavigation = (stage: typeof WORKFLOW_STAGES[0]) => {
    router.push(stage.path);
  };

  return (
    <div
      style={{
        backgroundColor: '#fafafa',
        borderRight: '1px solid #d5dbdb',
        padding: '20px 16px',
        minHeight: 'calc(100vh - 120px)',
        width: '280px',
      }}
    >
      <SpaceBetween size="xs">
        <Box variant="h3" padding={{ bottom: 's' }}>
          Workflow Stages
        </Box>
        
        {WORKFLOW_STAGES.map((stage, index) => {
          const status = getStepStatus(stage, index);
          const isClickable = status === 'completed' || status === 'current';
          
          return (
            <div
              key={stage.key}
              onClick={() => isClickable && handleNavigation(stage)}
              style={{
                padding: '12px',
                borderRadius: '8px',
                backgroundColor: status === 'current' ? '#fff8f0' : 'white',
                border: status === 'current' ? '2px solid #ff9900' : '1px solid #d5dbdb',
                cursor: isClickable ? 'pointer' : 'not-allowed',
                opacity: status === 'pending' ? 0.6 : 1,
                transition: 'all 0.2s ease',
                position: 'relative',
              }}
              onMouseEnter={(e) => {
                if (isClickable) {
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
                  e.currentTarget.style.transform = 'translateX(4px)';
                }
              }}
              onMouseLeave={(e) => {
                if (isClickable) {
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.transform = 'translateX(0)';
                }
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <div style={{ 
                  fontSize: '24px',
                  minWidth: '32px',
                  textAlign: 'center'
                }}>
                  {stage.icon}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ 
                    fontWeight: status === 'current' ? 'bold' : '600',
                    fontSize: '14px',
                    color: status === 'current' ? '#ff9900' : '#232f3e',
                    marginBottom: '4px'
                  }}>
                    {stage.label}
                  </div>
                  <div style={{ 
                    fontSize: '12px',
                    color: '#545b64',
                    marginBottom: '6px'
                  }}>
                    {stage.description}
                  </div>
                  <div>
                    {status === 'completed' && (
                      <StatusIndicator type="success">Completed</StatusIndicator>
                    )}
                    {status === 'current' && (
                      <StatusIndicator type="in-progress">In Progress</StatusIndicator>
                    )}
                    {status === 'pending' && (
                      <StatusIndicator type="pending">Pending</StatusIndicator>
                    )}
                  </div>
                </div>
              </div>
              
              <div style={{
                position: 'absolute',
                top: '8px',
                right: '8px',
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                backgroundColor: status === 'completed' ? '#037f0c' : status === 'current' ? '#ff9900' : '#d5dbdb',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                {status === 'completed' ? '✓' : index + 1}
              </div>
            </div>
          );
        })}
      </SpaceBetween>
      
      <Box padding={{ top: 'l' }} fontSize="body-s" color="text-body-secondary">
        Click on completed stages to navigate
      </Box>
    </div>
  );
}
