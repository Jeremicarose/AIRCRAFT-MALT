import path from 'node:path';
import { PRODUCTION_DIST_DIR } from './lib/standalone.mjs';

const distDir = process.env.NEXT_DIST_DIR
  || (process.env.NODE_ENV === 'development' ? '.next' : PRODUCTION_DIST_DIR);

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  distDir,
  output: 'standalone',
  outputFileTracingRoot: path.join(process.cwd(), '../../..'),
  transpilePackages: ['@aircraft-malt/registry-v2'],
  async headers() {
    return [{
      source: '/:path*',
      headers: [
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'Referrer-Policy', value: 'no-referrer' },
        { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
      ],
    }];
  },
};

export default nextConfig;
