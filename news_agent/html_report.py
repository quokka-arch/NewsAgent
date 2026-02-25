"""Generate a self-contained HTML report with visual charts and risk indicators."""
from __future__ import annotations

import html
import json
from datetime import datetime

from .analyzer import AnalyzedItem
from .config import COUNTRY_ZH, RISK_ZH, TOPIC_ZH


def _t_country(name: str) -> str:
    return COUNTRY_ZH.get(name, name)


def _t_topic(name: str) -> str:
    return TOPIC_ZH.get(name, name)


def _t_risk(level: str) -> str:
    return RISK_ZH.get(level, level)


_COUNTRY_FLAG: dict[str, str] = {
    "United States": "🇺🇸", "China": "🇨🇳", "Russia": "🇷🇺", "Ukraine": "🇺🇦",
    "Israel": "🇮🇱", "Palestine": "🇵🇸", "Iran": "🇮🇷", "United Kingdom": "🇬🇧",
    "France": "🇫🇷", "Germany": "🇩🇪", "Japan": "🇯🇵", "South Korea": "🇰🇷",
    "India": "🇮🇳", "Taiwan": "🇹🇼",
}


def _flag(name: str) -> str:
    return _COUNTRY_FLAG.get(name, "🌐")


_RISK_BADGE = {
    "HIGH": ('<span class="badge high">高风险</span>', "#ff4d4d"),
    "MEDIUM": ('<span class="badge medium">中风险</span>', "#ffa64d"),
    "LOW": ('<span class="badge low">低风险</span>', "#52c41a"),
}

_SENTIMENT_SIGN = {
    (True, True): ("极负面", "#ff4d4d"),
    (True, False): ("负面", "#fa8c16"),
    (False, False): ("中性", "#8c8c8c"),
    (False, True): ("正面", "#52c41a"),
}


def _senti_info(score: float) -> tuple[str, str]:
    if score <= -0.6:
        return "极负面", "#ff4d4d"
    if score <= -0.2:
        return "负面", "#fa8c16"
    if score < 0.2:
        return "中性", "#8c8c8c"
    if score < 0.6:
        return "正面", "#52c41a"
    return "极正面", "#1890ff"


