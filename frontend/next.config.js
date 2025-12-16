/** @type {import('next').NextConfig} */
const nextConfig = {
  // CRITICAL: Disable StrictMode to prevent duplicate API calls
  reactStrictMode: false,
  
  // Standalone output for Docker/App Runner deployment
  output: 'standalone',
  
  // Disable image optimization for simpler deployment
  images: {
    unoptimized: true,
  },
  
  // Handle useSearchParams warnings
  experimental: {
    missingSuspenseWithCSRBailout: false,
  },
};

module.exports = nextConfig;
