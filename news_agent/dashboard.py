"""Rich terminal dashboard for news sentiment monitoring."""
from __future__ import annotations

from datetime import datetime, timezone

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from .analyzer import AnalyzedItem
from .config import COUNTRY_ZH, RISK_ZH, TOPIC_ZH

console = Console()

_RISK_STYLE = {
    "HIGH": "bold white on red",
    "MEDIUM": "bold black on yellow",
    "LOW": "bold white on green",
}

_SENTIMENT_COLOR = {
    "very_neg": "red",
    "neg": "light_salmon3",
    "neutral": "white",
    "pos": "pale_green3",
    "very_pos": "green",
}


def _sentiment_label(score: float) -> tuple[str, str]:
    if score <= -0.6:
        return "极负面", "red"
    if score <= -0.2:
        return "负面", "light_salmon3"
    if score < 0.2:
        return "中性", "white"
    if score < 0.6:
        return "正面", "pale_green3"
    return "极正面", "green"


def _make_bar(value: int, max_val: int, width: int = 20) -> Text:
    if max_val == 0:
        filled = 0
    else:
        filled = int(round(value / max_val * width))
    bar = "█" * filled + "░" * (width - filled)
    pct = (value / max_val * 100) if max_val else 0
    t = Text()
    t.append(bar, style="cyan")
    t.append(f" {value} ({pct:.0f}%)", style="dim")
    return t


def _risk_overview_panel(summary: dict, generated_at: str, hours: int) -> Panel:
    total = summary["total"]
    high = summary["risk_levels"].get("HIGH", 0)
    medium = summary["risk_levels"].get("MEDIUM", 0)
    low = summary["risk_levels"].get("LOW", 0)

    table = Table.grid(padding=(0, 2))
    table.add_column(justify="center", min_width=14)
    table.add_column(justify="center", min_width=14)
    table.add_column(justify="center", min_width=14)
    table.add_column(justify="center", min_width=14)

    def _risk_cell(label: str, count: int, style: str) -> Text:
        t = Text(justify="center")
        t.append(f" {label} ", style=style)
        t.append(f"\n{count:^10}", style="bold white")
        return t

    table.add_row(
        _risk_cell("  总条目  ", total, "bold white on blue"),
        _risk_cell("  HIGH  ", high, _RISK_STYLE["HIGH"]),
        _risk_cell(" MEDIUM ", medium, _RISK_STYLE["MEDIUM"]),
        _risk_cell("  LOW   ", low, _RISK_STYLE["LOW"]),
    )

    subtitle = Text(f"📅 {generated_at}  ·  🕐 最近 {hours}h", style="dim")
    return Panel(table, title="[bold]国际政治舆情监控", subtitle=subtitle, border_style="bright_blue", padding=(1, 2))


def _country_table(countries: list[tuple[str, int]]) -> Panel:
    max_val = countries[0][1] if countries else 1
    t = Table(box=box.SIMPLE_HEAD, show_header=True, border_style="blue")
    t.add_column("国家 / 地区", style="cyan", min_width=16)
    t.add_column("提及次数", justify="right", min_width=6)
    t.add_column("频率分布", min_width=24)
    for country, count in countries[:10]:
        t.add_row(COUNTRY_ZH.get(country, country), str(count), _make_bar(count, max_val))
    return Panel(t, title="[bold cyan]🌍 高频国家", border_style="cyan", padding=(0, 1))


def _topic_table(topics: list[tuple[str, int]]) -> Panel:
    max_val = topics[0][1] if topics else 1
    t = Table(box=box.SIMPLE_HEAD, show_header=True, border_style="magenta")
    t.add_column("主题", style="magenta", min_width=18)
    t.add_column("条目", justify="right", min_width=6)
    t.add_column("频率分布", min_width=24)
    for topic, count in topics[:8]:
        t.add_row(TOPIC_ZH.get(topic, topic), str(count), _make_bar(count, max_val))
    return Panel(t, title="[bold magenta]🏷  主题分布", border_style="magenta", padding=(0, 1))


