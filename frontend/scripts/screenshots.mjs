/**
 * One-off screenshot capture for PRs (quality bar: 375px + 1440px).
 * Usage: npm run screenshots   (dev server must be running)
 * Writes PNGs to ../docs/screenshots/.
 */
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const BASE = process.env.BASE_URL ?? "http://localhost:5173";
const OUT = resolve(dirname(fileURLToPath(import.meta.url)), "../../docs/screenshots");

const viewports = [
  { name: "mobile-375", width: 375, height: 812 },
  { name: "desktop-1440", width: 1440, height: 900 },
];

const browser = await chromium.launch();
mkdirSync(OUT, { recursive: true });

for (const vp of viewports) {
  const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
  await page.goto(BASE, { waitUntil: "networkidle" });
  await page.screenshot({ path: `${OUT}/home-${vp.name}.png`, fullPage: true });
  console.log(`saved home-${vp.name}.png`);
  await page.close();
}

await browser.close();
