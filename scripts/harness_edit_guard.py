"""
모듈: 하네스 런타임 (scripts)
컴포넌트: 편집 가드 정책
역할: 두 어댑터의 편집 경로와 작업 연동을 공통 규칙으로 판단하고 호스트의 거부 관찰을 기록한다.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from harness_validator import root_fingerprint

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


def project_path(root: Path, entry: str, config_path: str, allow_root: bool = False) -> Path:
    """
    역할: 설정에 적힌 프로젝트 기준 경로를 절대 경로로 바꾸고 프로젝트 안인지 확인한다.

    입력:
        root: 프로젝트 루트(절대 경로)
        entry: 설정에 적힌 상대 경로
        config_path: 어댑터 가드 설정 경로
        allow_root: 프로젝트 루트 자체("." )를 허용할지
    출력:
        절대 경로
    예외:
        ValueError: 절대 경로이거나 프로젝트 밖을 가리키는 경우
    """
    candidate = (root / entry).resolve()
    if Path(entry).is_absolute() or not inside(root, candidate) or (candidate == root and not allow_root):
        raise ValueError(f"{config_path} path must stay inside the project: {entry}")
    return candidate


def load_config(root: Path, config_path: str) -> dict:
    """
    역할: 프로젝트의 가드 설정(예외 경로, 임시 강제 대상 작업)을 읽고 형식을 확인한다.

    입력:
        root: 프로젝트 루트(절대 경로)
        config_path: 프로젝트 기준 설정 경로
    출력:
        exempt(절대 경로 목록)와 enforce(None 또는 task_id·target 딕셔너리)를 담은 설정
    예외:
        ValueError: 파일을 읽을 수 없거나 형식이 틀린 경우
    """
    try:
        value = json.loads((root / config_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"exempt": [], "enforce": None}
    except (OSError, ValueError):
        raise ValueError(f"{config_path} is unreadable")
    if not isinstance(value, dict):
        raise ValueError(f"{config_path} must be a JSON object")
    entries = value.get("exempt_paths", [])
    if not isinstance(entries, list) or any(not isinstance(e, str) or not e.strip() for e in entries):
        raise ValueError(f"{config_path} exempt_paths must be an array of non-empty strings")
    enforce = value.get("enforce")
    if enforce is not None:
        if (not isinstance(enforce, dict) or not isinstance(enforce.get("task_id"), str)
                or not TASK_ID.match(enforce["task_id"]) or not isinstance(enforce.get("target_root"), str)):
            raise ValueError(f"{config_path} enforce needs a task_id and a target_root")
        enforce = {"task_id": enforce["task_id"],
                   "target": project_path(root, enforce["target_root"], config_path, allow_root=True),
                   "approval_id": enforce.get("approval_id")}
    return {"exempt": [project_path(root, entry, config_path) for entry in entries], "enforce": enforce}


def task_status(enforce: dict) -> tuple[str, int | None]:
    """
    역할: 임시 강제에 묶인 작업의 현재 상태를 대상 폴더의 작업 상태 파일에서 읽는다.

    입력:
        enforce: task_id 와 target(대상 폴더 절대 경로)을 담은 딕셔너리
    출력:
        작업 상태와 리비전. 시작 전에는 (not_started, 0), 읽을 수 없으면 (unreadable, None)
    """
    state_file = enforce["target"] / ".agents" / "state" / enforce["task_id"] / "state.json"
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "not_started", 0
    except (OSError, ValueError):
        return "unreadable", None
    if not isinstance(state, dict) or state.get("task_id") != enforce["task_id"]:
        return "unreadable", None
    fingerprint = state.get("target_root_fingerprint")
    if fingerprint is not None and fingerprint != root_fingerprint(enforce["target"]):
        return "unreadable", None
    status = state.get("status")
    if not isinstance(status, str):
        return "unreadable", None
    execution = state.get("execution")
    operator = execution.get("operator") if isinstance(execution, dict) else None
    if status == "active" and isinstance(operator, dict) and not operator.get("opened"):
        return "checkpoint_pending", state.get("revision")
    return status, state.get("revision")


def check_edit(project_root: Path, config_path: str, edit_cwd: Path,
               raw_paths: list[str], event: dict, adapter: str) -> tuple[bool, str]:
    """
    역할: 편집 경로를 작업의 휴면·활성·중단 상태에 맞게 판정한다.
    입력: project_root·config_path는 가드 위치, edit_cwd·raw_paths는 편집 대상,
          event·adapter는 호스트의 도구 이벤트와 어댑터다.
    출력: 허용 여부와 사용자에게 보여 줄 사유
    """
    root = project_root.resolve()
    try:
        config = load_config(root, config_path)
        enforce = config["enforce"]
        if enforce is None:
            return True, "dormant: no task is under temporary enforcement"
        status, revision = task_status(enforce)
        if status in FINISHED:
            return True, f"dormant: task {enforce['task_id']} is {status}"
        paths = [(edit_cwd / raw).resolve() for raw in raw_paths]
    except (OSError, ValueError, RuntimeError) as exc:
        return False, f"{exc}; the project owner must fix or remove the guard binding"

    if not paths:
        return False, "edit has no file path to check"
    if (root / config_path).resolve() in paths:
        return False, f"{config_path} cannot change while task {enforce['task_id']} is under enforcement"

    target = enforce["target"]
    guarded = any(
        inside(target, path) and not inside(target / ".agents" / "state", path)
        and not any(inside(exempt, path) for exempt in config["exempt"])
        for path in paths
    )
    if not guarded or status == "active":
        return True, f"edit permitted by task {enforce['task_id']} ({status})"

    hints = {
        "not_started": "start it with harness_runner.py after recording the host observation",
        "checkpoint_pending": "run and open the current jydlc gate before editing",
        "waiting_user": "record the pending decision with harness_runner.py resume",
        "blocked": "resolve the blocker and resume",
        "failed": "restart through a linked intake or ask the project owner to clear enforcement",
    }
    reason = f"task {enforce['task_id']} is {status}: {hints.get(status, 'its state cannot be read')}"
    receipt = edit_denial_receipt(enforce, status, revision, event, adapter)
    if receipt is not None:
        reason += "\nHARNESS_GUARD_OBSERVED=" + json.dumps(receipt, ensure_ascii=False)
    return False, reason


def edit_denial_receipt(enforce: dict, status: str, revision: int | None, event: dict, adapter: str) -> dict | None:
    """
    역할: 승인된 연동의 시작 전 또는 중단 중 편집 거부를 이식 가능한 증거로 기록한다.
    입력: enforce는 작업 연동, status·revision은 상태와 리비전, event는 호스트 도구 이벤트,
          adapter는 호스트 이름이다.
    출력: 가드 증거 객체 또는 관찰 식별자가 없을 때 None
    """
    approval_id = enforce.get("approval_id")
    session_id = event.get("session_id")
    tool_use_id = event.get("tool_use_id")
    if status not in {"not_started", "blocked", "waiting_user"} or type(revision) is not int or any(
        not isinstance(value, str) or not value.strip()
        for value in (approval_id, session_id, tool_use_id)
    ):
        return None
    return {
        "adapter": adapter,
        "task_id": enforce["task_id"],
        "target_root_fingerprint": root_fingerprint(enforce["target"]),
        "approval_id": approval_id,
        "session_id": session_id,
        "tool_use_id": tool_use_id,
        "tool": event["tool_name"],
        "decision": "denied",
        "task_status": status,
        "task_revision": revision,
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }


def emit_decision(allowed: bool, reason: str) -> int:
    """
    역할: 두 호스트가 이해하는 종료 코드와 표준 오류 메시지로 편집 판정을 전달한다.
    입력: allowed는 허용 여부, reason은 판정 사유다.
    출력: 허용이면 0, 거부이면 2
    """
    if not allowed:
        sys.stderr.write(f"harness_guard: {reason}\n")
    return 0 if allowed else 2