_CSS = """
:root {
  --bg: #0d1117; --surface: #161b22; --border: #30363d;
  --text: #e6edf3; --muted: #8b949e;
  --red: #ff4d4d; --orange: #ffa64d; --green: #3fb950; --blue: #58a6ff;
  --high: #ff4d4d; --medium: #ffa64d; --low: #3fb950;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; font-size: 14px; }
a { color: var(--blue); text-decoration: none; }
a:hover { text-decoration: underline; }

header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 20px 32px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
header h1 { font-size: 1.4rem; font-weight: 600; }
header .meta { color: var(--muted); font-size: 0.85rem; }

.container { max-width: 1400px; margin: 0 auto; padding: 24px 32px; }

/* Stats row */
.stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 24px; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px 20px; }
.stat-card .value { font-size: 2rem; font-weight: 700; }
.stat-card .label { color: var(--muted); font-size: 0.8rem; margin-top: 4px; }
.stat-card.high .value { color: var(--high); }
.stat-card.medium .value { color: var(--medium); }
.stat-card.low .value { color: var(--low); }

/* Charts row */
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
@media (max-width: 900px) { .charts-row { grid-template-columns: 1fr; } }

.chart-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }
.chart-card h2 { font-size: 0.9rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 16px; }

.bar-row { display: flex; align-items: center; margin-bottom: 9px; }
.bar-label { width: 160px; flex-shrink: 0; font-size: 0.85rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { flex: 1; background: var(--border); border-radius: 4px; height: 14px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width .4s; }
.bar-count { width: 42px; text-align: right; flex-shrink: 0; font-size: 0.8rem; color: var(--muted); }

/* Risk donut (pure CSS) */
.donut-wrap { display: flex; align-items: center; gap: 28px; }
.donut-legend { display: flex; flex-direction: column; gap: 8px; }
.donut-legend-item { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; }
.dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.dot.high { background: var(--high); }
.dot.medium { background: var(--medium); }
.dot.low { background: var(--low); }
.donut-value { font-weight: 600; }
.donut-pct { color: var(--muted); font-size: 0.78rem; }

/* News table */
.section-title { font-size: 1rem; font-weight: 600; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
.news-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.news-table th { background: #1c2128; color: var(--muted); text-align: left; padding: 10px 12px; font-weight: 500; border-bottom: 1px solid var(--border); white-space: nowrap; }
.news-table td { padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
.news-table tr:hover td { background: #1c2128; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; letter-spacing: .04em; }
.badge.high { background: rgba(255,77,77,.18); color: var(--high); border: 1px solid var(--high); }
.badge.medium { background: rgba(255,166,77,.18); color: var(--medium); border: 1px solid var(--medium); }
.badge.low { background: rgba(63,185,80,.18); color: var(--low); border: 1px solid var(--low); }
.senti-bar { height: 4px; border-radius: 2px; margin-top: 4px; }
.country-tag { display: inline-block; background: rgba(88,166,255,.12); color: var(--blue); border-radius: 3px; padding: 1px 5px; font-size: 0.75rem; margin: 1px 2px; }
.source-tag { color: var(--muted); font-size: 0.78rem; }
.ts { color: var(--muted); font-size: 0.78rem; white-space: nowrap; }
.news-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 24px; }
footer { text-align: center; color: var(--muted); font-size: 0.78rem; padding: 32px; border-top: 1px solid var(--border); margin-top: 16px; }
"""


def _bar_chart(items: list[tuple[str, int]], color: str) -> str:
    if not items:
        return "<p style='color:var(--muted)'>无数据</p>"
    max_val = items[0][1]
    rows = []
    for label, count in items:
        pct = (count / max_val * 100) if max_val else 0
        display = _t_country(_t_topic(label))
        rows.append(
            f"""<div class="bar-row">
  <div class="bar-label" title="{html.escape(display)}">{html.escape(display)}</div>
  <div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>
  <div class="bar-count">{count}</div>
</div>"""
        )
    return "\n".join(rows)


def _source_donut_html(sources: list[tuple[str, int]]) -> str:
    total = sum(c for _, c in sources) or 1
    source_colors = ["#58a6ff", "#3fb950", "#ffa64d", "#ff4d4d", "#d2a8ff"]
    items_html = []
    for i, (source, count) in enumerate(sources[:5]):
        color = source_colors[i % len(source_colors)]
        pct = count / total * 100
        items_html.append(
            f"""<div class="donut-legend-item">
  <div class="dot" style="background:{color}"></div>
  <span>{html.escape(source[:24])}</span>
  <span class="donut-value">{count}</span>
  <span class="donut-pct">({pct:.0f}%)</span>
</div>"""
        )
    return "\n".join(items_html)


