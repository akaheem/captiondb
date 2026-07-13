import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // ─── Output & Build ───────────────────────────────────────────────────
  // Use standalone output for Docker deployments
  output: "standalone",

  // ─── Security Headers ─────────────────────────────────────────────────
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-XSS-Protection",
            value: "1; mode=block",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          // CSP — tightened in production; adjust for OAuth popup flows
          ...(process.env.NODE_ENV === "production"
            ? [
                {
                  key: "Content-Security-Policy",
                  value: [
                    "default-src 'self'",
                    "script-src 'self' 'unsafe-inline'", // required for Next.js
                    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
                    "font-src 'self' https://fonts.gstatic.com",
                    "img-src 'self' data: https:",
                    "connect-src 'self' " +
                      (process.env.NEXT_PUBLIC_API_BASE_URL ?? ""),
                  ].join("; "),
                },
              ]
            : []),
        ],
      },
    ];
  },

  // ─── Images ────────────────────────────────────────────────────────────
  images: {
    remotePatterns: [
      // Google OAuth avatars
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
      // GitHub avatars
      { protocol: "https", hostname: "avatars.githubusercontent.com" },
    ],
  },

  // ─── TypeScript & ESLint ───────────────────────────────────────────────
  typescript: {
    // CI will fail on TS errors; this keeps dev fast without hiding errors
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
