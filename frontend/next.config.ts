import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  // Allow base64 images and unpkg CDN for Leaflet marker icons
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "unpkg.com" },
    ],
  },
  // Transpile Leaflet for Next.js
  transpilePackages: ["leaflet"],
}

export default nextConfig
