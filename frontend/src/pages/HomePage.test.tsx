import type { ReactElement } from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { HomePage } from "./HomePage";
import { apiClient } from "../api/client";
import { AuthProvider } from "../auth/AuthContext";

function renderWithProviders(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AuthProvider>
        <MemoryRouter>{ui}</MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  );
}

function mockGet(healthOk: boolean) {
  vi.spyOn(apiClient, "get").mockImplementation((url: string) => {
    if (url.includes("/auth/me/")) return Promise.reject(new Error("anonymous"));
    if (url.includes("/health/")) {
      return healthOk
        ? Promise.resolve({
            data: { status: "ok", db: "ok" },
            status: 200,
            statusText: "OK",
            headers: {},
            config: {} as never,
          })
        : Promise.reject(new Error("down"));
    }
    return Promise.reject(new Error(`unmocked ${url}`));
  });
}

describe("HomePage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows 'Backend connected' when the health endpoint succeeds", async () => {
    mockGet(true);
    renderWithProviders(<HomePage />);
    expect(await screen.findByText(/Backend connected/)).toBeInTheDocument();
  });

  it("does not show connected text when the backend is unreachable", async () => {
    mockGet(false);
    renderWithProviders(<HomePage />);
    // Health query fails silently in the new design (no error text) —
    // assert the success marker never appears.
    await screen.findByText("Welcome to PyArena");
    expect(screen.queryByText(/Backend connected/)).not.toBeInTheDocument();
  });
});
