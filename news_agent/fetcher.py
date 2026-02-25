from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

import feedparser
from dateutil import parser as date_parser

from .config import POLITICAL_KEYWORDS, RSS_FEEDS


@dataclass
class NewsItem:
    source: str
    title: str
    summary: str
    link: str
    published_at: datetime


def _safe_parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        dt = date_parser.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _is_political(text: str) -> bool:
    lower = text.lower()
    return any(keyword in lower for keyword in POLITICAL_KEYWORDS)


def fetch_news(hours: int = 24, per_source_limit: int = 80) -> list[NewsItem]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items: list[NewsItem] = []
    seen_links: set[str] = set()

    for source_name, url in RSS_FEEDS.items():
        parsed = feedparser.parse(url)
        entries: Iterable = parsed.entries[:per_source_limit]
        for entry in entries:
            title = (entry.get("title") or "").strip()
            summary = (entry.get("summary") or "").strip()
            link = (entry.get("link") or "").strip()
            published = _safe_parse_datetime(entry.get("published") or entry.get("updated"))

            if not title or not link:
                continue
            if link in seen_links:
                continue
            if published < cutoff:
                continue
            if not _is_political(f"{title} {summary}"):
                continue

            seen_links.add(link)
            items.append(
                NewsItem(
                    source=source_name,
                    title=title,
                    summary=summary,
                    link=link,
                    published_at=published,
                )
            )

    items.sort(key=lambda x: x.published_at, reverse=True)
    return items
