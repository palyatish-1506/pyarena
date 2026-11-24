import { apiClient } from "./client";

export interface HealthResponse {
  status: string;
  db: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  roll_no: string;
  branch: string;
  year: number | null;
  division: string;
  role: "student" | "senior" | "admin";
  senior_approved: boolean;
  senior_requested: boolean;
  xp: number;
  level: number;
  current_streak: number;
  longest_streak: number;
  streak_freezes: number;
  avatar_seed: string;
  date_joined: string;
}

export interface AuthResponse {
  user: User;
  access: string;
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

export interface ProfilePatch {
  full_name?: string;
  roll_no?: string;
  branch?: string;
  year?: number | null;
  division?: string;
  avatar_seed?: string;
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
  options_input: { text: string; is_correct: boolean }[];
}

export const api = {
  health: async (): Promise<HealthResponse> => {
    const { data } = await apiClient.get<HealthResponse>("/api/v1/health/");
    return data;
  },

  register: async (payload: RegisterPayload): Promise<AuthResponse> => {
    const { data } = await apiClient.post<AuthResponse>("/api/v1/auth/register/", payload);
    return data;
  },

  login: async (email: string, password: string): Promise<AuthResponse> => {
    const { data } = await apiClient.post<AuthResponse>("/api/v1/auth/login/", {
      email,
      password,
    });
    return data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post("/api/v1/auth/logout/");
  },

  me: async (): Promise<{ user: User }> => {
    const { data } = await apiClient.get<{ user: User }>("/api/v1/me/");
    return data;
  },

  updateMe: async (patch: ProfilePatch): Promise<{ user: User }> => {
    const { data } = await apiClient.patch<{ user: User }>("/api/v1/me/", patch);
    return data;
  },

  forgotPassword: async (email: string): Promise<void> => {
    await apiClient.post("/api/v1/auth/password-reset/", { email });
  },

  resetPassword: async (uid: string, token: string, new_password: string): Promise<void> => {
    await apiClient.post("/api/v1/auth/password-reset/confirm/", {
      uid,
      token,
      new_password,
    });
  },

  requestSenior: async (): Promise<{ user: User }> => {
    const { data } = await apiClient.post<{ user: User }>("/api/v1/auth/request-senior/");
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
    const { data } = await apiClient.get<SeniorQuestion[] | { results: SeniorQuestion[] }>(
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

  // ---- Submissions ----
  submitAnswer: async (
    questionId: number,
    selectedOptionIds: number[],
    timeTakenMs: number,
  ): Promise<SubmitResult> => {
    const { data } = await apiClient.post<SubmitResult>(
      `/api/v1/questions/${questionId}/submit/`,
      { selected_option_ids: selectedOptionIds, time_taken_ms: timeTakenMs },
    );
    return data;
  },
  myHistory: async (page = 1): Promise<HistoryPage> => {
    const { data } = await apiClient.get<HistoryPage>("/api/v1/me/history/", {
      params: { page },
    });
    return data;
  },
  myTopics: async (): Promise<TopicProgress[]> => {
    const { data } = await apiClient.get<TopicProgress[]>("/api/v1/me/topics/");
    return data;
  },
};

export interface SubmitResult {
  is_correct: boolean;
  points_awarded: number;
  correct_option_ids: number[];
  explanation: string;
  new_xp: number;
  new_level: number;
  level_name: string;
  streak: number;
  badges_earned: string[];
  is_late: boolean;
}

export interface HistoryItem {
  id: number;
  question: number;
  question_title: string;
  topic_name: string;
  difficulty: string;
  selected_option_ids: number[];
  is_correct: boolean;
  points: number;
  is_late: boolean;
  time_taken_ms: number;
  submitted_at: string;
}

export interface HistoryPage {
  count: number;
  next: string | null;
  previous: string | null;
  results: HistoryItem[];
}

export interface TopicProgress {
  topic: string;
  attempts: number;
  correct: number;
  accuracy: number;
}
