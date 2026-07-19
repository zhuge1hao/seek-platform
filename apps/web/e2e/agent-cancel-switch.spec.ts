import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const apiBaseURL = process.env.MEIZHAISEEK_API_BASE_URL || "http://127.0.0.1:8000";
const username = process.env.MEIZHAISEEK_E2E_USERNAME || "";
const password = process.env.MEIZHAISEEK_E2E_PASSWORD || "";
const videoPath = process.env.MEIZHAISEEK_E2E_VIDEO_PATH || "E:\\USE\\codexhome\\fenge\\videos\\test\\1.mp4";
const runRealVideo = process.env.MEIZHAISEEK_E2E_RUN_VIDEO === "1";

type LoginPayload = { token: string; user: { user_id: string; username: string; role: string; enabled?: boolean } };
type RunPayload = { run_id: string; conversation_id: string; status: string; progress?: number };

async function apiLogin(request: APIRequestContext): Promise<LoginPayload> {
  const response = await request.post(`${apiBaseURL}/api/auth/login`, { data: { username, password } });
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as LoginPayload;
}

async function seedBrowserSession(page: Page, login: LoginPayload): Promise<void> {
  await page.goto("/login");
  await page.evaluate((payload) => {
    window.localStorage.setItem("meizhaiseek_auth_token", payload.token);
    window.localStorage.setItem("meizhaiseek_user", JSON.stringify(payload.user));
  }, login);
}

async function createVideoRun(request: APIRequestContext, token: string, prompt: string): Promise<RunPayload & { queue_job_id?: string }> {
  const response = await request.post(`${apiBaseURL}/api/agent-runs`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      agent_type: "video_script_breakdown",
      mode: "shot_text_excel",
      prompt,
      video_path: videoPath,
      workflow_options: { export_excel: true, export_json: true, export_keyframes: true }
    },
    timeout: 30_000
  });
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as RunPayload & { queue_job_id?: string };
}

async function createFailedVideoRun(request: APIRequestContext, token: string, prompt: string): Promise<RunPayload> {
  const response = await request.post(`${apiBaseURL}/api/agent-runs`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { agent_type: "video_script_breakdown", mode: "shot_text_excel", prompt },
    timeout: 30_000
  });
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as RunPayload;
}

async function waitForStatus(request: APIRequestContext, token: string, runId: string, statuses: string[], timeoutMs = 90_000): Promise<RunPayload> {
  const deadline = Date.now() + timeoutMs;
  let latest: RunPayload | null = null;
  while (Date.now() < deadline) {
    const response = await request.get(`${apiBaseURL}/api/agent-runs/${encodeURIComponent(runId)}/summary`, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 20_000
    });
    expect(response.status()).toBeLessThan(500);
    if (response.ok()) {
      latest = (await response.json()) as RunPayload;
      if (statuses.includes(latest.status)) return latest;
    }
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  throw new Error(`run ${runId} did not reach ${statuses.join(",")}; latest=${JSON.stringify(latest)}`);
}

test.describe("agent cancel and run switch lifecycle", () => {
  test.skip(!runRealVideo || !username || !password, "Set MEIZHAISEEK_E2E_RUN_VIDEO=1 and credentials to run cancel/switch matrix.");

  test("cancels a queued or running run idempotently and preserves cancelled after refresh", async ({ page, request }) => {
    const login = await apiLogin(request);
    const token = login.token;
    const created = await createVideoRun(request, token, `v189-cancel-${Date.now()}`);
    expect(created.run_id).toMatch(/^run_/);
    expect(created.conversation_id).toMatch(/^conv_/);
    expect(created.queue_job_id || "").toContain(created.run_id);

    const firstCancel = await request.post(`${apiBaseURL}/api/agent-runs/${encodeURIComponent(created.run_id)}/cancel`, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 30_000
    });
    expect(firstCancel.ok()).toBeTruthy();
    expect(((await firstCancel.json()) as RunPayload).status).toBe("cancelled");

    const secondCancel = await request.post(`${apiBaseURL}/api/agent-runs/${encodeURIComponent(created.run_id)}/cancel`, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 30_000
    });
    expect(secondCancel.ok()).toBeTruthy();
    expect(((await secondCancel.json()) as RunPayload).status).toBe("cancelled");

    await waitForStatus(request, token, created.run_id, ["cancelled"], 30_000);
    await seedBrowserSession(page, login);
    await page.goto(`/agent?conversation_id=${encodeURIComponent(created.conversation_id)}`);
    await expect(page.getByText(created.run_id)).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/cancelled|已取消/).first()).toBeVisible({ timeout: 20_000 });
  });

  test("aborts the old run event stream when switching conversations", async ({ page, request }) => {
    const login = await apiLogin(request);
    const token = login.token;
    const source = await createVideoRun(request, token, `v189-switch-source-${Date.now()}`);
    const target = await createFailedVideoRun(request, token, `v189-switch-target-${Date.now()}`);
    await waitForStatus(request, token, source.run_id, ["running", "completed", "failed", "cancelled"], 45_000);

    await page.addInitScript(() => {
      const originalFetch = window.fetch.bind(window);
      (window as unknown as { __agentEventAborts: number; __agentEventUrls: string[] }).__agentEventAborts = 0;
      (window as unknown as { __agentEventAborts: number; __agentEventUrls: string[] }).__agentEventUrls = [];
      window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
        const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
        if (url.includes("/api/agent-runs/") && url.includes("/events")) {
          (window as unknown as { __agentEventUrls: string[] }).__agentEventUrls.push(url);
          init?.signal?.addEventListener("abort", () => {
            (window as unknown as { __agentEventAborts: number }).__agentEventAborts += 1;
          }, { once: true });
        }
        return originalFetch(input, init);
      }) as typeof window.fetch;
    });

    await seedBrowserSession(page, login);
    await page.goto(`/agent?conversation_id=${encodeURIComponent(source.conversation_id)}`);
    await expect(page.getByText(source.run_id)).toBeVisible({ timeout: 20_000 });
    await expect.poll(async () => page.evaluate(() => (window as unknown as { __agentEventUrls: string[] }).__agentEventUrls.length)).toBeGreaterThan(0);

    await page.goto(`/agent?conversation_id=${encodeURIComponent(target.conversation_id)}`);
    await expect(page.getByText(target.run_id)).toBeVisible({ timeout: 20_000 });
    await expect.poll(async () => page.evaluate(() => (window as unknown as { __agentEventAborts: number }).__agentEventAborts), { timeout: 20_000 }).toBeGreaterThan(0);
    await expect(page.getByText(source.run_id)).not.toBeVisible({ timeout: 10_000 });
  });
});
