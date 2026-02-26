"""GitHub Pages publisher – copies the latest report to docs/index.html
inside the NewsAgent repo itself and pushes, so it is visible at:

    https://quokka-arch.github.io/NewsAgent/
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DOCS_DIR  = REPO_ROOT / "docs"
PAGES_URL = "https://quokka-arch.github.io/NewsAgent/"


def _run(cmd: str, cwd: Path | None = None) -> str:
    """Run a shell command, raise on failure."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"命令失败: {cmd}\n--- stderr ---\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def _git(cmd: str) -> str:
    return _run(f"git {cmd}", cwd=REPO_ROOT)


def publish(html_path: str) -> str:
    """Copy HTML to docs/ and push to GitHub Pages.

    Returns the public Pages URL.
    """
    html_path = Path(html_path)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Copy to docs/ ─────────────────────────────────────────────────
    DOCS_DIR.mkdir(exist_ok=True)
    shutil.copy(html_path, DOCS_DIR / "index.html")

    # Keep an archive copy; prune to last 30
    archive_name = f"report_{html_path.stem}.html"
    shutil.copy(html_path, DOCS_DIR / archive_name)
    for old in sorted(DOCS_DIR.glob("report_*.html"))[:-30]:
        old.unlink()

    # ── Build archive index ───────────────────────────────────────────
    _write_archive_index(DOCS_DIR)

    # ── Git push ──────────────────────────────────────────────────────
    _git("config user.email 'newsagent-bot@auto'")
    _git("config user.name 'NewsAgent Bot'")
    _git("add docs/")

    try:
        _git(f'commit -m "📊 每日简报更新 {date_str}"')
    except RuntimeError:
        print("  ℹ️  docs/ 无变化，跳过 commit")
        return PAGES_URL

    try:
        _git("push origin main")
    except RuntimeError:
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if not token:
            raise ValueError("推送失败，请检查 SSH key 或设置 GITHUB_TOKEN")
        subprocess.run(
            f'git push "https://quokka-arch:{token}@github.com/quokka-arch/NewsAgent.git" main',
            shell=True, cwd=REPO_ROOT, check=True
        )

    print(f"  ✅ 已发布至 {PAGES_URL}")
    return PAGES_URL


def _write_archive_index(docs_dir: Path) -> None:
    """Generate docs/archive.html listing all past reports."""
    archives = sorted(docs_dir.glob("report_*.html"), reverse=True)
    rows = []
    for f in archives[:60]:
        name = f.stem.replace("report_brief_", "").replace("report_", "")
        rows.append(f'<li><a href="{f.name}">📄 {name}</a></li>')
    html = (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n"
        "<head><meta charset=\"utf-8\"><title>NewsAgent 历史简报</title>\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        "<style>\n"
        "body{background:#080c12;color:#d4e1f0;font-family:system-ui,sans-serif;"
        "max-width:700px;margin:60px auto;padding:0 24px}\n"
        "h1{font-size:1.4rem;margin-bottom:24px}a{color:#58a6ff}\n"
        "ul{list-style:none;padding:0}li{padding:10px 0;border-bottom:1px solid #1e2d3d}\n"
        "</style></head>\n<body>\n"
        "<h1>🌐 NewsAgent 历史简报</h1>\n"
        "<p><a href=\"index.html\">\u2190 最新简报</a></p>\n"
        f"<ul>{''.join(rows) or '<li>暂无历史记录</li>'}</ul>\n"
        "</body></html>"
    )
    (docs_dir / "archive.html").write_text(html, encoding="utf-8")
