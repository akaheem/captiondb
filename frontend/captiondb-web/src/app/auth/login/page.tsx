import type { Metadata } from "next";
import Link from "next/link";
import { ROUTES } from "@/lib/routes";

export const metadata: Metadata = { title: "Sign In" };

// This is a thin shell — the LoginForm feature component renders the actual form.
// Phase 10.2 will implement the full form with React Hook Form + Zod.
export default function LoginPage() {
  return (
    <div className="w-full max-w-sm space-y-6">
      {/* Header */}
      <div className="space-y-1.5 text-center">
        <h1 className="text-2xl font-bold tracking-tight">Welcome back</h1>
        <p className="text-sm text-muted-foreground">
          Sign in to your CaptionDB account
        </p>
      </div>

      {/* Placeholder — replaced by LoginForm in Phase 10.2 */}
      <div className="rounded-xl border border-dashed border-border bg-muted/30 p-8 text-center text-sm text-muted-foreground">
        Login form — implemented in Phase 10.2
      </div>

      <p className="text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link
          href={ROUTES.auth.register}
          className="font-medium text-primary hover:underline"
        >
          Create one
        </Link>
      </p>
    </div>
  );
}
