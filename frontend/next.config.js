/** @type {import('next').NextConfig} */
const nextConfig = {
  // CRITICAL: Disable StrictMode to prevent duplicate API calls
  // StrictMode intentionally double-invokes effects in development
  // This causes duplicate product creation calls
  reactStrictMode: false,
  
  // Allow external API calls
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*', // Proxy to FastAPI backend
      },
    ];
  },
};

module.exports = nextConfig;
