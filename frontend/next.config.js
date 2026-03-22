/** @type {import('next').NextConfig} */
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
        destination: 'http://localhost:9500/api/:path*',
      },
      {
        source: '/uploads/:path*',
        destination: 'http://localhost:9500/uploads/:path*',
      },
      {
        source: '/health',
        destination: 'http://localhost:9500/health',
      },
    ];
  },
};

module.exports = nextConfig;