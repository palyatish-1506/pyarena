import type { ReactElement } from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "../auth/AuthContext";
import { apiClient } from "../api/client";
import { LoginPage } from "./LoginPage";
import { RegisterPage } from "./RegisterPage";
import { ProtectedRoute } from "../components/ProtectedRoute";

function renderWithProviders(ui: ReactElement, route = "/") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AuthProvider>
        <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  );
}

describe("auth pages", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    // /me fails -> anonymous user for all tests in this file.
    vi.spyOn(apiClient, "get").mockRejectedValue(new Error("no session"));
    vi.spyOn(apiClient, "post").mockRejectedValue(new Error("no session"));
  });

  it("login shows field errors on empty submit", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
      </Routes>,
      "/login",
    );
    await user.click(screen.getByRole("button", { name: "Log in" }));
    expect(await screen.findByText("Enter a valid email")).toBeInTheDocument();
  });

  it("register flags mismatched passwords before hitting the API", async () => {
    const user = userEvent.setup();
    const postSpy = vi.spyOn(apiClient, "post");
    renderWithProviders(
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
      </Routes>,
      "/register",
    );
    await user.type(screen.getByLabelText("Email"), "a@b.com");
    await user.type(screen.getByLabelText("Password", { exact: true }), "Str0ng!Pass");
    await user.type(screen.getByLabelText("Confirm password"), "different");
    await user.click(screen.getByRole("button", { name: "Sign up" }));
    expect(await screen.findByText("Passwords do not match")).toBeInTheDocument();
    // Session-refresh may call /auth/refresh/ on mount — assert no REGISTER call.
    expect(postSpy).not.toHaveBeenCalledWith(
      "/api/v1/auth/register/",
      expect.anything(),
    );
  });

  it("protected route redirects anonymous users to /login", async () => {
    renderWithProviders(
      <Routes>
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <div>secret</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>login page</div>} />
      </Routes>,
      "/profile",
    );
    expect(await screen.findByText("login page")).toBeInTheDocument();
  });
});
