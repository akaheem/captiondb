import { GuestRoute } from "@/components/auth/guest-route";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: {
    default: "Sign In",
    template: "%s · CaptionDB",
  },
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <GuestRoute>
      <div className="grid min-h-screen lg:grid-cols-2">
        {/* Left — branding panel (hidden on mobile) */}
        <div className="relative hidden flex-col bg-zinc-900 p-10 text-white lg:flex">
          {/* Gradient orb */}
          <div
            className="absolute inset-0 bg-gradient-to-br from-violet-900/80 via-zinc-900 to-zinc-900"
            aria-hidden="true"
          />
          <div className="relative z-10 flex items-center gap-2 text-lg font-bold">
            <span className="rounded-md bg-primary px-2 py-0.5 text-sm text-primary-foreground">
              CB
            </span>
            CaptionDB
          </div>
          <div className="relative z-10 mt-auto space-y-3">
            <blockquote className="text-xl font-medium leading-relaxed text-white/90">
              &ldquo;AI-powered video captioning that understands context,
              not just words.&rdquo;
            </blockquote>
            <p className="text-sm text-white/50">CaptionDB Platform</p>
          </div>
        </div>

        {/* Right — form area */}
        <div className="flex items-center justify-center p-8">{children}</div>
      </div>
    </GuestRoute>
  );
}
