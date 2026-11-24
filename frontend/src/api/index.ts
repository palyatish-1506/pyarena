import { apiClient } from "./client";

export interface HealthResponse {
  status: string;
  db: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "student" | "senior" | "admin";
  division: string;
  year: number | null;
  branch: string;
  xp: number;
  level: number;
  current_streak: number;
  avatar_seed: string;
  date_joined: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  password_confirm: string;
  full_name?: string;
  roll_no?: string;
  branch?: string;
  year?: number | null;
  division?: string;
}

export const api = {
  health: async (): Promise<HealthResponse> => {
    const { data } = await apiClient.get<HealthResponse>("/api/v1/health/");
    return data;
  },

  register: async (payload: RegisterPayload): Promise<User> => {
    const { data } = await apiClient.post<User>("/api/v1/auth/register/", payload);
    return data;
  },

  login: async (email: string, password: string): Promise<User> => {
    const { data } = await apiClient.post<User>("/api/v1/auth/login/", {
      email,
      password,
    });
    return data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post("/api/v1/auth/logout/");
  },

  me: async (): Promise<User> => {
    const { data } = await apiClient.get<User>("/api/v1/auth/me/");
    return data;
  },
};
