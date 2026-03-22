/** @type {import('next').NextConfig} */
const BACKEND_PORT = process.env.BACKEND_PORT || '9501';
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;

const nextConfig = {
  reactStrictMode: true,
  experimental: {
    proxyTimeout: 300000,
    proxyClientMaxBodySize: '100mb',
  },
  rewrites: async () => {
    return [
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`,
      },
      {
        source: '/uploads/:path*',
        destination: `${BACKEND_URL}/uploads/:path*`,
      },
      {
        source: '/health',
        destination: `${BACKEND_URL}/health`,
      },
    ];
  },
};

module.exports = nextConfig;