import { apiClient } from "./client";

export interface HealthResponse {
  status: string;
  db: string;
}

export const api = {
  health: async (): Promise<HealthResponse> => {
    const { data } = await apiClient.get<HealthResponse>("/api/v1/health/");
    return data;
  },
};
