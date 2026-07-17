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
        with request.urlopen(req, timeout=60) as resp:  # nosec B310 - operator supplied acceptance target.
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                body = json.loads(raw or "{}")
            except json.JSONDecodeError:
                body = {"body_length": len(raw)}
            return resp.status, body
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"detail": body}
        return exc.code, parsed
    except Exception as exc:
        return 0, {"error": type(exc).__name__, "detail": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="v1.8.5 MinIO artifact storage acceptance")
    parser.add_argument("--base-url", default="http://127.0.0.1")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--artifact-id", default="")
    parser.add_argument("--size", default="10MB")
    parser.add_argument("--json-report", action="store_true")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "acceptance": "minio_storage",
        "status": "not_run",
        "requested_size": args.size,
        "checks": {},
        "started_at_epoch": time.time(),
    }
    base = args.base_url.rstrip("/")
    login_status, login_body = _json_request("POST", f"{base}/api/auth/login", payload={"username": args.username, "password": args.password})
    token = login_body.get("token") if login_status == 200 else None
    report["checks"]["login"] = {"status_code": login_status}
    if not token:
        report["reason"] = "api_login_failed"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    if not args.run_id or not args.artifact_id:
        report["reason"] = "run_id_and_artifact_id_required"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    signed_status, signed_body = _json_request("GET", f"{base}/api/agent-runs/{args.run_id}/artifacts/{args.artifact_id}/signed-url?ttl_seconds=5", token)
    download_status, download_body = _json_request("GET", f"{base}/api/agent-runs/{args.run_id}/artifacts/{args.artifact_id}/download", token)
    report["checks"]["signed_url"] = {"status_code": signed_status, "body": {k: v for k, v in signed_body.items() if k != "url"}}
    report["checks"]["download"] = {"status_code": download_status, "body": download_body}
    report["checks"]["secret_leak"] = {"passed": not any(key.lower().endswith("secret") or "access_key" in key.lower() for key in signed_body)}
    ok = signed_status == 200 and download_status == 200 and report["checks"]["secret_leak"]["passed"]
    report["status"] = "passed" if ok else "failed"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
