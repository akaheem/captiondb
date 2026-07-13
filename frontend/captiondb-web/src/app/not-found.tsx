import { Home } from "lucide-react";
import Link from "next/link";
import type { Metadata } from "next";
import { BackButton } from "@/components/back-button";

export const metadata: Metadata = {
  title: "Page Not Found",
};

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 bg-background px-4 text-center">
      {/* Big 404 */}
      <div className="relative">
        <p className="text-[8rem] font-black leading-none tracking-tighter text-primary/10 select-none">
          404
        </p>
        <p className="absolute inset-0 flex items-center justify-center text-7xl font-black tracking-tighter text-primary">
          404
        </p>
      </div>

      <div className="max-w-md space-y-3">
        <h1 className="text-2xl font-bold tracking-tight">Page not found</h1>
        <p className="text-muted-foreground">
          We couldn&apos;t find the page you were looking for. It may have been
          moved, deleted, or never existed.
        </p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90"
        >
          <Home className="h-4 w-4" />
          Go home
        </Link>
        <BackButton />
      </div>
    </div>
  );
}
