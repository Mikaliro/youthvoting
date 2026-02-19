import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow Mapbox GL JS worker to load correctly
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      // Mapbox GL JS uses worker-loader; suppress webpack warning
      "mapbox-gl": "mapbox-gl",
    };
    return config;
  },
};

export default nextConfig;
