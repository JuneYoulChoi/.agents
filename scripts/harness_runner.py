#!/usr/bin/env python3
"""
모듈: 하네스 런타임 (scripts)
컴포넌트: Runner
역할: 라우팅 결과를 스킬 실행 큐로 만들고, 스킬 결과 제출·재개·되돌림·작업 단위 기록을
      검증한 뒤 작업 상태를 한 단계씩 진행한다. (Fixed-stage workflow coordinator.)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from harness_bootstrap import verify_source
from harness_code_docs import check as check_code_docs
from harness_doc_sync import DEFAULT_MAP, changed_code_files, check as check_doc_sync
from harness_gate_evidence import evidence_record, requirements, test_plan, verify_results, verify_tdd
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
    validate_hook_guard,
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
GATE_IDS = tuple(f"G{index}" for index in range(8))


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
    """
    역할: 작업 상태와 실행 가능한 다음 스킬 또는 대기·차단 사유를 반환한다.
    입력: state는 작업 상태, entries는 승인된 스킬 경로, harness_root는 하네스 소스다.
    출력: Runner 응답
    """
    next_item = _next_item(state, entries, harness_root) if state["status"] == "active" else None
    operator = state["execution"].get("operator")
    if operator is not None and next_item is not None:
        if not operator["opened"] or next_item["execution_profile"]["gate_id"] != operator["gate"]:
            next_item = None
    if operator is not None:
        current_gate = next(gate for gate in state["route"]["gate_results"] if gate["gate_id"] == operator["gate"])
        if "operator_name" not in current_gate:
            manifest = _load_manifest(harness_root / "registry/routing-gates.json")
            current_gate = next(gate for gate in manifest["gates"] if gate["id"] == operator["gate"])
        operator = {**operator, "gate_name": current_gate.get("operator_name", operator["gate"]),
                    "gate_label": current_gate.get("operator_label", operator["gate"])}
    return {
        "schema_version": 1,
        "task_id": state["task_id"],
        "request_id": state["request_id"],
        "revision": state["revision"],
        "status": state["status"],
        "stage": state["stage"],
        "next": next_item,
        **({"operator": operator} if operator is not None else {}),
        **({"blocker": state["blocker"]} if state["status"] == "blocked" else {}),
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
    """
    역할: intake를 검증·라우팅하고, 강제 가능한 경우(훅 또는 유효한 수동 가드) 작업 상태를 만든다.
          권고 모드나 훅 요청 상태면 상태를 저장하지 않고 요약만 돌려준다.

    입력:
        target_root: 대상 프로젝트 루트(공용 하네스를 담은 폴더는 거부)
        task_id: 새 작업 ID
        intake_path: intake JSON 파일 경로
        adapter: 실행 어댑터 이름(codex 또는 claude)
        harness_revision: 호출자가 준 리비전 표시(신뢰하지 않고 검증된 값을 기록)
        harness_root: 하네스 소스 루트
        registry_path, taxonomy_path, manifest_path: 고정된 레지스트리·분류·라우팅 파일 경로
    출력:
        저장된 작업의 상태 요약과 다음 스킬, 또는 저장하지 않은 라우팅 요약(durable: False)
    예외:
        RunnerError, ContractError, StateError: 입력·무결성·대상 위치가 잘못된 경우
    """
    verified_revision = verify_source(harness_root, registry_path)
    if (taxonomy_path.resolve() != (harness_root / 'registry/taxonomy.json').resolve()
            or manifest_path.resolve() != (harness_root / 'registry/routing-gates.json').resolve()):
        raise RunnerError('execution requires pinned taxonomy and routing manifest')
    intake = validate_intake(read_object(intake_path), taxonomy_path, require_intent=True)
    manual_steps = intake.get("operator_mode") == "jydlc"
    if manual_steps and (intake["target"] != "project" or intake["scope"] not in {"software_engineering", "software_related"}):
        raise RunnerError("jydlc manual gates require a target software project")
    if intake.get("hook_guard") is not None:
        guard = validate_hook_guard(intake["hook_guard"], target_root, task_id, adapter)
        if guard["task_status"] != "not_started":
            raise RunnerError("start requires a hook observation for the not-yet-started task")
    previous = None
    if intake.get('supersedes_task_id') is not None:
        prior = StateStore(target_root, harness_root=harness_root).read(intake['supersedes_task_id'])
        if prior['task_id'] == task_id or prior['status'] not in {'waiting_user', 'blocked', 'failed'}:
            raise RunnerError('restart requires a distinct interrupted task')
        if any(r['status'] == 'running' for r in prior['execution'].get('work_records', {}).values()):
            raise RunnerError('terminate and record prior workers before restart')
        previous = {'task_id': prior['task_id'], 'revision': prior['revision'], 'status': prior['status']}

    approved = active_skill_ids(registry_path)
    route_result = validate_route_result(route(intake, _load_manifest(manifest_path), taxonomy_path), approved)
    durable_allowed = route_result["enforcement"]["level"] == "enforced"
    if not durable_allowed:
        level = route_result["enforcement"]["level"]
        reasons = {
            "advisory": "advisory_route_follow_skills_then_run_harness_finish",
            "requested": "ask_user_for_temporary_enforcement_or_record_a_waiver",
        }
        native_required = bool(route_result.get("work_plan", {}).get("required_native_roles"))
        advisory_status = route_result["status"]
        if native_required and advisory_status == "active":
            advisory_status = "waiting_user"
        return {
            "schema_version": 1,
            "status": advisory_status,
            "durable": False,
            "reason": ("native_receipts_need_durable_execution" if native_required and route_result["status"] == "active"
                       else "hook_guard_evidence_required" if intake.get("enforcement_mode") == "hook"
                       else reasons.get(level, "state_write_requires_hook_or_valid_manual_guard")),
            "enforcement": route_result["enforcement"],
            "activated_skills": route_result["activated_skills"],
            "suppressed_skills": route_result["suppressed_skills"],
            "blocked": [{"gate_id": gate["gate_id"], **item}
                        for gate in route_result["gate_results"] for item in gate["blocked"]],
            "next": None,
            **({"gate_results": route_result["gate_results"], "work_plan": route_result["work_plan"],
                "execution_profile": route_result["execution_profile"]} if manual_steps else {}),
        }
    operator = None
    if manual_steps and route_result["status"] == "active":
        verified = intake.get("initial_checkpoints")
        if not isinstance(verified, dict) or set(verified) != {"G0", "G1"}:
            raise RunnerError("jydlc start requires user checkpoints for G0 and G1")
        operator = {"gate": "G2", "opened": None, "completed": {}, "results": {}}
        for gate in ("G0", "G1"):
            operator["completed"][gate] = {
                **validate_checkpoint_evidence(verified[gate], target_root),
                "recorded_revision": 1,
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
            **({"operator": operator} if operator is not None else {}),
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
    """
    역할: 현재 차례 스킬의 결과를 검증하고, 통과하면 작업 상태를 다음 단계로 진행한다.

    입력:
        target_root: 작업 상태를 보관하는 대상 프로젝트 루트
        task_id: 진행할 작업 ID
        expected_revision: 호출자가 읽은 상태 리비전(동시 수정 방지)
        result_path: 스킬 결과 JSON 파일 경로
        harness_root: 하네스 소스 루트
        registry_path: 승인된 스킬 레지스트리 경로
        manifest_path: 라우팅 매니페스트 경로(생략 시 하네스 기본값)
    출력:
        갱신된 작업 상태 요약과 다음 스킬 안내
    예외:
        RunnerError, ContractError: 결과가 계약·순서·증거 규칙을 어긴 경우
    """
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
    operator = current["execution"].get("operator")
    current_gate = next_item["execution_profile"]["gate_id"]
    if operator is not None and (operator["gate"] != current_gate or not operator["opened"]):
        raise RunnerError("run and open the current user checkpoint before submitting its skill")
    if any(r["status"] == "running" for r in current["execution"].get("work_records", {}).values()):
        raise RunnerError("record worker termination before any skill transition")
    if result["status"] in {"completed", "not_applicable"}:
        require_join(current, result["skill_id"], target_root)
    if result['skill_id'] == 'core.verify-and-handoff' and result['status'] == 'completed':
        if not result['artifact_ids'] or not result['evidence_ids']:
            raise RunnerError('completion requires artifact and evidence IDs')
        validate_acceptance_evidence(result.get('verification'), current['intent']['success_criteria'], target_root)
    if result['skill_id'] == 'core.verify-and-handoff' and result['status'] == 'completed' \
            and next_item['execution_profile'].get('independent_context') \
            and not current["route"]["work_plan"].get("required_native_roles"):
        independent = result.get('independent_verification_evidence_ids')
        if (not isinstance(independent, list) or not independent
                or any(not isinstance(v, str) or not v.strip() for v in independent)):
            raise RunnerError('this route requires independent-context verification evidence')
    if (result['status'] == 'not_applicable' and result['skill_id'] in NON_SKIPPABLE_FOR_MUTATION
            and current['classification']['action'] in MUTATION_ACTIONS):
        raise RunnerError('an activated baseline or impact skill cannot be skipped for a mutation')
    if result["status"] == "not_applicable" and result["skill_id"] == "core.implementation-quality" and _quality_profiles(current):
        raise RunnerError("an activated implementation quality check cannot be skipped")
    _validate_typed_payload(result, target_root, _quality_profiles(current))
    if result["status"] == "completed":
        validate_engineering_result(current, result, target_root)
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
        """
        역할: 스킬 결과를 저장하고 상태 전이 또는 G0 가드 확인을 수행한다.
        입력: state는 잠긴 작업 상태의 갱신 사본이다.
        """
        if updated_plan is not None:
            state["route"]["work_plan"] = updated_plan
            state["intake"]["work_units"] = workflow_update["work_units"]
        execution = state["execution"]
        operator = execution.get("operator")
        execution["results"].append(result)
        execution["artifact_ids"] = list(
            dict.fromkeys([*execution["artifact_ids"], *result.get("artifact_ids", [])])
        )
        execution["evidence_ids"] = list(
            dict.fromkeys([*execution["evidence_ids"], *result.get("evidence_ids", [])])
        )
        previous_stage = state["stage"]
        if result["status"] in {"completed", "not_applicable"}:
            if operator is not None:
                operator["results"][result["skill_id"]] = result
            execution["cursor"] += 1
            if execution["cursor"] >= len(execution["queue"]):
                if result["skill_id"] != "core.verify-and-handoff" or result["status"] != "completed":
                    raise RunnerError("the execution queue must end with completed verification")
                if operator is None:
                    state["validation_status"] = "passed"
                    state["status"] = "complete"
                    state["stage"] = "handoff"
            else:
                pending = execution["queue"][execution["cursor"]]
                if operator is None or execution["skill_gates"][pending] == operator["gate"]:
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
        elif rewind is not None and rewind["action"] == "guard":
            execution.setdefault("feedback_attempts", {})["G0"] = rewind["attempt"]
            execution.setdefault("feedback_log", []).append(rewind["record"])
            state["status"] = "blocked"
            state["stage"] = "intake"
            state["suspended_by"] = "G0"
            if operator is not None:
                operator["opened"] = None
            state["blocker"] = {
                "reason": result["error"],
                "owner": "user_or_project_owner",
                "recovery": rewind["reason"],
            }
        elif rewind is not None and rewind["action"] == "rewind":
            # Bounded backward feedback: reopen the responsible gate, keep earlier results.
            execution.setdefault("feedback_attempts", {})[rewind["target_gate"]] = rewind["attempt"]
            execution.setdefault("feedback_log", []).append(rewind["record"])
            execution["cursor"] = rewind["cursor"]
            if operator is not None:
                stale = {unit: receipt for unit, receipt in execution.get("work_records", {}).items()
                         if execution["skill_gates"][receipt["skill_id"]] >= rewind["target_gate"]}
                if stale:
                    execution.setdefault("invalidated_work_records", []).append({
                        "feedback": rewind["record"], "records": stale,
                    })
                    for unit in stale:
                        del execution["work_records"][unit]
                reopen_checkpoint(state, rewind["target_gate"])
            else:
                state["stage"] = execution["skill_stages"][execution["queue"][rewind["cursor"]]]
        elif rewind is not None:
            execution.setdefault("feedback_attempts", {})[rewind["target_gate"] or "unrouted"] = rewind["attempt"]
            execution.setdefault("feedback_log", []).append(rewind["record"])
            state["status"] = "waiting_user"
            state["stage"] = "clarification"
            if rewind["action"] == "restart":
                state.pop("suspended_by", None)
            else:
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
        write_handoff(store, updated)
    return _response(updated, _registry_entries(registry_path), harness_root)



FEEDBACK_RETRY_LIMIT = 3


def _quality_profiles(state: dict) -> set[str]:
    """
    역할: G6 라우팅이 선택한 구현 품질 프로파일을 반환한다.
    입력: state는 작업 상태다.
    출력: 적용할 프로파일 ID 집합
    """
    gate = next(gate for gate in state["route"]["gate_results"] if gate["gate_id"] == "G6")
    return {item.split(":", 1)[1] for item in gate["activated_branches"] if item.startswith("implementation_quality:")}


def _required_check_kinds(state: dict) -> set[str]:
    """
    역할: 품질 특성과 라우팅된 실행 환경에서 반드시 입증할 시험 종류를 수집한다.
    입력: state는 작업 상태다.
    출력: 필수 시험 종류 집합
    """
    required = set(state["route"].get("verification_plan", {}).get("required_checks", []))
    profiles = _quality_profiles(state)
    if "performance" in profiles:
        required.add("performance_measurement")
    if "realtime_embedded" in profiles and not state["route"].get("verification_plan", {}).get("control"):
        required.add("deadline_measurement")
    return required


def _engineering_checkpoints(state: dict) -> bool:
    """
    역할: 사용자 단계 실행에서 요구사항·시험 계약을 강제해야 하는 변경인지 판단한다.
    입력: state는 작업 상태다.
    출력: 대상 프로젝트를 수정하는 사용자 단계 실행이면 참
    """
    return "operator" in state["execution"] and state["classification"]["action"] in MUTATION_ACTIONS


def _accepted_requirements(state: dict, target: Path) -> dict:
    """
    역할: 현재 유효한 G3 결과에서 요구사항을 읽고 복수 경로 간 충돌을 확인한다.
    입력: state는 작업 상태, target은 대상 프로젝트다.
    출력: 수용 기준에 바인딩된 요구사항
    """
    results = state["execution"]["operator"]["results"]
    records = [requirements(results[skill]["requirements"], state["intent"]["success_criteria"], target)
               for skill in ("core.brownfield-impact-analysis", "core.greenfield-planning") if skill in results]
    if not records or any(record != records[0] for record in records[1:]):
        raise RunnerError("G4 requires consistent G3 requirements")
    return records[0]


def _operator_test_plan(state: dict, value: Any, target: Path) -> dict:
    """
    역할: 사용자 단계 실행의 요구사항과 라우팅된 검증 조건을 계획에 적용한다.
    입력: state는 작업 상태, value는 시험 계획, target은 대상 프로젝트다.
    출력: 시험 ID별 유효한 계획
    """
    planned = test_plan(value, _accepted_requirements(state, target), _required_check_kinds(state),
                        target, state["route"].get("verification_plan"))
    if (state["classification"]["language_scope"] == "authored_in_scope"
            and state["intake"].get("work_type") in {"feature", "bugfix"}
            and not any(check["method"] == "tdd" for check in planned.values())):
        raise RunnerError("authored feature and bugfix tasks require a planned TDD check")
    return planned


def _documentation_targets(target: Path, documentation: dict) -> list[str]:
    """
    역할: 한글 주석과 모듈 맵 검사가 공유할 변경 코드 파일을 수집한다.
    입력: target은 대상 프로젝트, documentation은 검사 범위와 기준 리비전이다.
    출력: 중복 없는 검사 대상 코드 경로
    """
    files = list(documentation["files"])
    base = documentation.get("base_revision")
    if base:
        excluded = (*documentation.get("exempt_paths", []),
                    Path(documentation.get("module_map") or DEFAULT_MAP).parent.as_posix())
        files.extend(changed_code_files(target.resolve(), base, excluded))
    return list(dict.fromkeys(files))


def validate_engineering_result(state: dict, result: dict, target: Path) -> None:
    """
    역할: 현재 게이트의 기준선·요구사항·시험 결과가 이전 산출물과 일치하는지 확인한다.
    입력: state는 작업 상태, result는 스킬 결과, target은 프로젝트다.
    """
    skill = result["skill_id"]
    strict = _engineering_checkpoints(state)
    criteria = state["intent"]["success_criteria"]
    if strict and skill == "core.architecture-baseline-and-design":
        baseline = evidence_record(result.get("architecture_baseline"), target, "architecture_baseline")
        if baseline.get("status") != "confirmed":
            raise RunnerError("G2 requires a confirmed in-scope architecture baseline")
        if state["intake"].get("conformance_intent") == "conformance":
            evidence_record(baseline.get("standards_assessment"), target, "standards_assessment")
    if strict and skill in {"core.brownfield-impact-analysis", "core.greenfield-planning"}:
        requirements(result.get("requirements"), criteria, target)
    if strict and skill == "core.architecture-and-design-patterns":
        current_requirements = _accepted_requirements(state, target)
        reviews = result["pattern_review"] if isinstance(result["pattern_review"], list) else [result["pattern_review"]]
        if any(not set(review["drivers"]).intersection(current_requirements) for review in reviews):
            raise RunnerError("G5 pattern decisions must link an accepted REQ or QAS")
        if "object_oriented" in state["classification"]["change_characteristics"]:
            review = evidence_record(result.get("responsibility_review"), target, "SOLID/GRASP responsibility review")
            if not isinstance(review.get("checks"), list) or not review["checks"]:
                raise RunnerError("G5 requires recorded responsibility checks for object-oriented changes")
    if strict and skill in {"core.implementation-quality", "core.verify-and-handoff"}:
        operator = state["execution"]["operator"]
        planned = _operator_test_plan(state, operator["completed"]["G4"]["test_plan"], target)
        if skill == "core.implementation-quality":
            verify_tdd(result.get("tdd_results"), planned, target)
        else:
            quality = operator["results"].get("core.implementation-quality", {}).get("implementation_quality", {})
            documentation = quality.get("documentation_check")
            verification = result.get("verified_checks")
            verify_results(verification, planned, _documentation_targets(target, documentation) if documentation else [], target)
            plan = state["route"]["work_plan"]
            if plan.get("required_native_roles"):
                verifier = next(item for item in plan["units"] if item["role"] == "verifier" and item["skill_id"] == skill)
                receipt = state["execution"]["work_records"][verifier["id"]]
                if verification["target_revision"] != receipt["input_revision"]:
                    raise RunnerError("verification snapshot must match the independent worker input revision")
    elif skill == "core.verify-and-handoff":
        kinds = _required_check_kinds(state) & {"performance_measurement", "deadline_measurement"}
        if kinds:
            planned = test_plan(result.get("test_plan"), requirements(result.get("requirements"), criteria, target), kinds, target)
            verify_results(result.get("verified_checks"), planned, [], target)


def validate_checkpoint_evidence(value: Any, target: Path) -> dict:
    """
    역할: 사용자가 실행한 게이트를 확인할 근거를 프로젝트 내부의 실제 파일에 연결한다.
    입력: value는 확인 레코드, target은 프로젝트다.
    출력: 확인된 레코드
    """
    record = evidence_record(value, target, "checkpoint")
    note = record.get("user_decision")
    if not isinstance(note, str) or not note.strip():
        raise RunnerError("checkpoint requires the recorded user decision")
    return record


def reopen_checkpoint(state: dict, gate: str) -> None:
    """
    역할: 지정된 사용자 게이트부터 완료 기록을 무효화하고 정확한 위치로 되돌린다.
    입력: state는 작업 상태, gate는 다시 열 게이트다.
    """
    execution = state["execution"]
    operator = execution["operator"]
    operator["gate"] = gate
    operator["opened"] = None
    operator["completed"] = {key: value for key, value in operator["completed"].items() if key < gate}
    operator["results"] = {
        skill: value for skill, value in operator["results"].items()
        if execution["skill_gates"][skill] < gate
    }
    state["stage"] = GATE_STAGE[gate]


def checkpoint(target_root: Path, task_id: str, expected_revision: int, request_path: Path,
               harness_root: Path, registry_path: Path) -> dict:
    """
    역할: 사용자 요청과 증거가 일치하는 게이트 하나를 열거나 완료한다.
    입력: target_root·task_id는 작업 위치, expected_revision은 상태 버전, request_path는 요청,
          harness_root·registry_path는 승인된 소스와 레지스트리다.
    출력: 사용자 게이트와 현재 실행 가능한 스킬 안내
    """
    verify_source(harness_root, registry_path)
    request = read_object(request_path)
    gate, operation = request.get("gate"), request.get("operation")
    if isinstance(gate, str) and gate not in GATE_IDS:
        manifest = _load_manifest(harness_root / "registry/routing-gates.json")
        gate = next((item["id"] for item in manifest["gates"] if item.get("operator_name") == gate), None)
    if gate not in GATE_IDS[2:] or operation not in ("open", "close"):
        raise RunnerError("checkpoint requires a gate name or G2–G7 ID and an open or close operation")
    evidence = validate_checkpoint_evidence(request.get("confirmation"), target_root)
    store = StateStore(target_root, harness_root=harness_root)

    def mutate(state: dict) -> None:
        """
        역할: 잠긴 리비전에서 사용자 게이트 전이를 적용한다.
        입력: state는 작업 상태의 갱신 사본이다.
        """
        execution = state["execution"]
        operator = execution.get("operator")
        if state["status"] != "active" or operator is None or operator["gate"] != gate:
            raise RunnerError("only the current active user checkpoint can change")
        record = {**evidence, "recorded_revision": state["revision"] + 1}
        previous_stage = state["stage"]
        if operation == "open":
            if operator["opened"] is not None:
                raise RunnerError("checkpoint is already open")
            operator["opened"] = record
            state["stage"] = GATE_STAGE[gate]
        else:
            if operator["opened"] is None:
                raise RunnerError("open the user checkpoint before closing it")
            cursor, queue = execution["cursor"], execution["queue"]
            if cursor < len(queue) and execution["skill_gates"][queue[cursor]] <= gate:
                raise RunnerError("finish the current gate's queued skills before closing it")
            if gate == "G4" and _engineering_checkpoints(state):
                _operator_test_plan(state, request.get("test_plan"), target_root)
                record["test_plan"] = request["test_plan"]
            operator["completed"][gate] = {**record, "opening": operator["opened"]}
            operator["opened"] = None
            if gate == "G7":
                verified = operator["results"].get("core.verify-and-handoff")
                if verified is None:
                    raise RunnerError("G7 requires accepted verification")
                require_join(state, "core.verify-and-handoff", target_root)
                validate_acceptance_evidence(verified.get("verification"), state["intent"]["success_criteria"], target_root)
                validate_engineering_result(state, verified, target_root)
                state.update(status="complete", validation_status="passed", stage="handoff")
            else:
                operator["gate"] = GATE_IDS[GATE_IDS.index(gate) + 1]
                state["stage"] = GATE_STAGE[operator["gate"]]
        state["last_transition"] = {
            "from": previous_stage, "to": state["stage"], "reason": f"{operation} user checkpoint {gate}",
            "actor": "harness_runner", "at": utc_now(),
        }

    updated = store.update(task_id, expected_revision, f"checkpoint_{operation}", mutate, {"gate": gate})
    if updated["status"] == "complete":
        write_handoff(store, updated)
    return _response(updated, _registry_entries(registry_path), harness_root)


def write_handoff(store: StateStore, state: dict) -> None:
    """
    역할: 현재 유효한 산출물과 증거를 인계 문서에 기록한다.
    입력: store는 프로젝트 상태 저장소, state는 완료한 작업이다.
    """
    execution = state["execution"]
    operator = execution.get("operator")
    ids = {key: execution[key] for key in ("artifact_ids", "evidence_ids")}
    if operator is not None:
        ids = {key: list(dict.fromkeys(item for result in operator["results"].values() for item in result[key]))
               for key in ids}
    store.write_handoff(state["task_id"], "\n".join([
        "# Task handoff", "",
        f"- Task: {state['task_id']}", f"- Request: {state['request_id']}", f"- Revision: {state['revision']}",
        f"- Status: {state['status']}", f"- Completed skills: {execution['cursor']}",
        f"- Artifact IDs: {', '.join(ids['artifact_ids']) or 'none'}",
        f"- Evidence IDs: {', '.join(ids['evidence_ids']) or 'none'}",
    ]))


def _validate_typed_payload(result: dict[str, Any], target_root: Path, required_profiles: set[str]) -> None:
    """
    역할: 패턴 검토·구현 품질 스킬의 형식 기록을 검증하고, 구현 품질 완료 시
          코드 문서화(한글 헤더·함수 주석) 검사와 코드↔문서 동기화(모듈 맵) 검사를
          직접 다시 실행한다.

    입력:
        result: 제출된 스킬 결과
        target_root: 문서화 검사를 실행할 대상 프로젝트 루트
        required_profiles: 현재 라우팅이 요구한 구현 품질 프로파일
    예외:
        RunnerError, ContractError: 기록이 없거나 계약을 어기거나 문서화·동기화 검사가 실패한 경우
    """
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
        if status == "completed":
            submitted_profiles = {entry["id"] for entry in quality["activated_profiles"]}
            if not required_profiles <= submitted_profiles:
                raise RunnerError(f"required quality profiles are missing: {sorted(required_profiles - submitted_profiles)}")
            documentation = quality["documentation_check"]
            try:
                files = _documentation_targets(target_root, documentation)
                report = check_code_docs(target_root, files, documentation.get("base_revision"))
            except (OSError, ValueError, RuntimeError) as exc:
                raise RunnerError(f"documentation check could not run: {exc}") from exc
            if report["status"] != "passed":
                problems = [f["path"] for f in report["files"] if f["header"] != "ok" or f["function_problems"]]
                raise RunnerError("code documentation check failed (Korean header or function comments): "
                                  + ", ".join(problems))
            try:
                sync = check_doc_sync(target_root, files, None,
                                      documentation.get("module_map") or DEFAULT_MAP,
                                      documentation.get("exempt_paths", []))
            except (OSError, ValueError, RuntimeError) as exc:
                raise RunnerError(f"document sync check could not run: {exc}") from exc
            if sync["status"] != "passed":
                raise RunnerError("documents and code disagree (module map): "
                                  + "; ".join(f"{v['kind']} {v['path']}" for v in sync["violations"][:8]))


def _feedback_plan(state: dict[str, Any], result: dict[str, Any], manifest_path: Path) -> dict[str, Any] | None:
    """
    역할: 실패 신호를 실제 담당 게이트의 재실행, G0 재확인 또는 사용자 확인으로 연결한다.
    입력: state는 현재 상태, result는 실패 결과, manifest_path는 라우팅 계약 경로다.
    출력: 되돌림 계획 또는 피드백이 없으면 None
    """
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
    if target_gate == "G0":
        reason = "Recheck the task guard and record the recovery decision before resuming."
        if attempt >= FEEDBACK_RETRY_LIMIT:
            reason = "G0 reached the retry limit; obtain a user decision and recheck the task guard."
        return {**plan, "action": "guard", "reason": reason}
    if attempt >= FEEDBACK_RETRY_LIMIT:
        if target_gate == "G1" or ("operator" not in execution and target_gate not in execution["skill_gates"].values()):
            return {**plan, "action": "restart",
                    "reason": f"Feedback to {target_gate} reached the retry limit; use a user-approved linked restart."}
        return {**plan, "action": "escalate",
                "reason": f"Feedback to {target_gate} reached the retry limit; a user decision is required."}
    if target_gate == "G1" or ("operator" not in execution and target_gate not in execution["skill_gates"].values()):
        return {**plan, "action": "restart",
                "reason": f"{target_gate} has no queued owner; correct the intake through a linked restart."}
    gates = execution["skill_gates"]
    index = next((i for i, skill in enumerate(execution["queue"][:cursor + 1])
                  if int(gates[skill][1:]) >= int(target_gate[1:])), None)
    if index is None:
        return {**plan, "action": "escalate",
                "reason": f"{target_gate} has no queued owner; correct the intake through a linked restart."}
    reopened = set(execution["queue"][index:])
    if ("operator" not in execution
            and any(item.get("skill_id") in reopened for item in execution.get("work_records", {}).values())):
        return {**plan, "action": "escalate",
                "reason": "Recorded work units belong to the reopened gates; recover through a linked restart."}
    return {**plan, "action": "rewind", "cursor": index}


def resume(target_root: Path, task_id: str, expected_revision: int, request_path: Path,
           harness_root: Path, registry_path: Path) -> dict[str, Any]:
    """
    역할: 중단된 스킬을 재개하며, G0가 중단한 작업은 새로운 가드 증거를 확인한다.
    입력: target_root·task_id는 작업 위치, expected_revision은 상태 버전, request_path는 재개 요청,
          harness_root·registry_path는 승인된 하네스 소스와 레지스트리다.
    출력: 갱신된 작업 상태와 다음 스킬 안내
    """
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

    refreshed_intake = None
    if current["suspended_by"] == "G0":
        refreshed_intake = dict(current["intake"])
        if refreshed_intake.get("enforcement_mode") == "hook":
            guard = validate_hook_guard(request.get("hook_guard"), target_root, task_id, current["selected_adapter"])
            previous = refreshed_intake.get("hook_guard", {})
            if (guard["task_status"] != current["status"] or guard["task_revision"] != current["revision"]
                    or (guard["session_id"], guard["tool_use_id"]) == (previous.get("session_id"), previous.get("tool_use_id"))):
                raise RunnerError("G0 requires a fresh hook denial observed during this hold")
            refreshed_intake["hook_guard"] = guard
        else:
            guard = request.get("manual_guard")
            if guard == refreshed_intake.get("manual_guard"):
                raise RunnerError("G0 requires a fresh manual guard for this task")
            refreshed_intake.update(manual_guard=guard, manual_guard_valid=True)
        validate_intake(refreshed_intake, harness_root / "registry/taxonomy.json", require_intent=True)

    def mutate(state: dict[str, Any]) -> None:
        """
        역할: 확인된 결정과 새 가드 증거를 기록하고 중단된 스킬 위치에서 재개한다.
        입력: state는 잠긴 작업 상태의 갱신 사본이다.
        """
        execution = state["execution"]
        pending = execution["queue"][execution["cursor"]]
        execution.setdefault("decisions", []).append({
            "skill_id": state["suspended_by"], "previous_status": state["status"],
            "answer": answer, "decision_evidence_ids": evidence, "at": utc_now()})
        previous_stage = state["stage"]
        state["status"] = "active"
        operator = execution.get("operator")
        state["stage"] = GATE_STAGE[operator["gate"]] if operator is not None else execution["skill_stages"][pending]
        if refreshed_intake is not None:
            state["intake"] = refreshed_intake
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
    """
    역할: 현재 게이트의 워커 준비·종료 영수증을 잠긴 상태에 기록한다.
    입력: target_root·task_id는 작업 위치, expected_revision은 상태 버전, request_path와 command는 요청,
          harness_root·registry_path는 승인된 소스와 레지스트리다.
    출력: 작업 상태와 워커 결과
    """
    verify_source(harness_root, registry_path)
    request = read_object(request_path)
    store = StateStore(target_root, harness_root=harness_root)
    output: dict[str, Any] = {}

    def mutate(state: dict[str, Any]) -> None:
        """
        역할: 게이트가 열린 경우에만 새 워커를 준비하고 이미 실행된 결과를 기록한다.
        입력: state는 잠긴 작업 상태의 갱신 사본이다.
        """
        if command == "prepare-work":
            operator = state["execution"].get("operator")
            if operator is not None:
                pending = _next_item(state, _registry_entries(registry_path), harness_root)
                if not operator["opened"] or pending is None or pending["execution_profile"]["gate_id"] != operator["gate"]:
                    raise RunnerError("open the current user checkpoint before preparing work")
            output.update(prepare(state, request, target_root, harness_root=harness_root, registry_path=registry_path))
        else:
            record(state, request, target=target_root)

    updated = store.update(task_id, expected_revision, command.replace("-", "_"), mutate)
    return {**_response(updated, _registry_entries(registry_path), harness_root), **output}


def main(argv: Iterable[str] | None = None) -> int:
    """
    역할: Runner 명령에서 작업과 사용자 게이트 요청을 처리한다.
    입력: argv는 명령행 인자다.
    출력: 명령 종료 코드
    """
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

    for command in ("prepare-work", "record-work", "resume", "checkpoint"):
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
        elif args.command == "checkpoint":
            result = checkpoint(args.target_root, args.task_id, args.expected_revision,
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
