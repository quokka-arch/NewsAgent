#!/bin/bash
# install_schedule.sh – 注册 macOS launchd 每日定时任务
# 用法：bash install_schedule.sh

set -e
PLIST_SRC="$(dirname "$0")/com.newsagent.daily.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.newsagent.daily.plist"
LABEL="com.newsagent.daily"
LOG_DIR="$(dirname "$0")/logs"

echo "🔧 安装 NewsAgent 每日定时任务（每天 08:00）…"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 卸载旧任务（如果存在）
launchctl unload "$PLIST_DST" 2>/dev/null || true

# 复制 plist 到 LaunchAgents
cp "$PLIST_SRC" "$PLIST_DST"
echo "  ✅ plist 已复制至 $PLIST_DST"

# 加载任务
launchctl load "$PLIST_DST"
echo "  ✅ 任务已注册"

echo ""
echo "📋 状态查询：  launchctl list | grep newsagent"
echo "🧪 立即测试：  launchctl start $LABEL"
echo "🗑  取消定时：  launchctl unload $PLIST_DST && rm $PLIST_DST"
echo "📄 查看日志：  tail -f $LOG_DIR/daily.log"
