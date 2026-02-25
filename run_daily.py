#!/usr/bin/env python3
"""Daily orchestrator: fetch news → generate report → publish → email.

Run manually:
    python run_daily.py

Or let launchd call it every morning at 08:00 (see install_schedule.sh).
Credentials are loaded from .env in the same directory.
"""

import sys
import subprocess
from datetime import datetime
from pathlib import Path

# ── Load .env ──────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    print("⚠️  python-dotenv 未安装，将直接读取系统环境变量")

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
PYTHON = sys.executable


def _latest_html() -> Path | None:
    files = sorted(OUTPUT_DIR.glob("*.html"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def step_fetch_and_report() -> Path:
    """Run news_agent CLI, return path to generated HTML."""
    print(f"\n{'='*55}")
    print(f"  📡 [{datetime.now():%H:%M:%S}] 抓取新闻 + 生成报告 …")
    print(f"{'='*55}")

    result = subprocess.run(
        [
            PYTHON, "-m", "news_agent.cli",
            "--hours", "24",
            "--limit", "80",
            "--out-dir", str(OUTPUT_DIR),
            "--format", "md",
            "--no-dashboard",
        ],
        cwd=ROOT,
        text=True,
    )

    if result.returncode != 0:
        print("❌ 新闻抓取/报告生成失败，退出码:", result.returncode)
        sys.exit(1)

    html = _latest_html()
    if not html:
        print("❌ output/ 目录中未找到 HTML 报告。")
        sys.exit(1)

    print(f"  📄 报告路径: {html.name}")
    return html


def step_publish(html: Path) -> None:
    """Push HTML to GitHub Pages."""
    print(f"\n{'='*55}")
    print(f"  🚀 [{datetime.now():%H:%M:%S}] 发布至 GitHub Pages …")
    print(f"{'='*55}")
    try:
        from news_agent.publisher import publish
        publish(str(html))
    except Exception as exc:
        print(f"  ⚠️  GitHub Pages 发布失败（将继续发送邮件）: {exc}")


def step_email(html: Path) -> None:
    """Send HTML report by email."""
    print(f"\n{'='*55}")
    print(f"  📬 [{datetime.now():%H:%M:%S}] 发送每日邮件 …")
    print(f"{'='*55}")
    try:
        from news_agent.mailer import send_report
        send_report(str(html))
    except Exception as exc:
        print(f"  ⚠️  邮件发送失败: {exc}")


def main() -> None:
    print(f"\n🌍 NewsAgent 每日简报任务启动  [{datetime.now():%Y-%m-%d %H:%M}]")
    html = step_fetch_and_report()
    step_publish(html)
    step_email(html)
    print(f"\n✅ 全部完成！  [{datetime.now():%H:%M:%S}]\n")


if __name__ == "__main__":
    main()
