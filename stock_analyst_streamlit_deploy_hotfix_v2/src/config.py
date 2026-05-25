from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class Provider(str, Enum):
    HUGGINGFACE = "huggingface"
    ANTHROPIC = "anthropic"
    OPENAI_COMPATIBLE = "openai_compatible"


@dataclass(frozen=True)
class LLMSettings:
    provider: Provider
    api_key: str
    model: str
    base_url: str | None = None
    temperature: float = 0.2
    max_tokens: int = 3500
    anthropic_web_search: bool = False


def _streamlit_secret(name: str, default: Any = None) -> Any:
    """Read Streamlit Cloud secrets without breaking local CLI usage."""
    try:
        import streamlit as st  # type: ignore

        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return default


def setting(name: str, default: Any = "") -> Any:
    """Resolution order: environment variable -> Streamlit secret -> default."""
    value = os.getenv(name)
    if value not in (None, ""):
        return value
    secret_value = _streamlit_secret(name, None)
    if secret_value not in (None, ""):
        return secret_value
    return default


def env_default_provider() -> Provider:
    raw = str(setting("DEFAULT_PROVIDER", "huggingface")).strip().lower()
    try:
        return Provider(raw)
    except ValueError:
        return Provider.HUGGINGFACE


def default_model_for(provider: Provider) -> str:
    if provider == Provider.HUGGINGFACE:
        return str(setting("HF_MODEL", "google/gemma-4-26B-A4B-it"))
    if provider == Provider.ANTHROPIC:
        return str(setting("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"))
    return str(setting("OPENAI_MODEL", "gpt-4o-mini"))


def default_api_key_for(provider: Provider) -> str:
    if provider == Provider.HUGGINGFACE:
        return str(setting("HF_TOKEN", ""))
    if provider == Provider.ANTHROPIC:
        return str(setting("ANTHROPIC_API_KEY", ""))
    return str(setting("OPENAI_API_KEY", ""))


def default_base_url() -> str:
    return str(setting("OPENAI_BASE_URL", "https://api.openai.com/v1"))


def env_bool(name: str, default: bool = False) -> bool:
    raw = setting(name, default)
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}
