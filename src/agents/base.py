from __future__ import annotations

from dataclasses import dataclass

from src.llm.router import LLMClient
from src.agents.prompts import with_grounding


@dataclass(frozen=True)
class AgentSpec:
    key: str
    display_name: str
    system_prompt: str
    max_context_chars: int = 6000


class StockAgent:
    def __init__(self, spec: AgentSpec, llm: LLMClient):
        self.spec = spec
        self.llm = llm

    def analyze(self, *, ticker: str, company_name: str, market: str, data_context: str = "", prior_context: str = "") -> str:
        prompt = self.build_prompt(
            ticker=ticker,
            company_name=company_name,
            market=market,
            data_context=data_context,
            prior_context=prior_context,
        )
        return self.llm.complete(system=with_grounding(self.spec.system_prompt), user=prompt)

    def build_prompt(self, *, ticker: str, company_name: str, market: str, data_context: str, prior_context: str) -> str:
        name_hint = f"회사명 힌트: {company_name}" if company_name else "회사명 힌트: 없음"
        clipped_data = data_context[: self.spec.max_context_chars] if data_context else "앱 수집 데이터 없음"
        clipped_prior = prior_context[: self.spec.max_context_chars] if prior_context else "이전 에이전트 결과 없음"

        return f"""
분석 대상:
- 티커: {ticker}
- {name_hint}
- 시장: {market}

[앱 수집 데이터 컨텍스트]
{clipped_data}

[이전 에이전트 결과 컨텍스트]
{clipped_prior}

요청:
- 당신의 전문 역할에 맞춰 시스템 프롬프트의 출력 형식으로 작성하세요.
- 데이터가 부족하면 부족하다고 표시하고, 검증이 필요한 수치는 임의로 확정하지 마세요.
- 한국어로 작성하세요.
""".strip()
