"""Generate a rich self-contained HTML report with Chart.js interactive visualizations."""
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
    "India": "🇮🇳", "Taiwan": "🇹🇼", "Saudi Arabia": "🇸🇦", "Cuba": "🇨🇺",
    "Turkey": "🇹🇷", "North Korea": "🇰🇵", "Syria": "🇸🇾", "Iraq": "🇮🇶",
}


def _flag(name: str) -> str:
    return _COUNTRY_FLAG.get(name, "🌐")


_RISK_BADGE = {
    "HIGH": ('<span class="badge high">高风险</span>', "#ff4d4d"),
    "MEDIUM": ('<span class="badge medium">中风险</span>', "#ffa64d"),
    "LOW": ('<span class="badge low">低风险</span>', "#52c41a"),
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


def _coverage_badge(n: int) -> str:
    """Return a small badge showing cross-source coverage count."""
    if n == 0:
        return '<span class="cvg cvg0">独家</span>'
    if n == 1:
        return f'<span class="cvg cvg1">+{n} 家</span>'
    if n <= 3:
        return f'<span class="cvg cvg2">+{n} 家</span>'
    return f'<span class="cvg cvg3">+{n} 家 🔥</span>'


def _news_rows_html(analyzed_items: list[AnalyzedItem], n: int = 30) -> str:
    top = [e for e in analyzed_items if e.risk_level in {"HIGH", "MEDIUM"}][:n]
    if not top:
        top = analyzed_items[:n]
    rows = []
    for idx, entry in enumerate(top, start=1):
        badge_html, _ = _RISK_BADGE[entry.risk_level]
        senti_label, senti_color = _senti_info(entry.sentiment)
        bar_pct = int((entry.sentiment + 1) / 2 * 100)
        countries_html = " ".join(
            f'<span class="ctag">{html.escape(_flag(c))} {html.escape(_t_country(c))}</span>'
            for c in entry.countries[:4]
        ) or "—"
        ts = entry.item.published_at.strftime("%m-%d %H:%M")
        title_esc = html.escape(entry.item.title[:90])
        link = html.escape(entry.item.link)
        risk_cls = entry.risk_level.lower()
        imp = f"{entry.importance_score:.0f}"
        cvg = _coverage_badge(entry.cross_source_count)
        rows.append(
            f"""<tr class="nr" data-risk="{entry.risk_level}">
  <td class="dim" style="text-align:center">
    <div style="font-weight:700;font-size:.95rem;color:var(--blue)">{imp}</div>
    <div class="dim" style="font-size:.7rem">重要分</div>
  </td>
  <td>
    <a href="{link}" target="_blank" class="ntitle">{title_esc}</a>
    <div style="margin-top:3px">{cvg}</div>
  </td>
  <td class="src">{html.escape(entry.item.source)}</td>
  <td><span class="badge {risk_cls}">{_t_risk(entry.risk_level)}</span></td>
  <td>
    <div class="senti-wrap">
      <span style="color:{senti_color};font-size:.78rem;font-weight:600">{senti_label}</span>
      <div class="senti-track"><div class="senti-fill" style="width:{bar_pct}%;background:{senti_color}"></div></div>
      <span class="dim" style="font-size:.72rem">{entry.sentiment:+.2f}</span>
    </div>
  </td>
  <td class="ctags">{countries_html}</td>
  <td class="ts">{ts}</td>
</tr>"""
        )
    return "\n".join(rows)


def _conflict_rows_html(conflict_pairs: list[dict]) -> str:
    if not conflict_pairs:
        return '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:20px">当前窗口未检测到国家间冲突信号</td></tr>'
    rows = []
    for i, entry in enumerate(conflict_pairs[:12], 1):
        a, b = entry["pair"]
        avg_risk = entry["avg_risk"]
        if avg_risk >= 6:
            risk_color, risk_icon = "var(--red)", "🔴"
        elif avg_risk >= 3:
            risk_color, risk_icon = "var(--orange)", "🟠"
        else:
            risk_color, risk_icon = "var(--green)", "🟢"
        senti = entry["avg_sentiment"]
        _, s_color = _senti_info(senti)
        topics_str = html.escape(" · ".join(_t_topic(t) for t in entry["topics"][:2]) or "—")
        headline = html.escape(entry["headlines"][0][:55]) if entry["headlines"] else "—"
        a_zh, b_zh = _t_country(a), _t_country(b)
        heat = min(int(entry["count"] / 15 * 100), 100)
        rows.append(f"""
<tr>
  <td class="dim" style="text-align:center">{i}</td>
  <td style="white-space:nowrap">
    <span class="flag-pair">{_flag(a)}<strong>{html.escape(a_zh)}</strong>
    <span class="vs">↔</span>
    {_flag(b)}<strong>{html.escape(b_zh)}</strong></span>
  </td>
  <td style="text-align:center">
    <div class="heat-bar"><div class="heat-fill" style="width:{heat}%;background:{risk_color}"></div></div>
    <span style="font-weight:700">{entry['count']}</span>
  </td>
  <td style="text-align:center;color:{risk_color};font-weight:700">{risk_icon} {avg_risk:.1f}</td>
  <td style="text-align:center;color:{s_color};font-weight:600">{senti:+.2f}</td>
  <td class="dim" style="font-size:.8rem">{topics_str}</td>
</tr>""")
    return "\n".join(rows)


def generate_html(summary: dict, analyzed_items: list[AnalyzedItem], hours: int) -> str:
    now = datetime.now()
    generated_at = now.strftime("%Y-%m-%d %H:%M:%S")
    total = summary["total"]
    high = summary["risk_levels"].get("HIGH", 0)
    medium = summary["risk_levels"].get("MEDIUM", 0)
    low = summary["risk_levels"].get("LOW", 0)
    t = total or 1

    neg_count = len([e for e in analyzed_items if e.sentiment < -0.2])
    country_count = len(summary["countries"])

    # Chart.js data
    country_labels = json.dumps([_t_country(c) + " " + _flag(c) for c, _ in summary["countries"][:10]])
    country_values = json.dumps([v for _, v in summary["countries"][:10]])

    topic_labels = json.dumps([_t_topic(t) for t, _ in summary["topics"][:7]])
    topic_values = json.dumps([v for _, v in summary["topics"][:7]])

    source_labels = json.dumps([s for s, _ in summary["sources"][:6]])
    source_values = json.dumps([v for _, v in summary["sources"][:6]])

    conflict_rows = _conflict_rows_html(summary.get("conflict_pairs", []))
    news_rows = _news_rows_html(analyzed_items)

    # avg sentiment
    sentiments = [e.sentiment for e in analyzed_items]
    avg_senti = sum(sentiments) / len(sentiments) if sentiments else 0
    avg_label, avg_color = _senti_info(avg_senti)
    senti_pct = int((avg_senti + 1) / 2 * 100)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>🌐 政治舆情简报 · {generated_at[:10]}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg: #080c12;
  --surface: #0f1620;
  --surface2: #151e2b;
  --border: #1e2d3d;
  --text: #d4e1f0;
  --muted: #6a849e;
  --red: #f85149;
  --orange: #e3a04f;
  --green: #3fb950;
  --blue: #58a6ff;
  --purple: #bc8cff;
  --teal: #39d5c9;
  --glow-red: rgba(248,81,73,.25);
  --glow-blue: rgba(88,166,255,.15);
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
body {{ background: var(--bg); color: var(--text); font-family: -apple-system, 'SF Pro Display', 'Segoe UI', system-ui, sans-serif; font-size: 14px; line-height: 1.6; }}
a {{ color: var(--blue); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

/* ── NAV ── */
nav {{
  position: sticky; top: 0; z-index: 100;
  background: rgba(8,12,18,.88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
  padding: 0 32px;
  display: flex; align-items: center; justify-content: space-between; height: 56px;
}}
.nav-brand {{ display: flex; align-items: center; gap: 10px; }}
.nav-brand .logo {{ font-size: 1.25rem; font-weight: 700; letter-spacing: -.02em; }}
.nav-brand .badge-pill {{ background: var(--glow-red); color: var(--red); border: 1px solid var(--red); padding: 2px 8px; border-radius: 20px; font-size: .72rem; font-weight: 600; }}
.nav-meta {{ color: var(--muted); font-size: .8rem; }}
.nav-links {{ display: flex; gap: 20px; }}
.nav-links a {{ color: var(--muted); font-size: .82rem; transition: color .2s; }}
.nav-links a:hover {{ color: var(--text); text-decoration: none; }}

/* ── LAYOUT ── */
.page {{ max-width: 1440px; margin: 0 auto; padding: 28px 32px; }}

/* ── STAT CARDS ── */
.stats-grid {{
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
  margin-bottom: 28px;
}}
@media (max-width: 1100px) {{ .stats-grid {{ grid-template-columns: repeat(3, 1fr); }} }}
@media (max-width: 640px)  {{ .stats-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
.stat-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 18px 20px;
  position: relative;
  overflow: hidden;
  transition: border-color .2s, transform .2s;
}}
.stat-card:hover {{ border-color: #2e4a66; transform: translateY(-2px); }}
.stat-card::before {{
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
}}
.stat-card.total::before {{ background: linear-gradient(90deg,var(--blue),var(--purple)); }}
.stat-card.high::before  {{ background: var(--red); }}
.stat-card.medium::before{{ background: var(--orange); }}
.stat-card.low::before   {{ background: var(--green); }}
.stat-card.country::before{{ background: var(--teal); }}
.stat-card.neg::before   {{ background: var(--purple); }}
.stat-card .icon {{ font-size: 1.6rem; margin-bottom: 8px; display: block; }}
.stat-card .num {{ font-size: 2.2rem; font-weight: 800; letter-spacing: -.04em; line-height: 1; }}
.stat-card .lbl {{ color: var(--muted); font-size: .78rem; margin-top: 6px; }}
.stat-card.total  .num {{ color: var(--blue); }}
.stat-card.high   .num {{ color: var(--red); }}
.stat-card.medium .num {{ color: var(--orange); }}
.stat-card.low    .num {{ color: var(--green); }}
.stat-card.country.num {{ color: var(--teal); }}
.stat-card.neg    .num {{ color: var(--purple); }}

/* ── SENTIMENT METER ── */
.senti-meter-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 28px;
  display: flex; align-items: center; gap: 32px; flex-wrap: wrap;
}}
.senti-meter-title {{ font-size: .78rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-bottom: 8px; }}
.senti-track-big {{ flex: 1; min-width: 200px; height: 10px; background: linear-gradient(to right, #f85149, #e3a04f 40%, #3fb950); border-radius: 5px; position: relative; }}
.senti-needle {{ position: absolute; top: -5px; width: 4px; height: 20px; background: white; border-radius: 2px; transform: translateX(-50%); box-shadow: 0 0 8px rgba(255,255,255,.6); transition: left .8s cubic-bezier(.34,1.56,.64,1); }}

/* ── CHART GRID ── */
.charts-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 14px;
  margin-bottom: 28px;
}}
@media (max-width: 1100px) {{ .charts-grid {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 700px)  {{ .charts-grid {{ grid-template-columns: 1fr; }} }}
.chart-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  transition: border-color .2s;
}}
.chart-card:hover {{ border-color: #2e4a66; }}
.chart-card.wide {{ grid-column: span 2; }}
@media (max-width: 1100px) {{ .chart-card.wide {{ grid-column: span 1; }} }}
.card-title {{
  font-size: .72rem; font-weight: 600;
  color: var(--muted); text-transform: uppercase; letter-spacing: .1em;
  margin-bottom: 16px;
  display: flex; align-items: center; gap: 6px;
}}
.card-title .dot {{ width: 6px; height: 6px; border-radius: 50%; }}

/* ── CONFLICT TABLE ── */
.section-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}}
.section-hd {{
  font-size: 1rem; font-weight: 700;
  margin-bottom: 16px;
  display: flex; align-items: center; gap: 8px;
}}
.section-hd .sub {{ font-size: .75rem; color: var(--muted); font-weight: 400; }}
table.dtable {{ width: 100%; border-collapse: collapse; font-size: .83rem; }}
table.dtable th {{
  background: var(--surface2); color: var(--muted);
  text-align: left; padding: 9px 12px;
  font-weight: 500; white-space: nowrap;
  border-bottom: 1px solid var(--border);
}}
table.dtable td {{ padding: 9px 12px; border-bottom: 1px solid #131c26; vertical-align: middle; }}
table.dtable tr:hover td {{ background: var(--surface2); }}
.heat-bar {{ width: 100%; height: 4px; background: var(--border); border-radius: 2px; margin-bottom: 3px; }}
.heat-fill {{ height: 4px; border-radius: 2px; }}
.flag-pair {{ display: flex; align-items: center; gap: 4px; }}
.vs {{ color: var(--muted); padding: 0 4px; }}

/* ── NEWS TABLE ── */
.filter-bar {{ display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }}
.fbtn {{
  padding: 5px 14px; border-radius: 20px; border: 1px solid var(--border);
  background: var(--surface2); color: var(--muted); font-size: .78rem;
  cursor: pointer; transition: all .15s;
}}
.fbtn:hover, .fbtn.active {{ color: var(--text); border-color: var(--blue); background: var(--glow-blue); }}
.fbtn.active.h {{ border-color: var(--red);  background: rgba(248,81,73,.1);  color: var(--red); }}
.fbtn.active.m {{ border-color: var(--orange); background: rgba(227,160,79,.1); color: var(--orange); }}
.fbtn.active.l {{ border-color: var(--green); background: rgba(63,185,80,.1);  color: var(--green); }}
.search-box {{
  margin-left: auto;
  padding: 5px 12px; border-radius: 20px;
  border: 1px solid var(--border); background: var(--surface2);
  color: var(--text); font-size: .8rem; outline: none; width: 200px;
  transition: border-color .2s;
}}
.search-box:focus {{ border-color: var(--blue); }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: .72rem; font-weight: 700; letter-spacing: .04em; white-space: nowrap; }}
.badge.high   {{ background: rgba(248,81,73,.15);  color: var(--red);    border: 1px solid rgba(248,81,73,.4); }}
.badge.medium {{ background: rgba(227,160,79,.15); color: var(--orange); border: 1px solid rgba(227,160,79,.4); }}
.badge.low    {{ background: rgba(63,185,80,.15);  color: var(--green);  border: 1px solid rgba(63,185,80,.4); }}
.ntitle {{ font-size: .84rem; }}
.src {{ color: var(--muted); font-size: .76rem; white-space: nowrap; }}
.ts  {{ color: var(--muted); font-size: .76rem; white-space: nowrap; }}
.dim {{ color: var(--muted); }}
.ctags {{ white-space: nowrap; }}
.ctag {{
  display: inline-block; background: rgba(88,166,255,.1); color: var(--blue);
  border-radius: 3px; padding: 1px 5px; font-size: .72rem; margin: 1px 2px;
}}
.senti-wrap {{ display: flex; flex-direction: column; gap: 2px; min-width: 80px; }}
.senti-track {{ height: 3px; background: var(--border); border-radius: 2px; overflow: hidden; }}
.senti-fill  {{ height: 3px; border-radius: 2px; transition: width .4s; }}
/* Coverage badge */
.cvg {{ display:inline-block; padding:1px 6px; border-radius:3px; font-size:.7rem; font-weight:600; }}
.cvg0 {{ background:rgba(107,127,150,.15); color:var(--muted); }}
.cvg1 {{ background:rgba(88,166,255,.12); color:var(--blue); }}
.cvg2 {{ background:rgba(188,140,255,.15); color:var(--purple); }}
.cvg3 {{ background:rgba(248,81,73,.15);  color:var(--red); }}
/* ── FOOTER ── */
footer {{ text-align: center; color: var(--muted); font-size: .76rem; padding: 32px; border-top: 1px solid var(--border); margin-top: 8px; }}
footer a {{ color: var(--muted); }}

/* ── SCROLLBAR ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

/* ── ANIMATED COUNTER ── */
@keyframes countUp {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
.num {{ animation: countUp .5s ease both; }}
</style>
</head>
<body>

<nav>
  <div class="nav-brand">
    <span class="logo">🌐 NewsAgent</span>
    <span class="badge-pill">LIVE</span>
  </div>
  <div class="nav-links">
    <a href="#overview">总览</a>
    <a href="#charts">图表</a>
    <a href="#conflict">冲突矩阵</a>
    <a href="#news">新闻快讯</a>
  </div>
  <div class="nav-meta">监控窗口 {hours}h · 生成于 {generated_at}</div>
</nav>

<div class="page">

  <!-- STAT CARDS -->
  <div id="overview" class="stats-grid">
    <div class="stat-card total">
      <span class="icon">📰</span>
      <div class="num">{total}</div>
      <div class="lbl">抓取条目总数</div>
    </div>
    <div class="stat-card high">
      <span class="icon">🔴</span>
      <div class="num">{high}</div>
      <div class="lbl">高风险 ({high/t*100:.0f}%)</div>
    </div>
    <div class="stat-card medium">
      <span class="icon">🟠</span>
      <div class="num">{medium}</div>
      <div class="lbl">中风险 ({medium/t*100:.0f}%)</div>
    </div>
    <div class="stat-card low">
      <span class="icon">🟢</span>
      <div class="num">{low}</div>
      <div class="lbl">低风险 ({low/t*100:.0f}%)</div>
    </div>
    <div class="stat-card country">
      <span class="icon">🌍</span>
      <div class="num" style="color:var(--teal)">{country_count}</div>
      <div class="lbl">涉及国家/地区</div>
    </div>
    <div class="stat-card neg">
      <span class="icon">😟</span>
      <div class="num" style="color:var(--purple)">{neg_count}</div>
      <div class="lbl">负面情绪条目</div>
    </div>
  </div>

  <!-- SENTIMENT METER -->
  <div class="senti-meter-card">
    <div>
      <div class="senti-meter-title">整体情绪指数</div>
      <div style="font-size:1.5rem;font-weight:700;color:{avg_color}">{avg_label} &nbsp;<span style="font-size:.9rem">{avg_senti:+.3f}</span></div>
    </div>
    <div style="flex:1;min-width:220px">
      <div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--muted);margin-bottom:4px"><span>极负面 −1</span><span>中性</span><span>极正面 +1</span></div>
      <div class="senti-track-big">
        <div class="senti-needle" id="sentiNeedle" style="left:{senti_pct}%"></div>
      </div>
    </div>
    <div style="display:flex;gap:16px;flex-wrap:wrap">
      <div style="text-align:center"><div style="font-size:1.2rem;font-weight:700;color:var(--red)">{high}</div><div style="font-size:.72rem;color:var(--muted)">高风险</div></div>
      <div style="text-align:center"><div style="font-size:1.2rem;font-weight:700;color:var(--orange)">{medium}</div><div style="font-size:.72rem;color:var(--muted)">中风险</div></div>
      <div style="text-align:center"><div style="font-size:1.2rem;font-weight:700;color:var(--green)">{low}</div><div style="font-size:.72rem;color:var(--muted)">低风险</div></div>
    </div>
  </div>

  <!-- CHARTS -->
  <div id="charts" class="charts-grid">

    <!-- Risk Donut -->
    <div class="chart-card">
      <div class="card-title"><div class="dot" style="background:var(--red)"></div>风险等级分布</div>
      <canvas id="riskChart" height="220"></canvas>
    </div>

    <!-- Country Bar -->
    <div class="chart-card wide">
      <div class="card-title"><div class="dot" style="background:var(--blue)"></div>高频国家 / 地区 Top 10</div>
      <canvas id="countryChart" height="220"></canvas>
    </div>

    <!-- Source Donut -->
    <div class="chart-card">
      <div class="card-title"><div class="dot" style="background:var(--teal)"></div>新闻来源分布</div>
      <canvas id="sourceChart" height="220"></canvas>
    </div>

    <!-- Topic Radar -->
    <div class="chart-card">
      <div class="card-title"><div class="dot" style="background:var(--purple)"></div>议题主题分布</div>
      <canvas id="topicChart" height="220"></canvas>
    </div>

    <!-- Source Bar -->
    <div class="chart-card">
      <div class="card-title"><div class="dot" style="background:var(--orange)"></div>来源条目数量</div>
      <canvas id="sourceBarChart" height="220"></canvas>
    </div>

  </div>

  <!-- CONFLICT MATRIX -->
  <div id="conflict" class="section-card">
    <div class="section-hd">⚡ 国家冲突矩阵 <span class="sub">高/中风险文章中国家共现频率排序</span></div>
    <div style="overflow-x:auto">
      <table class="dtable">
        <thead>
          <tr>
            <th>#</th><th>冲突方</th><th>共现次数</th><th>均风险</th><th>均情绪</th><th>矛盾焦点</th>
          </tr>
        </thead>
        <tbody>{conflict_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- NEWS TABLE -->
  <div id="news" class="section-card">
    <div class="section-hd">🔥 高/中风险新闻 Top 30</div>
    <div class="filter-bar">
      <button class="fbtn active" onclick="filterNews('ALL',this)">全部</button>
      <button class="fbtn h"      onclick="filterNews('HIGH',this)">🔴 高风险</button>
      <button class="fbtn m"      onclick="filterNews('MEDIUM',this)">🟠 中风险</button>
      <button class="fbtn l"      onclick="filterNews('LOW',this)">🟢 低风险</button>
      <input class="search-box" type="text" placeholder="搜索标题 / 来源…" oninput="searchNews(this.value)" />
    </div>
    <div style="overflow-x:auto">
      <table class="dtable" id="newsTable">
        <thead>
          <tr>
            <th title="重要分 = 风险分×3 + 跨媒体覆盖数×2">重要分 ↓</th><th>标题 / 覆盖媒体数</th><th>来源</th><th>风险</th><th>情绪</th><th>相关国家</th><th>时间(UTC)</th>
          </tr>
        </thead>
        <tbody id="newsTbody">
          {news_rows}
        </tbody>
      </table>
    </div>
    <div id="noResults" style="display:none;text-align:center;padding:24px;color:var(--muted)">无匹配结果</div>
  </div>

</div>

<footer>
  NewsAgent · 生成于 {generated_at} · 数据来源 RSS 公开新闻源 · 仅供参考，不构成投资或政策建议
</footer>

<script>
// ── Chart.js global defaults ──────────────────────────────────────────────
Chart.defaults.color = '#6a849e';
Chart.defaults.font.family = "-apple-system,'SF Pro Display','Segoe UI',system-ui,sans-serif";
Chart.defaults.font.size = 12;

// ── Risk Donut ────────────────────────────────────────────────────────────
new Chart(document.getElementById('riskChart'), {{
  type: 'doughnut',
  data: {{
    labels: ['高风险', '中风险', '低风险'],
    datasets: [{{ data: [{high},{medium},{low}], backgroundColor: ['#f85149','#e3a04f','#3fb950'], borderWidth: 0, hoverOffset: 8 }}]
  }},
  options: {{
    cutout: '72%', plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 16 }} }}, tooltip: {{ callbacks: {{ label: c => ` ${{c.label}}: ${{c.raw}} (${{(c.raw/{t}*100).toFixed(1)}}%)` }} }} }},
    animation: {{ animateRotate: true, duration: 900 }}
  }}
}});

// ── Country Horizontal Bar ────────────────────────────────────────────────
new Chart(document.getElementById('countryChart'), {{
  type: 'bar',
  data: {{
    labels: {country_labels},
    datasets: [{{ label: '提及次数', data: {country_values},
      backgroundColor: 'rgba(88,166,255,0.7)', borderColor: '#58a6ff', borderWidth: 1, borderRadius: 4
    }}]
  }},
  options: {{
    indexAxis: 'y',
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: '#1e2d3d' }}, ticks: {{ color: '#6a849e' }} }},
      y: {{ grid: {{ display: false }}, ticks: {{ color: '#d4e1f0' }} }}
    }},
    animation: {{ duration: 900 }}
  }}
}});

