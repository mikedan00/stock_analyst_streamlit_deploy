from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class StockAlias:
    ticker: str
    company_name: str
    market: str
    exchange: str = ""
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class TickerResolution:
    original_input: str
    ticker: str
    company_name: str
    market: str
    exchange: str
    resolved: bool
    method: str
    confidence: float
    note: str = ""

    @property
    def display_name(self) -> str:
        if self.company_name:
            return f"{self.company_name} ({self.ticker})"
        return self.ticker

    def to_markdown(self) -> str:
        status = "성공" if self.resolved else "미확정"
        return f"""
| 항목 | 값 |
|---|---|
| 입력값 | `{self.original_input}` |
| 인식 상태 | {status} |
| 분석 티커 | `{self.ticker}` |
| 회사명 | {self.company_name or 'N/A'} |
| 시장 | {self.market} |
| 거래소 | {self.exchange or 'N/A'} |
| 인식 방식 | {self.method} |
| 신뢰도 | {self.confidence:.2f} |
| 메모 | {self.note or 'N/A'} |
""".strip()


# 자주 입력하는 한국 대형주/ETF/미국 빅테크 중심의 내장 별칭 사전입니다.
# Streamlit Cloud에서 별도 API 없이 동작하도록 정적 사전을 우선 사용합니다.
STOCK_ALIASES: tuple[StockAlias, ...] = (
    # KRX mega/large caps
    StockAlias("005930", "삼성전자", "KRX", "KOSPI", ("삼성", "samsung", "samsung electronics", "samsung elec", "samsung전자")),
    StockAlias("000660", "SK하이닉스", "KRX", "KOSPI", ("하이닉스", "sk hynix", "hynix", "에스케이하이닉스")),
    StockAlias("373220", "LG에너지솔루션", "KRX", "KOSPI", ("lg에너지솔루션", "엘지에너지솔루션", "lg energy solution", "lges", "엘지엔솔")),
    StockAlias("207940", "삼성바이오로직스", "KRX", "KOSPI", ("삼성바이오", "samsung biologics", "samsung bio")),
    StockAlias("005380", "현대차", "KRX", "KOSPI", ("현대자동차", "hyundai motor", "hyundai motors", "hyundai")),
    StockAlias("000270", "기아", "KRX", "KOSPI", ("기아차", "kia", "kia motors", "kia corp")),
    StockAlias("068270", "셀트리온", "KRX", "KOSPI", ("celltrion",)),
    StockAlias("005490", "POSCO홀딩스", "KRX", "KOSPI", ("포스코", "posco", "posco holdings")),
    StockAlias("035420", "NAVER", "KRX", "KOSPI", ("네이버", "naver", "naver corp")),
    StockAlias("035720", "카카오", "KRX", "KOSPI", ("kakao", "카카오톡")),
    StockAlias("051910", "LG화학", "KRX", "KOSPI", ("엘지화학", "lg chem", "lg화학")),
    StockAlias("006400", "삼성SDI", "KRX", "KOSPI", ("삼성sdi", "samsung sdi")),
    StockAlias("028260", "삼성물산", "KRX", "KOSPI", ("samsung c&t", "samsung cnt")),
    StockAlias("012330", "현대모비스", "KRX", "KOSPI", ("hyundai mobis", "모비스")),
    StockAlias("055550", "신한지주", "KRX", "KOSPI", ("신한금융지주", "shinhan", "shinhan financial")),
    StockAlias("105560", "KB금융", "KRX", "KOSPI", ("kb금융지주", "kb financial", "국민은행")),
    StockAlias("086790", "하나금융지주", "KRX", "KOSPI", ("하나금융", "hana financial")),
    StockAlias("316140", "우리금융지주", "KRX", "KOSPI", ("우리금융", "woori financial")),
    StockAlias("032830", "삼성생명", "KRX", "KOSPI", ("samsung life",)),
    StockAlias("018260", "삼성에스디에스", "KRX", "KOSPI", ("삼성sds", "samsung sds")),
    StockAlias("009150", "삼성전기", "KRX", "KOSPI", ("samsung electro-mechanics", "삼성전기우")),
    StockAlias("034020", "두산에너빌리티", "KRX", "KOSPI", ("두산중공업", "doosan energy", "doosan energibility")),
    StockAlias("042660", "한화오션", "KRX", "KOSPI", ("대우조선해양", "hanwha ocean")),
    StockAlias("329180", "HD현대중공업", "KRX", "KOSPI", ("현대중공업", "hd hyundai heavy", "hyundai heavy industries")),
    StockAlias("003550", "LG", "KRX", "KOSPI", ("엘지", "lg corp")),
    StockAlias("034730", "SK", "KRX", "KOSPI", ("에스케이", "sk holdings", "sk주식회사")),
    StockAlias("096770", "SK이노베이션", "KRX", "KOSPI", ("sk innovation", "에스케이이노베이션")),
    StockAlias("011200", "HMM", "KRX", "KOSPI", ("hmm", "현대상선")),
    StockAlias("015760", "한국전력", "KRX", "KOSPI", ("한전", "korea electric power", "kepco")),
    StockAlias("033780", "KT&G", "KRX", "KOSPI", ("케이티앤지", "kt&g", "korea tobacco")),
    StockAlias("030200", "KT", "KRX", "KOSPI", ("케이티", "kt corp")),
    StockAlias("017670", "SK텔레콤", "KRX", "KOSPI", ("sk telecom", "skt", "에스케이텔레콤")),
    StockAlias("003670", "포스코퓨처엠", "KRX", "KOSPI", ("포스코케미칼", "posco future m", "posco futurem")),
    StockAlias("066570", "LG전자", "KRX", "KOSPI", ("엘지전자", "lg electronics")),
    StockAlias("090430", "아모레퍼시픽", "KRX", "KOSPI", ("amorepacific", "아모레")),
    StockAlias("161390", "한국타이어앤테크놀로지", "KRX", "KOSPI", ("한국타이어", "hankook tire")),
    StockAlias("010130", "고려아연", "KRX", "KOSPI", ("korea zinc",)),
    StockAlias("086280", "현대글로비스", "KRX", "KOSPI", ("hyundai glovis",)),
    StockAlias("010950", "S-Oil", "KRX", "KOSPI", ("에쓰오일", "s-oil", "soil")),
    StockAlias("036570", "엔씨소프트", "KRX", "KOSPI", ("ncsoft", "엔씨", "ncsfot")),
    StockAlias("251270", "넷마블", "KRX", "KOSPI", ("netmarble",)),
    StockAlias("352820", "하이브", "KRX", "KOSPI", ("hybe", "빅히트", "bighit")),
    StockAlias("259960", "크래프톤", "KRX", "KOSPI", ("krafton", "배틀그라운드", "pubg")),
    # KOSDAQ / growth
    StockAlias("247540", "에코프로비엠", "KRX", "KOSDAQ", ("ecopro bm", "ecoprobm", "에코프로비엠")),
    StockAlias("086520", "에코프로", "KRX", "KOSDAQ", ("ecopro",)),
    StockAlias("091990", "셀트리온헬스케어", "KRX", "KOSDAQ", ("celltrion healthcare",)),
    StockAlias("035760", "CJ ENM", "KRX", "KOSDAQ", ("씨제이이엔엠", "cj enm")),
    StockAlias("112040", "위메이드", "KRX", "KOSDAQ", ("wemade",)),
    StockAlias("263750", "펄어비스", "KRX", "KOSDAQ", ("pearl abyss",)),
    StockAlias("041510", "에스엠", "KRX", "KOSDAQ", ("sm entertainment", "sm엔터", "sm", "에스엠엔터")),
    StockAlias("293490", "카카오게임즈", "KRX", "KOSDAQ", ("kakao games",)),
    StockAlias("196170", "알테오젠", "KRX", "KOSDAQ", ("alteogen",)),
    StockAlias("068760", "셀트리온제약", "KRX", "KOSDAQ", ("celltrion pharm", "celltrion pharmaceuticals")),
    StockAlias("058470", "리노공업", "KRX", "KOSDAQ", ("leeno", "leeno industrial")),
    StockAlias("278280", "천보", "KRX", "KOSDAQ", ("chunbo",)),
    StockAlias("222800", "심텍", "KRX", "KOSDAQ", ("simmtech",)),
    # US common names
    StockAlias("AAPL", "Apple", "US", "NASDAQ", ("애플", "apple", "apple inc", "아이폰")),
    StockAlias("MSFT", "Microsoft", "US", "NASDAQ", ("마이크로소프트", "microsoft", "ms", "msft")),
    StockAlias("NVDA", "NVIDIA", "US", "NASDAQ", ("엔비디아", "nvidia", "nvidia corp", "젠슨황")),
    StockAlias("GOOGL", "Alphabet", "US", "NASDAQ", ("구글", "알파벳", "google", "alphabet", "google class a")),
    StockAlias("GOOG", "Alphabet Class C", "US", "NASDAQ", ("google class c",)),
    StockAlias("AMZN", "Amazon", "US", "NASDAQ", ("아마존", "amazon", "amazon.com")),
    StockAlias("META", "Meta Platforms", "US", "NASDAQ", ("메타", "facebook", "페이스북", "meta", "meta platforms")),
    StockAlias("TSLA", "Tesla", "US", "NASDAQ", ("테슬라", "tesla", "tesla motors", "model y")),
    StockAlias("BRK-B", "Berkshire Hathaway", "US", "NYSE", ("버크셔", "berkshire", "berkshire hathaway", "brk.b")),
    StockAlias("LLY", "Eli Lilly", "US", "NYSE", ("일라이릴리", "eli lilly", "lilly")),
    StockAlias("AVGO", "Broadcom", "US", "NASDAQ", ("브로드컴", "broadcom")),
    StockAlias("JPM", "JPMorgan Chase", "US", "NYSE", ("제이피모건", "jp morgan", "jpmorgan", "jpmorgan chase")),
    StockAlias("V", "Visa", "US", "NYSE", ("비자", "visa")),
    StockAlias("MA", "Mastercard", "US", "NYSE", ("마스터카드", "mastercard")),
    StockAlias("UNH", "UnitedHealth Group", "US", "NYSE", ("유나이티드헬스", "unitedhealth", "united health")),
    StockAlias("XOM", "Exxon Mobil", "US", "NYSE", ("엑슨모빌", "exxon", "exxon mobil")),
    StockAlias("WMT", "Walmart", "US", "NYSE", ("월마트", "walmart")),
    StockAlias("COST", "Costco", "US", "NASDAQ", ("코스트코", "costco")),
    StockAlias("NFLX", "Netflix", "US", "NASDAQ", ("넷플릭스", "netflix")),
    StockAlias("AMD", "AMD", "US", "NASDAQ", ("에이엠디", "advanced micro devices", "amd")),
    StockAlias("INTC", "Intel", "US", "NASDAQ", ("인텔", "intel")),
    StockAlias("ORCL", "Oracle", "US", "NYSE", ("오라클", "oracle")),
    StockAlias("CRM", "Salesforce", "US", "NYSE", ("세일즈포스", "salesforce")),
    StockAlias("ADBE", "Adobe", "US", "NASDAQ", ("어도비", "adobe")),
    StockAlias("PLTR", "Palantir", "US", "NYSE", ("팔란티어", "palantir")),
    StockAlias("SMCI", "Super Micro Computer", "US", "NASDAQ", ("슈퍼마이크로", "supermicro", "super micro")),
)


