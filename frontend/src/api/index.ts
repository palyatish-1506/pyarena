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

export interface Topic {
  id: number;
  name: string;
  slug: string;
  order: number;
  description: string;
}

export interface QuestionOption {
  id: number;
  text: string;
  order: number;
}

export interface StudentQuestion {
  id: number;
  topic: Topic;
  type: "mcq_single" | "mcq_multi" | "output";
  title: string;
  body_markdown: string;
  code_snippet: string;
  difficulty: "easy" | "medium" | "hard";
  base_points: number;
  release_at: string | null;
  close_at: string | null;
  options: QuestionOption[];
}

export interface SeniorOption {
  id?: number;
  text: string;
  is_correct: boolean;
  order?: number;
}

export interface SeniorQuestion {
  id: number;
  topic: Topic;
  topic_id: number;
  type: StudentQuestion["type"];
  title: string;
  body_markdown: string;
  code_snippet: string;
  difficulty: StudentQuestion["difficulty"];
  explanation_markdown: string;
  base_points: number;
  release_at: string | null;
  close_at: string | null;
  status: "draft" | "scheduled" | "published" | "archived";
  author: string;
  options: SeniorOption[];
  created_at: string;
}

export interface QuestionPayload {
  topic_id: number;
  type: StudentQuestion["type"];
  title: string;
  body_markdown: string;
  code_snippet?: string;
  difficulty: StudentQuestion["difficulty"];
  explanation_markdown?: string;
  release_at?: string | null;
  close_at?: string | null;
  status?: string;
  options_input: { text: string; is_correct: boolean }[];
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

  // ---- Questions: student ----
  topics: async (): Promise<Topic[]> => {
    const { data } = await apiClient.get<Topic[]>("/api/v1/questions/topics/");
    return data;
  },
  todayQuestions: async (): Promise<StudentQuestion[]> => {
    const { data } = await apiClient.get<StudentQuestion[]>("/api/v1/questions/today/");
    return data;
  },
  question: async (id: number): Promise<StudentQuestion> => {
    const { data } = await apiClient.get<StudentQuestion>(`/api/v1/questions/${id}/`);
    return data;
  },

  // ---- Questions: senior ----
  seniorQuestions: async (status?: string): Promise<SeniorQuestion[]> => {
    const { data } = await apiClient.get<SeniorQuestion[]>(
      "/api/v1/questions/senior/questions/",
      { params: status ? { status } : {} },
    );
    return Array.isArray(data) ? data : data.results;
  },
  createQuestion: async (payload: QuestionPayload): Promise<SeniorQuestion> => {
    const { data } = await apiClient.post<SeniorQuestion>(
      "/api/v1/questions/senior/questions/",
      payload,
    );
    return data;
  },
  updateQuestion: async (id: number, payload: Partial<QuestionPayload>): Promise<SeniorQuestion> => {
    const { data } = await apiClient.patch<SeniorQuestion>(
      `/api/v1/questions/senior/questions/${id}/`,
      payload,
    );
    return data;
  },
  deleteQuestion: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/questions/senior/questions/${id}/`);
  },
  duplicateQuestion: async (id: number): Promise<SeniorQuestion> => {
    const { data } = await apiClient.post<SeniorQuestion>(
      `/api/v1/questions/senior/questions/${id}/duplicate/`,
    );
    return data;
  },
  previewQuestion: async (id: number): Promise<StudentQuestion> => {
    const { data } = await apiClient.get<StudentQuestion>(
      `/api/v1/questions/senior/questions/${id}/preview/`,
    );
    return data;
  },
};
