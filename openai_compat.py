"""
Normalize chat completion responses from quirky OpenAI-compatible gateways.

Some proxies return the full JSON body as a Python str (or wrap it in {data: "..."}),
so client.chat.completions.create() is not always a parsed object with .choices.
Others return non-JSON plain text (treated as a single assistant message).
"""

from __future__ import annotations

import json
import os
import re
import time
from types import SimpleNamespace
from typing import Any, Optional

try:
    from openai import RateLimitError
except ImportError:
    RateLimitError = None  # type: ignore[misc, assignment]


def _unwrap_json_string_blob(blob: Any) -> Any:
    """Repeatedly json.loads while the value is a JSON string (double-encoding)."""
    cur = blob
    for _ in range(6):
        if not isinstance(cur, str):
            return cur
        s = cur.strip()
        if not s:
            return cur
        try:
            cur = json.loads(s)
        except json.JSONDecodeError:
            return cur
    return cur


def _maybe_unwrap_envelope(d: dict) -> dict:
    """If body is nested under data/result/output, peel one level."""
    if "choices" in d and isinstance(d.get("choices"), list) and d["choices"]:
        return d
    for key in ("data", "result", "output", "response", "body", "payload"):
        inner = d.get(key)
        if inner is None:
            continue
        if isinstance(inner, str):
            inner = _unwrap_json_string_blob(inner)
        if isinstance(inner, dict) and isinstance(inner.get("choices"), list) and inner["choices"]:
            return inner
    return d


def _deep_find_choices_payload(obj: Any, depth: int = 0, max_depth: int = 14) -> Optional[dict]:
    """Depth-first search for a dict with a non-empty 'choices' list."""
    if depth > max_depth or obj is None:
        return None
    if isinstance(obj, dict):
        ch = obj.get("choices")
        if isinstance(ch, list) and len(ch) > 0:
            return obj
        for v in obj.values():
            found = _deep_find_choices_payload(v, depth + 1, max_depth)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for it in obj:
            found = _deep_find_choices_payload(it, depth + 1, max_depth)
            if found is not None:
                return found
    elif isinstance(obj, str):
        s = obj.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                inner = json.loads(s)
            except json.JSONDecodeError:
                return None
            return _deep_find_choices_payload(inner, depth + 1, max_depth)
    return None


def _raise_if_api_error(d: dict) -> None:
    err = d.get("error")
    if isinstance(err, dict):
        msg = err.get("message", json.dumps(err, ensure_ascii=False))
        raise RuntimeError(f"LLM API error: {msg}")
    if isinstance(err, str) and err.strip():
        raise RuntimeError(f"LLM API error: {err}")


def _looks_like_html_document(s: str) -> bool:
    """True if the HTTP body looks like a web page, not a chat API JSON payload."""
    t = (s or "").lstrip()[:12000]
    if not t:
        return False
    low = t.lower()
    if low.startswith("<!doctype html") or low.startswith("<html"):
        return True
    if re.match(r"^\s*<\?xml\b", low):
        return True
    # Chinese portals / error pages often include these early
    if "<html" in low[:2500] and ("<head" in low[:4000] or "<body" in low[:4000]):
        return True
    return False


def _reject_html_gateway_response(body: str) -> None:
    if not _looks_like_html_document(body):
        return
    head = (body or "").lstrip()[:240].replace("\n", " ")
    raise RuntimeError(
        "LLM base URL returned HTML (a web page), not a chat-completions API response. "
        "Typical causes: wrong CLAUDE_BASE_URL / --base-url (often must end with /v1 for OpenAI-compatible APIs), "
        "hitting the site's homepage, login/captcha page, or WAF block. "
        "Fix the URL and key per your provider docs, then retry. "
        f"Response starts with: {head!r}"
    )


def _synthetic_completion_from_plain_text(text: str) -> dict:
    """Build minimal OpenAI-shaped dict when the gateway returns raw assistant text only."""
    return {
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": text},
            }
        ]
    }


