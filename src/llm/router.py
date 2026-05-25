from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.config import LLMSettings, Provider


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

    def complete(self, *, system: str, user: str) -> str:
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise RuntimeError("huggingface_hub 패키지가 설치되어 있지 않습니다. pip install huggingface-hub") from exc

        if not self.settings.api_key:
            raise ValueError("HF_TOKEN이 비어 있습니다.")

        client = InferenceClient(token=self.settings.api_key)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        # Hugging Face InferenceClient의 chat.completions 인터페이스를 우선 사용합니다.
        # Gemma 계열 모델이 계정/Provider에서 활성화되어 있어야 합니다.
        try:
            response = client.chat.completions.create(
                model=self.settings.model,
                messages=messages,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as first_error:
            # 일부 Provider는 text_generation만 열려 있을 수 있어, 명확한 안내가 가능한 오류로 변환합니다.
            raise RuntimeError(
                "Hugging Face 호출에 실패했습니다. HF_TOKEN, 모델 라이선스 동의, "
                "Inference Provider 활성화 여부, 모델 ID를 확인하세요. "
                f"원본 오류: {first_error}"
            ) from first_error


def build_llm_client(settings: LLMSettings) -> LLMClient:
    if settings.provider == Provider.ANTHROPIC:
        return AnthropicClient(settings)
    if settings.provider == Provider.OPENAI_COMPATIBLE:
        return OpenAICompatibleClient(settings)
    if settings.provider == Provider.HUGGINGFACE:
        return HuggingFaceClient(settings)
    raise ValueError(f"지원하지 않는 provider입니다: {settings.provider}")
