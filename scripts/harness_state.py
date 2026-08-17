#!/usr/bin/env python3
"""Atomic target-local task state store for the reference harness runtime."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

from harness_validator import (
    ContractError,
    root_fingerprint,
    validate_identifier,
    validate_state,
    write_object,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class StateError(ContractError):
    """Raised when task state cannot be safely created, read, or updated."""


class StateStore:
    def __init__(
        self,
        target_root: Path,
        state_root: str = ".agents/state",
        harness_root: Path | None = None,
    ) -> None:
        try:
            self.target_root = target_root.resolve(strict=True)
        except OSError as exc:
            raise StateError(f"target root cannot be resolved: {exc}") from exc
        if not self.target_root.is_dir():
            raise StateError("target root must be an existing directory")
        if state_root != ".agents/state":
            raise StateError("reference MVP supports only .agents/state")
        self.state_root = self.target_root / ".agents" / "state"
        candidate_harness_root = harness_root or Path(__file__).resolve().parents[1]
        try:
            self.harness_root = candidate_harness_root.resolve(strict=True)
        except OSError as exc:
            raise StateError(f"harness root cannot be resolved: {exc}") from exc
        if not self.harness_root.is_dir():
            raise StateError("harness root must be an existing directory")

    def task_dir(self, task_id: str) -> Path:
        validate_identifier(task_id, "task_id")
        return self.state_root / task_id

    @contextmanager
    def lock(self, task_id: str) -> Iterator[None]:
        task_dir = self.task_dir(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        lock_path = task_dir / ".lock"
        try:
            descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise StateError(f"task is locked: {task_id}") from exc
        try:
            os.write(descriptor, f"pid={os.getpid()} at={utc_now()}\n".encode("utf-8"))
            os.fsync(descriptor)
            yield
        finally:
            os.close(descriptor)
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass

    def _atomic_write(self, path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        data = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(str(temporary), str(path))
        except OSError as exc:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise StateError(f"cannot atomically write {path}: {exc}") from exc

    def _append_event(self, task_id: str, event: dict[str, Any]) -> None:
        event_path = self.task_dir(task_id) / "events.ndjson"
        data = json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n"
        try:
            with event_path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as exc:
            raise StateError(f"cannot append task event: {exc}") from exc

    def create(self, state: dict[str, Any], artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
        task_id = validate_identifier(state.get("task_id"), "task_id")
        task_dir = self.task_dir(task_id)
        state_path = task_dir / "state.json"
        if state_path.exists():
            raise StateError(f"task already exists: {task_id}")
        validate_state(state, self.target_root, self.harness_root)
        with self.lock(task_id):
            if state_path.exists():
                raise StateError(f"task already exists: {task_id}")
            self._atomic_write(state_path, state)
            self._atomic_write(task_dir / "artifacts.json", artifacts or {"schema_version": 1, "artifacts": []})
            self._append_event(
                task_id,
                {
                    "schema_version": 1,
                    "type": "task_created",
                    "task_id": task_id,
                    "run_id": state["run_id"],
                    "revision": state["revision"],
                    "target_root_fingerprint": state["target_root_fingerprint"],
                    "harness_root_fingerprint": state["harness_root_fingerprint"],
                    "harness_source_revision": state["harness_source_revision"],
                    "selected_adapter": state["selected_adapter"],
                    "at": utc_now(),
                },
            )
        return copy.deepcopy(state)

    def read(self, task_id: str) -> dict[str, Any]:
        state_path = self.task_dir(task_id) / "state.json"
        try:
            value = json.loads(state_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise StateError(f"task does not exist: {task_id}") from exc
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise StateError(f"task state is unreadable; original preserved: {exc}") from exc
        if not isinstance(value, dict):
            raise StateError("task state must be a JSON object; original preserved")
        validate_state(value, self.target_root, self.harness_root)
        return value

    def update(
        self,
        task_id: str,
        expected_revision: int,
        event_type: str,
        mutate: Callable[[dict[str, Any]], None],
        event_details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        validate_identifier(event_type, "event_type")
        with self.lock(task_id):
            current = self.read(task_id)
            if current["revision"] != expected_revision:
                raise StateError(
                    f"revision conflict: expected {expected_revision}, actual {current['revision']}"
                )
            updated = copy.deepcopy(current)
            mutate(updated)
            updated["revision"] = current["revision"] + 1
            validate_state(updated, self.target_root, self.harness_root)
            self._atomic_write(self.task_dir(task_id) / "state.json", updated)
            event = {
                "schema_version": 1,
                "type": event_type,
                "task_id": task_id,
                "run_id": updated["run_id"],
                "revision": updated["revision"],
                "target_root_fingerprint": updated["target_root_fingerprint"],
                "harness_root_fingerprint": updated["harness_root_fingerprint"],
                "harness_source_revision": updated["harness_source_revision"],
                "selected_adapter": updated["selected_adapter"],
                "at": utc_now(),
            }
            if event_details:
                event["details"] = event_details
            self._append_event(task_id, event)
        return updated

    def write_handoff(self, task_id: str, content: str) -> Path:
        if not isinstance(content, str) or not content.strip():
            raise StateError("handoff content must be non-empty")
        path = self.task_dir(task_id) / "handoff.md"
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(content.rstrip() + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(str(temporary), str(path))
        except OSError as exc:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise StateError(f"cannot write handoff: {exc}") from exc
        return path


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["read", "validate"])
    parser.add_argument("--target-root", required=True, type=Path)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        state = StateStore(args.target_root).read(args.task_id)
        result = {"schema_version": 1, "status": "valid", "state": state}
        exit_code = 0
    except StateError as exc:
        result = {"schema_version": 1, "status": "invalid", "error": str(exc)}
        exit_code = 2
    if args.output:
        write_object(args.output, result)
    else:
        sys.stdout.write(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