def _dict_to_ns(obj: Any) -> Any:
    if isinstance(obj, dict):
        return SimpleNamespace(**{k: _dict_to_ns(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [_dict_to_ns(x) for x in obj]
    return obj


def _preview_for_error(obj: Any, limit: int = 900) -> str:
    try:
        s = json.dumps(obj, ensure_ascii=False) if isinstance(obj, (dict, list)) else str(obj)
    except (TypeError, ValueError):
        s = str(obj)
    s = s.replace("\n", " ").strip()
    return s if len(s) <= limit else s[: limit - 3] + "..."


def normalize_chat_completion_response(response: Any) -> Any:
    """
    Ensure a ChatCompletion-like object: .choices[i].message.content, optional .usage.
    """
    if response is None:
        raise TypeError("Chat completion response is None")

    if hasattr(response, "choices"):
        ch = getattr(response, "choices", None)
        if ch is not None:
            return response

    raw: Any = response
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")
    if isinstance(raw, str):
        raw = _unwrap_json_string_blob(raw)

    # Still a string: either non-JSON body or JSON that failed to parse — use as assistant text.
    if isinstance(raw, str):
        _reject_html_gateway_response(raw)
        raw = _synthetic_completion_from_plain_text(raw)

    if isinstance(raw, dict):
        _raise_if_api_error(raw)
        raw = _maybe_unwrap_envelope(raw)
        if not (isinstance(raw.get("choices"), list) and raw["choices"]):
            found = _deep_find_choices_payload(raw)
            if found is not None:
                raw = found
        if not (isinstance(raw.get("choices"), list) and raw["choices"]):
            raise TypeError(
                "Chat completion payload has no non-empty 'choices' list. "
                f"Top-level keys: {list(raw.keys())}. Preview: {_preview_for_error(raw)}"
            )
        return _dict_to_ns(raw)

    raise TypeError(
        f"Unexpected chat completion type {type(response)!r}; "
        f"preview: {_preview_for_error(raw)}"
    )


def _retry_after_seconds(exc: Exception) -> Optional[float]:
    resp = getattr(exc, "response", None)
    if resp is None:
        return None
    headers = getattr(resp, "headers", None)
    if headers is None:
        return None
    try:
        ra = headers.get("retry-after") or headers.get("Retry-After")
    except Exception:
        return None
    if ra is None:
        return None
    try:
        return float(ra)
    except (TypeError, ValueError):
        return None


def _coerce_model_id_str(model_kw: Any) -> str:
    if model_kw is None:
        return ""
    if isinstance(model_kw, str):
        return model_kw
    return str(model_kw)


def is_glm4_model_id(model: Optional[str]) -> bool:
    """
    True for Zhipu GLM-4 family (e.g. glm-4-flash). Excludes glm-5+ so DeepSeek / GLM-5 stay unchanged.
    """
    m = (model or "").lower()
    if not m or "glm-5" in m:
        return False
    return "glm-4" in m


# Appended to inner tier system prompt only when is_glm4_model_id(model).
GLM4_TOOL_LOOP_SYSTEM_ADDON = (
    "GLM-4 efficiency: In a single turn, avoid chaining many read_file calls (e.g. dozens of CSVs). "
    "Read 1–2 files to learn schema/delimiters, then use run_shell with Python/pandas to load and analyze the rest. "
    "Large batched read_file outputs inflate the next request and trigger provider rate limits."
)


def _is_429_rate_limit(exc: BaseException) -> bool:
    if RateLimitError is not None and isinstance(exc, RateLimitError):
        return True
    code = getattr(exc, "status_code", None)
    if code == 429:
        return True
    resp = getattr(exc, "response", None)
    if resp is not None and getattr(resp, "status_code", None) == 429:
        return True
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict) and str(err.get("code")) == "1302":
            return True
    s = str(exc)
    if "速率限制" in s or "1302" in s:
        return True
    low = s.lower()
    if "429" in s and ("rate" in low or "limit" in low or "throttl" in low):
        return True
    return False


def _is_retryable_server_error(exc: BaseException) -> bool:
    """
    Transient provider / gateway failures (5xx, overloaded upstream).
    SiliconFlow and similar sometimes return HTTP 500 with code 50507 in the message.
    """
    code = getattr(exc, "status_code", None)
    if code in (500, 502, 503, 504):
        return True
    resp = getattr(exc, "response", None)
    sc = getattr(resp, "status_code", None) if resp is not None else None
    if sc in (500, 502, 503, 504):
        return True
    s = str(exc)
    if "50507" in s:
        return True
    if "Error code: 500" in s or "status code 500" in s.lower():
        return True
    if "502" in s and ("bad gateway" in s.lower() or "Error code: 502" in s):
        return True
    if "503" in s and ("unavailable" in s.lower() or "Error code: 503" in s):
        return True
    if "504" in s and ("timeout" in s.lower() or "gateway" in s.lower() or "Error code: 504" in s):
        return True
    return False


def _should_retry_chat_completion(exc: BaseException) -> bool:
    return _is_429_rate_limit(exc) or _is_retryable_server_error(exc)


def chat_completions_create_with_429_backoff(client: Any, **kwargs: Any) -> Any:
    """
    Call client.chat.completions.create(**kwargs). On retryable failures, sleep with
    exponential backoff (and honor Retry-After when present for 429), then retry.

    Retries:
      - HTTP 429 / provider rate limits (as before)
      - HTTP 500 / 502 / 503 / 504 and similar (e.g. SiliconFlow 50507)

    Env (optional):
      LLM_429_MAX_RETRIES — default 8 (12 if model id is GLM-4 and this env is unset); also caps 5xx retries
      LLM_429_BACKOFF_BASE_SEC — default 2.0 (first wait ~= base * 2**(attempt-1))
      LLM_429_BACKOFF_MAX_SEC — cap per wait, default 120.0 (180.0 for GLM-4 if unset)

    GLM-4-only defaults apply when kwargs[\"model\"] matches is_glm4_model_id; other models unchanged.
    """
    model_str = _coerce_model_id_str(kwargs.get("model"))
    glm4 = is_glm4_model_id(model_str)
    default_retries = 12 if glm4 else 8
    default_max_delay = 180.0 if glm4 else 120.0
    max_retries = (
        max(1, int(os.environ["LLM_429_MAX_RETRIES"]))
        if "LLM_429_MAX_RETRIES" in os.environ
        else default_retries
    )
    base_delay = float(os.environ.get("LLM_429_BACKOFF_BASE_SEC", "2.0"))
    max_delay = (
        float(os.environ["LLM_429_BACKOFF_MAX_SEC"])
        if "LLM_429_BACKOFF_MAX_SEC" in os.environ
        else default_max_delay
    )
    base_delay = max(0.1, base_delay)
    max_delay = max(base_delay, max_delay)

    attempt = 0
    while True:
        try:
            return client.chat.completions.create(**kwargs)
        except BaseException as e:
            if not _should_retry_chat_completion(e):
                raise
            attempt += 1
            if attempt > max_retries:
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            ra = _retry_after_seconds(e)
            if ra is not None and ra > 0:
                delay = min(max_delay, max(delay, ra))
            if _is_429_rate_limit(e):
                tag = "Rate limited (429)"
            else:
                tag = "Server error (retryable 5xx / gateway)"
            print(
                f"  [LLM] {tag}, sleeping {delay:.1f}s "
                f"(retry {attempt}/{max_retries})...",
                flush=True,
            )
            time.sleep(delay)
