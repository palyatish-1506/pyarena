import { expect, test } from "@playwright/test";

test.describe("Home page", () => {
  test("renders header, nav, and backend status", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Welcome to PyArena" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Leaderboard" })).toBeVisible();
    // Backend status resolves to either connected or unreachable — both are valid renders.
    await expect(page.getByText(/Backend connected|Backend unreachable/)).toBeVisible();
  });

  test("navigates to leaderboard page", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Leaderboard" }).click();
    await expect(page.getByRole("heading", { name: "Leaderboard" })).toBeVisible();
  });
});
