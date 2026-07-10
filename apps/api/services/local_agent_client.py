import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

import requests

from schemas.agent_runs import DEFAULT_VIDEO_SCRIPT_SESSION_ID
from services.agent_protocol_parser import normalize_agent_protocol_response
from services import debug_payload_service
from services.mock_agent_scenarios import mock_generic, mock_video_script


SHELL_METACHARS = ("&", "|", ";", ">", "<", "$(", "`", "\n", "\r")


def _safe_cli_args(command: str) -> list[str]:
    if any(token in command for token in SHELL_METACHARS):
        raise ValueError("command contains unsafe shell metacharacters")
    args = shlex.split(command, posix=os.name != "nt")
    if not args:
        raise ValueError("command is empty")
    executable = Path(args[0])
    if executable.suffix.lower() in {".bat", ".cmd"} and not executable.is_absolute():
        raise ValueError("Windows batch commands must use an absolute path")
    return args


def _timeout_seconds(connector: dict[str, Any] | None = None) -> int:
    raw = str((connector or {}).get("timeout_seconds") or os.getenv("LOCAL_AGENT_TIMEOUT_SECONDS", "1800"))
    try:
        return max(1, int(raw))
    except ValueError:
        return 1800


def _agent_url(connector: dict[str, Any] | None = None) -> str:
    base_url = str((connector or {}).get("base_url") or os.getenv("LOCAL_AGENT_BASE_URL", "http://localhost:8001")).rstrip("/")
    endpoint = str((connector or {}).get("endpoint") or os.getenv("LOCAL_AGENT_RUN_ENDPOINT", "/run"))
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    return f"{base_url}{endpoint}"


def _legacy_body(payload: dict[str, Any]) -> dict[str, Any]:
    body = {"prompt": payload.get("prompt") or ""}
    if payload.get("session_id"):
        body["session_id"] = payload.get("session_id")
    return body


def _failure(error: str, session_id: str | None = None, raw: Any = None, run_id: str | None = None, http_status: int | None = None) -> dict[str, Any]:
    debug_payload_service.save_error(run_id, error)
    return {
        "ok": False,
        "status": "failed",
        "session_id": session_id,
        "answer": None,
        "summary": {},
        "files": [],
        "quality_warnings": [],
        "skill_suggestions": [],
        "raw": raw,
        "error": error,
        "http_status": http_status,
    }


def _success(raw_response: Any, session_id: str | None = None, output_dir: str | None = None) -> dict[str, Any]:
    normalized = normalize_agent_protocol_response(raw_response, output_dir=output_dir)
    normalized_status = str(normalized.get("status") or "success").lower()
    if normalized_status in {"failed", "failure", "error"}:
        raw = normalized.get("raw_response")
        error = ""
        if isinstance(raw, dict):
            error = str(raw.get("error") or raw.get("detail") or raw.get("message") or "")
        error = error or str(normalized.get("answer") or "本地 agent 返回失败状态。")
        return _failure(error, session_id=session_id, raw=raw)

    return {
        "ok": True,
        "status": normalized_status,
        "session_id": session_id,
        "answer": normalized.get("answer") or "",
        "summary": normalized.get("summary") or {},
        "files": normalized.get("files") or [],
        "quality_warnings": normalized.get("quality_warnings") or [],
        "skill_suggestions": normalized.get("skill_suggestions") or [],
        "raw": normalized.get("raw_response"),
        "error": None,
    }


