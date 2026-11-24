import { expect, test } from "@playwright/test";

/**
 * C3: senior creates + schedules a question; student sees it after release.
 * Uses demo accounts from `python manage.py seed_demo`.
 */

async function login(page: import("@playwright/test").Page, email: string, password: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
}

test.describe("question authoring", () => {
  test("senior schedules a question, student sees it after release", async ({ page, browser }) => {
    test.setTimeout(90_000); // includes a real ~20s release wait
    const stamp = Date.now();
    const title = `E2E question ${stamp}`;

    // --- Senior flow ---
    await login(page, "senior@demo.pyarena", "DemoSenior!234");
    await page.goto("/senior");
    await expect(page.getByRole("heading", { name: "Senior dashboard" })).toBeVisible();

    await page.getByLabel("Title").fill(title);
    await page.getByLabel("Topic").selectOption({ label: "Loops" });
    // Schedule ~20s in the future (IST wall clock, like a real senior would pick).
    const ist = new Date(Date.now() + 20_000 + 5.5 * 3600_000);
    const pad = (n: number) => String(n).padStart(2, "0");
    const local = `${ist.getUTCFullYear()}-${pad(ist.getUTCMonth() + 1)}-${pad(ist.getUTCDate())}T${pad(ist.getUTCHours())}:${pad(ist.getUTCMinutes())}`;
    await page.getByLabel("Publish at (IST)").fill(local);

    await page.getByLabel("Question (markdown)").fill("What does `range(3)` produce?");
    await page.getByLabel("Code snippet (optional)").fill("for i in range(3):\n    print(i)");
    // Options: two defaults exist; set texts and mark first correct (radio default: first is checked).
    const optionInputs = page.locator('input[placeholder^="Option"]');
    await optionInputs.nth(0).fill("0 1 2");
    await optionInputs.nth(1).fill("1 2 3");
    await page.getByRole("button", { name: "Schedule question" }).click();

    // Question appears in the scheduled list.
    await expect(page.getByText(title)).toBeVisible();

    // --- Student flow (separate context = separate cookies) ---
    const studentCtx = await browser.newContext();
    const studentPage = await studentCtx.newPage();
    await login(studentPage, "student@demo.pyarena", "DemoStudent!234");

    // Before release: not visible.
    await studentPage.goto("/");
    await expect(studentPage.getByText(title)).not.toBeVisible();

    // Wait for release, then it shows up on home.
    await studentPage.waitForTimeout(22_000);
    await studentPage.reload();
    await expect(studentPage.getByText(title)).toBeVisible();

    await studentCtx.close();
  });
});
