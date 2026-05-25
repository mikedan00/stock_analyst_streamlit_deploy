from __future__ import annotations

from src.agents.base import AgentSpec, StockAgent
from src.llm.router import LLMClient
from src.agents.prompts import (
    COMPANY_OVERVIEW_PROMPT,
    FINANCIAL_ANALYSIS_PROMPT,
    INDUSTRY_ANALYSIS_PROMPT,
    MOMENTUM_ANALYSIS_PROMPT,
    RISK_ANALYSIS_PROMPT,
    RECOMMENDATION_PROMPT,
)


AGENT_SPECS: dict[str, AgentSpec] = {
    "company_overview": AgentSpec(
        key="company_overview",
        display_name="기업 개요",
        system_prompt=COMPANY_OVERVIEW_PROMPT,
    ),
    "industry_analysis": AgentSpec(
        key="industry_analysis",
        display_name="산업 분석",
        system_prompt=INDUSTRY_ANALYSIS_PROMPT,
    ),
    "momentum_analysis": AgentSpec(
        key="momentum_analysis",
        display_name="모멘텀 분석",
        system_prompt=MOMENTUM_ANALYSIS_PROMPT,
    ),
    "financial_analysis": AgentSpec(
        key="financial_analysis",
        display_name="재무 분석",
        system_prompt=FINANCIAL_ANALYSIS_PROMPT,
    ),
    "risk_analysis": AgentSpec(
        key="risk_analysis",
        display_name="리스크 요인",
        system_prompt=RISK_ANALYSIS_PROMPT,
    ),
    "recommendation": AgentSpec(
        key="recommendation",
        display_name="종합 의견 & 추천픽",
        system_prompt=RECOMMENDATION_PROMPT,
        max_context_chars=18000,
    ),
}


def build_agents(llm: LLMClient) -> dict[str, StockAgent]:
    return {key: StockAgent(spec, llm) for key, spec in AGENT_SPECS.items()}
