#!/usr/bin/env python3
"""Fixed-stage workflow coordinator for the portable harness reference runtime."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from harness_bootstrap import verify_source
from harness_router import _load_manifest, route
from harness_delegation import prepare, record, require_join, usage_summary, validate_bindings
from harness_state import StateError, StateStore, utc_now
from harness_workflow import WorkflowError, compose_work_plan
from harness_validator import (
    ContractError,
    active_skill_ids,
    read_object,
    root_fingerprint,
    sha256_bytes,
    validate_intake,
    validate_acceptance_evidence,
    validate_implementation_quality,
    validate_pattern_review,
    validate_resolution_binding,
    MUTATION_ACTIONS,
    NON_SKIPPABLE_FOR_MUTATION,
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
            stages[skill_id] = (
                "assembly" if skill_id == "core.workflow-composition"
                else GATE_STAGE.get(gate_id, "assembly")
            )
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
    gate_result = next(
        gate for gate in state["route"]["gate_results"] if gate["gate_id"] == gate_id
    )
    application_depth = gate_result.get("application_depths", {}).get(
        skill_id, state["classification"]["depth"]
    )
    return {
        "position": cursor,
        "skill_id": skill_id,
        "stage": execution["skill_stages"][skill_id],
        "skill_entry": entry,
        "skill_path": str(skill_path),
        "execution_profile": execution_profile,
        "application_depth": application_depth,
        "work_plan": state["route"].get("work_plan"),
        "tool_profile": (
            state["route"].get("ros2_mcp_profile")
            if skill_id == "core.ros2-engineering"
            and state["route"].get("ros2_mcp_profile", {}).get("applicable")
            else None
        ),
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
        **({"worker_usage": usage_summary(state)}
           if state["execution"].get("work_records") else {}),
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
    verified_revision = verify_source(harness_root, registry_path)
    if (taxonomy_path.resolve() != (harness_root / 'registry/taxonomy.json').resolve()
            or manifest_path.resolve() != (harness_root / 'registry/routing-gates.json').resolve()):
        raise RunnerError('execution requires pinned taxonomy and routing manifest')
    intake = validate_intake(read_object(intake_path), taxonomy_path, require_intent=True)
    previous = None
    if intake.get('supersedes_task_id') is not None:
        prior = StateStore(target_root, harness_root=harness_root).read(intake['supersedes_task_id'])
        if prior['task_id'] == task_id or prior['status'] not in {'waiting_user', 'blocked', 'failed'}:
            raise RunnerError('restart requires a distinct interrupted task')
        if any(r['status'] == 'running' for r in prior['execution'].get('work_records', {}).values()):
            raise RunnerError('terminate and record prior workers before restart')
        previous = {'task_id': prior['task_id'], 'revision': prior['revision'], 'status': prior['status']}

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
    validate_bindings(route_result.get("work_plan", {}), queue, allow_unbound=True)
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
        "harness_source_revision": verified_revision,
        "supersedes": previous,
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
            "change_characteristics": intake.get("change_characteristics", []),
            "language_scope": intake.get(
                "language_scope", "authored_in_scope" if intake.get("languages") else "none"
            ),
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
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    verify_source(harness_root, registry_path)
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
    if any(r["status"] == "running" for r in current["execution"].get("work_records", {}).values()):
        raise RunnerError("record worker termination before any skill transition")
    if result["status"] in {"completed", "not_applicable"}:
        require_join(current, result["skill_id"])
    if result['skill_id'] == 'core.verify-and-handoff' and result['status'] == 'completed':
        if not result['artifact_ids'] or not result['evidence_ids']:
            raise RunnerError('completion requires artifact and evidence IDs')
        validate_acceptance_evidence(result.get('verification'), current['intent']['success_criteria'], target_root)
    if result['skill_id'] == 'core.verify-and-handoff' and result['status'] == 'completed' \
            and next_item['execution_profile'].get('independent_context'):
        independent = result.get('independent_verification_evidence_ids')
        if (not isinstance(independent, list) or not independent
                or any(not isinstance(v, str) or not v.strip() for v in independent)):
            raise RunnerError('this route requires independent-context verification evidence')
    if (result['status'] == 'not_applicable' and result['skill_id'] in NON_SKIPPABLE_FOR_MUTATION
            and current['classification']['action'] in MUTATION_ACTIONS):
        raise RunnerError('an activated baseline or impact skill cannot be skipped for a mutation')
    _validate_typed_payload(result)
    if (current['project_state'] == 'unknown'
            and result['skill_id'] == 'core.architecture-baseline-and-design'
            and result['status'] in {'completed', 'not_applicable'}):
        raise RunnerError('unknown project requires a discovery result as waiting_user or blocked, then linked reclassification')
    updated_plan = None
    workflow_update = result.get("workflow_update")
    if workflow_update is not None:
        if (result["skill_id"] != "core.workflow-composition" or result["status"] != "completed"
                or not isinstance(workflow_update, dict) or set(workflow_update) != {"work_units"}):
            raise RunnerError("only completed composition may update work_units; authority cannot change")
        if not result.get("artifact_ids") or not result.get("evidence_ids"):
            raise RunnerError("workflow_update requires plan artifacts and evidence")
        try:
            updated_plan = compose_work_plan(
                {**current["intake"], "work_units": workflow_update["work_units"]}, "active"
            )
        except WorkflowError as exc:
            raise RunnerError(str(exc)) from exc
        previous_units = {u["id"]: u for u in current["route"]["work_plan"]["units"]}
        updated_units = {u["id"]: u for u in updated_plan["units"]}
        for unit_id, receipt in current["execution"].get("work_records", {}).items():
            if receipt["status"] != "completed":
                raise RunnerError("cannot refine work with unsuccessful receipts; use responsible-gate recovery")
            if unit_id not in previous_units or updated_units.get(unit_id) != previous_units[unit_id]:
                raise RunnerError("workflow_update must preserve every prepared work unit unchanged")
    if result["skill_id"] == "core.workflow-composition" and result["status"] in {"completed", "not_applicable"}:
        validate_bindings(updated_plan or current["route"]["work_plan"],
                          current["execution"]["queue"], current["execution"]["cursor"] + 1,
                          current["execution"].get("work_records", {}))
    try:
        validate_resolution_binding(result['execution_resolution'], current['selected_adapter'],
                                    next_item['execution_profile']['reasoning'])
    except ContractError as exc:
        raise RunnerError(str(exc)) from exc
    if result["skill_id"] == "core.verify-and-handoff" and result["status"] == "not_applicable":
        raise RunnerError("verify-and-handoff cannot be marked not_applicable")

    rewind = _feedback_plan(current, result, manifest_path or harness_root / "registry/routing-gates.json")

    def mutate(state: dict[str, Any]) -> None:
        if updated_plan is not None:
            state["route"]["work_plan"] = updated_plan
            state["intake"]["work_units"] = workflow_update["work_units"]
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
            state["suspended_by"] = result["skill_id"]
            state["pending_question"] = {
                "question_id": f"QUESTION-{result['skill_id'].upper().replace('.', '-')}",
                "prompt": result.get("error") or "A user decision is required to continue.",
            }
        elif result["status"] == "blocked":
            state["status"] = "blocked"
            state["suspended_by"] = result["skill_id"]
            state["blocker"] = {
                "reason": result["error"],
                "owner": "user_or_project_owner",
                "recovery": "Resolve the reported blocker and resume with a new validated result.",
            }
        elif rewind is not None and rewind["action"] == "rewind":
            # Bounded backward feedback: reopen the responsible gate, keep earlier results.
            execution.setdefault("feedback_attempts", {})[rewind["target_gate"]] = rewind["attempt"]
            execution.setdefault("feedback_log", []).append(rewind["record"])
            execution["cursor"] = rewind["cursor"]
            state["stage"] = execution["skill_stages"][execution["queue"][rewind["cursor"]]]
        elif rewind is not None:
            execution.setdefault("feedback_attempts", {})[rewind["target_gate"] or "unrouted"] = rewind["attempt"]
            execution.setdefault("feedback_log", []).append(rewind["record"])
            state["status"] = "waiting_user"
            state["stage"] = "clarification"
            state["suspended_by"] = result["skill_id"]
            state["pending_question"] = {
                "question_id": "QUESTION-FEEDBACK-ESCALATION",
                "prompt": rewind["reason"],
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



FEEDBACK_RETRY_LIMIT = 3


def _validate_typed_payload(result: dict[str, Any]) -> None:
    """Bind the skill-specific contracts to the gate transition they justify."""
    skill_id, status = result["skill_id"], result["status"]
    if skill_id == "core.architecture-and-design-patterns":
        review = result.get("pattern_review")
        if review is None:
            if status == "completed":
                raise RunnerError("completed pattern review requires a pattern_review record")
            return
        reviews = review if isinstance(review, list) else [review]
        if not reviews:
            raise RunnerError("pattern_review must not be empty")
        for item in reviews:
            if not isinstance(item, dict):
                raise RunnerError("pattern_review must be an object or an array of objects")
            validate_pattern_review(item)
            if status == "completed" and item["decision"]["status"] == "user_decision_required":
                raise RunnerError("an open pattern decision must be returned as waiting_user")
    elif skill_id == "core.implementation-quality":
        quality = result.get("implementation_quality")
        if quality is None:
            if status == "completed":
                raise RunnerError("completed implementation quality requires its typed record")
            return
        if not isinstance(quality, dict):
            raise RunnerError("implementation_quality must be an object")
        validate_implementation_quality(quality)
        if quality["status"] != status:
            raise RunnerError("implementation_quality status must match the skill result status")


def _feedback_plan(state: dict[str, Any], result: dict[str, Any], manifest_path: Path) -> dict[str, Any] | None:
    """Plan a bounded in-task reopen for a failed result that names a routed signal."""
    feedback = result.get("feedback")
    if feedback is None:
        return None
    if result["status"] != "failed" or not isinstance(feedback, dict) or not isinstance(feedback.get("kind"), str):
        raise RunnerError("feedback requires a failed result and a signal kind")
    routes = {item["signal"]: item["target_gate"] for item in read_object(manifest_path)["backward_routes"]}
    target_gate = routes.get(feedback["kind"])
    execution = state["execution"]
    attempts = execution.get("feedback_attempts", {})
    attempt = attempts.get(target_gate or "unrouted", 0) + 1  # counted here, never self-reported
    cursor = execution["cursor"]
    record_item = {"kind": feedback["kind"], "source_skill": result["skill_id"],
                   "target_gate": target_gate, "attempt": attempt, "error": result["error"]}
    plan = {"target_gate": target_gate, "attempt": attempt, "record": record_item}
    if target_gate is None:
        return {**plan, "action": "escalate", "reason": "Unrouted feedback signal requires a user decision."}
    if attempt >= FEEDBACK_RETRY_LIMIT:
        return {**plan, "action": "escalate",
                "reason": f"Feedback to {target_gate} reached the retry limit; a user decision is required."}
    gates = execution["skill_gates"]
    index = next((i for i, skill in enumerate(execution["queue"][:cursor + 1])
                  if int(gates[skill][1:]) >= int(target_gate[1:])), None)
    if index is None:
        return {**plan, "action": "escalate",
                "reason": f"{target_gate} has no queued owner; correct the intake through a linked restart."}
    reopened = set(execution["queue"][index:])
    if any(item.get("skill_id") in reopened for item in execution.get("work_records", {}).values()):
        return {**plan, "action": "escalate",
                "reason": "Recorded work units belong to the reopened gates; recover through a linked restart."}
    return {**plan, "action": "rewind", "cursor": index}


def resume(target_root: Path, task_id: str, expected_revision: int, request_path: Path,
           harness_root: Path, registry_path: Path) -> dict[str, Any]:
    """Continue a task that a skill suspended, at the same skill, after a recorded decision."""
    verify_source(harness_root, registry_path)
    request = read_object(request_path)
    evidence = request.get("decision_evidence_ids")
    answer = request.get("answer")
    if (not isinstance(answer, str) or not answer.strip() or not isinstance(evidence, list) or not evidence
            or any(not isinstance(v, str) or not v.strip() for v in evidence)):
        raise RunnerError("resume requires the recorded answer and decision evidence IDs")
    store = StateStore(target_root, harness_root=harness_root)
    current = store.read(task_id)
    if current["status"] not in {"waiting_user", "blocked"} or not current.get("suspended_by"):
        raise RunnerError("only a task suspended by a skill result can resume; a routing block needs a linked restart")
    if any(r["status"] == "running" for r in current["execution"].get("work_records", {}).values()):
        raise RunnerError("record worker termination before resuming")

    def mutate(state: dict[str, Any]) -> None:
        execution = state["execution"]
        pending = execution["queue"][execution["cursor"]]
        execution.setdefault("decisions", []).append({
            "skill_id": state["suspended_by"], "previous_status": state["status"],
            "answer": answer, "decision_evidence_ids": evidence, "at": utc_now()})
        previous_stage = state["stage"]
        state["status"] = "active"
        state["stage"] = execution["skill_stages"][pending]
        state["pending_question"] = None
        state.pop("blocker", None)
        state.pop("suspended_by", None)
        state["last_transition"] = {"from": previous_stage, "to": state["stage"],
                                    "reason": "user decision recorded; skill resumed",
                                    "actor": "harness_runner", "at": utc_now()}

    updated = store.update(task_id, expected_revision, "task_resumed", mutate, {"decision_evidence_ids": evidence})
    return _response(updated, _registry_entries(registry_path), harness_root)


def work_event(target_root: Path, task_id: str, expected_revision: int,
               request_path: Path, command: str, harness_root: Path,
               registry_path: Path) -> dict[str, Any]:
    verify_source(harness_root, registry_path)
    request = read_object(request_path)
    store = StateStore(target_root, harness_root=harness_root)
    output: dict[str, Any] = {}

    def mutate(state: dict[str, Any]) -> None:
        if command == "prepare-work":
            output.update(prepare(state, request, target_root, harness_root=harness_root, registry_path=registry_path))
        else:
            record(state, request, target=target_root)

    updated = store.update(task_id, expected_revision, command.replace("-", "_"), mutate)
    return {**_response(updated, _registry_entries(registry_path), harness_root), **output}


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

    for command in ("prepare-work", "record-work", "resume"):
        work_parser = subparsers.add_parser(command)
        work_parser.add_argument("--target-root", required=True, type=Path)
        work_parser.add_argument("--task-id", required=True)
        work_parser.add_argument("--expected-revision", required=True, type=int)
        work_parser.add_argument("--request", required=True, type=Path)

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
        elif args.command == "resume":
            result = resume(args.target_root, args.task_id, args.expected_revision,
                            args.request, harness_root, registry)
        elif args.command in {"prepare-work", "record-work"}:
            result = work_event(args.target_root, args.task_id, args.expected_revision,
                                args.request, args.command, harness_root, registry)
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
