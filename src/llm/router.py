from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.config import LLMSettings, Provider, setting


class LLMClient(Protocol):
    def complete(self, *, system: str, user: str) -> str:
        ...


@dataclass
class AnthropicClient:
    settings: LLMSettings

    def complete(self, *, system: str, user: str) -> str:
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic 패키지가 설치되어 있지 않습니다. pip install anthropic") from exc

        if not self.settings.api_key:
            raise ValueError("ANTHROPIC_API_KEY가 비어 있습니다.")

        client = anthropic.Anthropic(api_key=self.settings.api_key)
        kwargs = {
            "model": self.settings.model,
            "max_tokens": self.settings.max_tokens,
            "temperature": self.settings.temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }

        # Anthropic 모델에서만 네이티브 웹 검색 도구를 옵션으로 사용합니다.
        # 사용 계정/모델/지역에 따라 도구 지원 여부가 다를 수 있으므로 실패 시 오류 메시지를 앱에 표시합니다.
        if self.settings.anthropic_web_search:
            kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]

        response = client.messages.create(**kwargs)
        text_parts: list[str] = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                text_parts.append(text)
        return "\n".join(text_parts).strip()


@dataclass
class OpenAICompatibleClient:
    settings: LLMSettings

    def complete(self, *, system: str, user: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai 패키지가 설치되어 있지 않습니다. pip install openai") from exc

        if not self.settings.api_key:
            raise ValueError("OPENAI_API_KEY 또는 호환 API Key가 비어 있습니다.")

        client = OpenAI(
            api_key=self.settings.api_key,
            base_url=self.settings.base_url or "https://api.openai.com/v1",
        )
        response = client.chat.completions.create(
            model=self.settings.model,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (response.choices[0].message.content or "").strip()


@dataclass
class HuggingFaceClient:
    settings: LLMSettings

    def _router_model_id(self) -> str:
        """Return the model id to send to the Hugging Face Inference Router.

        The current Hugging Face Inference Providers API is OpenAI-compatible and
        uses https://router.huggingface.co/v1.  Some models require an explicit
        provider suffix such as `:novita`, `:deepinfra`, `:together`, etc.
        You can set HF_PROVIDER_SUFFIX in Streamlit Secrets or in the sidebar.
        """
        model = (self.settings.model or "").strip()
        suffix = str(setting("HF_PROVIDER_SUFFIX", "")).strip().lstrip(":")
        if suffix and ":" not in model.split("/")[-1]:
            model = f"{model}:{suffix}"
        return model

    def complete(self, *, system: str, user: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai 패키지가 설치되어 있지 않습니다. pip install openai") from exc

        if not self.settings.api_key:
            raise ValueError("HF_TOKEN이 비어 있습니다.")

        base_url = str(setting("HF_BASE_URL", "https://router.huggingface.co/v1")).strip()
        model = self._router_model_id()
        client = OpenAI(api_key=self.settings.api_key, base_url=base_url)

        try:
            response = client.chat.completions.create(
                model=model,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as first_error:
            raise RuntimeError(
                "Hugging Face Router 호출에 실패했습니다. HF_TOKEN 권한, Gemma 라이선스 동의, "
                "Inference Providers 활성화 여부, 모델 ID 및 provider suffix를 확인하세요. "
                f"사용한 endpoint={base_url}, model={model}, 원본 오류: {first_error}"
            ) from first_error


def build_llm_client(settings: LLMSettings) -> LLMClient:
    if settings.provider == Provider.ANTHROPIC:
        return AnthropicClient(settings)
    if settings.provider == Provider.OPENAI_COMPATIBLE:
        return OpenAICompatibleClient(settings)
    if settings.provider == Provider.HUGGINGFACE:
        return HuggingFaceClient(settings)
    raise ValueError(f"지원하지 않는 provider입니다: {settings.provider}")
