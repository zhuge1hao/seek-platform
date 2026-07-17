from __future__ import annotations

import argparse
import json
import os
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
        with request.urlopen(req, timeout=20) as resp:  # nosec B310 - acceptance target is operator supplied.
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


def _login(base_url: str, username: str, password: str) -> tuple[str | None, dict[str, Any]]:
    status, body = _json_request("POST", f"{base_url}/api/auth/login", payload={"username": username, "password": password})
    return body.get("token") if status == 200 else None, {"status_code": status, "body": body}


def main() -> int:
    parser = argparse.ArgumentParser(description="v1.8.7 dataset queue acceptance")
    parser.add_argument("--base-url", default="http://127.0.0.1")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    parser.add_argument("--token-env", default="MEIZHAISEEK_ACCEPTANCE_TOKEN")
    parser.add_argument("--dataset-id", default="")
    parser.add_argument("--json-report", action="store_true")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "acceptance": "dataset_queue",
        "status": "not_run",
        "checks": {},
        "started_at_epoch": time.time(),
    }
    token = os.getenv(args.token_env)
    login = {"status_code": 0, "body": {"auth": "token_env" if token else "password"}}
    if not token:
        token, login = _login(args.base_url.rstrip("/"), args.username, args.password)
    report["checks"]["login"] = login
    if not token:
        report["reason"] = "api_login_failed"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    if not args.dataset_id:
        list_status, list_body = _json_request("GET", f"{args.base_url.rstrip('/')}/api/datasets", token)
        report["checks"]["dataset_discovery"] = {"status_code": list_status, "body": list_body}
        datasets = list_body.get("datasets") or []
        if datasets:
            args.dataset_id = str(datasets[0].get("dataset_id") or "")
    if not args.dataset_id:
        report["reason"] = "dataset_id_required"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    base = args.base_url.rstrip("/")
    clean_status, clean_body = _json_request("POST", f"{base}/api/datasets/{args.dataset_id}/clean", token, {"rules": {"drop_empty": True}})
    export_status, export_body = _json_request("POST", f"{base}/api/datasets/{args.dataset_id}/export", token, {"format": "xlsx"})
    report["checks"]["dataset_clean_enqueue"] = {"status_code": clean_status, "body": clean_body}
    report["checks"]["dataset_export_enqueue"] = {"status_code": export_status, "body": export_body}

    job_id = export_body.get("job_id")
    if job_id:
        status_code, body = _json_request("GET", f"{base}/api/datasets/jobs/{job_id}", token)
        report["checks"]["job_status"] = {"status_code": status_code, "body": body}
        cancel_status, cancel_body = _json_request("POST", f"{base}/api/datasets/jobs/{job_id}/cancel", token, {})
        retry_status, retry_body = _json_request("POST", f"{base}/api/datasets/jobs/{job_id}/retry", token, {})
        report["checks"]["job_cancel"] = {"status_code": cancel_status, "body": cancel_body}
        report["checks"]["job_retry"] = {"status_code": retry_status, "body": retry_body}

    ok = clean_status in {200, 202} and export_status in {200, 202} and bool(job_id)
    report["status"] = "passed" if ok else "failed"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
