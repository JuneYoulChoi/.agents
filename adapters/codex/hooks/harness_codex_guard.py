#!/usr/bin/env python3
"""
모듈: Codex 어댑터 (adapters/codex)
컴포넌트: 편집 가드 훅
역할: Codex PreToolUse의 apply_patch 경로를 공통 편집 가드 정책에 전달한다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from harness_edit_guard import check_edit, emit_decision

CONFIG = ".codex/harness-guard.json"
PATCH_PATH_PREFIXES = ("*** Add File: ", "*** Update File: ", "*** Delete File: ", "*** Move to: ")


def decide(event: dict, project_root: Path) -> tuple[bool, str]:
    """
    역할: apply_patch의 추가·수정·삭제·이동 경로를 모두 공통 가드 정책으로 검사한다.
    입력: event는 도구 이벤트, project_root는 훅을 등록한 작업 공간 루트다.
    출력: 허용 여부와 사유
    """
    if event.get("tool_name") != "apply_patch":
        return True, "tool is not guarded"
    tool_input = event.get("tool_input")
    patch = tool_input.get("command") if isinstance(tool_input, dict) else None
    paths = []
    if isinstance(patch, str):
        for line in patch.splitlines():
            for prefix in PATCH_PATH_PREFIXES:
                if line.startswith(prefix):
                    paths.append(line.removeprefix(prefix))
                    break
    cwd = Path(event.get("cwd") or project_root)
    return check_edit(project_root, CONFIG, cwd, [path for path in paths if path], event, "codex")


def main() -> int:
    """
    역할: 등록된 프로젝트 루트와 Codex 이벤트로 편집 도구의 실행 여부를 반환한다.
    출력: 허용이면 0, 거부이면 2
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return emit_decision(False, "unreadable Codex hook input")
    if not isinstance(event, dict):
        return emit_decision(False, "Codex hook input must be an object")
    return emit_decision(*decide(event, args.project_root))


if __name__ == "__main__":
    raise SystemExit(main())
