#!/bin/bash
set -euo pipefail
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_ROOT="${FREE_TOKEN_INTEGRATIONS_DIR:-$HOME/Documents/CYeahhOS/08_AutomationOS/Integrations}"
mkdir -p "$DEST_ROOT"
for project in free-token-hub trae-cn-bridge workbuddy-9router workdaddy-local; do
  src="$SOURCE_DIR/vendor/$project"
  dst="$DEST_ROOT/$project"
  if [ ! -d "$src" ]; then echo "缺少源码：$src" >&2; exit 1; fi
  if [ -e "$dst" ]; then
    echo "保留已有目录：$dst"
  else
    cp -R "$src" "$dst"
    echo "已安装：$dst"
  fi
done
echo "请检查 node --version >= 22；TRAE 桥接目录需运行 npm ci。"
