# NewsAgent: 国际政治新闻/舆情监控（MVP）

一个轻量级本地工具：
- 抓取多家国际媒体 RSS 新闻
- 过滤国际政治相关内容
- 做基础情绪评分（VADER）
- 计算地缘风险强度并按国家/主题聚合
- 生成 Markdown / JSON 报告

## 1) 安装

```bash
cd NewsAgent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) 运行

```bash
python -m news_agent.cli --hours 24 --limit 80 --out-dir output --format both
```

可选参数：
- `--hours`: 回看多少小时（默认 `24`）
- `--limit`: 每个来源最多取多少条（默认 `80`）
- `--out-dir`: 报告输出目录（默认 `output`）
- `--format`: `md` / `json` / `both`（默认 `both`）

## 3) 输出内容

默认会在 `output/` 生成：
- `brief_YYYYMMDD_HHMM.md`
- `brief_YYYYMMDD_HHMM.json`

报告包含：
- 风险总览（高/中/低）
- 高频国家提及
- 高频主题
- 高风险新闻 Top N（含情绪分）

## 4) 注意

- 这是 MVP，适合快速监控和预警，不是投资或政策建议。
- 情绪分析主要对英文文本更有效。
- 可在 `news_agent/config.py` 中扩展 RSS 源、国家词典、风险关键词。
