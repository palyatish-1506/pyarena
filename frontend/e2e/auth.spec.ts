import { expect, test } from "@playwright/test";

/**
 * Happy path: register -> land on home logged in -> profile shows user ->
 * logout -> back to anonymous nav.
 * Requires the Django backend on :8000 (Vite proxies /api).
 */
const email = `e2e-${Date.now()}@test.dev`;

test.describe("auth flow", () => {
  test("register, view profile, logout", async ({ page }) => {
    await page.goto("/register");
    await page.getByLabel("Full name").fill("E2E Student");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Roll no.").fill("E2E001");
    await page.getByLabel("Password", { exact: true }).fill("Str0ng!Pass");
    await page.getByLabel("Confirm password").fill("Str0ng!Pass");
    await page.getByRole("button", { name: "Sign up" }).click();

    // Register redirects home and nav shows the user's name + logout.
    await expect(page).toHaveURL("/");
    await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();

    await page.goto("/profile");
    await expect(page.getByRole("heading", { name: "E2E Student" })).toBeVisible();
    await expect(page.getByText(email)).toBeVisible();

    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page.getByRole("link", { name: "Log in" })).toBeVisible();
  });
});
