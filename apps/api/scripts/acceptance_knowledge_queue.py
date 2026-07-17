from __future__ import annotations

import argparse
import json
import os
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
    parser = argparse.ArgumentParser(description="v1.8.7 knowledge queue acceptance")
    parser.add_argument("--base-url", default="http://127.0.0.1")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    parser.add_argument("--token-env", default="MEIZHAISEEK_ACCEPTANCE_TOKEN")
    parser.add_argument("--seed-documents", nargs="*", default=[])
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--json-report", action="store_true")
    args = parser.parse_args()

    report: dict[str, Any] = {"acceptance": "knowledge_queue", "status": "not_run", "checks": {}, "started_at_epoch": time.time()}
    base = args.base_url.rstrip("/")
    token = os.getenv(args.token_env) or _login(base, args.username, args.password)
    if not token:
        report["reason"] = "api_login_failed"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    if not args.seed_documents:
        seed_dir = Path("runtime/logs/v187_knowledge_seed")
        seed_dir.mkdir(parents=True, exist_ok=True)
        generated = []
        for idx in range(5):
            path = seed_dir / f"knowledge_seed_{idx + 1}.md"
            path.write_text((f"# v1.8.7 knowledge seed {idx + 1}\n\n" + "This controlled acceptance document has non-sensitive commerce BI text. " * 80), encoding="utf-8")
            generated.append(str(path))
        args.seed_documents = generated
        report["generated_seed_documents"] = len(generated)

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

    terminal: dict[str, Any] = {}
    deadline = time.time() + 180
    while uploaded and time.time() < deadline:
        time.sleep(2)
        poll_status, poll_body = _request("GET", f"{base}/api/qa/knowledge/documents", token)
        docs = poll_body.get("documents") or []
        by_id = {str(item.get("doc_id")): item for item in docs}
        terminal = {doc_id: by_id.get(doc_id, {}) for doc_id in uploaded}
        if all((item.get("status") in {"ready", "completed", "failed"}) for item in terminal.values()):
            report["checks"]["documents_after_ingest"] = {"status_code": poll_status, "body": {"uploaded": terminal}}
            break
    ready_docs = [doc_id for doc_id, item in terminal.items() if item.get("status") in {"ready", "completed"} and int(item.get("chunk_count") or 0) > 0]

    if ready_docs:
        uploaded[0] = ready_docs[0]
        reindex_status, reindex_body = _json("POST", f"{base}/api/qa/knowledge/documents/{uploaded[0]}/reindex", token, {})
        report["checks"]["reindex"] = {"status_code": reindex_status, "body": reindex_body}
        reindex_deadline = time.time() + 180
        while time.time() < reindex_deadline:
            time.sleep(2)
            detail_status, detail_body = _request("GET", f"{base}/api/qa/knowledge/documents/{uploaded[0]}", token)
            document = detail_body.get("document") or {}
            if document.get("status") in {"ready", "completed", "failed"}:
                report["checks"]["reindex_after_completion"] = {"status_code": detail_status, "body": {"document": document}}
                break
        retrieval_status, retrieval_body = _json("POST", f"{base}/api/qa/test-retrieval", token, {"question": "commerce BI controlled acceptance document", "top_k": 5})
        report["checks"]["top_k_retrieval"] = {"status_code": retrieval_status, "body": retrieval_body}
    if args.cleanup:
        for doc_id in uploaded:
            status, body = _request("DELETE", f"{base}/api/qa/knowledge/documents/{doc_id}", token)
            report["checks"][f"delete:{doc_id}"] = {"status_code": status, "body": body}

    reindex_document = (report["checks"].get("reindex_after_completion", {}).get("body") or {}).get("document") or {}
    retrieval_body = (report["checks"].get("top_k_retrieval", {}).get("body") or {})
    ok = (
        len(ready_docs) >= min(5, len(args.seed_documents))
        and stats_status == 200
        and docs_status == 200
        and (not ready_docs or (reindex_document.get("status") in {"ready", "completed"} and int(reindex_document.get("chunk_count") or 0) > 0))
        and (not ready_docs or int(retrieval_body.get("source_count") or 0) > 0)
    )
    report["uploaded_documents"] = uploaded
    report["ready_documents"] = ready_docs
    report["status"] = "passed" if ok else "failed"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