def _conflict_rows_html(conflict_pairs: list[dict]) -> str:
    if not conflict_pairs:
        return '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:16px">当前窗口未检测到国家间冲突信号</td></tr>'
    rows = []
    for i, entry in enumerate(conflict_pairs[:12], 1):
        a, b = entry["pair"]
        avg_risk = entry["avg_risk"]
        if avg_risk >= 6:
            risk_color, risk_icon = "var(--high)", "★"
        elif avg_risk >= 3:
            risk_color, risk_icon = "var(--medium)", "▲"
        else:
            risk_color, risk_icon = "var(--low)", "·"

        senti = entry["avg_sentiment"]
        _, s_color = _senti_info(senti)
        topics_str = html.escape(" · ".join(_t_topic(t) for t in entry["topics"][:2]) or "—")
        headline = html.escape(entry["headlines"][0][:60]) if entry["headlines"] else "—"
        a_zh, b_zh = _t_country(a), _t_country(b)

        rows.append(f"""
<tr>
  <td style="text-align:center;color:var(--muted)">{i}</td>
  <td style="white-space:nowrap">
    <span style="font-size:1.1em">{_flag(a)}</span> <strong>{html.escape(a_zh)}</strong>
    <span style="color:var(--muted);padding:0 6px">↔</span>
    <span style="font-size:1.1em">{_flag(b)}</span> <strong>{html.escape(b_zh)}</strong>
  </td>
  <td style="text-align:center;font-weight:700">{entry['count']}</td>
  <td style="text-align:center;color:{risk_color};font-weight:700">{risk_icon}{avg_risk:.0f}</td>
  <td style="text-align:center;color:{s_color};font-weight:600">{senti:+.2f}</td>
  <td style="color:var(--muted);font-size:.82rem">{topics_str}</td>
  <td style="font-size:.82rem">{headline}</td>
</tr>""")
    return "\n".join(rows)


def _news_rows_html(analyzed_items: list[AnalyzedItem], n: int = 20) -> str:
    top = [e for e in analyzed_items if e.risk_level in {"HIGH", "MEDIUM"}][:n]
    if not top:
        top = analyzed_items[:n]
    rows = []
    for idx, entry in enumerate(top, start=1):
        badge_html, _ = _RISK_BADGE[entry.risk_level]
        senti_label, senti_color = _senti_info(entry.sentiment)
        # sentiment bar: map -1..1 → 0..100%
        bar_pct = (entry.sentiment + 1) / 2 * 100
        countries_html = " ".join(
            f'<span class="country-tag">{html.escape(_t_country(c))}</span>' for c in entry.countries[:4]
        ) or "—"
        ts = entry.item.published_at.strftime("%m-%d %H:%M")
        title_esc = html.escape(entry.item.title)
        link = html.escape(entry.item.link)
        rows.append(
            f"""<tr>
  <td style="color:var(--muted)">{idx}</td>
  <td><a href="{link}" target="_blank">{title_esc}</a></td>
  <td class="source-tag">{html.escape(entry.item.source)}</td>
  <td style="text-align:center">{badge_html}</td>
  <td style="text-align:center">
    <span style="color:{senti_color};font-weight:600">{senti_label}</span>
    <div class="senti-bar" style="background:linear-gradient(to right, #ff4d4d, #ffa64d, #3fb950);opacity:.5;width:100%"></div>
    <div style="font-size:.75rem;color:{senti_color}">{entry.sentiment:+.2f}</div>
  </td>
  <td>{countries_html}</td>
  <td class="ts">{ts}</td>
</tr>"""
        )
    return "\n".join(rows)


