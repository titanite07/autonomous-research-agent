import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Fix Turbopack root directory warning
  turbopack: {
    root: path.resolve(__dirname),
  },
  
  // Transpile packages that might cause issues with Turbopack
  transpilePackages: ['react-markdown', 'remark-gfm', 'rehype-highlight'],
  
  // Optimize for development
  reactStrictMode: true,
  
  // Ensure proper handling of external dependencies
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },
  
  // Enable standalone output for Docker deployment
  output: 'standalone',
};

export default nextConfig;
