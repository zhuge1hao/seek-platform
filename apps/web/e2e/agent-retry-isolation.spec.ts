import { expect, test, type APIRequestContext } from "@playwright/test";

const apiBaseURL = process.env.MEIZHAISEEK_API_BASE_URL || "http://127.0.0.1:8000";
const username = process.env.MEIZHAISEEK_E2E_USERNAME || "";
const password = process.env.MEIZHAISEEK_E2E_PASSWORD || "";
const otherUsername = process.env.MEIZHAISEEK_E2E_OTHER_USERNAME || "";
const otherPassword = process.env.MEIZHAISEEK_E2E_OTHER_PASSWORD || "";

type LoginPayload = { token: string };
type RunPayload = { run_id: string; conversation_id: string; status: string };

async function apiLogin(request: APIRequestContext, name: string, secret: string): Promise<string> {
  const response = await request.post(`${apiBaseURL}/api/auth/login`, { data: { username: name, password: secret } });
  expect(response.ok()).toBeTruthy();
  return ((await response.json()) as LoginPayload).token;
}

async function waitForTerminalRun(request: APIRequestContext, token: string, runId: string): Promise<RunPayload> {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    const response = await request.get(`${apiBaseURL}/api/agent-runs/${encodeURIComponent(runId)}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(response.status()).toBeLessThan(500);
    if (response.ok()) {
      const run = (await response.json()) as RunPayload;
      if (["completed", "failed", "cancelled"].includes(run.status)) return run;
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(`run ${runId} did not reach terminal state`);
}

test.describe("agent retry and isolation matrix", () => {
  test.skip(!username || !password || !otherUsername || !otherPassword, "MEIZHAISEEK_E2E credentials are required.");

  test("failed video run retries into a new run and stays isolated", async ({ request }) => {
    const token = await apiLogin(request, username, password);
    const createdResponse = await request.post(`${apiBaseURL}/api/agent-runs`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { agent_type: "video_script_breakdown", mode: "shot_text_excel", prompt: `v1.8.9 retry matrix ${Date.now()}` }
    });
    expect(createdResponse.ok()).toBeTruthy();
    const created = (await createdResponse.json()) as RunPayload;
    const failed = await waitForTerminalRun(request, token, created.run_id);
    expect(failed.status).toBe("failed");

    const retryResponse = await request.post(`${apiBaseURL}/api/agent-runs/${encodeURIComponent(created.run_id)}/retry`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(retryResponse.ok()).toBeTruthy();
    const retried = (await retryResponse.json()) as RunPayload;
    expect(retried.run_id).not.toBe(created.run_id);
    expect(retried.conversation_id).toBe(created.conversation_id);

    const detailResponse = await request.get(`${apiBaseURL}/api/conversations/${encodeURIComponent(created.conversation_id)}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(detailResponse.ok()).toBeTruthy();
    const detailText = JSON.stringify(await detailResponse.json());
    expect(detailText).toContain(created.run_id);
    expect(detailText).toContain(retried.run_id);

    const otherToken = await apiLogin(request, otherUsername, otherPassword);
    for (const path of [
      `/api/agent-runs/${encodeURIComponent(created.run_id)}`,
      `/api/agent-runs/${encodeURIComponent(created.run_id)}/summary`,
      `/api/agent-runs/${encodeURIComponent(created.run_id)}/events`,
      `/api/conversations/${encodeURIComponent(created.conversation_id)}`
    ]) {
      const isolated = await request.get(`${apiBaseURL}${path}`, { headers: { Authorization: `Bearer ${otherToken}` } });
      expect([403, 404]).toContain(isolated.status());
    }
  });
});