def _call_local_agent(payload: dict[str, Any], run_id: str | None = None, connector: dict[str, Any] | None = None) -> dict[str, Any]:
    mode = str((connector or {}).get("mode") or os.getenv("LOCAL_AGENT_MODE", "http")).strip().lower()
    timeout = _timeout_seconds(connector)
    session_id = (connector or {}).get("session_id") or payload.get("session_id")
    platform_agent_type = payload.get("_platform_agent_type") or payload.get("agent_type")
    debug_user_id = payload.get("_debug_user_id")
    if platform_agent_type == "video_script_breakdown" and not payload.get("agent_type"):
        payload = {key: value for key, value in payload.items() if not str(key).startswith("_")}
    else:
        payload = {**payload, "session_id": session_id}
    output_dir = payload.get("output_dir")
    metadata = {"agent_type": platform_agent_type, "connector_id": (connector or {}).get("connector_id"), "mode": mode, "user_id": debug_user_id}
    debug_payload_service.save_request(run_id, payload, metadata=metadata)

    if mode == "http":
        body = payload
        payload_style = str((connector or {}).get("payload_style") or os.getenv("LOCAL_AGENT_PAYLOAD_STYLE", "protocol")).strip().lower()
        if payload_style == "legacy":
            body = _legacy_body(payload)
        try:
            response = requests.post(_agent_url(connector), json=body, timeout=timeout)
        except requests.ConnectionError as exc:
            return _failure(
                f"本地 agent HTTP 服务无法连接，请检查 LOCAL_AGENT_BASE_URL 和 LOCAL_AGENT_RUN_ENDPOINT。原始错误：{exc}",
                session_id=session_id,
                run_id=run_id,
                http_status=None,
            )
        except requests.RequestException as exc:
            return _failure(f"本地 agent HTTP 调用失败：{exc}", session_id=session_id, run_id=run_id)

        if not response.ok:
            return _failure(
                f"本地 agent HTTP 返回非 2xx 状态码：{response.status_code}。响应内容：{response.text}",
                session_id=session_id,
                raw=response.text,
                run_id=run_id,
            )
        try:
            raw_response = response.json()
        except ValueError:
            raw_response = response.text
        debug_payload_service.save_response(run_id, raw_response, metadata=metadata)
        result = _success(raw_response, session_id=session_id, output_dir=output_dir)
        result["http_status"] = response.status_code
        return result

    if mode == "cli":
        command = str((connector or {}).get("cli_command") or os.getenv("LOCAL_AGENT_CLI_COMMAND", "")).strip()
        if not command:
            return _failure("本地 agent CLI 命令尚未配置，请设置 LOCAL_AGENT_CLI_COMMAND。", session_id=session_id, run_id=run_id)
        try:
            args = _safe_cli_args(command)
        except ValueError as exc:
            return _failure(f"Local agent CLI command rejected: {exc}", session_id=session_id, run_id=run_id)
        try:
            completed = subprocess.run(
                args,
                input=json.dumps(payload, ensure_ascii=False),
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
                env={**os.environ, "LOCAL_AGENT_SESSION_ID": session_id or ""},
            )
        except subprocess.TimeoutExpired as exc:
            return _failure(f"本地 agent CLI 调用超时：{exc}", session_id=session_id, run_id=run_id)
        except (OSError, subprocess.SubprocessError) as exc:
            return _failure(f"本地 agent CLI 调用失败：{exc}", session_id=session_id, run_id=run_id)

        if completed.returncode != 0:
            return _failure(
                completed.stderr or f"本地 agent CLI 调用失败，退出码：{completed.returncode}",
                session_id=session_id,
                raw={"stdout": completed.stdout, "stderr": completed.stderr},
                run_id=run_id,
            )
        try:
            cli_response: Any = json.loads(completed.stdout.strip())
        except ValueError:
            cli_response = completed.stdout.strip()
        debug_payload_service.save_response(run_id, cli_response, metadata=metadata)
        result = _success(cli_response, session_id=session_id, output_dir=output_dir)
        if completed.stderr:
            result["raw"] = {"response": result.get("raw"), "stderr": completed.stderr}
        return result

    if mode == "mock":
        if platform_agent_type == "video_script_breakdown":
            raw = mock_video_script(payload)
        else:
            raw = mock_generic(payload)
        debug_payload_service.save_response(run_id, raw, metadata=metadata)
        return _success(raw, session_id=session_id, output_dir=output_dir)

    return _failure(f"未知 LOCAL_AGENT_MODE：{mode}", session_id=session_id, run_id=run_id)


def run_video_script_breakdown_protocol(payload: dict[str, Any], run_id: str | None = None, connector: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {**payload, "_platform_agent_type": "video_script_breakdown"}
    return _call_local_agent(payload, run_id=run_id, connector=connector)


def run_generic_agent_protocol(payload: dict[str, Any], run_id: str | None = None, connector: dict[str, Any] | None = None) -> dict[str, Any]:
    return _call_local_agent(payload, run_id=run_id, connector=connector)


def run_video_script_breakdown(prompt: str, session_id: str | None = None) -> dict[str, Any]:
    return run_video_script_breakdown_protocol(
        {
            "session_id": session_id or os.getenv("LOCAL_AGENT_VIDEO_SCRIPT_SESSION_ID") or DEFAULT_VIDEO_SCRIPT_SESSION_ID,
            "agent_type": "video_script_breakdown",
            "mode": "standard_breakdown",
            "prompt": prompt,
            "video_path": "",
            "video_url": "",
            "output_dir": os.getenv("LOCAL_AGENT_OUTPUT_DIR", ""),
            "baseline_image_dir": "",
            "previous_excel_path": "",
            "options": {},
        }
    )
