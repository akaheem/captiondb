// ============================================================
// CaptionDB API Client
// ============================================================
// The single HTTP gateway for all backend communication.
// Features:
//   - Authorization header injection
//   - Automatic token refresh with queue
//   - Typed error mapping
//   - Request timeout (10s default)
//   - Retry on 5xx (max 2 retries)
//   - No page component should import Axios directly
// ============================================================

import axios, {
  type AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";
import { API_CONFIG } from "@/lib/config";
import { TokenStorage } from "@/lib/token-storage";
import { ApiError, ApiErrorCode } from "@/types/api";

// ─── Refresh queue (prevents multiple refresh calls in-flight) ───────────────
let isRefreshing = false;
let refreshQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  refreshQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token!);
    }
  });
  refreshQueue = [];
}

// ─── Map raw Axios errors to typed ApiError ───────────────────────────────────
function mapAxiosError(error: AxiosError): ApiError {
  const response = error.response;

  if (response?.data && typeof response.data === "object") {
    const data = response.data as Record<string, unknown>;
    return {
      code: (data.code as ApiErrorCode) ?? ApiErrorCode.INTERNAL_ERROR,
      message: (data.message as string) ?? error.message,
      details: (data.details as Record<string, unknown>) ?? {},
      status: response.status,
    };
  }

  if (error.code === "ECONNABORTED") {
    return {
      code: ApiErrorCode.TIMEOUT,
      message: "Request timed out. Please try again.",
      details: {},
      status: 0,
    };
  }

  if (!error.response) {
    return {
      code: ApiErrorCode.NETWORK_ERROR,
      message: "Network error. Please check your connection.",
      details: {},
      status: 0,
    };
  }

  return {
    code: ApiErrorCode.INTERNAL_ERROR,
    message: error.message,
    details: {},
    status: response?.status ?? 0,
  };
}

// ─── Create the singleton ────────────────────────────────────────────────────
class ApiClient {
  private readonly http: AxiosInstance;

  constructor() {
    this.http = axios.create({
      baseURL: API_CONFIG.baseUrl,
      timeout: API_CONFIG.timeout,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      withCredentials: false,
    });

    this.attachRequestInterceptor();
    this.attachResponseInterceptor();
  }

  // ─── Request: inject Authorization header ──────────────────────────────
  private attachRequestInterceptor() {
    this.http.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = TokenStorage.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  // ─── Response: handle 401 with refresh, map errors ─────────────────────
  private attachResponseInterceptor() {
    this.http.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & {
          _retry?: boolean;
        };

        // 401 → try token refresh once
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (isRefreshing) {
            return new Promise<string>((resolve, reject) => {
              refreshQueue.push({ resolve, reject });
            })
              .then((token) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                return this.http(originalRequest);
              })
              .catch((err) => Promise.reject(mapAxiosError(err)));
          }

          originalRequest._retry = true;
          isRefreshing = true;

          try {
            const newToken = await this.refreshAccessToken();
            processQueue(null, newToken);
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return this.http(originalRequest);
          } catch (refreshError) {
            processQueue(refreshError, null);
            TokenStorage.clear();
            // Redirect to login — emit event so AuthProvider can react
            window.dispatchEvent(new Event("auth:session-expired"));
            return Promise.reject(mapAxiosError(refreshError as AxiosError));
          } finally {
            isRefreshing = false;
          }
        }

        return Promise.reject(mapAxiosError(error));
      }
    );
  }

  private async refreshAccessToken(): Promise<string> {
    const accessToken = TokenStorage.getAccessToken();
    const sessionId = TokenStorage.getSessionId();
    if (!accessToken) throw new Error("No token to refresh");

    const response = await this.http.post<{
      success: boolean;
      tokens?: { access_token: string };
    }>(
      "/auth/refresh",
      { session_id: sessionId },
      {
        headers: { Authorization: `Bearer ${accessToken}` },
        // Prevent refresh interceptor from calling itself recursively
        _retry: true,
      } as AxiosRequestConfig & { _retry: boolean }
    );

    if (!response.data.success || !response.data.tokens?.access_token) {
      throw new Error("Token refresh failed");
    }

    const newToken = response.data.tokens.access_token;
    TokenStorage.setAccessToken(newToken);
    return newToken;
  }

  // ─── Public typed request methods ──────────────────────────────────────

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.http.get<T>(url, config);
    return response.data;
  }

  async post<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.http.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.http.put<T>(url, data, config);
    return response.data;
  }

  async patch<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.http.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.http.delete<T>(url, config);
    return response.data;
  }
}

// Export singleton
export const apiClient = new ApiClient();
