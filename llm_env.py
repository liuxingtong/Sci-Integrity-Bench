"""
Resolve OpenAI-compatible (api_key, base_url, model) from .env.

Supports split credentials:
  DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
  GLM_API_KEY, GLM_BASE_URL, GLM_MODEL
  CLAUDE_API_KEY, CLAUDE_BASE_URL, CLAUDE_MODEL (OpenAI-compatible gateway)
  SILICON_API_KEY, SILICON_BASE_URL, SILICON_MODEL (硅基流动等；base 无 /v1 时会自动补上)
  OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL (OpenRouter；base 无 /v1 时会自动补上)

Legacy fallbacks:
  LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class ResolvedLlm:
    api_key: str
    base_url: str
    model: str


def load_project_dotenv(env_path: Optional[Path] = None) -> None:
    load_dotenv(env_path or (PROJECT_ROOT / ".env"))


def _norm_base(url: str) -> str:
    return (url or "").strip().rstrip("/")


def _silicon_openai_base(url: Optional[str]) -> str:
    """SiliconFlow OpenAI-compatible root must end with /v1 for the Python SDK."""
    u = _norm_base(url or "") if url else ""
    if not u:
        return "https://api.siliconflow.cn/v1"
    if u.endswith("/v1"):
        return u
    return f"{u}/v1"


def _openrouter_openai_base(url: Optional[str]) -> str:
    """OpenRouter Chat Completions root must end with /v1 for the OpenAI Python SDK."""
    u = _norm_base(url or "") if url else ""
    if not u:
        return "https://openrouter.ai/api/v1"
    if u.endswith("/v1"):
        return u
    return f"{u}/v1"


def add_llm_cli_args(parser) -> None:
    """Register standard LLM flags on an ArgumentParser."""
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=(
            "Model id (e.g. deepseek-chat, glm-4-flash). "
            "With .env DEEPSEEK_* / GLM_* / CLAUDE_* / SILICON_* / OPENROUTER_*: provider is inferred from the name unless --provider is set."
        ),
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        choices=["deepseek", "glm", "claude", "silicon", "openrouter"],
        help="Use DEEPSEEK_* / GLM_* / CLAUDE_* / SILICON_* / OPENROUTER_* block from .env (default model from that block if --model omitted).",
    )
    parser.add_argument("--api-key", type=str, default=None, dest="api_key", help="Override API key.")
    parser.add_argument("--base-url", type=str, default=None, dest="base_url", help="Override base URL.")


def resolve_llm_config(
    *,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    env_path: Optional[Path] = None,
) -> ResolvedLlm:
    load_project_dotenv(env_path)

    key_o = (api_key or "").strip() or None
    url_o = _norm_base(base_url) if base_url else None

    if key_o:
        bu = url_o or _norm_base(os.getenv("LLM_BASE_URL")) or "https://api.deepseek.com"
        mid = (model or "").strip() or os.getenv("DEEPSEEK_MODEL") or os.getenv("GLM_MODEL") or os.getenv("LLM_MODEL")
        if not mid:
            mid = "deepseek-chat"
        return ResolvedLlm(api_key=key_o, base_url=bu, model=mid)

    prov = (provider or "").strip().lower() or None
    mid_in = (model or "").strip() or None

    if not prov and mid_in:
        ml = mid_in.lower()
        if "glm" in ml or "chatglm" in ml or "cogview" in ml:
            prov = "glm"
        elif "deepseek" in ml:
            prov = "deepseek"
        elif os.getenv("OPENROUTER_API_KEY") and mid_in.startswith(
            ("anthropic/", "openai/", "google/")
        ):
            prov = "openrouter"
        elif "claude" in ml:
            prov = "claude"
        elif "minimax" in ml or ml.startswith("minimaxai/"):
            prov = "silicon"

    if prov == "deepseek":
        key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")
        bu = url_o or _norm_base(os.getenv("DEEPSEEK_BASE_URL")) or "https://api.deepseek.com"
        mid = mid_in or os.getenv("DEEPSEEK_MODEL") or os.getenv("LLM_MODEL") or "deepseek-chat"
    elif prov == "glm":
        key = os.getenv("GLM_API_KEY") or os.getenv("LLM_API_KEY")
        bu = url_o or _norm_base(os.getenv("GLM_BASE_URL")) or "https://open.bigmodel.cn/api/paas/v4"
        mid = mid_in or os.getenv("GLM_MODEL") or os.getenv("LLM_MODEL") or "glm-4-flash"
    elif prov == "claude":
        key = os.getenv("CLAUDE_API_KEY") or os.getenv("LLM_API_KEY")
        bu = url_o or _norm_base(os.getenv("CLAUDE_BASE_URL")) or _norm_base(os.getenv("LLM_BASE_URL")) or ""
        mid = mid_in or os.getenv("CLAUDE_MODEL") or os.getenv("LLM_MODEL") or "claude-sonnet-4-20250514"
        if not bu:
            raise RuntimeError(
                "Provider claude requires CLAUDE_BASE_URL (OpenAI-compatible root, often .../v1) in .env or --base-url."
            )
    elif prov == "silicon":
        key = os.getenv("SILICON_API_KEY") or os.getenv("LLM_API_KEY")
        bu = _silicon_openai_base(url_o or os.getenv("SILICON_BASE_URL"))
        mid = (
            mid_in
            or os.getenv("SILICON_MODEL")
            or os.getenv("LLM_MODEL")
            or "MiniMaxAI/MiniMax-M2.5"
        )
    elif prov == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY")
        bu = _openrouter_openai_base(url_o or os.getenv("OPENROUTER_BASE_URL"))
        mid = (
            mid_in
            or os.getenv("OPENROUTER_MODEL")
            or os.getenv("LLM_MODEL")
            or "anthropic/claude-sonnet-4.6"
        )
    else:
        key = os.getenv("LLM_API_KEY")
        bu = url_o or _norm_base(os.getenv("LLM_BASE_URL")) or _norm_base(os.getenv("DEEPSEEK_BASE_URL")) or "https://api.deepseek.com"
        mid = mid_in or os.getenv("LLM_MODEL") or os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"
        if not key:
            key = os.getenv("DEEPSEEK_API_KEY")
        if not key:
            key = os.getenv("GLM_API_KEY")
            if key:
                bu = url_o or _norm_base(os.getenv("GLM_BASE_URL")) or "https://open.bigmodel.cn/api/paas/v4"
                mid = mid_in or os.getenv("GLM_MODEL") or "glm-4-flash"
        if not key:
            key = os.getenv("CLAUDE_API_KEY")
            if key:
                bu = url_o or _norm_base(os.getenv("CLAUDE_BASE_URL")) or _norm_base(os.getenv("LLM_BASE_URL"))
                mid = mid_in or os.getenv("CLAUDE_MODEL") or os.getenv("LLM_MODEL") or "claude-sonnet-4-20250514"
                if not bu:
                    raise RuntimeError(
                        "CLAUDE_API_KEY set but CLAUDE_BASE_URL is missing. "
                        "Set CLAUDE_BASE_URL to your OpenAI-compatible base URL (often ending in /v1)."
                    )
        if not key:
            key = os.getenv("SILICON_API_KEY")
            if key:
                bu = _silicon_openai_base(url_o or os.getenv("SILICON_BASE_URL"))
                mid = mid_in or os.getenv("SILICON_MODEL") or os.getenv("LLM_MODEL") or "MiniMaxAI/MiniMax-M2.5"
        if not key:
            key = os.getenv("OPENROUTER_API_KEY")
            if key:
                bu = _openrouter_openai_base(url_o or os.getenv("OPENROUTER_BASE_URL"))
                mid = (
                    mid_in
                    or os.getenv("OPENROUTER_MODEL")
                    or os.getenv("LLM_MODEL")
                    or "anthropic/claude-sonnet-4.6"
                )

    if not key:
        raise RuntimeError(
            "No API key resolved. In .env set DEEPSEEK_API_KEY, GLM_API_KEY, CLAUDE_API_KEY, SILICON_API_KEY, "
            "and/or OPENROUTER_API_KEY "
            "(or legacy LLM_API_KEY), or pass --api-key. "
            "Select credentials with --provider deepseek|glm|claude|silicon|openrouter or --model containing "
            "'deepseek', 'glm', 'claude', 'minimax', or (with OPENROUTER_API_KEY) ids like anthropic/..., openai/..., google/...."
        )

    return ResolvedLlm(api_key=key, base_url=bu, model=mid)


def resolve_llm_from_args(args, env_path: Optional[Path] = None) -> ResolvedLlm:
    return resolve_llm_config(
        model=getattr(args, "model", None),
        provider=getattr(args, "provider", None),
        api_key=getattr(args, "api_key", None),
        base_url=getattr(args, "base_url", None),
        env_path=env_path,
    )
