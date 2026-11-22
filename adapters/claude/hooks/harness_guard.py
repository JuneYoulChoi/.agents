#!/usr/bin/env python3
"""
모듈: Claude 어댑터 (adapters/claude)
컴포넌트: 편집 가드 훅
역할: Claude PreToolUse 편집 이벤트를 공통 편집 가드 정책에 전달한다.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from harness_edit_guard import check_edit, emit_decision

GUARDED_TOOLS = {"Edit", "Write", "NotebookEdit"}
CONFIG = ".claude/harness-guard.json"


def decide(event: dict, project_root: Path) -> tuple[bool, str]:
    """
    역할: Claude 편집 이벤트의 경로와 작업 정보를 공통 가드 정책에 전달한다.
    입력: event는 도구 이벤트, project_root는 Claude 프로젝트 루트다.
    출력: 허용 여부와 사유
    """
    if event.get("tool_name") not in GUARDED_TOOLS:
        return True, "tool is not guarded"
    tool_input = event.get("tool_input")
    raw = None
    if isinstance(tool_input, dict):
        raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    paths = [raw] if isinstance(raw, str) and raw.strip() else []
    cwd = Path(event.get("cwd") or project_root)
    return check_edit(project_root, CONFIG, cwd, paths, event, "claude")


def main() -> int:
    """
    역할: Claude 이벤트를 표준 입력으로 받아 가드 결과를 반환한다.
    출력: 허용이면 0, 거부이면 2
    """
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return emit_decision(False, "unreadable Claude hook input")
    if not isinstance(event, dict):
        return emit_decision(False, "Claude hook input must be an object")
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd())
    return emit_decision(*decide(event, root))


if __name__ == "__main__":
    raise SystemExit(main())
