import axios, { AxiosError } from "axios";
import type { InternalAxiosRequestConfig } from "axios";

/**
 * Single place for all backend calls.
 *
 * Token model: access token lives in MEMORY only (AuthContext) and is sent
 * as `Authorization: Bearer`. Refresh token is an httpOnly cookie the
 * browser attaches automatically (withCredentials). On 401 we call
 * /auth/refresh/ once, store the new access token, and retry.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
  timeout: 15_000,
});

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const config = error.config as RetriableConfig | undefined;
    const isAuthEndpoint = config?.url?.includes("/auth/") || config?.url?.includes("/me/");

    if (error.response?.status === 401 && config && !config._retried && !isAuthEndpoint) {
      config._retried = true;
      try {
        const { data } = await apiClient.post<{ access: string }>("/api/v1/auth/refresh/");
        setAccessToken(data.access);
        return apiClient.request(config);
      } catch {
        window.dispatchEvent(new Event("pyarena:session-expired"));
      }
    }
    return Promise.reject(error);
  },
);
