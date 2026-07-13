"use client";

// ============================================================
// AuthenticationProvider
// ============================================================
// Wraps the app tree. Runs the initialize() once on mount.
// Also listens for the "auth:session-expired" event emitted
// by the API client when a 401 cannot be refreshed.
// ============================================================

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth.store";
import { AUTH_CONFIG } from "@/lib/config";
import { TokenStorage } from "@/lib/token-storage";

interface AuthenticationProviderProps {
  children: React.ReactNode;
}

export function AuthenticationProvider({
  children,
}: AuthenticationProviderProps) {
  const router = useRouter();
  const initialize = useAuthStore((s) => s.initialize);
  const setUser = useAuthStore((s) => s.setUser);
  const hasInitialized = useRef(false);

  // Run once on mount — rehydrates session from stored token
  useEffect(() => {
    if (hasInitialized.current) return;
    hasInitialized.current = true;
    initialize();
  }, [initialize]);

  // Listen for the global session-expired event emitted by ApiClient
  useEffect(() => {
    const handler = () => {
      TokenStorage.clear();
      setUser(null);
      router.replace(AUTH_CONFIG.loginPath + "?reason=session_expired");
    };
    window.addEventListener("auth:session-expired", handler);
    return () => window.removeEventListener("auth:session-expired", handler);
  }, [router, setUser]);

  return <>{children}</>;
}
