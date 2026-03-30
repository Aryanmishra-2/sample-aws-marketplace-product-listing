// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
'use client';

import { useStore } from '@/lib/store';
import { useRouter, usePathname } from 'next/navigation';
import { Box, SpaceBetween, StatusIndicator } from '@cloudscape-design/components';
import { useState, useEffect } from 'react';

interface WorkflowStage {
  key: string;
  label: string;
  path: string;
  icon: string;
  description: string;
}

const WORKFLOW_STAGES: WorkflowStage[] = [
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

  // Map store step keys to WorkflowNav stage keys
  const stepKeyMapping: Record<string, string> = {
    'credentials': 'credentials',
    'seller_registration': 'seller_registration',
    'gather_context': 'gather_context',
    'ai_analysis': 'analyze_product',
    'review_suggestions': 'review_suggestions',
    'create_listing': 'create_listing',
    'listing_success': 'create_listing',
    'saas_deployment': 'saas_deployment',
  };

  const getStepStatus = (stage: WorkflowStage, index: number) => {
    // Find the current page's stage index based on pathname
    const currentPageIndex = WORKFLOW_STAGES.findIndex(s => s.path === pathname);
    
    // Check if this is the current page - takes highest priority
    if (pathname === stage.path) {
      return 'current';
    }
    
    // If we're on a valid workflow page, use pathname-based logic
    if (currentPageIndex >= 0) {
      // Stages before the current page are completed
      if (index < currentPageIndex) {
        return 'completed';
      }
      // Stages after the current page are pending
      return 'pending';
    }
    
    // Fallback: use store's currentStep if pathname doesn't match any stage
    const currentStepKey = stepKeyMapping[currentStep] || currentStep;
    const currentStepIndex = WORKFLOW_STAGES.findIndex(s => s.key === currentStepKey);
    
    // Check if this stage is in completedSteps (map the keys)
    const isInCompletedSteps = completedSteps.some(step => {
      const mappedKey = stepKeyMapping[step] || step;
      return mappedKey === stage.key;
    });
    
    if (isInCompletedSteps) {
      return 'completed';
    }
    
    // Check if this stage index is less than current step index
    if (currentStepIndex >= 0 && index < currentStepIndex) {
      return 'completed';
    }
    
    // Check if this stage index equals current step index
    if (currentStepIndex >= 0 && index === currentStepIndex) {
      return 'current';
    }
    
    return 'pending';
  };

  const handleNavigation = (stage: WorkflowStage) => {
    router.push(stage.path);
  };

  return (
    <div
      style={{
        backgroundColor: '#fafafa',
        borderRight: '1px solid #d5dbdb',
        padding: '20px 16px',
        minHeight: 'calc(100vh - 120px)',
        maxHeight: 'calc(100vh - 120px)',
        width: '320px',
        overflowY: 'auto',
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
            <div key={stage.key}>
              <div
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
