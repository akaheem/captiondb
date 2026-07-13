// ============================================================
// useSessions — React Query hook for session management
// ============================================================

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { authService } from "@/services/auth.service";
import { queryKeys } from "@/lib/query-keys";
import { toast } from "sonner";

export function useSessions() {
  const queryClient = useQueryClient();

  const sessionsQuery = useQuery({
    queryKey: queryKeys.auth.sessions(),
    queryFn: () => authService.listSessions(),
  });

  const revokeMutation = useMutation({
    mutationFn: (sessionId: string) => authService.revokeSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.sessions() });
      toast.success("Session revoked");
    },
    onError: () => {
      toast.error("Failed to revoke session. Please try again.");
    },
  });

  const revokeAllMutation = useMutation({
    mutationFn: () => authService.revokeAllSessions(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.sessions() });
      toast.success("All other sessions have been signed out");
    },
    onError: () => {
      toast.error("Failed to sign out all sessions.");
    },
  });

  return {
    sessions: sessionsQuery.data?.sessions ?? [],
    total: sessionsQuery.data?.total ?? 0,
    isLoading: sessionsQuery.isLoading,
    isError: sessionsQuery.isError,
    revokeSession: revokeMutation.mutate,
    isRevoking: revokeMutation.isPending,
    revokeAllSessions: revokeAllMutation.mutate,
    isRevokingAll: revokeAllMutation.isPending,
  };
}