def generate_html(summary: dict, analyzed_items: list[AnalyzedItem], hours: int) -> str:
    now = datetime.now()
    generated_at = now.strftime("%Y-%m-%d %H:%M:%S")
    total = summary["total"]
    high = summary["risk_levels"].get("HIGH", 0)
    medium = summary["risk_levels"].get("MEDIUM", 0)
    low = summary["risk_levels"].get("LOW", 0)

    country_chart = _bar_chart(summary["countries"][:10], "#58a6ff")
    topic_chart = _bar_chart(summary["topics"][:8], "#d2a8ff")
    source_legend = _source_donut_html(summary["sources"])
    conflict_rows = _conflict_rows_html(summary.get("conflict_pairs", []))
    news_rows = _news_rows_html(analyzed_items)

    # compute risk donut segment percentages (conic-gradient)
    t = (total or 1)
    high_pct = high / t * 360
    med_pct = medium / t * 360
    low_pct = low / t * 360
    conic = (
        f"conic-gradient(var(--high) 0deg {high_pct:.1f}deg,"
        f"var(--medium) {high_pct:.1f}deg {high_pct+med_pct:.1f}deg,"
        f"var(--low) {high_pct+med_pct:.1f}deg 360deg)"
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>国际政治舆情简报 {generated_at}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <div>
    <h1>🌐 国际政治舆情监控</h1>
    <div class="meta">监控窗口：最近 {hours} 小时 &nbsp;·&nbsp; 生成时间：{generated_at}</div>
  </div>
  <div class="meta">NewsAgent MVP · 仅供参考</div>
</header>

<div class="container">

  <!-- Stats -->
  <div class="stats-row">
    <div class="stat-card"><div class="value">{total}</div><div class="label">📰 抓取总条目</div></div>
    <div class="stat-card high"><div class="value">{high}</div><div class="label">🔴 高风险</div></div>
    <div class="stat-card medium"><div class="value">{medium}</div><div class="label">🟠 中风险</div></div>
    <div class="stat-card low"><div class="value">{low}</div><div class="label">🟢 低风险</div></div>
    <div class="stat-card"><div class="value">{len(summary['countries'])}</div><div class="label">🌍 涉及国家</div></div>
    <div class="stat-card"><div class="value">{len(analyzed_items and [e for e in analyzed_items if e.sentiment < -0.2])}</div><div class="label">😟 负面情绪条目</div></div>
  </div>

  <!-- Charts row -->
  <div class="charts-row">
    <div class="chart-card">
      <h2>🌍 高频国家 / 地区</h2>
      {country_chart}
    </div>
    <div class="chart-card">
      <h2>🏷 议题主题分布</h2>
      {topic_chart}
    </div>
  </div>

  <div class="charts-row">
    <div class="chart-card">
      <h2>⚠ 风险等级分布</h2>
      <div class="donut-wrap">
        <div style="width:90px;height:90px;border-radius:50%;background:{conic};flex-shrink:0"></div>
        <div class="donut-legend">
          <div class="donut-legend-item"><div class="dot high"></div>高风险<span class="donut-value">{high}</span><span class="donut-pct">({high/t*100:.0f}%)</span></div>
          <div class="donut-legend-item"><div class="dot medium"></div>中风险<span class="donut-value">{medium}</span><span class="donut-pct">({medium/t*100:.0f}%)</span></div>
          <div class="donut-legend-item"><div class="dot low"></div>低风险<span class="donut-value">{low}</span><span class="donut-pct">({low/t*100:.0f}%)</span></div>
        </div>
      </div>
    </div>
    <div class="chart-card">
      <h2>📰 来源分布</h2>
      {source_legend}
    </div>
  </div>

  <!-- Conflict matrix -->
  <div class="news-card" style="margin-bottom:24px">
    <div class="section-title">⚡ 国家冲突矩阵 <span style="font-size:.8rem;color:var(--muted);font-weight:400">（高/中风险文章中国家共现频率排序）</span></div>
    <div style="overflow-x:auto">
      <table class="news-table">
        <thead>
          <tr>
            <th>#</th><th>冲突方</th><th>共现</th><th>风险</th><th>情绪</th><th>矛盾焦点</th><th>代表性标题</th>
          </tr>
        </thead>
        <tbody>
          {conflict_rows}
        </tbody>
      </table>
    </div>
  </div>

  <!-- News highlights -->
  <div class="news-card">
    <div class="section-title">🔥 高风险新闻快讯 Top 20</div>
    <div style="overflow-x:auto">
      <table class="news-table">
        <thead>
          <tr>
            <th>#</th><th>标题</th><th>来源</th><th>风险</th><th>情绪</th><th>相关国家</th><th>时间 (UTC)</th>
          </tr>
        </thead>
        <tbody>
          {news_rows}
        </tbody>
      </table>
    </div>
  </div>

</div>
<footer>NewsAgent MVP · 生成于 {generated_at} · 数据来自 RSS 公开新闻源 · 仅供学习参考，不构成投资或政策建议</footer>
</body>
</html>"""
