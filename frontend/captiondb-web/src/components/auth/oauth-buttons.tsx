"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useOAuthBegin } from "@/hooks/use-auth";
import { OAuthProvider } from "@/types/api";
import { Globe } from "lucide-react"; // Generic icons for others

export function OAuthButtons() {
  const { mutateAsync: beginOAuth } = useOAuthBegin();
  const [loadingProvider, setLoadingProvider] = useState<OAuthProvider | null>(null);

  const handleOAuth = async (provider: OAuthProvider) => {
    try {
      setLoadingProvider(provider);
      // Generate a random state string
      const state = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
      
      // Store state in sessionStorage to verify it on callback
      sessionStorage.setItem(`oauth_state`, state);
      
      // Append provider so we know which one to complete
      const redirectUri = `${window.location.origin}/auth/callback?provider=${provider}`;

      const response = await beginOAuth({
        provider,
        state,
        redirect_uri: redirectUri,
      });

      if (response.success && response.authorization_url) {
        window.location.href = response.authorization_url;
      }
    } catch (error) {
      console.error("OAuth error:", error);
    } finally {
      setLoadingProvider(null);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <Button
        variant="outline"
        onClick={() => handleOAuth("google")}
        disabled={loadingProvider !== null}
        className="w-full"
      >
        <Globe className="mr-2 h-4 w-4" />
        {loadingProvider === "google" ? "Redirecting..." : "Continue with Google"}
      </Button>
      <Button
        variant="outline"
        onClick={() => handleOAuth("github")}
        disabled={loadingProvider !== null}
        className="w-full"
      >
        <Globe className="mr-2 h-4 w-4" />
        {loadingProvider === "github" ? "Redirecting..." : "Continue with GitHub"}
      </Button>
      <Button
        variant="outline"
        onClick={() => handleOAuth("apple")}
        disabled={loadingProvider !== null}
        className="w-full"
      >
        <Globe className="mr-2 h-4 w-4" />
        {loadingProvider === "apple" ? "Redirecting..." : "Continue with Apple"}
      </Button>
      <Button
        variant="outline"
        onClick={() => handleOAuth("microsoft")}
        disabled={loadingProvider !== null}
        className="w-full"
      >
        <Globe className="mr-2 h-4 w-4" />
        {loadingProvider === "microsoft" ? "Redirecting..." : "Continue with Microsoft"}
      </Button>
    </div>
  );
}
