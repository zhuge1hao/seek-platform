from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


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


def _bytes_request(url: str, token: str | None = None, timeout: int = 120) -> tuple[int, bytes, dict[str, str]]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - operator supplied acceptance target.
            digest = hashlib.sha256()
            total = 0
            chunks = 0
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                chunks += 1
                total += len(chunk)
                digest.update(chunk)
            body = json.dumps({"size_bytes": total, "sha256": digest.hexdigest(), "chunks": chunks}).encode()
            return resp.status, body, dict(resp.headers)
    except error.HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers)
    except Exception as exc:
        return 0, str(exc).encode("utf-8", errors="replace"), {}


def _parse_size(value: str) -> int:
    text = value.strip().upper()
    if text.endswith("MB"):
        return int(text[:-2]) * 1024 * 1024
    if text.endswith("KB"):
        return int(text[:-2]) * 1024
    return int(text)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_binary(path: Path, size_bytes: int) -> None:
    block = hashlib.sha256(path.name.encode("utf-8")).digest() * 32768
    remaining = size_bytes
    with path.open("wb") as handle:
        while remaining > 0:
            chunk = block[: min(len(block), remaining)]
            handle.write(chunk)
            remaining -= len(chunk)


def _write_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        archive.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        archive.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="acceptance" sheetId="1" r:id="rId1"/></sheets></workbook>')
        archive.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        archive.writestr("xl/worksheets/sheet1.xml", '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>v1.8.7 artifact acceptance</t></is></c></row></sheetData></worksheet>')


