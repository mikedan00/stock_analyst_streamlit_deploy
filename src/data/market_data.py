from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import math

import pandas as pd


@dataclass
class MarketSnapshot:
    ticker: str
    market: str
    ok: bool
    summary_markdown: str
    price_frame: pd.DataFrame | None = None
    error: str | None = None


def _normalize_ticker(ticker: str, market: str) -> str:
    t = ticker.strip().upper()
    if market == "KRX" and t.isdigit() and len(t) == 6:
        return f"{t}.KS"
    return t


def _pct(a: float, b: float) -> float | None:
    try:
        if b == 0 or math.isnan(a) or math.isnan(b):
            return None
        return (a / b - 1.0) * 100.0
    except Exception:
        return None


def _fmt_pct(x: float | None) -> str:
    if x is None:
        return "N/A"
    return f"{x:+.2f}%"


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series) -> tuple[pd.Series, pd.Series]:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal


def fetch_market_snapshot(ticker: str, company_name: str = "", market: str = "AUTO") -> MarketSnapshot:
    """Fetches price history through yfinance and computes simple technical context."""
    try:
        import yfinance as yf
    except ImportError as exc:
        return MarketSnapshot(ticker, market, False, "", error="yfinance가 설치되어 있지 않습니다.")

    yf_ticker = _normalize_ticker(ticker, "KRX" if market == "KRX" else market)
    try:
        data = yf.download(yf_ticker, period="1y", interval="1d", auto_adjust=True, progress=False, threads=False)
        if data is None or data.empty:
            # 자동 감지: 한국 6자리라면 .KQ도 시도
            if ticker.isdigit() and len(ticker) == 6:
                for suffix in [".KS", ".KQ"]:
                    yf_ticker_try = f"{ticker}{suffix}"
                    data = yf.download(yf_ticker_try, period="1y", interval="1d", auto_adjust=True, progress=False, threads=False)
                    if data is not None and not data.empty:
                        yf_ticker = yf_ticker_try
                        break
        if data is None or data.empty:
            return MarketSnapshot(ticker, market, False, "", error=f"가격 데이터를 가져오지 못했습니다: {ticker}")

        # yfinance may return multi-index columns
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [c[0] for c in data.columns]

        close = data["Close"].dropna()
        if close.empty:
            return MarketSnapshot(ticker, market, False, "", error="Close 가격이 비어 있습니다.")

        current = float(close.iloc[-1])
        last_date = close.index[-1].strftime("%Y-%m-%d")
        returns = {}
        windows = {"1M": 21, "3M": 63, "6M": 126, "12M": 252}
        for label, n in windows.items():
            if len(close) > n:
                returns[label] = _pct(current, float(close.iloc[-n-1]))
            else:
                returns[label] = None

        ma20 = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else None
        ma60 = float(close.rolling(60).mean().iloc[-1]) if len(close) >= 60 else None
        ma120 = float(close.rolling(120).mean().iloc[-1]) if len(close) >= 120 else None
        rsi14 = float(_rsi(close).iloc[-1]) if len(close) >= 20 and pd.notna(_rsi(close).iloc[-1]) else None
        macd, signal = _macd(close)
        macd_text = "N/A"
        if len(macd) > 0 and pd.notna(macd.iloc[-1]) and pd.notna(signal.iloc[-1]):
            macd_text = "MACD > Signal" if macd.iloc[-1] > signal.iloc[-1] else "MACD < Signal"

        high_52w = float(close.max())
        low_52w = float(close.min())

        info: dict[str, Any] = {}
        try:
            info = yf.Ticker(yf_ticker).info or {}
        except Exception:
            info = {}

        currency = info.get("currency", "")
        market_cap = info.get("marketCap", None)
        trailing_pe = info.get("trailingPE", None)
        forward_pe = info.get("forwardPE", None)
        pb = info.get("priceToBook", None)
        roe = info.get("returnOnEquity", None)

        summary = f"""
## 앱 수집 시장 데이터 컨텍스트

| 항목 | 값 |
|---|---:|
| 입력 티커 | `{ticker}` |
| yfinance 티커 | `{yf_ticker}` |
| 회사명 힌트 | `{company_name or 'N/A'}` |
| 마지막 거래일 | {last_date} |
| 현재가/종가 | {current:,.2f} {currency} |
| 52주 고가 | {high_52w:,.2f} |
| 52주 저가 | {low_52w:,.2f} |
| 시가총액 | {market_cap if market_cap else 'N/A'} |
| Trailing PER | {trailing_pe if trailing_pe else 'N/A'} |
| Forward PER | {forward_pe if forward_pe else 'N/A'} |
| PBR | {pb if pb else 'N/A'} |
| ROE | {roe if roe else 'N/A'} |

### 기간별 수익률
| 기간 | 수익률 |
|---|---:|
| 1개월 | {_fmt_pct(returns['1M'])} |
| 3개월 | {_fmt_pct(returns['3M'])} |
| 6개월 | {_fmt_pct(returns['6M'])} |
| 12개월 | {_fmt_pct(returns['12M'])} |

### 기술적 지표
| 지표 | 값 |
|---|---:|
| 20일 이동평균 | {ma20 and f'{ma20:,.2f}' or 'N/A'} |
| 60일 이동평균 | {ma60 and f'{ma60:,.2f}' or 'N/A'} |
| 120일 이동평균 | {ma120 and f'{ma120:,.2f}' or 'N/A'} |
| RSI(14) | {rsi14 and f'{rsi14:.2f}' or 'N/A'} |
| MACD | {macd_text} |

주의: 위 데이터는 앱이 보조적으로 수집한 공개 시장 데이터이며, 분석 시점/데이터 소스 차이로 실제 증권사 데이터와 다를 수 있습니다.
""".strip()

        frame = data.tail(260).reset_index()
        return MarketSnapshot(ticker, market, True, summary, frame)
    except Exception as exc:
        return MarketSnapshot(ticker, market, False, "", error=str(exc))
