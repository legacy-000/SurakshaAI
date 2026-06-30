import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  /* config options here */
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
