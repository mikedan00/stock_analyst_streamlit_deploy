from __future__ import annotations

import argparse

from src.config import Provider, LLMSettings, default_api_key_for, default_base_url, default_model_for, env_bool
from src.llm.router import build_llm_client
from src.orchestrator import MultiAgentOrchestrator
from src.data.market_data import fetch_market_snapshot
from src.data.news import fetch_news_snapshot
from src.reports import write_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(description="멀티 LLM 주식 애널리스트 AI CLI")
    parser.add_argument("--ticker", required=True, help="예: 005930, AAPL, NVDA")
    parser.add_argument("--company", default="", help="회사명 힌트")
    parser.add_argument("--market", default="AUTO", choices=["AUTO", "KRX", "US"], help="시장")
    parser.add_argument("--provider", default="huggingface", choices=[p.value for p in Provider])
    parser.add_argument("--model", default="", help="모델 ID")
    parser.add_argument("--base-url", default="", help="OpenAI-compatible base URL")
    parser.add_argument("--no-data", action="store_true", help="앱의 yfinance/RSS 데이터 수집 비활성화")
    args = parser.parse_args()

    provider = Provider(args.provider)
    settings = LLMSettings(
        provider=provider,
        api_key=default_api_key_for(provider),
        model=args.model or default_model_for(provider),
        base_url=args.base_url or (default_base_url() if provider == Provider.OPENAI_COMPATIBLE else None),
        anthropic_web_search=env_bool("ANTHROPIC_ENABLE_WEB_SEARCH", True) if provider == Provider.ANTHROPIC else False,
    )
    llm = build_llm_client(settings)

    contexts: list[str] = []
    if not args.no_data:
        snap = fetch_market_snapshot(args.ticker, args.company, args.market)
        if snap.ok:
            contexts.append(snap.summary_markdown)
        news = fetch_news_snapshot(args.ticker, args.company)
        if news.ok:
            contexts.append(news.summary_markdown)

    orch = MultiAgentOrchestrator(llm=llm)

    def on_status(name: str, status: str) -> None:
        print(f"[{status.upper()}] {name}")

    def on_result(key: str, name: str, result: str) -> None:
        print(f"\n\n===== {name} 완료 =====\n")
        print(result[:1200] + ("..." if len(result) > 1200 else ""))

    state = orch.run(
        ticker=args.ticker,
        company_name=args.company,
        market=args.market,
        data_context="\n\n".join(contexts),
        on_status=on_status,
        on_result=on_result,
    )
    report = orch.build_full_report(state)
    path = write_markdown_report(report, args.ticker)
    print(f"\n리포트 저장 완료: {path}")


if __name__ == "__main__":
    main()
