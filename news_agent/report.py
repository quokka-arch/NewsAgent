from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .analyzer import AnalyzedItem


def _ascii_bar(count: int, max_val: int, width: int = 20) -> str:
    filled = int(round(count / max_val * width)) if max_val else 0
    return "█" * filled + "░" * (width - filled)


def _to_markdown(summary: dict, analyzed_items: list[AnalyzedItem], generated_at: str, hours: int) -> str:
    lines: list[str] = []
    lines.append(f"# 🌐 国际政治舆情简报 ({generated_at})")
    lines.append("")
    lines.append(f"> 监控窗口：最近 **{hours} 小时** | 抓取总数：**{summary['total']}**")
    lines.append("")

    # ── Risk overview ──────────────────────────────────
    total = summary["total"] or 1
    high = summary["risk_levels"].get("HIGH", 0)
    medium = summary["risk_levels"].get("MEDIUM", 0)
    low = summary["risk_levels"].get("LOW", 0)
    lines.append("## ⚠ 风险总览")
    lines.append("")
    lines.append(f"| 等级   | 数量 | 占比   | 分布                       |")
    lines.append(f"|--------|------|--------|----------------------------|")
    for label, count in [("🔴 HIGH", high), ("🟠 MEDIUM", medium), ("🟢 LOW", low)]:
        bar = _ascii_bar(count, total, 20)
        lines.append(f"| {label} | {count:4d} | {count/total*100:5.1f}% | `{bar}` |")
    lines.append("")

    # ── Countries ──────────────────────────────────────
    lines.append("## 🌍 高频国家 / 地区")
    lines.append("")
    if summary["countries"]:
        max_c = summary["countries"][0][1]
        lines.append("| 国家 / 地区         | 提及 | 频率分布                   |")
        lines.append("|---------------------|------|----------------------------|")
        for country, count in summary["countries"][:10]:
            bar = _ascii_bar(count, max_c, 20)
            lines.append(f"| {country:<20}| {count:4d} | `{bar}` |")
    else:
        lines.append("- 无")
    lines.append("")

    # ── Topics ─────────────────────────────────────────
    lines.append("## 🏷 议题主题分布")
    lines.append("")
    if summary["topics"]:
        max_t = summary["topics"][0][1]
        lines.append("| 主题                    | 条目 | 频率分布                   |")
        lines.append("|-------------------------|------|----------------------------|")
        for topic, count in summary["topics"][:8]:
            bar = _ascii_bar(count, max_t, 20)
            lines.append(f"| {topic:<24}| {count:4d} | `{bar}` |")
    else:
        lines.append("- 无")
    lines.append("")

    # ── Highlights ─────────────────────────────────────
    lines.append("## 🔥 高风险新闻 Top 15")
    lines.append("")
    top = [entry for entry in analyzed_items if entry.risk_level in {"HIGH", "MEDIUM"}][:15]
    if not top:
        lines.append("- 当前窗口未发现中高风险事件")
    else:
        lines.append("| # | 标题 | 来源 | 风险 | 情绪 | 时间 |")
        lines.append("|---|------|------|------|------|------|")
        for idx, entry in enumerate(top, start=1):
            ts = entry.item.published_at.strftime("%m-%d %H:%M")
            senti = f"{entry.sentiment:+.2f}"
            risk_label = f"**{entry.risk_level}**({entry.risk_score})"
            title_link = f"[{entry.item.title[:60]}]({entry.item.link})"
            lines.append(f"| {idx} | {title_link} | {entry.item.source} | {risk_label} | {senti} | {ts} |")
    lines.append("")

    # ── Conflict pairs ─────────────────────────────────
    conflict_pairs = summary.get("conflict_pairs", [])
    lines.append("## ⚡ 国家冲突矩阵")
    lines.append("")
    if conflict_pairs:
        lines.append("| 冲突方 A | 冲突方 B | 共现次数 | 均风险 | 均情绪 | 矛盾焦点 |")
        lines.append("|----------|----------|---------|--------|--------|---------|")
        for entry in conflict_pairs[:10]:
            a, b = entry["pair"]
            topics = " / ".join(entry["topics"][:2]) or "—"
            lines.append(
                f"| {a} | {b} | {entry['count']} "
                f"| {entry['avg_risk']:.1f} | {entry['avg_sentiment']:+.2f} | {topics} |"
            )
    else:
        lines.append("- 当前窗口未检测到国家间冲突信号")
    lines.append("")

    # ── Sources ────────────────────────────────────────
    lines.append("## 📰 来源统计")
    lines.append("")
    if summary["sources"]:
        max_s = summary["sources"][0][1]
        lines.append("| 来源                  | 条目 | 分布                       |")
        lines.append("|-----------------------|------|----------------------------|")
        for source, count in summary["sources"]:
            bar = _ascii_bar(count, max_s, 20)
            lines.append(f"| {source:<22}| {count:4d} | `{bar}` |")
    else:
        lines.append("- 无")

    return "\n".join(lines)


def _to_json(summary: dict, analyzed_items: list[AnalyzedItem], generated_at: str, hours: int) -> dict:
    return {
        "generated_at": generated_at,
        "window_hours": hours,
        "summary": summary,
        "highlights": [
            {
                "title": entry.item.title,
                "source": entry.item.source,
                "link": entry.item.link,
                "published_at": entry.item.published_at.isoformat(),
                "risk_level": entry.risk_level,
                "risk_score": entry.risk_score,
                "sentiment": entry.sentiment,
                "countries": entry.countries,
                "topics": entry.topics,
            }
            for entry in analyzed_items[:50]
        ],
    }


def write_reports(
    summary: dict,
    analyzed_items: list[AnalyzedItem],
    out_dir: str,
    output_format: str,
    hours: int,
) -> list[Path]:
    from .html_report import generate_html

    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M")
    generated_at = now.strftime("%Y-%m-%d %H:%M:%S")
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths: list[Path] = []

    if output_format in {"md", "both"}:
        md_path = output_dir / f"brief_{stamp}.md"
        md_path.write_text(_to_markdown(summary, analyzed_items, generated_at, hours), encoding="utf-8")
        output_paths.append(md_path)

    if output_format in {"json", "both"}:
        json_path = output_dir / f"brief_{stamp}.json"
        payload = _to_json(summary, analyzed_items, generated_at, hours)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        output_paths.append(json_path)

    # Always generate HTML
    html_path = output_dir / f"brief_{stamp}.html"
    html_path.write_text(generate_html(summary, analyzed_items, hours), encoding="utf-8")
    output_paths.append(html_path)

    return output_paths