// ── Source Donut ─────────────────────────────────────────────────────────
new Chart(document.getElementById('sourceChart'), {{
  type: 'doughnut',
  data: {{
    labels: {source_labels},
    datasets: [{{ data: {source_values},
      backgroundColor: ['#58a6ff','#3fb950','#e3a04f','#f85149','#bc8cff','#39d5c9'],
      borderWidth: 0, hoverOffset: 6
    }}]
  }},
  options: {{
    cutout: '65%', plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 14 }} }} }},
    animation: {{ duration: 900 }}
  }}
}});

// ── Topic Radar ───────────────────────────────────────────────────────────
new Chart(document.getElementById('topicChart'), {{
  type: 'radar',
  data: {{
    labels: {topic_labels},
    datasets: [{{ label: '条目数', data: {topic_values},
      backgroundColor: 'rgba(188,140,255,0.2)', borderColor: '#bc8cff',
      borderWidth: 2, pointBackgroundColor: '#bc8cff', pointRadius: 3
    }}]
  }},
  options: {{
    scales: {{ r: {{ grid: {{ color: '#1e2d3d' }}, angleLines: {{ color: '#1e2d3d' }}, ticks: {{ display: false }} }} }},
    plugins: {{ legend: {{ display: false }} }},
    animation: {{ duration: 900 }}
  }}
}});

