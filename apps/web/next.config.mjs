/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Server-side proxy so the browser never talks to the API origin directly
    // (and never sees any server-side secrets).
    const api = process.env.API_URL ?? "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
};

export default nextConfig;
