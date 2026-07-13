"use client";

import { useMe } from "@/hooks/use-auth";
import { ProfileCard } from "@/components/dashboard/profile-card";
import { SessionsCard } from "@/components/dashboard/sessions-card";
import { DashboardSkeleton } from "@/components/ui/skeletons";

export default function SettingsPage() {
  const { data, isLoading, error } = useMe();
  const user = data?.user;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your profile and account security.
        </p>
      </div>

      {isLoading ? (
        <DashboardSkeleton />
      ) : error || !user ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-destructive/20 bg-destructive/10 p-8 text-center text-destructive">
          <h3 className="text-lg font-semibold">Error loading account</h3>
          <p className="text-sm">Please try again later.</p>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <ProfileCard user={user} />
          <SessionsCard />
        </div>
      )}
    </div>
  );
}
