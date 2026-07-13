"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { authService } from "@/services/auth.service";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useQueryClient } from "@tanstack/react-query";
import { authKeys } from "@/hooks/use-auth";
import { OAuthProvider } from "@/types/api";

function CallbackProcessor() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const processCallback = async () => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const provider = searchParams.get("provider");

      if (!code || !state || !provider) {
        setErrorMsg("Missing required OAuth parameters.");
        return;
      }

      const savedState = sessionStorage.getItem("oauth_state");
      if (state !== savedState) {
        setErrorMsg("Invalid state parameter. Possible CSRF attack.");
        return;
      }

      sessionStorage.removeItem("oauth_state");

      try {
        const redirectUri = `${window.location.origin}/auth/callback?provider=${provider}`;
        const response = await authService.completeOAuthLogin({
          provider: provider as OAuthProvider,
          code,
          redirect_uri: redirectUri,
        } as any);

        if (response.success) {
          queryClient.invalidateQueries({ queryKey: authKeys.me });
          router.push("/dashboard");
        } else {
          setErrorMsg(response.error?.message || "OAuth login failed");
        }
      } catch (err: any) {
        setErrorMsg(err.message || "An unexpected error occurred during OAuth");
      }
    };

    processCallback();
  }, [searchParams, router, queryClient]);

  if (errorMsg) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{errorMsg}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
      <p className="text-muted-foreground">Completing authentication...</p>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle>Authenticating</CardTitle>
        </CardHeader>
        <CardContent>
          <Suspense fallback={<div className="text-center">Loading...</div>}>
            <CallbackProcessor />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}
