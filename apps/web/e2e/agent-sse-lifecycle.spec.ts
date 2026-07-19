import { expect, test, type APIRequestContext } from "@playwright/test";

const apiBaseURL = process.env.MEIZHAISEEK_API_BASE_URL || "http://127.0.0.1:8000";
const username = process.env.MEIZHAISEEK_E2E_USERNAME || "";
const password = process.env.MEIZHAISEEK_E2E_PASSWORD || "";

type LoginPayload = { token: string };
type RunPayload = { run_id: string; conversation_id: string; status: string };

async function apiLogin(request: APIRequestContext): Promise<string> {
  const response = await request.post(`${apiBaseURL}/api/auth/login`, { data: { username, password } });
  expect(response.ok()).toBeTruthy();
  return ((await response.json()) as LoginPayload).token;
}

async function createFailedVideoRun(request: APIRequestContext, token: string): Promise<RunPayload> {
  const response = await request.post(`${apiBaseURL}/api/agent-runs`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { agent_type: "video_script_breakdown", mode: "shot_text_excel", prompt: `v1.8.9 sse lifecycle ${Date.now()}` }
  });
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as RunPayload;
}

test.describe("agent SSE lifecycle", () => {
  test.skip(!username || !password, "MEIZHAISEEK_E2E_USERNAME/PASSWORD are required.");

  test("terminal event closes stream and omits sensitive fields", async ({ request }) => {
    const token = await apiLogin(request);
    const created = await createFailedVideoRun(request, token);
    const response = await request.get(`${apiBaseURL}/api/agent-runs/${encodeURIComponent(created.run_id)}/events`, {
      headers: { Authorization: `Bearer ${token}`, Accept: "text/event-stream" },
      timeout: 30_000
    });
    expect(response.ok()).toBeTruthy();
    const text = await response.text();
    expect(text).toContain(`"run_id": "${created.run_id}"`);
    expect(text).toMatch(/event: (completed|failed|cancelled|status)/);
    expect(text.toLowerCase()).not.toContain("raw_response");
    expect(text.toLowerCase()).not.toContain("workflow_options");
    expect(text.toLowerCase()).not.toContain("authorization");
    expect(text.toLowerCase()).not.toContain("bearer ");
    expect(text.toLowerCase()).not.toContain("api_key");
    expect(text.toLowerCase()).not.toContain("secret");
  });
});
