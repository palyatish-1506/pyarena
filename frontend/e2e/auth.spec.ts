import { execSync } from "node:child_process";
import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BACKEND = path.resolve(__dirname, "../../backend");

function djangoShell(code: string): string {
  return execSync(
    `.venv\\Scripts\\python.exe manage.py shell -c "${code.replace(/"/g, '\\"')}"`,
    { cwd: BACKEND, encoding: "utf-8" },
  ).trim();
}

/**
 * Auth flow e2e: login -> profile -> logout -> login again.
 * User is created via ORM because the register endpoint is rate-limited
 * (10/hour) and repeated e2e runs would exhaust it. Registration itself is
 * covered by pytest.
 */
test.describe("auth flow", () => {
  test("login, view profile, logout, login again", async ({ page }) => {
    const email = `e2e-auth-${Date.now()}@test.dev`;
    const roll = `E2E${Date.now() % 100000}`;
    djangoShell(
      `from django.contrib.auth import get_user_model; ` +
        `U=get_user_model(); U.objects.create_user(email='${email}', password='E2e!Pass234', full_name='E2E Student', roll_no='${roll}')`,
    );

    await page.goto("/login");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password", { exact: true }).fill("E2e!Pass234");
    await page.getByRole("button", { name: "Log in" }).click();

    await expect(page).toHaveURL("/");
    await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();

    await page.goto("/profile");
    await expect(page.getByRole("heading", { name: "E2E Student" })).toBeVisible();
    await expect(page.getByText(email)).toBeVisible();

    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page.getByRole("link", { name: "Log in" })).toBeVisible();

    // Log back in — session really ended.
    await page.goto("/login");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password", { exact: true }).fill("E2e!Pass234");
    await page.getByRole("button", { name: "Log in" }).click();
    await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
  });
});
