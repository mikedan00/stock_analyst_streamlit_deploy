from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus
import datetime as dt

import feedparser


@dataclass
class NewsSnapshot:
    ok: bool
    summary_markdown: str
    error: str | None = None


def fetch_news_snapshot(ticker: str, company_name: str = "", max_items: int = 8) -> NewsSnapshot:
    query = company_name.strip() or ticker.strip()
    if not query:
        return NewsSnapshot(False, "", "뉴스 검색어가 비어 있습니다.")

    try:
        url = f"https://news.google.com/rss/search?q={quote_plus(query + ' stock earnings')}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        entries = feed.entries[:max_items]
        if not entries:
            return NewsSnapshot(False, "", "뉴스 RSS 결과가 없습니다.")

        lines = ["## 앱 수집 최근 뉴스 컨텍스트", ""]
        for i, e in enumerate(entries, 1):
            title = getattr(e, "title", "").replace("\n", " ").strip()
            published = getattr(e, "published", "")
            source = ""
            if hasattr(e, "source") and isinstance(e.source, dict):
                source = e.source.get("title", "")
            link = getattr(e, "link", "")
            lines.append(f"{i}. **{title}**")
            if published or source:
                lines.append(f"   - 발행/출처: {published or 'N/A'} / {source or 'N/A'}")
            if link:
                lines.append(f"   - 링크: {link}")
        lines.append("")
        lines.append("주의: RSS 제목 기반 보조 컨텍스트입니다. 중요한 수치는 원문·공시·재무제표로 재확인해야 합니다.")
        return NewsSnapshot(True, "\n".join(lines))
    except Exception as exc:
        return NewsSnapshot(False, "", str(exc))
