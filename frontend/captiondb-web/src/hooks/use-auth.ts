import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authService } from "@/services/auth.service";
import { TokenStorage } from "@/lib/token-storage";
import {
  LoginRequest,
  RegisterRequest,
  OAuthBeginRequest,
} from "@/types/api";

export const authKeys = {
  me: ["auth", "me"] as const,
};

export function useMe() {
  return useQuery({
    queryKey: authKeys.me,
    queryFn: () => authService.getMe(),
    // Only query if we have an access token
    enabled: !!TokenStorage.getAccessToken(),
    retry: false, // Don't retry auth checks
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: LoginRequest) => authService.login(data),
    onSuccess: (res) => {
      if (res.success && res.tokens) {
        queryClient.invalidateQueries({ queryKey: authKeys.me });
      }
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: (data: RegisterRequest) => authService.register(data),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => {
      const sessionId = TokenStorage.getSessionId();
      return authService.logout(sessionId);
    },
    onSuccess: () => {
      queryClient.setQueryData(authKeys.me, null);
      queryClient.clear();
      window.location.href = "/login";
    },
    onError: () => {
      // Force clear client state even if backend logout fails
      TokenStorage.clear();
      queryClient.setQueryData(authKeys.me, null);
      window.location.href = "/login";
    }
  });
}

export function useOAuthBegin() {
  return useMutation({
    mutationFn: (data: OAuthBeginRequest) => authService.beginOAuthLogin(data),
  });
}
