import type { ReactElement } from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { HomePage } from "./HomePage";
import { apiClient } from "../api/client";

function renderWithProviders(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("HomePage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows 'Backend connected' when the health endpoint succeeds", async () => {
    vi.spyOn(apiClient, "get").mockResolvedValue({
      data: { status: "ok", db: "ok" },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {} as never,
    });

    renderWithProviders(<HomePage />);

    expect(await screen.findByText(/Backend connected/)).toBeInTheDocument();
  });

  it("shows an error when the backend is unreachable", async () => {
    vi.spyOn(apiClient, "get").mockRejectedValue(new Error("network down"));

    renderWithProviders(<HomePage />);

    expect(await screen.findByText(/Backend unreachable/)).toBeInTheDocument();
  });
});
