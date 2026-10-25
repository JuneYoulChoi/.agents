#!/bin/sh
set -eu
tool_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -x "$tool_root/.runtime/venv/bin/python" ]; then
    echo 'ROS MCP runtime is missing. Run tools/ros-mcp-server/setup.sh first.' >&2
    exit 1
fi
export PYTHONDONTWRITEBYTECODE=1
exec "$tool_root/.runtime/venv/bin/python" "$tool_root/inspect_server.py" "$@"
