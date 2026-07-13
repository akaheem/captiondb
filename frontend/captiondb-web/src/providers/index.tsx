// ============================================================
// Root Providers
// ============================================================
// Single entry-point that composes every provider in the
// correct nesting order. Import this into app/layout.tsx.
//
// Order (outer → inner):
//   ThemeProvider
//   QueryProvider
//   AuthenticationProvider
//   Toaster (sonner)
// ============================================================

import { ThemeProvider } from "./theme-provider";
import { QueryProvider } from "./query-provider";
import { AuthenticationProvider } from "./authentication-provider";
import { Toaster } from "@/components/ui/sonner";

interface RootProvidersProps {
  children: React.ReactNode;
}

export function RootProviders({ children }: RootProvidersProps) {
  return (
    <ThemeProvider>
      <QueryProvider>
        <AuthenticationProvider>
          {children}
          <Toaster richColors closeButton position="top-right" />
        </AuthenticationProvider>
      </QueryProvider>
    </ThemeProvider>
  );
}
