import { execSync } from "node:child_process";
import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * C3: student answers a question -> sees explanation -> XP updates on Home.
 * The correct option is fetched via Django shell because the API
 * deliberately never reveals it to the client.
 */

const BACKEND = path.resolve(__dirname, "../../backend");

function djangoShell(code: string): string {
  return execSync(
    `.venv\\Scripts\\python.exe manage.py shell -c "${code.replace(/"/g, '\\"')}"`,
    { cwd: BACKEND, encoding: "utf-8" },
  ).trim();
}

test("student answers -> explanation -> XP on home", async ({ page }) => {
  // Pick a visible question + its correct option text via ORM.
  const info = djangoShell(
    "from questions.services import visible_to_students; " +
      "q = visible_to_students().exclude(explanation_markdown='').first(); " +
      "o = q.options.get(is_correct=True); " +
      "print(f'{q.id}|{o.text}')",
  )
    .split("\n")
    .filter((l) => l.includes("|"))
    .pop()!;
  const [questionId, correctText] = info.split("|");

  // Fresh student so XP starts at 0.
  const email = `e2e-${Date.now()}@test.dev`;
  djangoShell(
    `from django.contrib.auth import get_user_model; ` +
      `U=get_user_model(); u=U.objects.create_user(email='${email}', password='E2e!Pass234', full_name='E2E'); print(u.id)`,
  );

  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill("E2e!Pass234");
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();

  // Client-side nav via the question card (keeps the in-memory access token;
  // a full reload would race the refresh-token rotation).
  await page.goto("/");
  await page.locator(`a[href="/questions/${questionId}"]`).click();
  await page.getByRole("button", { name: correctText }).click();
  await page.getByRole("button", { name: "Submit answer" }).click();

  // Result panel: correct + explanation.
  await expect(page.getByText("Correct!")).toBeVisible();
  await expect(page.getByText("Explanation")).toBeVisible();

  // Home shows updated XP (> 0).
  await page.goto("/");
  await expect(page.getByText(/\d+ XP/)).toBeVisible();

  // Profile shows the first_answer badge (C3).
  await page.goto("/profile");
  await expect(page.getByText("First Answer")).toBeVisible();
});
