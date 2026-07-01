/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ["localhost"],
  },
  // Ensure that routing works nicely when building Single Page App views or standard pages
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*", // Proxy backend FastAPI in development
      },
    ];
  },
};

export default nextConfig;