def _seed_sample_artifacts(size_bytes: int) -> dict[str, Any]:
    from services import task_store, user_admin_service
    from services.artifact_service import register_run_artifacts

    suffix = uuid.uuid4().hex[:10]
    username_a = f"minio_a_{suffix}"
    username_b = f"minio_b_{suffix}"
    password_a = f"Aa1_{uuid.uuid4().hex}"
    password_b = f"Bb1_{uuid.uuid4().hex}"
    user_admin_service.create_user(username_a, password_a, "viewer", remark="v1.8.7 MinIO acceptance user A")
    user_admin_service.create_user(username_b, password_b, "viewer", remark="v1.8.7 MinIO acceptance user B")

    run = task_store.create_run_from_payload(
        {
            "user_id": username_a,
            "username": username_a,
            "role": "viewer",
            "agent_type": "artifact_storage_acceptance",
            "mode": "v187_minio",
            "prompt": "v1.8.7 artifact storage acceptance seed",
        }
    )
    run_id = run["run_id"]
    sample_dir = API_ROOT / "runtime" / "acceptance" / "v187_minio" / run_id
    sample_dir.mkdir(parents=True, exist_ok=True)
    data_path = sample_dir / f"验收-{size_bytes // (1024 * 1024)}MB.bin"
    json_path = sample_dir / "report.json"
    xlsx_path = sample_dir / "video-breakdown.xlsx"
    png_path = sample_dir / "evidence.png"
    _write_binary(data_path, size_bytes)
    json_path.write_text(json.dumps({"run_id": run_id, "acceptance": "v1.8.7"}, ensure_ascii=False), encoding="utf-8")
    _write_xlsx(xlsx_path)
    png_path.write_bytes(bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154789c6360000002000100ffff03000006000557bfab540000000049454e44ae426082"))

    records = register_run_artifacts(
        username_a,
        run_id,
        [
            {"path": str(data_path), "type": "file", "filename": data_path.name},
            {"path": str(json_path), "type": "json", "filename": json_path.name},
            {"path": str(xlsx_path), "type": "excel", "filename": xlsx_path.name},
            {"path": str(png_path), "type": "image", "filename": png_path.name},
        ],
    )
    run["status"] = "completed"
    run["progress"] = 100
    run["current_step"] = "artifact acceptance seed completed"
    run["completed_at"] = datetime.now(timezone.utc).isoformat()
    run["result"] = {"files": records, "summary": {"acceptance": "v1.8.7 MinIO"}}
    task_store._write_run(run)
    return {
        "username_a": username_a,
        "password_a": password_a,
        "username_b": username_b,
        "password_b": password_b,
        "run_id": run_id,
        "artifact_id": records[0]["artifact_id"],
        "records": records,
        "source_sha256": _sha256(data_path),
        "source_size_bytes": data_path.stat().st_size,
    }


def _login(base: str, username: str, password: str) -> tuple[int, str | None]:
    status, body = _json_request("POST", f"{base}/api/auth/login", payload={"username": username, "password": password})
    return status, body.get("token") if status == 200 else None


def _has_secret_leak(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if "secret" in lowered or lowered in {"password", "token"}:
                return True
            if _has_secret_leak(item):
                return True
    elif isinstance(value, list):
        return any(_has_secret_leak(item) for item in value)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="v1.8.7 MinIO artifact storage acceptance")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default="")
    parser.add_argument("--password", default="")
    parser.add_argument("--token-env", default="MEIZHAISEEK_ACCEPTANCE_TOKEN")
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
    size_bytes = _parse_size(args.size)
    token = os.getenv(args.token_env)
    token_b: str | None = None
    run_id = args.run_id
    artifact_id = args.artifact_id
    records: list[dict[str, Any]] = []
    source_sha256 = ""
    source_size = 0
    owner_user_id = ""

    if not run_id or not artifact_id:
        try:
            seed = _seed_sample_artifacts(size_bytes)
            run_id = seed["run_id"]
            artifact_id = seed["artifact_id"]
            records = seed["records"]
            source_sha256 = seed["source_sha256"]
            source_size = seed["source_size_bytes"]
            owner_user_id = seed["username_a"]
            login_status, token = _login(base, seed["username_a"], seed["password_a"])
            login_b_status, token_b = _login(base, seed["username_b"], seed["password_b"])
            report["seed"] = {
                "created": True,
                "run_id": run_id,
                "artifact_count": len(records),
                "storage_backend": records[0].get("storage_backend") if records else None,
                "user_a": seed["username_a"],
                "user_b": seed["username_b"],
            }
            report["checks"]["login_user_a"] = {"status_code": login_status}
            report["checks"]["login_user_b"] = {"status_code": login_b_status}
        except Exception as exc:
            report["status"] = "failed"
            report["reason"] = "sample_seed_failed"
            report["error"] = {"type": type(exc).__name__, "detail": str(exc)}
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 1
    elif not token and args.username and args.password:
        login_status, token = _login(base, args.username, args.password)
        report["checks"]["login"] = {"status_code": login_status, "auth": "password"}

    if not token:
        report["reason"] = "api_login_failed"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    signed_status, signed_body = _json_request("GET", f"{base}/api/agent-runs/{run_id}/artifacts/{artifact_id}/signed-url?ttl_seconds=2", token)
    direct_now_status = 0
    direct_expired_status = 0
    if signed_status == 200 and signed_body.get("storage_backend") == "s3" and signed_body.get("url"):
        direct_now_status, _, _ = _bytes_request(str(signed_body["url"]), timeout=60)
        time.sleep(3)
        direct_expired_status, _, _ = _bytes_request(str(signed_body["url"]), timeout=60)
    download_status, download_body, download_headers = _bytes_request(f"{base}/api/agent-runs/{run_id}/artifacts/{artifact_id}/download", token)
    parsed_download = json.loads(download_body.decode("utf-8", errors="replace")) if download_status == 200 else {}
    report["checks"]["signed_url"] = {"status_code": signed_status, "body": {k: v for k, v in signed_body.items() if k != "url"}}
    report["checks"]["download"] = {
        "status_code": download_status,
        "size_bytes": parsed_download.get("size_bytes"),
        "sha256": parsed_download.get("sha256"),
        "chunks": parsed_download.get("chunks"),
        "content_type": download_headers.get("content-type"),
        "content_disposition": download_headers.get("content-disposition"),
    }
    report["checks"]["secret_leak"] = {"passed": not _has_secret_leak({k: v for k, v in signed_body.items() if k != "url"})}
    report["checks"]["checksum"] = {"passed": bool(source_sha256) and parsed_download.get("sha256") == source_sha256}
    report["checks"]["streaming_size"] = {"passed": bool(source_size) and parsed_download.get("size_bytes") == source_size}
    report["checks"]["chinese_filename"] = {"passed": "filename*=UTF-8''" in str(download_headers.get("content-disposition") or "")}

    object_key = str(records[0].get("object_key") if records else "")
    report["checks"]["object_key_partition"] = {"passed": object_key.startswith(f"artifacts/{owner_user_id}/{run_id}/{artifact_id}/") if records else None, "object_key": object_key}

    if token_b:
        forbidden_status, forbidden_body = _json_request("GET", f"{base}/api/agent-runs/{run_id}/artifacts/{artifact_id}/signed-url?ttl_seconds=60", token_b)
        report["checks"]["user_b_forbidden"] = {"status_code": forbidden_status, "body": forbidden_body}

    missing_status, missing_body = _json_request("GET", f"{base}/api/agent-runs/{run_id}/artifacts/missing-artifact/download", token)
    traversal_status, traversal_body = _json_request("GET", f"{base}/api/artifacts/download?path={parse.quote('../secret.txt')}", token)
    report["checks"]["missing_artifact"] = {"status_code": missing_status, "body": missing_body}
    report["checks"]["path_traversal"] = {"status_code": traversal_status, "body": traversal_body}

    report["checks"]["signed_url_immediate"] = {"status_code": direct_now_status}
    report["checks"]["signed_url_expired"] = {"status_code": direct_expired_status}

    artifact_statuses = {}
    for record in records[1:]:
        status, body, headers = _bytes_request(f"{base}/api/agent-runs/{run_id}/artifacts/{record['artifact_id']}/download", token)
        artifact_statuses[record["file_type"]] = {"status_code": status, "content_type": headers.get("content-type"), "body_length": len(body)}
    report["checks"]["artifact_matrix"] = artifact_statuses

    required = [
        signed_status == 200,
        download_status == 200,
        report["checks"]["secret_leak"]["passed"],
        report["checks"]["checksum"]["passed"],
        report["checks"]["streaming_size"]["passed"],
        report["checks"]["chinese_filename"]["passed"],
        report["checks"]["object_key_partition"]["passed"] is True,
        report["checks"].get("user_b_forbidden", {}).get("status_code") == 403 if token_b else True,
        missing_status == 404,
        traversal_status in {400, 403},
        direct_now_status == 200,
        direct_expired_status in {400, 403},
        all(item["status_code"] == 200 for item in artifact_statuses.values()),
    ]
    report["status"] = "passed" if all(required) else "failed"
    report["completed_at_epoch"] = time.time()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
