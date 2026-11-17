#!/bin/bash
set -euo pipefail
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_BIN="$(command -v node || true)"
if [ -z "$NODE_BIN" ]; then echo "未找到 node，请先安装 Node.js 22+" >&2; exit 1; fi
mkdir -p "$HOME/Library/LaunchAgents"
for name in com.cyeahh.workdaddy com.cyeahh.workbuddy-9router; do
  src="$SOURCE_DIR/launch-agents/$name.xml"
  dst="$HOME/Library/LaunchAgents/$name.plist"
  sed -e "s|__HOME__|$HOME|g" -e "s|__NODE__|$NODE_BIN|g" "$src" > "$dst"
  chmod 600 "$dst"
  echo "已生成：${dst}（未自动加载）"
done
echo "本人确认后可用 launchctl bootstrap gui/\$(id -u) <plist> 加载。"
