"use client";

// ============================================================
// ProtectedRoute — Route Guard for authenticated routes
// ============================================================
// Use inside any layout that requires authentication.
// Redirects to /auth/login with a returnUrl when the user
// is not authenticated after initialization is complete.
// ============================================================

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth.store";
import { AUTH_CONFIG } from "@/lib/config";
import { FullPageSpinner } from "@/components/ui/full-page-spinner";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isInitialized = useAuthStore((s) => s.isInitialized);

  useEffect(() => {
    if (!isInitialized) return;
    if (!isAuthenticated) {
      const returnUrl = encodeURIComponent(window.location.pathname);
      router.replace(`${AUTH_CONFIG.loginPath}?returnUrl=${returnUrl}`);
    }
  }, [isAuthenticated, isInitialized, router]);

  // While initializing, show a full-page spinner
  if (!isInitialized) return <FullPageSpinner />;

  // Not authenticated — redirect is in-flight, render nothing
  if (!isAuthenticated) return null;

  return <>{children}</>;
}
