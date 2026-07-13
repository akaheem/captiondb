"use client";

import { useState } from "react";
import { Monitor, LogOut, ShieldCheck } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useSessions } from "@/hooks/use-sessions";
import { TokenStorage } from "@/lib/token-storage";
import { formatDateTime, formatRelativeTime } from "@/lib/format";
import type { SessionInfoDTO } from "@/types/api";

/** Derive a short, human-friendly device label from a user-agent string. */
function describeDevice(userAgent: string | null): string {
  if (!userAgent) return "Unknown device";
  const browser =
    /edg/i.test(userAgent) ? "Edge"
    : /chrome|crios/i.test(userAgent) ? "Chrome"
    : /firefox|fxios/i.test(userAgent) ? "Firefox"
    : /safari/i.test(userAgent) ? "Safari"
    : "Browser";
  const os =
    /windows/i.test(userAgent) ? "Windows"
    : /mac os|macintosh/i.test(userAgent) ? "macOS"
    : /android/i.test(userAgent) ? "Android"
    : /iphone|ipad|ios/i.test(userAgent) ? "iOS"
    : /linux/i.test(userAgent) ? "Linux"
    : "";
  return os ? `${browser} on ${os}` : browser;
}

function SessionRow({
  session,
  isCurrent,
  onRevoke,
  isRevoking,
}: {
  session: SessionInfoDTO;
  isCurrent: boolean;
  onRevoke: (id: string) => void;
  isRevoking: boolean;
}) {
  return (
    <li className="flex items-center justify-between gap-4 py-3">
      <div className="flex items-start gap-3">
        <Monitor className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">
              {describeDevice(session.user_agent)}
            </span>
            {isCurrent ? <Badge variant="success">This device</Badge> : null}
            {session.is_expired ? (
              <Badge variant="muted">Expired</Badge>
            ) : null}
          </div>
          <p className="text-xs text-muted-foreground">
            {session.ip_address ?? "Unknown IP"} · Signed in{" "}
            {formatDateTime(session.created_at)}
          </p>
          <p className="text-xs text-muted-foreground">
            Last active {formatRelativeTime(session.last_seen_at)}
          </p>
        </div>
      </div>
      {isCurrent ? (
        <span className="text-xs text-muted-foreground">Current</span>
      ) : (
        <Button
          variant="outline"
          size="sm"
          onClick={() => onRevoke(session.session_id)}
          disabled={isRevoking}
        >
          Revoke
        </Button>
      )}
    </li>
  );
}

/** Active-session management for the current user. */
export function SessionsCard() {
  const {
    sessions,
    total,
    isLoading,
    isError,
    revokeSession,
    isRevoking,
    revokeAllSessions,
    isRevokingAll,
  } = useSessions();
  const [confirmRevokeAll, setConfirmRevokeAll] = useState(false);

  const currentSessionId = TokenStorage.getSessionId();
  const otherCount = sessions.filter(
    (s) => s.session_id !== currentSessionId
  ).length;

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div className="space-y-1.5">
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-muted-foreground" />
            Active sessions
          </CardTitle>
          <CardDescription>
            Devices currently signed in to your account.
          </CardDescription>
        </div>
        {otherCount > 0 ? (
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setConfirmRevokeAll(true)}
            disabled={isRevokingAll}
          >
            <LogOut className="mr-1 h-4 w-4" />
            Sign out others
          </Button>
        ) : null}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="py-4 text-sm text-muted-foreground">
            Loading sessions…
          </p>
        ) : isError ? (
          <p className="py-4 text-sm text-destructive">
            Failed to load sessions. Please try again later.
          </p>
        ) : sessions.length === 0 ? (
          <p className="py-4 text-sm text-muted-foreground">
            No active sessions.
          </p>
        ) : (
          <>
            <ul className="divide-y divide-border">
              {sessions.map((session) => (
                <SessionRow
                  key={session.session_id}
                  session={session}
                  isCurrent={session.session_id === currentSessionId}
                  onRevoke={revokeSession}
                  isRevoking={isRevoking}
                />
              ))}
            </ul>
            <p className="pt-3 text-xs text-muted-foreground">
              {total} active session{total === 1 ? "" : "s"}
            </p>
          </>
        )}
      </CardContent>

      <ConfirmDialog
        open={confirmRevokeAll}
        onOpenChange={setConfirmRevokeAll}
        title="Sign out all other sessions?"
        description="Every device except this one will be signed out immediately. You will stay signed in here."
        confirmLabel="Sign out others"
        loading={isRevokingAll}
        onConfirm={() => {
          revokeAllSessions();
          setConfirmRevokeAll(false);
        }}
      />
    </Card>
  );
}
