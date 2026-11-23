import axios from "axios";

/**
 * Single place for all backend calls (per spec: src/api/).
 *
 * - baseURL is empty in dev so Vite's /api proxy handles routing.
 * - In production set VITE_API_BASE_URL to the Render backend origin.
 * - Later: attach the SimpleJWT access token here as an interceptor.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
  headers: { "Content-Type": "application/json" },
  timeout: 15_000,
});
