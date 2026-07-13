"use client";

// ============================================================
// QueryProvider — TanStack React Query
// ============================================================

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";
import { QUERY_CONFIG } from "@/lib/config";
import { ApiErrorCode } from "@/types/api";
import type { ApiError } from "@/types/api";

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: QUERY_CONFIG.staleTime,
        gcTime: QUERY_CONFIG.gcTime,
        retry: (failureCount, error) => {
          // Never retry on auth or not-found errors
          const apiErr = error as unknown as ApiError;
          const noRetry: string[] = [
            ApiErrorCode.INVALID_CREDENTIALS,
            ApiErrorCode.AUTHENTICATION_ERROR,
            ApiErrorCode.TOKEN_EXPIRED,
            ApiErrorCode.NOT_FOUND,
          ];
          if (noRetry.includes(apiErr?.code)) return false;
          return failureCount < QUERY_CONFIG.retry;
        },
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: 0,
      },
    },
  });
}

// Use a module-level client to avoid recreating on SSR hydration
let browserQueryClient: QueryClient | undefined;

function getQueryClient() {
  if (typeof window === "undefined") {
    // Server: always make a new client
    return makeQueryClient();
  }
  // Browser: reuse the same client
  if (!browserQueryClient) browserQueryClient = makeQueryClient();
  return browserQueryClient;
}

interface QueryProviderProps {
  children: React.ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  // useState so the client isn't shared across requests on the server
  const [queryClient] = useState(() => getQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
