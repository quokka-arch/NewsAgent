"""GitHub Pages publisher for daily news reports.

Maintains a local clone of the `quokka-arch/news-reports` repository,
copies the latest HTML report as index.html, and pushes to GitHub so
the report is visible at:  https://quokka-arch.github.io/news-reports/
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

PAGES_REPO = "quokka-arch/news-reports"
PAGES_URL = "https://quokka-arch.github.io/news-reports/"
LOCAL_CLONE = Path.home() / ".cache" / "news-agent-pages"


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


def _git(cmd: str, cwd: Path) -> str:
    return _run(f"git {cmd}", cwd=cwd)


def publish(html_path: str) -> str:
    """Push the given HTML report to GitHub Pages.

    Requires env var:
        GITHUB_TOKEN – Personal Access Token with `repo` scope
    Returns the public Pages URL.
    """
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise ValueError("请在 .env 文件中设置 GITHUB_TOKEN")

    auth_url = f"https://{token}@github.com/{PAGES_REPO}.git"
    html_path = Path(html_path)
    date_str = datetime.now().strftime("%Y%m%d_%H%M")

    # ── Ensure local clone exists ─────────────────────────────────────
    if not LOCAL_CLONE.exists():
        print(f"  📦 首次克隆 GitHub Pages 仓库 …")
        LOCAL_CLONE.parent.mkdir(parents=True, exist_ok=True)
        try:
            _run(f'git clone "{auth_url}" "{LOCAL_CLONE}"')
        except RuntimeError:
            # Repo may be empty — init a fresh local repo instead
            LOCAL_CLONE.mkdir(parents=True, exist_ok=True)
            _git("init", cwd=LOCAL_CLONE)
            _git(f'remote add origin "{auth_url}"', cwd=LOCAL_CLONE)
    else:
        # Refresh from remote (ignore error on empty repo)
        try:
            _git("pull --rebase origin main", cwd=LOCAL_CLONE)
        except RuntimeError:
            pass

    # ── Copy HTML files ───────────────────────────────────────────────
    dest_index = LOCAL_CLONE / "index.html"
    dest_archive = LOCAL_CLONE / f"report_{date_str}.html"
    shutil.copy(html_path, dest_index)
    shutil.copy(html_path, dest_archive)

    # Keep only the last 30 archived reports to avoid repo bloat
    archives = sorted(LOCAL_CLONE.glob("report_*.html"))
    for old in archives[:-30]:
        old.unlink()

    # ── Git commit & push ─────────────────────────────────────────────
    _git("config user.email 'newsagent-bot@auto'", cwd=LOCAL_CLONE)
    _git("config user.name 'NewsAgent Bot'", cwd=LOCAL_CLONE)
    _git("add -A", cwd=LOCAL_CLONE)
    try:
        _git(f'commit -m "📊 每日简报 {date_str}"', cwd=LOCAL_CLONE)
    except RuntimeError:
        print("  ℹ️  无新内容，跳过 commit")
        return PAGES_URL

    _run(f'git -C "{LOCAL_CLONE}" push "{auth_url}" HEAD:main', cwd=LOCAL_CLONE)

    print(f"  ✅ 已发布至 {PAGES_URL}")
    return PAGES_URL
