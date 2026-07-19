import os
import time
from itertools import count

from locust import HttpUser, between, task


USERNAME = os.getenv("LOCUST_ADMIN_USERNAME", "admin")
PASSWORD = os.getenv("LOCUST_ADMIN_PASSWORD", "admin123")
AGENT_TYPE = os.getenv("LOCUST_AGENT_TYPE", "title_writing")
USER_PREFIX = os.getenv("LOCUST_USER_PREFIX", "").strip()
USER_COUNT = int(os.getenv("LOCUST_USER_COUNT", "0") or "0")
_USER_INDEX = count()


def _credentials() -> tuple[str, str]:
    if USER_PREFIX and USER_COUNT > 0:
        index = next(_USER_INDEX) % USER_COUNT
        return f"{USER_PREFIX}{index}", PASSWORD
    return USERNAME, PASSWORD


class MeizhaiseekUser(HttpUser):
    wait_time = between(1, 4)
    token: str | None = None
    last_run_id: str | None = None

    def on_start(self) -> None:
        username, password = _credentials()
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
            name="/api/auth/login",
        )
        if response.status_code == 200:
            self.token = response.json().get("token")

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(12)
    def browse_runtime(self) -> None:
        self.client.get("/health", name="/health")
        if not self.token:
            return
        self.client.get("/api/agents", headers=self.headers, name="/api/agents")
        self.client.get("/api/conversations?limit=20", headers=self.headers, name="/api/conversations")

    @task(1)
    def submit_agent_run(self) -> None:
        if not self.token:
            return
        payload = {
            "agent_type": AGENT_TYPE,
            "prompt": "Locust capacity baseline request",
            "workflow_options": {"source": "locust"},
        }
        with self.client.post("/api/agent-runs", json=payload, headers=self.headers, name="/api/agent-runs", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"submit failed: {response.status_code}")
                return
            body = response.json()
            run_id = body.get("run_id")
            if not run_id:
                response.failure("missing run_id")
                return
            self.last_run_id = str(run_id)
        self.client.get(f"/api/agent-runs/{run_id}/summary", headers=self.headers, name="/api/agent-runs/:id/summary")

    @task(2)
    def qa_basic_flow(self) -> None:
        if not self.token:
            return
        self.client.get("/api/qa/health", headers=self.headers, name="/api/qa/health")

    @task(1)
    def sse_active_run_smoke(self) -> None:
        if not self.token:
            return
        run_id = self.last_run_id
        if not run_id:
            return
        start = time.time()
        with self.client.get(
            f"/api/agent-runs/{run_id}/events",
            headers={**self.headers, "Accept": "text/event-stream"},
            name="/api/agent-runs/:id/events",
            stream=True,
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"SSE failed: {response.status_code}")
                return
            for _line in response.iter_lines(chunk_size=1):
                if time.time() - start > 5:
                    break
