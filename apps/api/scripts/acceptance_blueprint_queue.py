from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any
from urllib import error, request


def _json_request(method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=30) as resp:  # nosec B310 - operator supplied acceptance target.
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"detail": body}
        return exc.code, parsed
    except Exception as exc:
        return 0, {"error": type(exc).__name__, "detail": str(exc)}


def _login(base_url: str, username: str, password: str) -> str | None:
    status, body = _json_request("POST", f"{base_url}/api/auth/login", payload={"username": username, "password": password})
    return body.get("token") if status == 200 else None


def main() -> int:
    parser = argparse.ArgumentParser(description="v1.8.5 blueprint queue acceptance")
    parser.add_argument("--base-url", default="http://127.0.0.1")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    parser.add_argument("--blueprint-id", default="")
    parser.add_argument("--test-case-id", default="")
    parser.add_argument("--json-report", action="store_true")
    args = parser.parse_args()

    report: dict[str, Any] = {"acceptance": "blueprint_queue", "status": "not_run", "checks": {}, "started_at_epoch": time.time()}
    base = args.base_url.rstrip("/")
    token = _login(base, args.username, args.password)
    if not token:
        report["reason"] = "api_login_failed"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    if not args.blueprint_id or not args.test_case_id:
        report["reason"] = "blueprint_id_and_test_case_id_required"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    run_status, run_body = _json_request("POST", f"{base}/api/agent-blueprints/{args.blueprint_id}/test-cases/{args.test_case_id}/run", token, {})
    report["checks"]["test_run_enqueue"] = {"status_code": run_status, "body": run_body}
    test_run = run_body.get("test_run") or {}
    test_run_id = test_run.get("test_run_id")
    if test_run_id:
        status, body = _json_request("GET", f"{base}/api/agent-blueprints/{args.blueprint_id}/test-runs/{test_run_id}", token)
        report["checks"]["test_run_status"] = {"status_code": status, "body": body}
    gate_status, gate_body = _json_request("POST", f"{base}/api/agent-blueprints/{args.blueprint_id}/release-gate", token, {})
    report["checks"]["release_gate"] = {"status_code": gate_status, "body": gate_body}

    ok = run_status in {200, 202} and bool(test_run_id) and gate_status in {200, 400, 422}
    report["status"] = "passed" if ok else "failed"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
