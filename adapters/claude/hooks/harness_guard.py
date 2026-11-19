#!/usr/bin/env python3
"""
모듈: Claude 어댑터 (adapters/claude)
컴포넌트: 편집 가드 훅
역할: Claude의 PreToolUse 훅. 평소에는 휴면 상태로 모든 편집을 통과시키고, 사용자가 큰 변경에
      대해 임시 강제를 승인해 작업을 묶어 두면 그 작업이 끝날 때까지 대상 폴더의 편집을
      작업 상태에 따라 허용하거나 거부한다. 종료 코드 0은 허용, 2는 거부(사유는 stderr).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

GUARDED_TOOLS = {"Edit", "Write", "NotebookEdit"}
CONFIG = ".claude/harness-guard.json"
TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FINISHED = {"complete", "cancelled"}


def inside(parent: Path, path: Path) -> bool:
    """
    역할: 경로가 어떤 폴더 자신이거나 그 아래에 있는지 판단한다.

    입력:
        parent: 기준 폴더(절대 경로)
        path: 확인할 경로(절대 경로)
    출력:
        같거나 아래에 있으면 True
    """
    return parent == path or parent in path.parents


def project_path(root: Path, entry: str, allow_root: bool = False) -> Path:
    """
    역할: 설정에 적힌 프로젝트 기준 경로를 절대 경로로 바꾸고 프로젝트 안인지 확인한다.

    입력:
        root: 프로젝트 루트(절대 경로)
        entry: 설정에 적힌 상대 경로
        allow_root: 프로젝트 루트 자체("." )를 허용할지
    출력:
        절대 경로
    예외:
        ValueError: 절대 경로이거나 프로젝트 밖을 가리키는 경우
    """
    candidate = (root / entry).resolve()
    if Path(entry).is_absolute() or not inside(root, candidate) or (candidate == root and not allow_root):
        raise ValueError(f"{CONFIG} path must stay inside the project: {entry}")
    return candidate


def load_config(root: Path) -> dict:
    """
    역할: 프로젝트의 가드 설정(예외 경로, 임시 강제 대상 작업)을 읽고 형식을 확인한다.

    입력:
        root: 프로젝트 루트(절대 경로)
    출력:
        exempt(절대 경로 목록)와 enforce(None 또는 task_id·target 딕셔너리)를 담은 설정
    예외:
        ValueError: 파일을 읽을 수 없거나 형식이 틀린 경우
    """
    try:
        value = json.loads((root / CONFIG).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"exempt": [], "enforce": None}
    except (OSError, ValueError):
        raise ValueError(f"{CONFIG} is unreadable")
    if not isinstance(value, dict):
        raise ValueError(f"{CONFIG} must be a JSON object")
    entries = value.get("exempt_paths", [])
    if not isinstance(entries, list) or any(not isinstance(e, str) or not e.strip() for e in entries):
        raise ValueError(f"{CONFIG} exempt_paths must be an array of non-empty strings")
    enforce = value.get("enforce")
    if enforce is not None:
        if (not isinstance(enforce, dict) or not isinstance(enforce.get("task_id"), str)
                or not TASK_ID.match(enforce["task_id"]) or not isinstance(enforce.get("target_root"), str)):
            raise ValueError(f"{CONFIG} enforce needs a task_id and a target_root")
        enforce = {"task_id": enforce["task_id"],
                   "target": project_path(root, enforce["target_root"], allow_root=True)}
    return {"exempt": [project_path(root, entry) for entry in entries], "enforce": enforce}


def task_status(enforce: dict) -> str:
    """
    역할: 임시 강제에 묶인 작업의 현재 상태를 대상 폴더의 작업 상태 파일에서 읽는다.

    입력:
        enforce: task_id 와 target(대상 폴더 절대 경로)을 담은 딕셔너리
    출력:
        작업 상태 문자열. 상태 파일이 아직 없으면 not_started, 읽을 수 없으면 unreadable
    """
    state_file = enforce["target"] / ".agents" / "state" / enforce["task_id"] / "state.json"
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "not_started"
    except (OSError, ValueError):
        return "unreadable"
    status = state.get("status") if isinstance(state, dict) else None
    return status if isinstance(status, str) else "unreadable"


def decide(event: dict, project_root: Path) -> tuple[bool, str]:
    """
    역할: 편집 도구 호출 하나를 허용할지 결정한다.

    입력:
        event: 훅이 받은 도구 호출 정보(tool_name, tool_input)
        project_root: Claude 세션의 프로젝트 루트
    출력:
        (허용 여부, 사유) 쌍
    """
    if event.get("tool_name") not in GUARDED_TOOLS:
        return True, "tool is not guarded"
    root = project_root.resolve()
    try:
        config = load_config(root)
    except ValueError as exc:
        return False, f"{exc}; the project owner must fix or remove it"  # 깨진 설정은 허용이 아니라 거부
    enforce = config["enforce"]
    if enforce is None:
        return True, "dormant: no task is under temporary enforcement"
    status = task_status(enforce)
    if status in FINISHED:
        return True, f"dormant: task {enforce['task_id']} is {status}"
    tool_input = event.get("tool_input") or {}
    raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(raw, str) or not raw:
        return False, "edit has no file path to check"
    path = Path(raw)
    path = (path if path.is_absolute() else root / path).resolve()
    if path == (root / CONFIG).resolve():
        return False, f"{CONFIG} cannot change while task {enforce['task_id']} is under enforcement"
    target = enforce["target"]
    if not inside(target, path):
        return True, "path is outside the enforced target"
    if inside(target / ".agents" / "state", path):
        return True, "task state write"
    if any(inside(item, path) for item in config["exempt"]):
        return True, "exempt path"
    if status == "active":
        return True, f"active task {enforce['task_id']}"
    hints = {
        "not_started": "start it with harness_runner.py (enforcement_mode: hook) before editing",
        "waiting_user": "a user decision is pending; record it with harness_runner.py resume",
        "blocked": "it is blocked; resolve the blocker and resume",
        "failed": "it failed; restart through a linked intake or ask the project owner to clear enforcement",
    }
    return False, f"task {enforce['task_id']} is {status}: {hints.get(status, 'its state cannot be read')}"


def main() -> int:
    """
    역할: 표준 입력의 훅 JSON을 읽어 판정하고 종료 코드로 알린다.

    출력:
        종료 코드. 허용 0, 거부 2
    """
    try:
        event = json.load(sys.stdin)
    except ValueError:
        sys.stderr.write("harness_guard: unreadable hook input; edit denied\n")
        return 2
    event = event if isinstance(event, dict) else {}
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd())
    allowed, reason = decide(event, root)
    if allowed:
        return 0
    sys.stderr.write(f"harness_guard: {reason}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
