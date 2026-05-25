from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from src.config import (
    Provider,
    LLMSettings,
    default_api_key_for,
    default_base_url,
    default_model_for,
    env_bool,
    env_default_provider,
    setting,
)
from src.llm.router import build_llm_client
from src.orchestrator import MultiAgentOrchestrator
from src.data.market_data import fetch_market_snapshot
from src.data.news import fetch_news_snapshot
from src.reports import write_markdown_report

load_dotenv()

st.set_page_config(
    page_title="주식 애널리스트 AI · Multi LLM",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Noto+Sans+KR:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background: #080c14; color: #d4d8e2; }
[data-testid="stSidebar"] { background: #0d1120; border-right: 1px solid #1e2d4a; }
.term-header { font-family:'JetBrains Mono', monospace; letter-spacing:3px; color:#4a6fa5; font-size:11px; text-transform:uppercase; }
.term-title { font-family:'JetBrains Mono', monospace; color:#f0b429; font-size:30px; font-weight:700; line-height:1.1; }
.term-subtitle { font-family:'JetBrains Mono', monospace; color:#7090b0; font-size:12px; margin-top:6px; }
.metric-card { background:#0d1120; border:1px solid #1e2d4a; border-radius:8px; padding:14px 16px; }
.agent-card { background:#0d1120; border:1px solid #1e2d4a; border-left:4px solid #1e3a5f; border-radius:8px; padding:18px 20px; margin:12px 0; }
.agent-card.done { border-left-color:#00d97e; }
.agent-card.running { border-left-color:#f0b429; }
.agent-title { font-family:'JetBrains Mono', monospace; color:#f0b429; font-weight:700; font-size:14px; letter-spacing:1px; margin-bottom:8px; }
.status-badge { font-family:'JetBrains Mono', monospace; border:1px solid #1e3a5f; padding:2px 8px; border-radius:4px; color:#7090b0; font-size:10px; }
.status-running { color:#f0b429; border-color:#f0b429; }
.status-done { color:#00d97e; border-color:#00d97e; }
.status-error { color:#ff647c; border-color:#ff647c; }
.stButton button { background:#f0b429 !important; color:#080c14 !important; font-weight:700 !important; border:0 !important; width:100%; }
hr { border-color:#1e2d4a; }
</style>
""",
    unsafe_allow_html=True,
)


def require_app_password() -> None:
    """Optional simple app gate for public Streamlit deployments.

    Set APP_PASSWORD in Streamlit Secrets to prevent anonymous users from
    consuming your LLM API credits. If APP_PASSWORD is empty, the app remains open.
    """
    app_password = str(setting("APP_PASSWORD", "")).strip()
    if not app_password:
        return

    if st.session_state.get("auth_ok") is True:
        return

    st.markdown("### 🔐 배포 앱 접근 비밀번호")
    entered = st.text_input("APP_PASSWORD", type="password", placeholder="Streamlit Secrets에 설정한 APP_PASSWORD")
    if st.button("입장"):
        if entered == app_password:
            st.session_state.auth_ok = True
            st.rerun()
        else:
            st.error("비밀번호가 맞지 않습니다.")
    st.stop()


require_app_password()


def provider_label(p: Provider) -> str:
    return {
        Provider.HUGGINGFACE: "Hugging Face · HF_TOKEN · google/gemma-4-26B-A4B-it",
        Provider.ANTHROPIC: "Anthropic API · Claude",
        Provider.OPENAI_COMPATIBLE: "OpenAI-compatible API · OpenAI/OpenRouter/DeepInfra/Local",
    }[p]


def render_price_chart(df: pd.DataFrame | None) -> None:
    if df is None or df.empty or "Close" not in df.columns:
        return
    date_col = "Date" if "Date" in df.columns else df.columns[0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[date_col], y=df["Close"], mode="lines", name="Close"))
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="#0d1120",
        plot_bgcolor="#0d1120",
        font=dict(color="#d4d8e2"),
        xaxis=dict(gridcolor="#1e2d4a"),
        yaxis=dict(gridcolor="#1e2d4a"),
    )
    st.plotly_chart(fig, use_container_width=True)


st.markdown(
    '<div class="term-header">MULTI LLM · MULTI AGENT EQUITY RESEARCH</div>'
    '<div class="term-title">📊 주식 애널리스트 AI</div>'
    '<div class="term-subtitle">Claude Code 스타일의 6개 서브에이전트 파이프라인을 VS Code + Streamlit 앱으로 구현</div>',
    unsafe_allow_html=True,
)
st.divider()

with st.sidebar:
    st.markdown('<div class="term-header">LLM ROUTER</div>', unsafe_allow_html=True)

    providers = [Provider.HUGGINGFACE, Provider.ANTHROPIC, Provider.OPENAI_COMPATIBLE]
    default_provider = env_default_provider()
    provider = st.selectbox(
        "LLM 엔진 선택",
        providers,
        index=providers.index(default_provider) if default_provider in providers else 0,
        format_func=provider_label,
    )

    secret_or_env_key = default_api_key_for(provider)
    if secret_or_env_key:
        st.success("Secrets/.env에서 API Key를 감지했습니다. 입력창을 비워도 이 Key를 사용합니다.")
    api_key_input = st.text_input(
        "API Key / Token 직접 입력",
        type="password",
        value="",
        placeholder="비워두면 Streamlit Secrets 또는 .env 값을 사용",
        help="HF는 HF_TOKEN, Anthropic은 ANTHROPIC_API_KEY, 호환 API는 OPENAI_API_KEY를 사용합니다. 배포 앱에서는 실제 Key를 화면에 노출하지 않습니다.",
    )
    api_key = api_key_input.strip() or secret_or_env_key

    model = st.text_input("모델 ID", value=default_model_for(provider))

    base_url = None
    if provider == Provider.OPENAI_COMPATIBLE:
        base_url = st.text_input("Base URL", value=default_base_url())

    anthropic_web_search = False
    if provider == Provider.ANTHROPIC:
        anthropic_web_search = st.checkbox(
            "Anthropic 네이티브 Web Search 사용",
            value=env_bool("ANTHROPIC_ENABLE_WEB_SEARCH", True),
            help="계정/모델에서 지원되지 않으면 오류가 발생할 수 있습니다.",
        )

    st.divider()
    st.markdown('<div class="term-header">ANALYSIS INPUT</div>', unsafe_allow_html=True)

    ticker = st.text_input("종목 티커", placeholder="005930 / AAPL / NVDA")
    company_name = st.text_input("회사명 힌트", placeholder="삼성전자 / Apple / NVIDIA")
    market = st.selectbox("시장", ["AUTO", "KRX", "US"], index=0)
    collect_data = st.checkbox("앱에서 yfinance + Google News RSS 보조 데이터 수집", value=env_bool("APP_ENABLE_DATA_COLLECTOR", True))
    max_workers = st.slider("Phase 1 병렬 에이전트 수", min_value=1, max_value=3, value=3)
    temperature = st.slider("LLM temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.05)
    max_tokens = st.slider("에이전트별 max_tokens", min_value=1000, max_value=8000, value=3500, step=500)

    run = st.button("▶ 분석 시작")

st.markdown(
    """
<div class="metric-card">
<b>Pipeline</b><br>
① 기업 개요 · 산업 분석 · 모멘텀 분석 <span class="status-badge">PARALLEL</span>
→ ② 재무 분석 <span class="status-badge">SEQ</span>
→ ③ 리스크 요인 <span class="status-badge">SEQ</span>
→ ④ 종합 의견 & 추천픽 <span class="status-badge">FINAL</span>
</div>
""",
    unsafe_allow_html=True,
)

if "last_report" not in st.session_state:
    st.session_state.last_report = ""
if "last_ticker" not in st.session_state:
    st.session_state.last_ticker = ""

if run:
    if not ticker.strip():
        st.error("종목 티커를 입력하세요.")
        st.stop()
    if not str(api_key).strip():
        st.error("선택한 LLM 엔진의 API Key / Token을 입력하거나 Streamlit Secrets에 설정하세요.")
        st.stop()

    settings = LLMSettings(
        provider=provider,
        api_key=str(api_key).strip(),
        model=model.strip(),
        base_url=base_url.strip() if base_url else None,
        temperature=temperature,
        max_tokens=max_tokens,
        anthropic_web_search=anthropic_web_search,
    )

    data_contexts: list[str] = []
    price_frame = None

    with st.status("앱 보조 데이터 수집 중...", expanded=True) as data_status:
        if collect_data:
            snap = fetch_market_snapshot(ticker.strip(), company_name.strip(), market)
            if snap.ok:
                st.write("가격/기술적 지표 수집 완료")
                data_contexts.append(snap.summary_markdown)
                price_frame = snap.price_frame
            else:
                st.warning(f"가격 데이터 수집 실패: {snap.error}")

            news = fetch_news_snapshot(ticker.strip(), company_name.strip())
            if news.ok:
                st.write("뉴스 RSS 수집 완료")
                data_contexts.append(news.summary_markdown)
            else:
                st.warning(f"뉴스 수집 실패: {news.error}")
        else:
            st.write("앱 보조 데이터 수집 비활성화")
        data_status.update(label="데이터 준비 완료", state="complete")

    if price_frame is not None:
        render_price_chart(price_frame)

    llm = build_llm_client(settings)
    orchestrator = MultiAgentOrchestrator(llm=llm, max_workers=max_workers)

    status_box = st.empty()
    results_box = st.container()
    statuses: dict[str, str] = {}
    result_placeholders: dict[str, object] = {}

    agent_display_order = [
        "기업 개요",
        "산업 분석",
        "모멘텀 분석",
        "재무 분석",
        "리스크 요인",
        "종합 의견 & 추천픽",
    ]

    with results_box:
        for name in agent_display_order:
            result_placeholders[name] = st.empty()

    def redraw_status() -> None:
        with status_box:
            st.markdown("### 진행 상태")
            cols = st.columns(3)
            for i, name in enumerate(agent_display_order):
                status = statuses.get(name, "waiting")
                cls = {
                    "waiting": "",
                    "running": "status-running",
                    "done": "status-done",
                    "error": "status-error",
                }.get(status, "")
                with cols[i % 3]:
                    st.markdown(f'<span class="status-badge {cls}">{name}: {status.upper()}</span>', unsafe_allow_html=True)

    def on_status(name: str, status: str) -> None:
        statuses[name] = status
        redraw_status()

    def on_result(key: str, name: str, result: str) -> None:
        placeholder = result_placeholders.get(name)
        if placeholder:
            with placeholder.container():
                st.markdown(
                    f'<div class="agent-card done"><div class="agent-title">{name}</div></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(result)

    redraw_status()

    started = time.time()
    try:
        state = orchestrator.run(
            ticker=ticker.strip().upper(),
            company_name=company_name.strip(),
            market=market,
            data_context="\n\n".join(data_contexts),
            on_status=on_status,
            on_result=on_result,
        )
        report = orchestrator.build_full_report(state)
        st.session_state.last_report = report
        st.session_state.last_ticker = ticker.strip().upper()

        st.success(f"분석 완료 · 소요 시간 {time.time() - started:.1f}초")
        deploy_mode = str(setting("STREAMLIT_DEPLOY_MODE", "local")).strip().lower()
        if deploy_mode != "cloud":
            try:
                report_path = write_markdown_report(report, ticker.strip().upper())
                st.info(f"로컬 리포트 저장: {report_path}")
            except Exception as save_exc:
                st.warning(f"리포트 파일 저장은 건너뜁니다: {save_exc}")

        st.download_button(
            "⬇ Markdown 리포트 다운로드",
            data=report.encode("utf-8"),
            file_name=f"{ticker.strip().upper()}_stock_report.md",
            mime="text/markdown",
        )
    except Exception as exc:
        st.error(f"실행 실패: {exc}")

elif st.session_state.last_report:
    st.download_button(
        "⬇ 마지막 Markdown 리포트 다운로드",
        data=st.session_state.last_report.encode("utf-8"),
        file_name=f"{st.session_state.last_ticker or 'stock'}_stock_report.md",
        mime="text/markdown",
    )

st.divider()
st.caption("본 앱은 투자 리서치 보조 도구입니다. 매수·매도 판단 전 공시, 재무제표, 증권사 리포트, 실시간 시세를 반드시 별도로 확인하세요.")
