import '@cloudscape-design/global-styles/index.css';
import './globals.css';
import type { Metadata } from 'next';
import dynamic from 'next/dynamic';
import ProgressBar from '@/components/ProgressBar';
import GlobalHeader from '@/components/GlobalHeader';

// OPTIMIZATION: Lazy load heavy components to improve startup time
// This prevents the Chatbot from blocking initial page render
const Chatbot = dynamic(() => import('@/components/Chatbot'), {
  ssr: false, // Disable server-side rendering for this component
  loading: () => null, // No loading indicator needed for chatbot
});

export const metadata: Metadata = {
  title: 'AWS Marketplace Seller Portal',
  description: 'AI-Guided AWS Marketplace Listing Creation',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" style={{ minHeight: '100vh' }}>
      <body style={{ margin: 0, padding: 0, minHeight: '100vh' }}>
        <GlobalHeader />
        <ProgressBar />
        <div style={{ minHeight: 'calc(100vh - 120px)' }}>
          {children}
        </div>
        <Chatbot />
      </body>
    </html>
  );
}
