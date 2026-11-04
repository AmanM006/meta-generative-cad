import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const backend = process.env.BACKEND_URL || "http://127.0.0.1:8000";
    return [
      { source: "/backend/api/workflow/run", destination: `${backend}/api/workflow/run` },
      { source: "/backend/api/intent/examples", destination: `${backend}/api/intent/examples` },
      { source: "/backend/api/intent/interpret", destination: `${backend}/api/intent/interpret` },
      { source: "/backend/api/live/:path*", destination: `${backend}/api/live/:path*` },
      { source: "/backend/api/runs/:id", destination: `${backend}/api/runs/:id` },
      { source: "/backend/artifacts/:name", destination: `${backend}/artifacts/:name` },
    ];
  },
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
