from __future__ import annotations

import concurrent.futures
import threading
from dataclasses import dataclass, field
from typing import Callable

from src.llm.router import LLMClient
from src.agents.stock_agents import build_agents, AGENT_SPECS


StatusCallback = Callable[[str, str], None]
ResultCallback = Callable[[str, str, str], None]


@dataclass
class AnalysisState:
    ticker: str
    company_name: str
    market: str
    data_context: str = ""
    results: dict[str, str] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def set_result(self, key: str, value: str) -> None:
        with self._lock:
            self.results[key] = value

    def set_error(self, key: str, value: str) -> None:
        with self._lock:
            self.errors[key] = value
            self.results[key] = f"⚠️ {value}"

    def get_result(self, key: str) -> str:
        with self._lock:
            return self.results.get(key, "")

    def has_error(self, key: str) -> bool:
        with self._lock:
            return key in self.errors

    def merged_context(self, keys: list[str] | None = None) -> str:
        with self._lock:
            selected = keys or list(self.results.keys())
            chunks = []
            for key in selected:
                if key in self.results:
                    title = AGENT_SPECS[key].display_name
                    chunks.append(f"\n\n# [{title} 결과]\n{self.results[key]}")
            return "\n".join(chunks).strip()


class MultiAgentOrchestrator:
    """
    Claude Code 스타일의 서브에이전트 구조를 일반 Python 프로그램으로 구현한 오케스트레이터.

    Streamlit Cloud 안정성을 위해 worker thread 안에서는 Streamlit UI를 직접 호출하지 않습니다.
    Phase 1 병렬 실행은 유지하되, callback은 main thread에서만 호출됩니다.
    """

    phase1 = ["company_overview", "industry_analysis", "momentum_analysis"]
    phase2 = ["financial_analysis"]
    phase3 = ["risk_analysis"]
    phase4 = ["recommendation"]
    final_order = [
        "company_overview",
        "financial_analysis",
        "industry_analysis",
        "momentum_analysis",
        "risk_analysis",
        "recommendation",
    ]

    def __init__(self, llm: LLMClient, max_workers: int = 3):
        self.llm = llm
        self.max_workers = max(1, min(max_workers, 3))
        self.agents = build_agents(llm)

    def _run_one(self, key: str, state: AnalysisState, prior_context: str = "") -> str:
        display = AGENT_SPECS[key].display_name
        try:
            result = self.agents[key].analyze(
                ticker=state.ticker,
                company_name=state.company_name,
                market=state.market,
                data_context=state.data_context,
                prior_context=prior_context,
            )
            state.set_result(key, result)
            return result
        except Exception as exc:
            msg = f"{display} 실행 중 오류: {exc}"
            state.set_error(key, msg)
            return state.get_result(key)

    def _emit_result(
        self,
        key: str,
        state: AnalysisState,
        on_status: StatusCallback | None,
        on_result: ResultCallback | None,
    ) -> None:
        display = AGENT_SPECS[key].display_name
        if on_result:
            on_result(key, display, state.get_result(key))
        if on_status:
            on_status(display, "error" if state.has_error(key) else "done")

    def run(
        self,
        *,
        ticker: str,
        company_name: str = "",
        market: str = "AUTO",
        data_context: str = "",
        on_status: StatusCallback | None = None,
        on_result: ResultCallback | None = None,
    ) -> AnalysisState:
        state = AnalysisState(
            ticker=ticker,
            company_name=company_name,
            market=market,
            data_context=data_context,
        )

        # Phase 1: independent agents in parallel. Status/result callbacks are emitted on the main thread.
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures: dict[concurrent.futures.Future[str], str] = {}
            for key in self.phase1:
                display = AGENT_SPECS[key].display_name
                if on_status:
                    on_status(display, "running")
                futures[pool.submit(self._run_one, key, state, "")] = key

            for future in concurrent.futures.as_completed(futures):
                key = futures[future]
                # Exception should already be handled inside _run_one, but keep this guard for safety.
                try:
                    future.result()
                except Exception as exc:
                    state.set_error(key, f"{AGENT_SPECS[key].display_name} 실행 중 오류: {exc}")
                self._emit_result(key, state, on_status, on_result)

        # Phase 2: financial analysis uses phase 1 context
        for key in self.phase2:
            display = AGENT_SPECS[key].display_name
            if on_status:
                on_status(display, "running")
            self._run_one(key, state, prior_context=state.merged_context(self.phase1))
            self._emit_result(key, state, on_status, on_result)

        # Phase 3: risk analysis uses all prior context
        for key in self.phase3:
            display = AGENT_SPECS[key].display_name
            if on_status:
                on_status(display, "running")
            self._run_one(key, state, prior_context=state.merged_context(self.phase1 + self.phase2))
            self._emit_result(key, state, on_status, on_result)

        # Phase 4: recommendation synthesizes all context
        for key in self.phase4:
            display = AGENT_SPECS[key].display_name
            if on_status:
                on_status(display, "running")
            self._run_one(key, state, prior_context=state.merged_context(self.phase1 + self.phase2 + self.phase3))
            self._emit_result(key, state, on_status, on_result)

        return state

    def build_full_report(self, state: AnalysisState) -> str:
        header = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 {state.company_name or state.ticker} ({state.ticker}) 투자 리서치 리포트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
시장: {state.market}
주의: 본 리포트는 AI 기반 리서치 보조 자료이며 투자 판단의 최종 책임은 사용자에게 있습니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()

        sections = [header]
        for key in self.final_order:
            if key in state.results:
                sections.append(state.results[key])
        if state.errors:
            sections.append("\n## 실행 오류 로그\n" + "\n".join(f"- {k}: {v}" for k, v in state.errors.items()))
        return "\n\n".join(sections)
