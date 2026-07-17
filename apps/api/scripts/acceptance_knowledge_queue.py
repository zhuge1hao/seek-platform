from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error, request


def _request(method: str, url: str, token: str | None = None, data: bytes | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    merged = dict(headers or {})
    if token:
        merged["Authorization"] = f"Bearer {token}"
    req = request.Request(url, data=data, headers=merged, method=method)
    try:
        with request.urlopen(req, timeout=60) as resp:  # nosec B310 - operator supplied acceptance target.
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


def _json(method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    return _request(method, url, token, body, {"Content-Type": "application/json"})


def _login(base_url: str, username: str, password: str) -> str | None:
    status, body = _json("POST", f"{base_url}/api/auth/login", payload={"username": username, "password": password})
    return body.get("token") if status == 200 else None


def main() -> int:
    parser = argparse.ArgumentParser(description="v1.8.5 knowledge queue acceptance")
    parser.add_argument("--base-url", default="http://127.0.0.1")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    parser.add_argument("--seed-documents", nargs="*", default=[])
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--json-report", action="store_true")
    args = parser.parse_args()

    report: dict[str, Any] = {"acceptance": "knowledge_queue", "status": "not_run", "checks": {}, "started_at_epoch": time.time()}
    base = args.base_url.rstrip("/")
    token = _login(base, args.username, args.password)
    if not token:
        report["reason"] = "api_login_failed"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    if not args.seed_documents:
        report["reason"] = "seed_documents_required"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    uploaded: list[str] = []
    for raw_path in args.seed_documents:
        path = Path(raw_path)
        if not path.exists():
            report["checks"][str(path)] = {"status": "failed", "reason": "file_not_found"}
            continue
        boundary = f"----meizhaiseek{int(time.time() * 1000)}"
        payload = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\n{path.stem}\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8") + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
        status, body = _request("POST", f"{base}/api/qa/knowledge/upload", token, payload, {"Content-Type": f"multipart/form-data; boundary={boundary}"})
        report["checks"][f"upload:{path.name}"] = {"status_code": status, "body": body}
        doc_id = body.get("doc_id")
        if doc_id:
            uploaded.append(doc_id)

    stats_status, stats_body = _request("GET", f"{base}/api/qa/knowledge/stats", token)
    docs_status, docs_body = _request("GET", f"{base}/api/qa/knowledge/documents", token)
    report["checks"]["stats"] = {"status_code": stats_status, "body": stats_body}
    report["checks"]["documents"] = {"status_code": docs_status, "body": docs_body}
    if uploaded:
        reindex_status, reindex_body = _json("POST", f"{base}/api/qa/knowledge/documents/{uploaded[0]}/reindex", token, {})
        report["checks"]["reindex"] = {"status_code": reindex_status, "body": reindex_body}
    if args.cleanup:
        for doc_id in uploaded:
            status, body = _request("DELETE", f"{base}/api/qa/knowledge/documents/{doc_id}", token)
            report["checks"][f"delete:{doc_id}"] = {"status_code": status, "body": body}

    ok = len(uploaded) >= min(5, len(args.seed_documents)) and stats_status == 200 and docs_status == 200
    report["uploaded_documents"] = uploaded
    report["status"] = "passed" if ok else "failed"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
