import { expect, test, type APIRequestContext } from "@playwright/test";

const apiBaseURL = process.env.MEIZHAISEEK_API_BASE_URL || "http://127.0.0.1:8000";
const username = process.env.MEIZHAISEEK_E2E_USERNAME || "";
const password = process.env.MEIZHAISEEK_E2E_PASSWORD || "";
const videoPath = process.env.MEIZHAISEEK_E2E_VIDEO_PATH || "E:\\USE\\codexhome\\fenge\\videos\\test\\1.mp4";
const runRealVideo = process.env.MEIZHAISEEK_E2E_RUN_VIDEO === "1";

type LoginPayload = { token: string };
type RunPayload = { run_id: string; conversation_id: string; status: string; result?: { files?: Array<{ artifact_id?: string; file_type?: string; type?: string; filename?: string; name?: string; download_url?: string }> } };

async function apiLogin(request: APIRequestContext): Promise<string> {
  const response = await request.post(`${apiBaseURL}/api/auth/login`, { data: { username, password } });
  expect(response.ok()).toBeTruthy();
  return ((await response.json()) as LoginPayload).token;
}

async function waitForTerminalRun(request: APIRequestContext, token: string, runId: string): Promise<RunPayload> {
  const deadline = Date.now() + 30 * 60_000;
  while (Date.now() < deadline) {
    const response = await request.get(`${apiBaseURL}/api/agent-runs/${encodeURIComponent(runId)}/summary`, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 30_000
    });
    expect(response.status()).toBeLessThan(500);
    if (response.ok()) {
      const run = (await response.json()) as RunPayload;
      if (["completed", "failed", "cancelled"].includes(run.status)) return run;
    }
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }
  throw new Error(`video run ${runId} did not reach terminal state`);
}

test.describe("agent real video downloads", () => {
  test.skip(!runRealVideo || !username || !password, "Set MEIZHAISEEK_E2E_RUN_VIDEO=1 and credentials to run real 8001 video matrix.");

  test("completes real video run and downloads Excel/JSON/evidence artifacts", async ({ request }) => {
    const token = await apiLogin(request);
    const health = await request.get(`${apiBaseURL}/api/agents/video-script/status`, { headers: { Authorization: `Bearer ${token}` } });
    expect(health.ok()).toBeTruthy();
    expect((await health.json()).status).toBe("connected");

    const createdResponse = await request.post(`${apiBaseURL}/api/agent-runs`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        agent_type: "video_script_breakdown",
        mode: "shot_text_excel",
        prompt: `v1.8.9 real video matrix ${Date.now()}`,
        video_path: videoPath,
        workflow_options: { export_excel: true, export_json: true, export_keyframes: true, keep_debug_payload: true }
      },
      timeout: 30_000
    });
    expect(createdResponse.ok()).toBeTruthy();
    const created = (await createdResponse.json()) as RunPayload;
    const completed = await waitForTerminalRun(request, token, created.run_id);
    expect(completed.status).toBe("completed");

    const resultResponse = await request.get(`${apiBaseURL}/api/agent-runs/${encodeURIComponent(created.run_id)}/result`, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 30_000
    });
    expect(resultResponse.ok()).toBeTruthy();
    const result = (await resultResponse.json()).result as RunPayload["result"];
    const files = result?.files || [];
    expect(files.some((file) => (file.file_type || file.type) === "excel")).toBeTruthy();
    expect(files.some((file) => String(file.filename || file.name || "").endsWith(".json"))).toBeTruthy();

    for (const file of files.filter((item) => item.download_url).slice(0, 5)) {
      const download = await request.get(`${apiBaseURL}${file.download_url}`, { headers: { Authorization: `Bearer ${token}` }, timeout: 30_000 });
      expect(download.ok()).toBeTruthy();
      expect((await download.body()).length).toBeGreaterThan(0);
    }
  });
});
