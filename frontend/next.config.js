/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    // feat-252: API 代理超时时间（毫秒）- 5分钟，支持长时间 AI 处理
    proxyTimeout: 300000,
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