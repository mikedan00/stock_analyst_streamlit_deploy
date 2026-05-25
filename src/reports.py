from __future__ import annotations

import datetime as dt
from pathlib import Path


def safe_filename(text: str) -> str:
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    return "".join(c if c in allowed else "_" for c in text)[:80].strip("_") or "report"


def write_markdown_report(report: str, ticker: str, output_dir: str | Path = "reports") -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out / f"{safe_filename(ticker)}_{stamp}_stock_report.md"
    path.write_text(report, encoding="utf-8")
    return path
