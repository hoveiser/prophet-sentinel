import { test, expect } from "@playwright/test";
import path from "node:path";
const cache = path.resolve(import.meta.dirname, "../../../.cache");

test("unconfigured deployment is honest and makes zero initial RPC calls", async ({
  page,
}) => {
  let rpc = 0;
  const errors: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("studio.genlayer.com/api")) rpc++;
  });
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("./");
  await expect(
    page.getByText("DEPLOYMENT NOT VERIFIED", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Execute ↗", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Claim native refund ↗" }),
  ).toBeDisabled();
  expect(rpc).toBe(0);
  expect(errors).toEqual([]);
  await page.screenshot({
    path: path.join(cache, "observatory-desktop.png"),
    animations: "disabled",
  });
});

test("workbench changes Brier bands without changing source-based routing", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("./");
  await page.locator("#calibration").scrollIntoViewIfNeeded();
  await page.getByRole("slider").nth(0).focus();
  await page.getByRole("slider").nth(0).press("End");
  await expect(page.getByRole("slider").nth(0)).toHaveValue("10000");
  await page.getByLabel("Hypothetical resolved outcome").selectOption("NO");
  await expect(page.locator(".band-result")).toContainText(
    "DRIFT QUARANTINE WARN",
  );
  await expect(page.locator(".chart-values")).toContainText("100%");
  await page.getByLabel("Model proven fabrication").check();
  await expect(page.locator(".band-result")).toContainText(
    "HALLUCINATED SOURCE SLASH",
  );
  await page.getByLabel("Model proven fabrication").uncheck();
  await page.getByLabel("Hypothetical resolved outcome").selectOption("YES");
  await page.screenshot({
    path: path.join(cache, "observatory-calibration.png"),
    animations: "disabled",
  });
});

test("burner is explicit and memory-only; no deployment means no writes", async ({
  page,
}) => {
  await page.goto("./");
  await page.getByRole("button", { name: "Agent operator +" }).click();
  await page.getByRole("button", { name: "Create burner agent" }).click();
  await expect(
    page.getByText("Memory-only burner created.", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Submit register ↗" }),
  ).toBeDisabled();
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual([]);
  expect(await page.evaluate(() => Object.keys(sessionStorage))).toEqual([]);
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Connect MetaMask" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Agent operator +" }).click();
  await page.getByRole("button", { name: "Connect MetaMask" }).click();
  await expect(
    page.getByText("Wallet connection failed or was declined.", {
      exact: false,
    }),
  ).toBeVisible();
});

test("mobile layout stays within the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("./");
  await expect(
    page.getByRole("heading", {
      name: "Many forecasts. One accountable signal.",
    }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.getByRole("button", { name: "Agent operator +" }).click();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.screenshot({
    path: path.join(cache, "observatory-mobile.png"),
    animations: "disabled",
  });
});