def normalize_name(text: str) -> str:
    s = unicodedata.normalize("NFKC", text or "").strip().lower()
    s = re.sub(r"[\s\-_.,/()\[\]{}·㈜주식회사]+", "", s)
    s = s.replace("보통주", "")
    s = s.replace("commonstock", "")
    s = s.replace("incorporated", "inc")
    s = s.replace("corporation", "corp")
    s = s.replace("company", "co")
    return s


def _is_korean(text: str) -> bool:
    return bool(re.search(r"[가-힣]", text or ""))


def _looks_like_krx_code(text: str) -> bool:
    return bool(re.fullmatch(r"\d{6}(?:\.(?:KS|KQ))?", text.strip().upper()))


def _looks_like_us_ticker(text: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{1,5}(?:[-.][A-Z])?", text.strip().upper()))


def _iter_alias_keys(alias: StockAlias) -> list[str]:
    values = [alias.company_name, alias.ticker, *alias.aliases]
    keys = []
    for v in values:
        nv = normalize_name(v)
        if nv and nv not in keys:
            keys.append(nv)
    return keys


_LOOKUP: dict[str, StockAlias] = {}
for item in STOCK_ALIASES:
    for key in _iter_alias_keys(item):
        _LOOKUP[key] = item


def resolve_stock_input(raw_input: str, company_hint: str = "", market: str = "AUTO") -> TickerResolution:
    """Resolve a user input that can be either ticker or company name.

    Examples:
    - 삼성전자 -> 005930
    - 네이버 -> 035420
    - Apple / 애플 -> AAPL
    - 005930 -> 005930
    - AAPL -> AAPL
    """
    original = (raw_input or "").strip()
    hint = (company_hint or "").strip()
    selected_market = (market or "AUTO").upper()
    if not original:
        return TickerResolution(original, "", hint, selected_market, "", False, "empty", 0.0, "입력값이 비어 있습니다.")

    # 1) Exact KRX numeric ticker input
    upper = original.upper().replace(".", "-") if original.upper() == "BRK.B" else original.upper()
    if _looks_like_krx_code(upper):
        ticker = upper.replace(".KS", "").replace(".KQ", "")
        return TickerResolution(
            original, ticker, hint, "KRX", "KOSPI/KOSDAQ", True, "ticker_code", 0.98,
            "6자리 숫자 코드를 한국 종목 코드로 인식했습니다.",
        )

    # 2) Exact alias/company match, using input first and hint second.
    # Important: run this before generic US ticker detection so "Apple" resolves to AAPL, not APPLE.
    for source, label in ((original, "name_alias"), (hint, "company_hint_alias")):
        key = normalize_name(source)
        if key in _LOOKUP:
            item = _LOOKUP[key]
            return TickerResolution(
                original, item.ticker, item.company_name, item.market, item.exchange, True, label, 0.99,
                "내장 종목명 사전에서 정확히 매칭했습니다.",
            )

    # 3) Generic US ticker input. Unknown uppercase symbols such as ABNB or COIN still work.
    if _looks_like_us_ticker(upper):
        known = _LOOKUP.get(normalize_name(upper))
        return TickerResolution(
            original,
            upper,
            hint or (known.company_name if known else ""),
            known.market if known else ("US" if selected_market in {"AUTO", "US"} else selected_market),
            known.exchange if known else "",
            True,
            "ticker_symbol",
            0.95,
            "알파벳 티커 심볼로 인식했습니다.",
        )

    # 4) Partial alias/company match. This catches inputs like "삼성전자우는 말고 삼성전자" or "테슬라 주가".
    normalized_original = normalize_name(original)
    candidates: list[tuple[int, StockAlias, str]] = []
    for item in STOCK_ALIASES:
        for key in _iter_alias_keys(item):
            if len(key) >= 2 and (key in normalized_original or normalized_original in key):
                # Prefer longer key matches.
                candidates.append((len(key), item, key))
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        item = candidates[0][1]
        return TickerResolution(
            original, item.ticker, item.company_name, item.market, item.exchange, True, "partial_name_match", 0.86,
            "입력 문장 안의 종목명을 부분 매칭했습니다. 동명이인이거나 우선주/보통주 구분이 필요한 경우 티커를 직접 입력하세요.",
        )

    # 5) Unknown name. Continue with original input so LLM can still reason, but warn user.
    inferred_market = "KRX" if _is_korean(original) and selected_market in {"AUTO", "KRX"} else selected_market
    return TickerResolution(
        original,
        original.upper(),
        hint or original,
        inferred_market,
        "",
        False,
        "unresolved_name",
        0.25,
        "내장 사전에서 종목코드를 찾지 못했습니다. 가격 데이터는 실패할 수 있으므로 정확한 티커를 확인하세요.",
    )
