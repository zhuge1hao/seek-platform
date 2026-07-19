import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const apiBaseURL = process.env.MEIZHAISEEK_API_BASE_URL || "http://127.0.0.1:8000";
const username = process.env.MEIZHAISEEK_E2E_USERNAME || "";
const password = process.env.MEIZHAISEEK_E2E_PASSWORD || "";
const otherUsername = process.env.MEIZHAISEEK_E2E_OTHER_USERNAME || "";
const otherPassword = process.env.MEIZHAISEEK_E2E_OTHER_PASSWORD || "";

type LoginPayload = {
  token: string;
  user: { username: string; role: string; user_id: string };
};

type RunPayload = {
  run_id: string;
  conversation_id: string;
  status: string;
};

async function uiLogin(page: Page, name: string, secret: string): Promise<string> {
  const loginResponse = page.waitForResponse((response) => response.url().includes("/api/auth/login") && response.request().method() === "POST");
  await page.goto("/login");
  await page.evaluate(() => {
    localStorage.removeItem("meizhaiseek_active_conversation_id");
  });
  await page.locator("input").first().fill(name);
  await page.locator('input[type="password"]').fill(secret);
  await page.locator('button[type="submit"]').click();
  const response = await loginResponse;
  expect(response.ok()).toBeTruthy();
  const payload = (await response.json()) as LoginPayload;
  await expect(page).toHaveURL(/\/agent/, { timeout: 20_000 });
  return payload.token;
}

async function openFreshAgentSelection(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.removeItem("meizhaiseek_active_conversation_id");
  });
  const conversationsLoaded = page
    .waitForResponse((response) => response.url().includes("/api/conversations") && response.request().method() === "GET", { timeout: 15_000 })
    .catch(() => null);
  await page.goto("/agent");
  await conversationsLoaded;
  await expect(page.getByTestId("agent-new-conversation")).toBeVisible({ timeout: 10_000 });
  await page.getByTestId("agent-new-conversation").click();
  await expect(page.getByTestId("agent-card-0")).toBeVisible({ timeout: 10_000 });
  await page.waitForTimeout(300);
}

async function apiLogin(request: APIRequestContext, name: string, secret: string): Promise<string> {
  const response = await request.post(`${apiBaseURL}/api/auth/login`, {
    data: { username: name, password: secret }
  });
  expect(response.ok()).toBeTruthy();
  return ((await response.json()) as LoginPayload).token;
}

async function waitForTerminalRun(request: APIRequestContext, token: string, runId: string): Promise<RunPayload> {
  const deadline = Date.now() + 90_000;
  let latest: RunPayload | null = null;
  while (Date.now() < deadline) {
    const response = await request.get(`${apiBaseURL}/api/agent-runs/${encodeURIComponent(runId)}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(response.status()).toBeLessThan(500);
    if (response.ok()) {
      latest = (await response.json()) as RunPayload;
      if (["completed", "failed", "cancelled"].includes(latest.status)) return latest;
    }
    await new Promise((resolve) => setTimeout(resolve, 2_000));
  }
  throw new Error(`run ${runId} did not reach a terminal state; latest=${JSON.stringify(latest)}`);
}

test.describe("agent run card production smoke", () => {
  test.skip(!username || !password || !otherUsername || !otherPassword, "MEIZHAISEEK_E2E_USERNAME/PASSWORD and OTHER credentials are required.");

  test("creates a real run, refreshes the conversation list, restores after reload, and enforces user isolation", async ({ page, request }) => {
    const consoleErrors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });

    const token = await uiLogin(page, username, password);
    await openFreshAgentSelection(page);
    await page.getByTestId("agent-card-0").click({ force: true });

    const prompt = `v1.8.9 browser smoke ${Date.now()}`;
    await page.locator("#generic-agent-prompt").fill(prompt);
    const createdResponse = page.waitForResponse((response) => response.url().includes("/api/agent-runs") && response.request().method() === "POST");
    await page.getByTestId("agent-submit-run").click();
    const created = (await (await createdResponse).json()) as RunPayload & { queue_job_id?: string };

    expect(created.run_id).toMatch(/^run_/);
    expect(created.conversation_id).toMatch(/^conv_/);
    if (created.queue_job_id) expect(created.queue_job_id).toContain(created.run_id);

    await expect(page.getByText(created.run_id)).toBeVisible({ timeout: 20_000 });
    await expect(page).toHaveURL(new RegExp(`conversation_id=${created.conversation_id}`), { timeout: 20_000 });

    const terminalRun = await waitForTerminalRun(request, token, created.run_id);
    await page.reload();
    await expect(page.getByText(created.run_id)).toBeVisible({ timeout: 20_000 });

    const ownerConversation = await request.get(`${apiBaseURL}/api/conversations/${encodeURIComponent(created.conversation_id)}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(ownerConversation.ok()).toBeTruthy();
    const ownerDetail = await ownerConversation.json();
    expect(JSON.stringify(ownerDetail)).toContain(created.run_id);

    const otherToken = await apiLogin(request, otherUsername, otherPassword);
    const isolatedRun = await request.get(`${apiBaseURL}/api/agent-runs/${encodeURIComponent(created.run_id)}`, {
      headers: { Authorization: `Bearer ${otherToken}` }
    });
    expect([403, 404]).toContain(isolatedRun.status());
    const isolatedConversation = await request.get(`${apiBaseURL}/api/conversations/${encodeURIComponent(created.conversation_id)}`, {
      headers: { Authorization: `Bearer ${otherToken}` }
    });
    expect([403, 404]).toContain(isolatedConversation.status());

    await page.evaluate(() => localStorage.clear());
    await uiLogin(page, otherUsername, otherPassword);
    await page.goto(`/agent?conversation_id=${created.conversation_id}`);
    await expect(page.getByText(created.run_id)).not.toBeVisible({ timeout: 5_000 });

    expect(["completed", "failed", "cancelled"]).toContain(terminalRun.status);
    const severeErrors = consoleErrors.filter((message) => !message.includes("favicon") && !message.includes("status of 404"));
    expect(severeErrors).toEqual([]);
  });
});
