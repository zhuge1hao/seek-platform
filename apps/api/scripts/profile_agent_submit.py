from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[3]


def _load_env() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip() and not raw.lstrip().startswith("#") and "=" in raw:
            key, value = raw.split("=", 1)
            os.environ.setdefault(key.strip().lstrip("\ufeff"), value.strip().strip('"').strip("'"))


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, int(len(ordered) * quantile + 0.999999) - 1))]


def _summary(values: list[float]) -> dict[str, float | None]:
    return {"p50": _percentile(values, 0.5), "p95": _percentile(values, 0.95), "p99": _percentile(values, 0.99)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile POST /api/agent-runs without exposing credentials.")
    parser.add_argument("--base-url", default="http://127.0.0.1")
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--json-report", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--include-stage-timing", action="store_true")
    args = parser.parse_args()
    _load_env()
    base = args.base_url.rstrip("/")
    username = os.getenv("SMOKE_ADMIN_USERNAME") or os.getenv("MEIZHAISEEK_ADMIN_USERNAME")
    password = os.getenv("SMOKE_ADMIN_PASSWORD") or os.getenv("MEIZHAISEEK_ADMIN_INITIAL_PASSWORD")
    if not username or not password:
        raise RuntimeError("smoke admin credentials are required")
    token = requests.post(f"{base}/api/auth/login", json={"username": username, "password": password}, timeout=20).json()["token"]
    runtime = requests.get(f"{base}/api/admin/runtime/health", headers={"Authorization": f"Bearer {token}"}, timeout=20).json()
    if runtime.get("version") != args.expected_version:
        raise RuntimeError(f"runtime version mismatch: {runtime.get('version')}")

    def submit(index: int) -> dict[str, Any]:
        started = time.perf_counter()
        response = requests.post(
            f"{base}/api/agent-runs",
            headers={"Authorization": f"Bearer {token}"},
            json={"agent_type": "competitor_analysis", "prompt": f"v1.8.10 submit profile {index}"},
            timeout=30,
        )
        elapsed = (time.perf_counter() - started) * 1000
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        return {
            "ok": response.ok, "status": response.status_code, "elapsed_ms": elapsed,
            "transactions": int(response.headers.get("X-App-DB-Transactions", 0)),
            "acquires": int(response.headers.get("X-App-DB-Acquires", 0)),
            "executes": int(response.headers.get("X-App-DB-Executes", 0)),
            "commits": int(response.headers.get("X-App-DB-Commits", 0)),
            "rollbacks": int(response.headers.get("X-App-DB-Rollbacks", 0)),
            "run_id": body.get("run_id"), "conversation_id": body.get("conversation_id"), "queue_job_id": body.get("queue_job_id"),
        }

    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        rows = list(pool.map(submit, range(max(1, args.requests))))
    successful = [row for row in rows if row["ok"]]
    report = {
        "requests": len(rows), "success": len(successful), "failed": len(rows) - len(successful),
        "latency_ms": _summary([row["elapsed_ms"] for row in successful]),
        **{name: _summary([float(row[name]) for row in successful]) for name in ("transactions", "acquires", "executes", "commits", "rollbacks")},
        "ids": [{key: row[key] for key in ("run_id", "conversation_id", "queue_job_id")} for row in successful[:3]],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2 if args.json_report else None)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if len(successful) == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