def _highlights_table(analyzed_items: list[AnalyzedItem], n: int = 15) -> Panel:
    top = [e for e in analyzed_items if e.risk_level in {"HIGH", "MEDIUM"}][:n]
    if not top:
        top = analyzed_items[:n]

    t = Table(box=box.ROUNDED, show_header=True, border_style="red", show_lines=True)
    t.add_column("#", justify="right", style="dim", width=3)
    t.add_column("标题", min_width=40, max_width=70, no_wrap=False)
    t.add_column("来源", min_width=12, max_width=18)
    t.add_column("风险", justify="center", min_width=8)
    t.add_column("情绪", justify="center", min_width=10)
    t.add_column("国家", min_width=18)
    t.add_column("时间 (UTC)", min_width=12)

    for idx, entry in enumerate(top, start=1):
        risk_txt = Text(f" {RISK_ZH.get(entry.risk_level, entry.risk_level)} ", style=_RISK_STYLE[entry.risk_level])
        label, s_color = _sentiment_label(entry.sentiment)
        sentiment_txt = Text(f"{label}\n{entry.sentiment:+.2f}", style=s_color, justify="center")
        country_txt = ", ".join(COUNTRY_ZH.get(c, c) for c in entry.countries[:3]) or "—"
        ts = entry.item.published_at.astimezone(timezone.utc).strftime("%m-%d %H:%M")
        t.add_row(
            str(idx),
            entry.item.title,
            entry.item.source,
            risk_txt,
            sentiment_txt,
            country_txt,
            ts,
        )

    return Panel(t, title=f"[bold red]🔥 高风险新闻 Top {n}", border_style="red", padding=(0, 1))


def _source_table(sources: list[tuple[str, int]]) -> Panel:
    max_val = sources[0][1] if sources else 1
    t = Table(box=box.SIMPLE_HEAD, show_header=True, border_style="green")
    t.add_column("来源", style="green", min_width=20)
    t.add_column("条目", justify="right", min_width=6)
    t.add_column("占比", min_width=22)
    for source, count in sources:
        t.add_row(source, str(count), _make_bar(count, max_val))
    return Panel(t, title="[bold green]📰 来源分布", border_style="green", padding=(0, 1))


_COUNTRY_FLAG: dict[str, str] = {
    "United States": "🇺🇸",
    "China": "🇨🇳",
    "Russia": "🇷🇺",
    "Ukraine": "🇺🇦",
    "Israel": "🇮🇱",
    "Palestine": "🇵🇸",
    "Iran": "🇮🇷",
    "United Kingdom": "🇬🇧",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Japan": "🇯🇵",
    "South Korea": "🇰🇷",
    "India": "🇮🇳",
    "Taiwan": "🇹🇼",
}


def _country_label(name: str, flag_key: str | None = None) -> str:
    flag = _COUNTRY_FLAG.get(flag_key or name, "🌐")
    return f"{flag} {name}"


def _conflict_panel(conflict_pairs: list[dict]) -> Panel:
    if not conflict_pairs:
        return Panel("[dim]当前窗口未检测到国家间冲突信号", title="[bold yellow]⚡ 国家冲突矩阵", border_style="yellow")

    t = Table(box=box.SIMPLE_HEAD, show_header=True, border_style="yellow", show_lines=False)
    t.add_column("冲突方", min_width=38, no_wrap=True)
    t.add_column("共现", justify="center", min_width=5)
    t.add_column("风险", justify="center", min_width=6)
    t.add_column("情绪", justify="center", min_width=8)
    t.add_column("矛盾焦点", min_width=36)
    t.add_column("代表性标题", min_width=40, max_width=55, no_wrap=False)

    for entry in conflict_pairs[:12]:
        a, b = entry["pair"]
        a_zh, b_zh = COUNTRY_ZH.get(a, a), COUNTRY_ZH.get(b, b)
        pair_str = Text()
        pair_str.append(_country_label(a_zh, flag_key=a), style="cyan")
        pair_str.append("  ↔  ", style="dim")
        pair_str.append(_country_label(b_zh, flag_key=b), style="cyan")

        risk_score = entry["avg_risk"]
        if risk_score >= 6:
            risk_txt = Text(f"★{risk_score:.0f}", style="bold red")
        elif risk_score >= 3:
            risk_txt = Text(f"▲{risk_score:.0f}", style="bold yellow")
        else:
            risk_txt = Text(f"·{risk_score:.0f}", style="dim")

        senti = entry["avg_sentiment"]
        _, s_color = _sentiment_label(senti)
        senti_txt = Text(f"{senti:+.2f}", style=s_color)

        topics_str = " · ".join(TOPIC_ZH.get(t, t) for t in entry["topics"][:2]) or "—"
        headline = entry["headlines"][0][:52] if entry["headlines"] else "—"

        t.add_row(pair_str, str(entry["count"]), risk_txt, senti_txt, topics_str, headline)

    return Panel(t, title="[bold yellow]⚡ 国家冲突矩阵（按共现频率排序）", border_style="yellow", padding=(0, 1))


def render_dashboard(summary: dict, analyzed_items: list[AnalyzedItem], hours: int = 24) -> None:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print()
    console.print(_risk_overview_panel(summary, generated_at, hours))
    console.print(Columns([_country_table(summary["countries"]), _topic_table(summary["topics"])], equal=False))
    console.print(_conflict_panel(summary.get("conflict_pairs", [])))
    console.print(_highlights_table(analyzed_items))
    console.print(Columns([_source_table(summary["sources"])], equal=False))
