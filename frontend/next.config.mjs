/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  distDir: 'out',
  images: {
    unoptimized: true,
    domains: ["localhost"],
  },
  trailingSlash: true,
};

export default nextConfig;
