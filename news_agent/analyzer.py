from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import combinations

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .config import COUNTRY_ALIASES, RISK_KEYWORDS, TOPIC_KEYWORDS
from .fetcher import NewsItem


@dataclass
class AnalyzedItem:
    item: NewsItem
    sentiment: float
    risk_score: int
    risk_level: str
    countries: list[str]
    topics: list[str]


def _extract_countries(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for country, aliases in COUNTRY_ALIASES.items():
        if any(alias in lower for alias in aliases):
            found.append(country)
    return found


def _extract_topics(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for topic, keys in TOPIC_KEYWORDS.items():
        if any(key in lower for key in keys):
            found.append(topic)
    return found


def _risk_from_text(text: str, sentiment: float) -> tuple[int, str]:
    lower = text.lower()
    high_hits = sum(1 for key in RISK_KEYWORDS["high"] if key in lower)
    medium_hits = sum(1 for key in RISK_KEYWORDS["medium"] if key in lower)
    score = high_hits * 3 + medium_hits * 1

    if sentiment <= -0.5:
        score += 2
    elif sentiment <= -0.2:
        score += 1

    if score >= 6:
        return score, "HIGH"
    if score >= 3:
        return score, "MEDIUM"
    return score, "LOW"


def analyze(items: list[NewsItem]) -> list[AnalyzedItem]:
    analyzer = SentimentIntensityAnalyzer()
    analyzed: list[AnalyzedItem] = []

    for item in items:
        text = f"{item.title}. {item.summary}"
        sentiment = analyzer.polarity_scores(text)["compound"]
        risk_score, risk_level = _risk_from_text(text, sentiment)
        countries = _extract_countries(text)
        topics = _extract_topics(text)

        analyzed.append(
            AnalyzedItem(
                item=item,
                sentiment=sentiment,
                risk_score=risk_score,
                risk_level=risk_level,
                countries=countries,
                topics=topics,
            )
        )

    analyzed.sort(key=lambda x: (x.risk_score, x.item.published_at), reverse=True)
    return analyzed


def _extract_conflict_pairs(analyzed_items: list[AnalyzedItem]) -> list[dict]:
    """Extract country-vs-country conflict pairs from HIGH/MEDIUM risk articles."""
    pair_counts: Counter = Counter()
    pair_risk: dict[tuple, list[int]] = defaultdict(list)
    pair_sentiment: dict[tuple, list[float]] = defaultdict(list)
    pair_topics: dict[tuple, Counter] = defaultdict(Counter)
    pair_headlines: dict[tuple, list[str]] = defaultdict(list)

    for entry in analyzed_items:
        if entry.risk_level not in {"HIGH", "MEDIUM"}:
            continue
        countries = entry.countries
        if len(countries) < 2:
            continue
        for a, b in combinations(sorted(set(countries)), 2):
            key = (a, b)
            pair_counts[key] += 1
            pair_risk[key].append(entry.risk_score)
            pair_sentiment[key].append(entry.sentiment)
            for topic in entry.topics:
                pair_topics[key][topic] += 1
            if len(pair_headlines[key]) < 2:
                pair_headlines[key].append(entry.item.title)

    results = []
    for (a, b), count in pair_counts.most_common(15):
        key = (a, b)
        avg_risk = sum(pair_risk[key]) / len(pair_risk[key])
        avg_senti = sum(pair_sentiment[key]) / len(pair_sentiment[key])
        top_topics = [t for t, _ in pair_topics[key].most_common(3)]
        results.append({
            "pair": (a, b),
            "count": count,
            "avg_risk": round(avg_risk, 1),
            "avg_sentiment": round(avg_senti, 2),
            "topics": top_topics,
            "headlines": pair_headlines[key],
        })

    results.sort(key=lambda x: (x["count"], x["avg_risk"]), reverse=True)
    return results


def aggregate(analyzed_items: list[AnalyzedItem]) -> dict:
    level_counter = Counter(entry.risk_level for entry in analyzed_items)
    country_counter = Counter(country for entry in analyzed_items for country in entry.countries)
    topic_counter = Counter(topic for entry in analyzed_items for topic in entry.topics)
    source_counter = Counter(entry.item.source for entry in analyzed_items)
    conflict_pairs = _extract_conflict_pairs(analyzed_items)

    return {
        "total": len(analyzed_items),
        "risk_levels": dict(level_counter),
        "countries": country_counter.most_common(10),
        "topics": topic_counter.most_common(10),
        "sources": source_counter.most_common(10),
        "conflict_pairs": conflict_pairs,
    }
