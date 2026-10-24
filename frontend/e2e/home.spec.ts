import { expect, test } from "@playwright/test";

test("home page shows the product name", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle("CAWASMA");
  await expect(
    page.getByRole("heading", { level: 1, name: "CAWASMA" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "API docs" })).toHaveAttribute(
    "href",
    /\/docs$/,
  );
});
