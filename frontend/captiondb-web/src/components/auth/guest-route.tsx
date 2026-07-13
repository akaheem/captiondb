"use client";

// ============================================================
// GuestRoute — Route Guard for unauthenticated-only routes
// ============================================================
// Use in auth layouts (/auth/login, /auth/register).
// Redirects authenticated users away from the login page.
// ============================================================

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth.store";
import { AUTH_CONFIG } from "@/lib/config";
import { FullPageSpinner } from "@/components/ui/full-page-spinner";

interface GuestRouteProps {
  children: React.ReactNode;
}

export function GuestRoute({ children }: GuestRouteProps) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isInitialized = useAuthStore((s) => s.isInitialized);

  useEffect(() => {
    if (!isInitialized) return;
    if (isAuthenticated) {
      // Honour the returnUrl if set (e.g. login?returnUrl=/dashboard/projects)
      const params = new URLSearchParams(window.location.search);
      const returnUrl = params.get("returnUrl") ?? AUTH_CONFIG.defaultPostLoginPath;
      router.replace(decodeURIComponent(returnUrl));
    }
  }, [isAuthenticated, isInitialized, router]);

  if (!isInitialized) return <FullPageSpinner />;
  if (isAuthenticated) return null;

  return <>{children}</>;
}
