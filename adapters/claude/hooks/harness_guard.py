#!/usr/bin/env python3
"""Claude PreToolUse guard: project edits require an active harness task.

Reads the hook JSON on stdin. Exit 0 allows the tool call; exit 2 denies it and
shows stderr to the agent. It checks that a Runner task is active for the
target; it does not judge the edit itself.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

GUARDED_TOOLS = {"Edit", "Write", "NotebookEdit"}
CONFIG = ".claude/harness-guard.json"


def exempt_paths(root: Path) -> list[Path]:
    """Project-owned exemptions: literal project-relative files or directories, no globs."""
    try:
        value = json.loads((root / CONFIG).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (OSError, ValueError):
        raise ValueError(f"{CONFIG} is unreadable")
    entries = value.get("exempt_paths") if isinstance(value, dict) else None
    if not isinstance(entries, list) or any(not isinstance(e, str) or not e.strip() for e in entries):
        raise ValueError(f"{CONFIG} requires an exempt_paths array of non-empty strings")
    resolved = []
    for entry in entries:
        candidate = (root / entry).resolve()
        if Path(entry).is_absolute() or candidate == root or root not in candidate.parents:
            raise ValueError(f"{CONFIG} exempt path must stay inside the project: {entry}")
        resolved.append(candidate)
    return resolved


def decide(event: dict, project_root: Path) -> tuple[bool, str]:
    if event.get("tool_name") not in GUARDED_TOOLS:
        return True, "tool is not guarded"
    tool_input = event.get("tool_input") or {}
    raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(raw, str) or not raw:
        return False, "edit has no file path to check"
    root = project_root.resolve()
    path = Path(raw)
    path = (path if path.is_absolute() else root / path).resolve()
    if root != path and root not in path.parents:
        return True, "path is outside the project"
    state_root = root / ".agents" / "state"
    if state_root == path or state_root in path.parents:
        return True, "task state write"
    try:
        exemptions = exempt_paths(root)
    except ValueError as exc:
        return False, f"{exc}; fix or remove it"  # a broken exemption list never widens access
    if (root / CONFIG).resolve() == path:
        return False, f"{CONFIG} is changed by the project owner, not by the agent"
    if any(item == path or item in path.parents for item in exemptions):
        return True, "exempt path"
    if state_root.is_dir():
        for state_file in sorted(state_root.glob("*/state.json")):
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(state, dict) and state.get("status") == "active":
                return True, f"active task {state.get('task_id')}"
    return False, (
        "No active harness task for this project. Run intake-and-route, write the intake JSON "
        "under .agents/state/, and start it with harness_runner.py before editing project files."
    )


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except ValueError:
        sys.stderr.write("harness_guard: unreadable hook input; edit denied\n")
        return 2
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd())
    allowed, reason = decide(event if isinstance(event, dict) else {}, root)
    if allowed:
        return 0
    sys.stderr.write(f"harness_guard: {reason}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
