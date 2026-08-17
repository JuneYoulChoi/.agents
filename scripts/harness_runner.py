#!/usr/bin/env python3
"""Fixed-stage workflow coordinator for the portable harness reference runtime."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from harness_router import _load_manifest, route
from harness_state import StateError, StateStore, utc_now
from harness_validator import (
    ContractError,
    active_skill_ids,
    read_object,
    root_fingerprint,
    sha256_bytes,
    validate_intake,
    validate_route_result,
    validate_skill_result,
    write_object,
)


GATE_STAGE = {
    "G2": "architecture",
    "G3": "impact",
    "G4": "assembly",
    "G5": "execution",
    "G6": "execution",
    "G7": "verification",
}


class RunnerError(ContractError):
    """Raised when a workflow transition cannot be safely applied."""


def _registry_entries(path: Path) -> dict[str, str]:
    value = read_object(path)
    skills = value.get("skills")
    if not isinstance(skills, list):
        raise RunnerError("active registry must contain a skills array")
    result: dict[str, str] = {}
    for skill in skills:
        if not isinstance(skill, dict) or not isinstance(skill.get("id"), str) or not isinstance(
            skill.get("entry"), str
        ):
            raise RunnerError("active registry skill entries require id and entry")
        result[skill["id"]] = skill["entry"]
    return result


def _execution_queue(
    route_result: dict[str, Any],
) -> tuple[list[str], dict[str, str], dict[str, str]]:
    queue: list[str] = []
    stages: dict[str, str] = {}
    gates: dict[str, str] = {}
    for gate in route_result["gate_results"]:
        gate_id = gate["gate_id"]
        for skill_id in gate.get("activated_skills", []):
            if skill_id == "core.intake-and-route" or skill_id in queue:
                continue
            queue.append(skill_id)
            stages[skill_id] = GATE_STAGE.get(gate_id, "assembly")
            gates[skill_id] = gate_id
    return queue, stages, gates


def _next_item(state: dict[str, Any], entries: dict[str, str], harness_root: Path) -> dict[str, Any] | None:
    execution = state["execution"]
    cursor = execution["cursor"]
    queue = execution["queue"]
    if cursor >= len(queue):
        return None
    skill_id = queue[cursor]
    entry = entries.get(skill_id)
    if entry is None:
        raise RunnerError(f"queued skill is missing from the active registry: {skill_id}")
    skill_path = harness_root.joinpath(entry).resolve(strict=True)
    if harness_root.resolve(strict=True) not in skill_path.parents:
        raise RunnerError(f"queued skill path escapes the harness root: {skill_id}")
    gate_id = execution["skill_gates"][skill_id]
    profiles = state["route"]["execution_profile"]["gate_profiles"]
    execution_profile = next(profile for profile in profiles if profile["gate_id"] == gate_id)
    return {
        "position": cursor,
        "skill_id": skill_id,
        "stage": execution["skill_stages"][skill_id],
        "skill_entry": entry,
        "skill_path": str(skill_path),
        "execution_profile": execution_profile,
        "expected_result": {
            "schema_version": 1,
            "skill_id": skill_id,
            "status": "completed | not_applicable | waiting_user | blocked | failed",
            "artifact_ids": [],
            "evidence_ids": [],
            "transition": {"next_stage": execution["skill_stages"][skill_id]},
            "execution_resolution": {
                "adapter": state["selected_adapter"],
                "model": "platform-selected-or-default",
                "reasoning": execution_profile["reasoning"],
                "native_reasoning": "platform-reported-value",
                "status": "exact | upgraded | degraded | platform_default | unavailable",
                "evidence_ids": [],
            },
            "error": None,
        },
    }


def _response(state: dict[str, Any], entries: dict[str, str], harness_root: Path) -> dict[str, Any]:
    next_item = _next_item(state, entries, harness_root) if state["status"] == "active" else None
    return {
        "schema_version": 1,
        "task_id": state["task_id"],
        "request_id": state["request_id"],
        "revision": state["revision"],
        "status": state["status"],
        "stage": state["stage"],
        "next": next_item,
        "queue_progress": {
            "completed": state["execution"]["cursor"],
            "total": len(state["execution"]["queue"]),
        },
    }


def start(
    target_root: Path,
    task_id: str,
    intake_path: Path,
    adapter: str,
    harness_revision: str,
    harness_root: Path,
    registry_path: Path,
    taxonomy_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    intake = validate_intake(read_object(intake_path), taxonomy_path, require_intent=True)
    approved = active_skill_ids(registry_path)
    route_result = validate_route_result(route(intake, _load_manifest(manifest_path)), approved)
    durable_allowed = intake.get("enforcement_mode") == "hook" or (
        intake.get("enforcement_mode", "manual") == "manual" and intake.get("manual_guard_valid") is True
    )
    if not durable_allowed:
        return {
            "schema_version": 1,
            "status": route_result["status"],
            "durable": False,
            "reason": "state_write_requires_hook_or_valid_manual_guard",
            "route": route_result,
            "next": None,
        }
    queue, stages, gates = _execution_queue(route_result)
    if route_result["status"] == "waiting_user":
        state_stage = "clarification"
    elif route_result["status"] == "blocked":
        state_stage = "intake"
    elif queue:
        state_stage = stages[queue[0]]
    else:
        state_stage = "handoff"
    state = {
        "schema_version": 1,
        "task_id": task_id,
        "run_id": "RUN-" + sha256_bytes(f"{task_id}:{intake['request_id']}:1".encode("utf-8"))[:16].upper(),
        "request_id": intake["request_id"],
        "revision": 1,
        "target_root_fingerprint": root_fingerprint(target_root),
        "harness_root_fingerprint": root_fingerprint(harness_root),
        "harness_source_revision": harness_revision,
        "selected_adapter": adapter,
        "status": route_result["status"],
        "stage": state_stage,
        "session_scope": intake["scope"],
        "project_state": intake["project_state"],
        "classification": {
            "fields": intake["fields"],
            "action": intake["action"],
            "risk": intake["risk"],
            "depth": intake["depth"],
            "confidence": intake["confidence"],
            "evidence_ids": intake.get("evidence_ids", []),
        },
        "intent": intake["intent"],
        "gate_network": {
            "model": route_result["model"],
            "forward_revision": route_result["forward_revision"],
            "evaluated_gate_ids": [gate["gate_id"] for gate in route_result["gate_results"]],
            "active_skill_ids": route_result["activated_skills"],
            "pending_feedback_ids": [
                item["feedback_id"]
                for item in route_result.get("feedback_results", [])
                if item.get("requires_user")
            ],
        },
        "pending_question": None,
        "open_issue_ids": [],
        "required_artifact_ids": [],
        "validation_status": "not_run",
        "intake": intake,
        "route": route_result,
        "execution": {
            "queue": queue,
            "cursor": 0,
            "skill_stages": stages,
            "skill_gates": gates,
            "results": [],
            "artifact_ids": [],
            "evidence_ids": [],
        },
        "last_transition": {
            "from": "intake",
            "to": state_stage,
            "reason": "portable route accepted",
            "actor": "harness_runner",
            "at": utc_now(),
        },
    }
    if route_result["status"] == "waiting_user":
        state["pending_question"] = {
            "question_id": "QUESTION-ROUTE-CLARIFICATION",
            "prompt": "Routing requires a user decision before execution.",
        }
    elif route_result["status"] == "blocked":
        state["blocker"] = {
            "reason": "A required routing gate is blocked.",
            "owner": "user_or_project_owner",
            "recovery": "Resolve the blocked gate and restart or resume the task.",
        }
    stored = StateStore(target_root, harness_root=harness_root).create(state)
    return _response(stored, _registry_entries(registry_path), harness_root)


def submit(
    target_root: Path,
    task_id: str,
    expected_revision: int,
    result_path: Path,
    harness_root: Path,
    registry_path: Path,
) -> dict[str, Any]:
    approved = active_skill_ids(registry_path)
    result = validate_skill_result(read_object(result_path), approved)
    store = StateStore(target_root, harness_root=harness_root)
    current = store.read(task_id)
    if current["status"] != "active":
        raise RunnerError(f"task is not active: {current['status']}")
    next_item = _next_item(current, _registry_entries(registry_path), harness_root)
    if next_item is None:
        raise RunnerError("task has no pending skill")
    if result["skill_id"] != next_item["skill_id"]:
        raise RunnerError(
            f"out-of-order skill result: expected {next_item['skill_id']}, got {result['skill_id']}"
        )
    resolution = result["execution_resolution"]
    if resolution["adapter"] != current["selected_adapter"]:
        raise RunnerError("execution resolution adapter does not match the task adapter")
    expected_reasoning = next_item["execution_profile"]["reasoning"]
    actual_reasoning = resolution["reasoning"]
    resolution_status = resolution["status"]
    rank = {"low": 0, "medium": 1, "high": 2}
    if resolution_status == "exact" and actual_reasoning != expected_reasoning:
        raise RunnerError("exact execution resolution must match recommended reasoning")
    if resolution_status == "upgraded" and (
        actual_reasoning == "unknown" or rank[actual_reasoning] <= rank[expected_reasoning]
    ):
        raise RunnerError("upgraded execution resolution must exceed recommended reasoning")
    if resolution_status == "degraded" and (
        actual_reasoning == "unknown" or rank[actual_reasoning] >= rank[expected_reasoning]
    ):
        raise RunnerError("degraded execution resolution must be below recommended reasoning")
    if resolution_status in {"exact", "upgraded", "degraded"} and actual_reasoning == "unknown":
        raise RunnerError("known execution resolution status requires a known reasoning level")
    if result["skill_id"] == "core.verify-and-handoff" and result["status"] == "not_applicable":
        raise RunnerError("verify-and-handoff cannot be marked not_applicable")

    def mutate(state: dict[str, Any]) -> None:
        execution = state["execution"]
        execution["results"].append(result)
        execution["artifact_ids"] = list(
            dict.fromkeys([*execution["artifact_ids"], *result.get("artifact_ids", [])])
        )
        execution["evidence_ids"] = list(
            dict.fromkeys([*execution["evidence_ids"], *result.get("evidence_ids", [])])
        )
        previous_stage = state["stage"]
        if result["status"] in {"completed", "not_applicable"}:
            execution["cursor"] += 1
            if execution["cursor"] >= len(execution["queue"]):
                if result["skill_id"] != "core.verify-and-handoff" or result["status"] != "completed":
                    raise RunnerError("the execution queue must end with completed verification")
                state["validation_status"] = "passed"
                state["status"] = "complete"
                state["stage"] = "handoff"
            else:
                pending = execution["queue"][execution["cursor"]]
                state["stage"] = execution["skill_stages"][pending]
        elif result["status"] == "waiting_user":
            state["status"] = "waiting_user"
            state["stage"] = "clarification"
            state["pending_question"] = {
                "question_id": f"QUESTION-{result['skill_id'].upper().replace('.', '-')}",
                "prompt": result.get("error") or "A user decision is required to continue.",
            }
        elif result["status"] == "blocked":
            state["status"] = "blocked"
            state["blocker"] = {
                "reason": result["error"],
                "owner": "user_or_project_owner",
                "recovery": "Resolve the reported blocker and resume with a new validated result.",
            }
        else:
            state["status"] = "failed"
            state["error_record"] = {
                "error": result["error"],
                "skill_id": result["skill_id"],
            }
        state["last_transition"] = {
            "from": previous_stage,
            "to": state["stage"],
            "reason": f"{result['skill_id']} returned {result['status']}",
            "actor": "harness_runner",
            "at": utc_now(),
        }

    updated = store.update(
        task_id,
        expected_revision,
        "skill_result_recorded",
        mutate,
        {"skill_id": result["skill_id"], "status": result["status"]},
    )
    if updated["status"] == "complete":
        store.write_handoff(
            task_id,
            "\n".join(
                [
                    "# Task handoff",
                    "",
                    f"- Task: {task_id}",
                    f"- Request: {updated['request_id']}",
                    f"- Status: {updated['status']}",
                    f"- Revision: {updated['revision']}",
                    f"- Completed skills: {updated['execution']['cursor']}",
                    f"- Artifact IDs: {', '.join(updated['execution']['artifact_ids']) or 'none'}",
                    f"- Evidence IDs: {', '.join(updated['execution']['evidence_ids']) or 'none'}",
                ]
            ),
        )
    return _response(updated, _registry_entries(registry_path), harness_root)


def main(argv: Iterable[str] | None = None) -> int:
    harness_root = Path(__file__).resolve().parents[1]
    registry = harness_root / "registry" / "active-skills.json"
    taxonomy = harness_root / "registry" / "taxonomy.json"
    manifest = harness_root / "registry" / "routing-gates.json"
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--target-root", required=True, type=Path)
    start_parser.add_argument("--task-id", required=True)
    start_parser.add_argument("--intake", required=True, type=Path)
    start_parser.add_argument("--adapter", required=True, choices=["codex", "claude"])
    start_parser.add_argument("--harness-revision", required=True)

    for command in ("next", "status"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--target-root", required=True, type=Path)
        command_parser.add_argument("--task-id", required=True)

    submit_parser = subparsers.add_parser("submit")
    submit_parser.add_argument("--target-root", required=True, type=Path)
    submit_parser.add_argument("--task-id", required=True)
    submit_parser.add_argument("--expected-revision", required=True, type=int)
    submit_parser.add_argument("--result", required=True, type=Path)

    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "start":
            result = start(
                args.target_root,
                args.task_id,
                args.intake,
                args.adapter,
                args.harness_revision,
                harness_root,
                registry,
                taxonomy,
                manifest,
            )
        elif args.command == "submit":
            result = submit(
                args.target_root,
                args.task_id,
                args.expected_revision,
                args.result,
                harness_root,
                registry,
            )
        else:
            state = StateStore(args.target_root, harness_root=harness_root).read(args.task_id)
            result = _response(state, _registry_entries(registry), harness_root)
        exit_code = 0
    except (ContractError, StateError, OSError) as exc:
        result = {"schema_version": 1, "status": "failed", "error": str(exc)}
        exit_code = 2
    if args.output:
        write_object(args.output, result)
    else:
        sys.stdout.write(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
