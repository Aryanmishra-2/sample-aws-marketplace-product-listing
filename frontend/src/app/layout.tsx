import '@cloudscape-design/global-styles/index.css';
import './globals.css';
import type { Metadata } from 'next';
import Chatbot from '@/components/Chatbot';
import ProgressBar from '@/components/ProgressBar';
import GlobalHeader from '@/components/GlobalHeader';

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
    <html lang="en">
      <body style={{ margin: 0, padding: 0 }}>
        <GlobalHeader />
        <ProgressBar />
        {children}
        <Chatbot />
      </body>
    </html>
  );
}
