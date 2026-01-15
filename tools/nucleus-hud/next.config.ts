import type { NextConfig } from "next";
import withPWAInit from "@ducanh2912/next-pwa";

const withPWA = withPWAInit({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
});

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    // Use environment variable for production, fallback to localhost for dev
    const backendUrl = process.env.NEXT_PUBLIC_APP_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`, // Proxy to Python Backend
      },
    ];
  },
};

export default withPWA(nextConfig);
