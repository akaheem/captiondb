import { ProtectedRoute } from "@/components/auth/protected-route";
import { DashboardNav } from "@/components/dashboard/nav";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: {
    default: "Dashboard",
    template: "%s · CaptionDB",
  },
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <div className="flex min-h-screen flex-col bg-background">
        {/* Top nav — implemented in Phase 10.3 */}
        <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
            <span className="flex items-center gap-2 font-bold text-foreground">
              <span className="rounded-md bg-primary px-2 py-0.5 text-xs text-primary-foreground">
                CB
              </span>
              CaptionDB
            </span>
            <DashboardNav />
          </div>
        </header>

        {/* Page content */}
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>
    </ProtectedRoute>
  );
}
