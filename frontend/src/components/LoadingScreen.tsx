'use client';

import { Box, Spinner, StatusIndicator } from '@cloudscape-design/components';

interface LoadingScreenProps {
  message?: string;
  showSpinner?: boolean;
}

export default function LoadingScreen({ 
  message = "Initializing AWS Marketplace Seller Portal...", 
  showSpinner = true 
}: LoadingScreenProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        padding: '2rem',
        textAlign: 'center',
      }}
    >
      {showSpinner && (
        <div style={{ marginBottom: '1rem' }}>
          <Spinner size="large" />
        </div>
      )}
      
      <Box variant="h2" color="text-body-secondary" margin={{ bottom: 's' }}>
        {message}
      </Box>
      
      <StatusIndicator type="loading">
        Loading application components...
      </StatusIndicator>
      
      <Box 
        variant="small" 
        color="text-body-secondary" 
        margin={{ top: 'm' }}
        textAlign="center"
      >
        This may take a few moments on first load
      </Box>
    </div>
  );
}