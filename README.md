# NewsAgent: 国际政治新闻/舆情监控

一个轻量级本地工具，每日自动抓取多家国际媒体 RSS、过滤政治相关内容、评估情绪与地缘风险，并生成可视化报告。

🔗 **每日简报在线版**：[https://quokka-arch.github.io/NewsAgent/](https://quokka-arch.github.io/NewsAgent/)
📂 **历史归档**：[https://quokka-arch.github.io/NewsAgent/archive.html](https://quokka-arch.github.io/NewsAgent/archive.html)

---

## 功能概览

- 抓取 10+ 家国际媒体 RSS（BBC、Guardian、NYT、Al Jazeera、DW、France24 等）
- 过滤国际政治相关内容
- 情绪评分（VADER）+ 地缘风险评分（关键词加权）
- 按国家 / 主题聚合，检测国家间冲突对
- 生成交互式 HTML 仪表盘 / Markdown / JSON 报告

---

## 1) 安装

```bash
cd NewsAgent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) 运行

```bash
# 生成今日简报（同时输出 HTML + Markdown）
python -m news_agent.cli --hours 24 --limit 80 --out-dir output --format md

# 抓取 + 生成 + 发布到 GitHub Pages
python run_daily.py
```

可选参数：

| 参数 | 说明 | 默认值 |
|---|---|---|
| `--hours` | 回看时间窗口（小时） | `24` |
| `--limit` | 每个来源最多取条数 | `80` |
| `--out-dir` | 报告输出目录 | `output` |
| `--format` | `md` / `json` / `both` | `both` |

## 3) 输出内容

`output/` 目录生成：
- `brief_YYYYMMDD_HHMM.html` — 交互式仪表盘（Chart.js 图表、可过滤新闻表格）
- `brief_YYYYMMDD_HHMM.md` — Markdown 简报
- `brief_YYYYMMDD_HHMM.json` — 结构化数据

报告包含：风险总览、高频国家、议题分布、国家冲突矩阵、高风险新闻 Top 30。

---

## 4) 评分方法说明

### 😟 情绪分（Sentiment Score）

使用 **[VADER](https://github.com/cjhutto/vaderSentiment)**（Valence Aware Dictionary and sEntiment Reasoner），一个专为新闻/社交媒体英文文本设计的规则式情感分析库，无需 GPU 或 API。

**输入**：`标题 + 摘要`（英文原文）

**输出**：`compound` 分，范围 **−1.0 → +1.0**

| 分值区间 | 标签 |
|---|---|
| ≤ −0.6 | 😱 极负面 |
| −0.6 ~ −0.2 | 😟 负面 |
| −0.2 ~ +0.2 | 😐 中性 |
| +0.2 ~ +0.6 | 🙂 正面 |
| ≥ +0.6 | 😊 极正面 |

---

### ⚠️ 风险分（Risk Score）

纯**关键词频次加权**，无需 AI，计算公式：

```
score = (高危词命中数 × 3) + (中危词命中数 × 1) + 情绪惩罚
```

**高危词（每次命中 +3）**：
`war` · `missile` · `invasion` · `nuclear` · `airstrike` · `sanction` · `military` · `attack` · `conflict` · `blockade` · `escalation` · `coup` · `hostage`

**中危词（每次命中 +1）**：
`protest` · `tension` · `tariff` · `diplomatic` · `negotiation` · `ceasefire` · `summit` · `election` · `policy`

**情绪惩罚**（负面情绪加分）：

| 情绪分 | 额外加分 |
|---|---|
| ≤ −0.5 | +2 |
| −0.5 ~ −0.2 | +1 |

**最终等级**：

| 总分 | 等级 |
|---|---|
| ≥ 6 | 🔴 HIGH（高风险） |
| 3 ~ 5 | 🟠 MEDIUM（中风险） |
| < 3 | 🟢 LOW（低风险） |

> **局限性**：整套方案是纯规则式，无 LLM，准确性依赖关键词覆盖度。可在 `news_agent/config.py` 中自定义 RSS 源、国家词典、风险关键词。如需更高精度，可接入 OpenAI / 本地模型做二次分析。

---

## 5) 注意

- MVP 版本，适合快速监控和预警，不构成投资或政策建议。
- 情绪分析对英文文本效果最佳，中文内容会被低估。
