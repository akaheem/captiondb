"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import AuthShell, { Field, OAuthRow } from "@/components/AuthShell";
import { PinkButton } from "@/components/ui";
import { login, setUserToken, ApiError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await login(email, password);
      if (res.success && res.tokens?.access_token) {
        setUserToken(res.tokens.access_token);
        router.push("/dashboard");
      } else {
        setError(res.error?.message ?? "Login failed.");
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 500) {
        setError(
          "Sign-in service isn't available yet on this deployment — you can continue to the dashboard without an account.",
        );
      } else {
        setError(err instanceof Error ? err.message : "Login failed.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      headline={
        <>
          Welcome Back,
          <br />
          Let&apos;s{" "}
          <em className="not-italic text-[#ffd9e2] border-b-[3px] border-pink">
            Caption
          </em>
          <br />
          Something.
        </>
      }
      blurb="Sign in to manage your projects, watch processing live and browse captions in five tones."
      quote={{
        tone: "SCENE 04 · SARCASTIC",
        text: '"Oh look, another login screen. At least this one is pretty."',
      }}
    >
      <h2 className="font-serif font-medium text-3xl">Sign In</h2>
      <p className="text-gray-400 text-[13.5px] mt-2 mb-7">
        Continue to your CaptionDB dashboard
      </p>
      <form onSubmit={onSubmit}>
        <Field
          label="Email Address"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Field
          label="Password"
          type="password"
          placeholder="••••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <div className="flex justify-between items-center mt-3.5 text-[13px]">
          <label className="flex items-center gap-1.5 text-gray-600">
            <input type="checkbox" /> Remember me
          </label>
          <span className="text-pink font-semibold cursor-pointer">
            Forgot password?
          </span>
        </div>
        {error && (
          <div className="mt-4 bg-[#fde2e6] text-[#c22f4f] text-[13px] rounded-md px-4 py-3">
            {error}{" "}
            {error.includes("dashboard") && (
              <Link href="/dashboard" className="underline font-bold">
                Go to dashboard →
              </Link>
            )}
          </div>
        )}
        <PinkButton type="submit" disabled={busy} className="w-full mt-6 py-4 text-[15px]">
          {busy ? "Signing in…" : "Sign In ➜"}
        </PinkButton>
      </form>
      <OAuthRow />
      <p className="text-center mt-6 text-[13.5px] text-gray-500">
        New to CaptionDB?{" "}
        <Link href="/signup" className="text-pink font-bold">
          Create an account
        </Link>
      </p>
    </AuthShell>
  );
}
