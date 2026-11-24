import axios, { AxiosError } from "axios";
import type { InternalAxiosRequestConfig } from "axios";

/**
 * Single place for all backend calls (per spec: src/api/).
 *
 * - withCredentials: browser attaches the httpOnly JWT cookies automatically
 *   (ADR-0002 — tokens never touch JavaScript).
 * - On a 401 we silently POST /auth/refresh/ once, then retry the original
 *   request. If refresh also fails, the user is logged out via the auth
 *   context's event below.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
  timeout: 15_000,
});

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const config = error.config as RetriableConfig | undefined;
    const isAuthEndpoint = config?.url?.includes("/auth/");

    if (error.response?.status === 401 && config && !config._retried && !isAuthEndpoint) {
      config._retried = true;
      try {
        await apiClient.post("/api/v1/auth/refresh/");
        return apiClient.request(config);
      } catch {
        // Refresh failed — notify the app so it can clear auth state.
        window.dispatchEvent(new Event("pyarena:session-expired"));
      }
    }
    return Promise.reject(error);
  },
);
