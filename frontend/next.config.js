/** @type {import('next').NextConfig} */
const nextConfig = {
  // CRITICAL: Disable StrictMode to prevent duplicate API calls
  reactStrictMode: false,
  
  // Use standalone output for fastest startup
  output: 'standalone',
  
  // Skip TypeScript errors during build — avoids cross-environment type resolution issues
  // (e.g. different @smithy type versions between laptops/CodeBuild)
  typescript: {
    ignoreBuildErrors: true,
  },

  // Disable image optimization for simpler deployment
  images: {
    unoptimized: true,
  },
  
  // Handle useSearchParams warnings
  experimental: {
    missingSuspenseWithCSRBailout: false,
    // Enable optimized package imports for faster startup
    optimizePackageImports: ['@cloudscape-design/components'],
  },
  
  // Optimize for production startup speed
  swcMinify: true,
  
  // Reduce bundle size by excluding unused modules
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Reduce client bundle size
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    
    return config;
  },
  
  // Enable compression for faster loading
  compress: true,
  
  // Optimize fonts loading
  optimizeFonts: true,
};

module.exports = nextConfig;
