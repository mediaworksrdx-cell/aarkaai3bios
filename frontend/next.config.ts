import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:5000';
    return [
      // Auth flows
      {
        source: '/auth/:path*',
        destination: `${backendUrl}/auth/:path*`,
      },
      // Core API proxy — /api/* → backend (strips the /api prefix)
      {
        source: '/api/settings',
        destination: `${backendUrl}/settings`,
      },
      {
        source: '/api/rlhf',
        destination: `${backendUrl}/rlhf`,
      },
      {
        source: '/api/chat',
        destination: `${backendUrl}/prompt`,
      },
      {
        source: '/api/skills/:path*',
        destination: `${backendUrl}/skills/:path*`,
      },
      {
        source: '/api/subscription/:path*',
        destination: `${backendUrl}/subscription/:path*`,
      },
      {
        source: '/api/metrics',
        destination: `${backendUrl}/metrics`,
      },
      // Direct backend passthrough (no /api prefix)
      {
        source: '/prompt/stream',
        destination: `${backendUrl}/prompt/stream`,
      },
      {
        source: '/prompt',
        destination: `${backendUrl}/prompt`,
      },
      {
        source: '/strategy',
        destination: `${backendUrl}/strategy`,
      },
      {
        source: '/health',
        destination: `${backendUrl}/health`,
      },
      {
        source: '/upload',
        destination: `${backendUrl}/upload`,
      },
      {
        source: '/download/:filename*',
        destination: `${backendUrl}/download/:filename*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-inline' https://accounts.google.com https://apis.google.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: blob: https://*.googleusercontent.com https://avatars.githubusercontent.com; font-src 'self' data: https://fonts.gstatic.com; connect-src 'self' https://synthetixanalytics.com https://aarka-ai.com https://accounts.google.com http://127.0.0.1:5000; frame-src 'self' https://accounts.google.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self' https://accounts.google.com https://github.com/login/oauth/authorize;",
          },
          { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
        ],
      },
    ];
  },
};

export default nextConfig;
