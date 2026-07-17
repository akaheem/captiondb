"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import AuthShell, { Field, OAuthRow } from "@/components/AuthShell";
import { PinkButton } from "@/components/ui";
import { register, ApiError } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    try {
      const res = await register(email, username, password);
      if (res.success) {
        router.push("/login");
      } else {
        setError(res.error?.message ?? "Registration failed.");
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 500) {
        setError(
          "Account creation isn't available yet on this deployment — you can continue to the dashboard without an account.",
        );
      } else {
        setError(err instanceof Error ? err.message : "Registration failed.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      headline={
        <>
          Give Every Video
          <br />A{" "}
          <em className="not-italic text-[#ffd9e2] border-b-[3px] border-pink">
            Voice
          </em>{" "}
          Today.
        </>
      }
      blurb="Create your free account — upload videos, watch the AI pipeline work, and get captions in five distinct tones."
      quote={{
        tone: "SCENE 01 · HUMOROUS TECH",
        text: '"Sign up flow so smooth it must have been tested. Twice."',
      }}
    >
      <h2 className="font-serif font-medium text-3xl">Create Account</h2>
      <p className="text-gray-400 text-[13.5px] mt-2 mb-7">
        Start captioning in minutes
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
          label="Username"
          type="text"
          placeholder="yourname"
          minLength={3}
          maxLength={50}
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <Field
          label="Password"
          type="password"
          placeholder="At least 8 characters"
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
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
          {busy ? "Creating account…" : "Create Account ➜"}
        </PinkButton>
      </form>
      <OAuthRow />
      <p className="text-center mt-6 text-[13.5px] text-gray-500">
        Already have an account?{" "}
        <Link href="/login" className="text-pink font-bold">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
