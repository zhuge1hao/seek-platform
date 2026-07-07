import asyncio
import json
import os
from typing import Any, AsyncIterator, Iterator

import requests


class DeepSeekError(RuntimeError):
    pass


def model_name() -> str:
    return os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")


def is_configured() -> bool:
    return bool(os.getenv("DEEPSEEK_API_KEY", "").strip())


def _timeout() -> int:
    try:
        return max(1, int(os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "60")))
    except ValueError:
        return 60


def _request_body(messages: list[dict[str, str]], temperature: float, stream: bool = False) -> dict[str, Any]:
    body: dict[str, Any] = {"model": model_name(), "messages": messages, "temperature": temperature}
    if stream:
        body["stream"] = True
    return body


def _headers() -> dict[str, str]:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise DeepSeekError("DeepSeek API Key 未配置，请设置 DEEPSEEK_API_KEY。")
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def generate_answer(messages: list[dict[str, str]], temperature: float = 0.3) -> str:
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    try:
        # Bandit B113 reviewed: timeout is provided via _timeout().
        response = requests.post(  # nosec B113
            f"{base_url}/chat/completions",
            headers=_headers(),
            json=_request_body(messages, temperature),
            timeout=_timeout(),
        )
    except requests.RequestException as exc:
        raise DeepSeekError(f"DeepSeek 接口调用失败：{exc}") from exc
    if not response.ok:
        raise DeepSeekError(f"DeepSeek 接口返回错误状态：{response.status_code}。")
    try:
        data: dict[str, Any] = response.json()
        answer = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise DeepSeekError("DeepSeek 返回内容格式异常。") from exc
    return str(answer or "").strip()


async def async_generate_answer(messages: list[dict[str, str]], temperature: float = 0.3) -> str:
    return await asyncio.to_thread(generate_answer, messages, temperature)


def stream_answer(messages: list[dict[str, str]], temperature: float = 0.3) -> Iterator[str]:
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    try:
        # Bandit B113 reviewed: streaming request still has timeout via _timeout().
        with requests.post(  # nosec B113
            f"{base_url}/chat/completions",
            headers=_headers(),
            json=_request_body(messages, temperature, stream=True),
            timeout=_timeout(),
            stream=True,
        ) as response:
            if not response.ok:
                raise DeepSeekError(f"DeepSeek 接口返回错误状态：{response.status_code}。")
            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                line = raw_line.strip()
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    break
                try:
                    data = json.loads(line)
                    delta = data["choices"][0].get("delta") or {}
                except (ValueError, KeyError, IndexError, TypeError) as exc:
                    raise DeepSeekError("DeepSeek 流式返回内容格式异常。") from exc
                text = delta.get("content") or ""
                if text:
                    yield str(text)
    except requests.RequestException as exc:
        raise DeepSeekError(f"DeepSeek 流式接口调用失败：{exc}") from exc


async def async_stream_answer(messages: list[dict[str, str]], temperature: float = 0.3) -> AsyncIterator[str]:
    for delta in await asyncio.to_thread(lambda: list(stream_answer(messages, temperature))):
        yield delta