// ── Source Bar ────────────────────────────────────────────────────────────
new Chart(document.getElementById('sourceBarChart'), {{
  type: 'bar',
  data: {{
    labels: {source_labels},
    datasets: [{{ label: '条目数', data: {source_values},
      backgroundColor: ['rgba(57,213,201,.7)','rgba(57,213,201,.55)','rgba(57,213,201,.45)','rgba(57,213,201,.38)','rgba(57,213,201,.3)','rgba(57,213,201,.22)'],
      borderRadius: 4, borderWidth: 0
    }}]
  }},
  options: {{
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ display: false }}, ticks: {{ color: '#6a849e', maxRotation: 30 }} }},
      y: {{ grid: {{ color: '#1e2d3d' }}, ticks: {{ color: '#6a849e' }} }}
    }},
    animation: {{ duration: 900 }}
  }}
}});

// ── News filter & search ──────────────────────────────────────────────────
function filterNews(level, btn) {{
  document.querySelectorAll('.fbtn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const rows = document.querySelectorAll('#newsTbody .nr');
  let shown = 0;
  rows.forEach(r => {{
    const show = level === 'ALL' || r.dataset.risk === level;
    r.style.display = show ? '' : 'none';
    if (show) shown++;
  }});
  document.getElementById('noResults').style.display = shown ? 'none' : '';
}}

function searchNews(q) {{
  const lq = q.toLowerCase();
  const rows = document.querySelectorAll('#newsTbody .nr');
  let shown = 0;
  rows.forEach(r => {{
    const text = r.textContent.toLowerCase();
    const show = text.includes(lq);
    r.style.display = show ? '' : 'none';
    if (show) shown++;
  }});
  document.getElementById('noResults').style.display = shown ? 'none' : '';
}}

// ── Animate sentiment needle ──────────────────────────────────────────────
window.addEventListener('load', () => {{
  const needle = document.getElementById('sentiNeedle');
  if (needle) {{ needle.style.left = '{senti_pct}%'; }}
}});
</script>
</body>
</html>"""
