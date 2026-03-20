/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  rewrites: async () => {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8001/api/:path*',
      },
      {
        source: '/uploads/:path*',
        destination: 'http://localhost:8001/uploads/:path*',
      },
      {
        source: '/health',
        destination: 'http://localhost:8001/health',
      },
    ];
  },
};

module.exports = nextConfig;