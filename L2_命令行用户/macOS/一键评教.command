#!/bin/bash
# ============================================================
#  评教自动化 · macOS 启动入口（L2 命令行版）
#
#  用法：双击本文件即可。若提示「无法打开，因为来自身份不明的开发者」，
#        请右键 →「打开」→ 再点「打开」；
#        或在终端执行：chmod +x 一键评教.command
#
#  本文件必须是 UTF-8 编码 + 可执行权限（chmod +x）。
# ============================================================

cd "$(dirname "$0")" || exit 1
export LANG="${LANG:-en_US.UTF-8}"
export PYTHONIOENCODING=utf-8

PY=""
if command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
fi

if [ -z "$PY" ]; then
    echo ""
    echo "  [错误] 没有找到 Python 3。"
    echo ""
    echo "  安装方法（任选其一）："
    echo "    1) 官网下载：https://www.python.org/downloads/macos/"
    echo "    2) 终端执行：brew install python"
    echo ""
    echo "  装好后重新双击本文件即可。"
    echo ""
    read -n 1 -s -r -p "  按任意键关闭窗口..."
    exit 1
fi

"$PY" launcher.py
RC=$?

echo ""
if [ "$RC" -ne 0 ]; then
    echo "  [退出码 $RC] 请看上面的提示。"
fi
read -n 1 -s -r -p "  按任意键关闭窗口..."
exit "$RC"
