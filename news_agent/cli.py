from __future__ import annotations

import argparse

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .analyzer import aggregate, analyze
from .dashboard import render_dashboard
from .fetcher import fetch_news
from .report import write_reports

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="International political news monitoring agent")
    parser.add_argument("--hours", type=int, default=24, help="Lookback window in hours")
    parser.add_argument("--limit", type=int, default=80, help="Per-source max entries")
    parser.add_argument("--out-dir", type=str, default="output", help="Output directory")
    parser.add_argument(
        "--format",
        type=str,
        default="both",
        choices=["md", "json", "both"],
        help="Output format (html is always generated)",
    )
    parser.add_argument("--no-dashboard", action="store_true", help="Skip rich terminal dashboard")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        t1 = progress.add_task("📡 正在抓取 RSS 新闻…", total=None)
        items = fetch_news(hours=args.hours, per_source_limit=args.limit)
        progress.update(t1, description=f"✅ 抓取完成，政治相关 {len(items)} 条")

        t2 = progress.add_task("🧠 情绪与风险分析中…", total=None)
        analyzed_items = analyze(items)
        summary = aggregate(analyzed_items)
        progress.update(t2, description="✅ 分析完成")

        t3 = progress.add_task("📝 生成报告文件…", total=None)
        outputs = write_reports(
            summary=summary,
            analyzed_items=analyzed_items,
            out_dir=args.out_dir,
            output_format=args.format,
            hours=args.hours,
        )
        progress.update(t3, description="✅ 报告已写入")

    if not args.no_dashboard:
        render_dashboard(summary, analyzed_items, hours=args.hours)

    console.print()
    console.print("[bold green]📁 输出文件：")
    for path in outputs:
        console.print(f"   [cyan]{path}")
    console.print()


if __name__ == "__main__":
    main()
