"""
모듈: 하네스 런타임 (scripts)
컴포넌트: 작업 계획기
역할: 범위가 제한된 작업 단위, 의존성 및 실행 방식을 계산한다.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any


PROFILES = {
    "standard": ["baseline", "impact_or_requirements", "implement", "verify", "handoff"],
    "bugfix": ["baseline", "reproduce", "impact", "fix", "regression", "handoff"],
    "feature": ["baseline", "requirements", "contracts", "vertical_slice", "integration", "handoff"],
    "refactor": ["baseline", "behavior_contract", "impact", "refactor", "regression", "handoff"],
    "research": ["question", "evidence", "synthesis", "verify_claims", "handoff"],
    "document": ["purpose", "source_evidence", "draft", "check_links_and_claims", "handoff"],
    "infrastructure": ["baseline", "configuration", "rollback", "authorized_change", "verify", "handoff"],
    "maintenance": ["harness_baseline", "approved_change", "fixtures", "document_sync", "handoff"],
}
ROLES = {"analyst", "designer", "implementer", "reviewer", "verifier", "documenter"}
REASONING_LENSES = {"meticulous", "minimal_sufficient"}
NATIVE_DEVELOPMENT_ROLES = ("implementer", "verifier")


class WorkflowError(ValueError):
    pass


def native_development_required(context: dict[str, Any]) -> bool:
    """
    역할: 사용자 주도 개발 경로에 독립 실행 작업자가 필요한지 판정한다.
    입력: context는 검증된 작업 분류와 실행 방식이다.
    출력: G6 구현자와 G7 검증자의 실제 실행이 필요한 경우 True
    """
    return (
        context.get("operator_mode") == "jydlc"
        and context.get("target") == "project"
        and context.get("scope") in ("software_engineering", "software_related")
        and context.get("action") in ("implement", "change")
        and (context.get("language_scope") == "authored_in_scope"
             or "authored_code" in context.get("change_characteristics", [])
             or (bool(context.get("languages")) and "language_scope" not in context))
    )


def _strings(obj: dict, key: str, required: bool = False) -> list[str]:
    value = obj.get(key, [])
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise WorkflowError(f"{key} must be an array of non-empty strings")
    if required and not value:
        raise WorkflowError(f"{key} must not be empty")
    if len(value) != len(set(value)):
        raise WorkflowError(f"{key} must not contain duplicates")
    return value


def _paths(unit: dict, key: str) -> list[str]:
    values = _strings(unit, key)
    for value in values:
        path = PurePosixPath(value)
        if (path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value
                or any(c in value for c in "*?[]") or value != path.as_posix()):
            raise WorkflowError(f"{key} requires canonical relative paths, without globs")
    return values


def validate_workflow_input(context: dict[str, Any]) -> None:
    """
    역할: 스코프, 작업 분류, 위임 권한과 작업 단위의 구조를 검증한다.
    입력: context는 라우팅에 제출할 작업 구성이다.
    """
    if context.get("operator_mode") not in (None, "jydlc"):
        raise WorkflowError("operator_mode must be jydlc when specified")
    profile = context.get("work_type", "standard")
    if not isinstance(profile, str) or profile not in PROFILES:
        raise WorkflowError(f"unsupported work_type: {profile}")
    characteristics = _strings(context, "change_characteristics")
    only = set(characteristics) & {"documentation_only", "generated_code_only"}
    if only and (len(only) > 1 or "authored_code" in characteristics
                 or context.get("language_scope") == "authored_in_scope"):
        raise WorkflowError("only-content classification conflicts with authored code or another only flag")
    units = context.get("work_units", [])
    if not isinstance(units, list):
        raise WorkflowError("work_units must be an array")
    seen: set[str] = set()
    for unit in units:
        if not isinstance(unit, dict):
            raise WorkflowError("each work unit must be an object")
        for key in ("id", "goal", "input_revision", "expected_output"):
            if not isinstance(unit.get(key), str) or not unit[key].strip():
                raise WorkflowError(f"work unit requires {key}")
        if unit["id"] in seen:
            raise WorkflowError("duplicate work unit id")
        seen.add(unit["id"])
        if "skill_id" in unit and (not isinstance(unit["skill_id"], str) or not unit["skill_id"].startswith("core.")):
            raise WorkflowError("work unit skill_id must name a core skill")
        if (not isinstance(unit.get("role"), str) or unit["role"] not in ROLES
                or not isinstance(unit.get("mutation"), str)
                or unit["mutation"] not in {"none", "workspace"}):
            raise WorkflowError("invalid unit role or mutation")
        if unit["role"] in {"analyst", "designer", "reviewer", "verifier"} and unit["mutation"] != "none":
            raise WorkflowError("analysis and review personas are read-only")
        if "reasoning_lens" in unit and (not isinstance(unit["reasoning_lens"], str)
                or unit["reasoning_lens"] not in REASONING_LENSES):
            raise WorkflowError("unsupported reasoning_lens")
        _strings(unit, "depends_on")
        _strings(unit, "evidence_ids", required=True)
        _strings(unit, "acceptance", required=True)
        _strings(unit, "allowed_tools", required=True)
        _strings(unit, "shared_resources")
        _paths(unit, "skill_references")
        _paths(unit, "read_paths")
        writes = _paths(unit, "write_paths")
        if (unit["mutation"] == "workspace") != bool(writes):
            raise WorkflowError("workspace units require write paths; read-only units cannot own writes")
    for unit in units:
        if set(unit.get("depends_on", [])) - seen or unit["id"] in unit.get("depends_on", []):
            raise WorkflowError("unknown or self-referencing work dependency")
    remaining = {u["id"]: set(u.get("depends_on", [])) for u in units}
    done: set[str] = set()
    while remaining:
        ready = {key for key, deps in remaining.items() if deps <= done}
        if not ready:
            raise WorkflowError("cyclic work dependencies")
        done |= ready
        remaining = {key: deps for key, deps in remaining.items() if key not in ready}
    delegation = context.get("delegation", {})
    if not isinstance(delegation, dict):
        raise WorkflowError("delegation must be an object")
    for key in ("requested", "authorized", "available"):
        if key in delegation and type(delegation[key]) is not bool:
            raise WorkflowError(f"delegation.{key} must be boolean")
    for key in ("max_workers", "timeout_seconds", "worker_token_budget"):
        if key in delegation and (type(delegation[key]) is not int or delegation[key] < 1):
            raise WorkflowError(f"delegation.{key} must be a positive integer")
    if "native_worker_capacity" in delegation and (type(delegation["native_worker_capacity"]) is not int or delegation["native_worker_capacity"] < 0):
        raise WorkflowError("native_worker_capacity must be a nonnegative integer")
    for key in ("benefit_evidence_ids", "authorization_evidence_ids", "capability_evidence_ids"):
        _strings(delegation, key)


def validate_work_plan(plan: Any, route_status: str) -> None:
    """
    역할: 작업 계획에 포함된 역할·의존성·실행 수와 권한 경계를 검증한다.
    입력: plan은 작업 계획이며 route_status는 현재 라우팅 상태다.
    """
    if not isinstance(plan, dict) or plan.get("schema_version") != 1:
        raise WorkflowError("work_plan must be a versioned object")
    validate_workflow_input({"work_type": plan.get("work_type"), "work_units": plan.get("units")})
    if plan.get("dispatch_authorized") is not False or plan.get("adapter_recheck_required") is not True:
        raise WorkflowError("work_plan cannot grant dispatch authority")
    if plan.get("mandatory_gate_checks") != [f"G{i}" for i in range(8)]:
        raise WorkflowError("work_plan cannot omit mandatory gates")
    if plan.get("steps") != PROFILES[plan["work_type"]]:
        raise WorkflowError("work_plan steps do not match work type")
    if plan.get("depth") not in {"light", "standard", "deep"}:
        raise WorkflowError("invalid work_plan depth")
    required_native = plan.get("required_native_roles", [])
    if required_native not in ([], list(NATIVE_DEVELOPMENT_ROLES)):
        raise WorkflowError("invalid required native worker roles")
    units = {u["id"]: u for u in plan["units"]}
    done: set[str] = set()
    batches = plan.get("batches")
    if not isinstance(batches, list):
        raise WorkflowError("work_plan batches must be an array")
    for batch in batches:
        if (not isinstance(batch, list) or not batch
                or any(not isinstance(key, str) for key in batch)
                or len(batch) != len(set(batch))):
            raise WorkflowError("invalid work_plan batch")
        if set(batch) - units.keys() or set(batch) & done:
            raise WorkflowError("unknown or repeated batch unit")
        if len(batch) > 1 and (not units[batch[0]].get("skill_id") or
                len({units[key].get("skill_id") for key in batch}) != 1):
            raise WorkflowError("concurrent units require the same bound skill")
        for i, key in enumerate(batch):
            if not set(units[key].get("depends_on", [])) <= done:
                raise WorkflowError("work_plan dependency not joined")
            if any(_conflict(units[key], units[other]) for other in batch[:i]):
                raise WorkflowError("work_plan has conflicting concurrent units")
        done.update(batch)
    if done != units.keys():
        raise WorkflowError("work_plan omitted a unit")
    workers = max((len(b) for b in batches), default=1)
    if type(plan.get("max_workers")) is not int or plan["max_workers"] != workers:
        raise WorkflowError("work_plan worker count mismatch")
    if plan.get("mode") != ("parallel" if workers > 1 else "single"):
        raise WorkflowError("work_plan mode mismatch")
    if workers > 1 and route_status != "active":
        raise WorkflowError("inactive route cannot plan parallel work")


def _overlap(left: str, right: str) -> bool:
    a, b = PurePosixPath(left), PurePosixPath(right)
    return a == b or a in b.parents or b in a.parents


def _conflict(a: dict, b: dict) -> bool:
    if set(a.get("shared_resources", [])) & set(b.get("shared_resources", [])):
        return True
    for writer, other in ((a, b), (b, a)):
        if writer.get("write_paths") and not other.get("read_paths") and not other.get("write_paths"):
            return True  # Unknown read scope is not evidence of independence.
        if any(_overlap(w, p) for w in writer.get("write_paths", [])
               for p in other.get("read_paths", []) + other.get("write_paths", [])):
            return True
    return False


def compose_work_plan(context: dict[str, Any], route_status: str) -> dict[str, Any]:
    """
    역할: 작업 의존성을 배열하고 실행 가능 인원과 필수 실제 작업자 역할을 표시한다.
    입력: context는 작업 분류와 후보 작업 단위이며 route_status는 현재 라우팅 상태다.
    출력: 바인딩·배치·위임 조건을 담은 작업 계획
    """
    validate_workflow_input(context)
    target, action = context.get("target"), context.get("action")
    profile = context.get("work_type", "standard")
    if target == "harness":
        profile = "maintenance"
    elif action == "document" or target == "harness_overview":
        profile = "document"
    elif profile == "standard" and action in {"investigate", "review"}:
        profile = "research"
    units = context.get("work_units", [])
    delegation = context.get("delegation", {})
    reasons = []
    for key in ("requested", "authorized", "available"):
        if delegation.get(key) is not True:
            reasons.append(f"delegation_{key}_not_confirmed")
    for key in ("benefit_evidence_ids", "authorization_evidence_ids", "capability_evidence_ids"):
        if not delegation.get(key):
            reasons.append(f"missing_{key}")
    if "timeout_seconds" not in delegation:
        reasons.append("missing_timeout")
    if len(units) < 2:
        reasons.append("fewer_than_two_units")
    if route_status != "active":
        reasons.append("route_not_active")
    if not delegation.get("native_worker_capacity"):
        reasons.append("native_worker_capacity_unconfirmed_or_zero")
    if "worker_token_budget" in delegation:
        reasons.append("worker_token_budget_requires_reported_usage_before_next_dispatch")
    limit = min(delegation.get("max_workers", 1), delegation.get("native_worker_capacity", 1)) if not reasons else 1
    remaining = list(units)
    done: set[str] = set()
    batches = []
    while remaining:
        ready = [u for u in remaining if set(u.get("depends_on", [])) <= done]
        batch: list[dict] = []
        for unit in ready:
            if (len(batch) < limit
                    and (not batch or (unit.get("skill_id") and unit.get("skill_id") == batch[0].get("skill_id")))
                    and not any(_conflict(unit, selected) for selected in batch)):
                batch.append(unit)
        batches.append([u["id"] for u in batch])
        done.update(batches[-1])
        remaining = [u for u in remaining if u["id"] not in done]
    parallel = any(len(batch) > 1 for batch in batches)
    if not parallel and not reasons:
        reasons.append("dependencies_ownership_or_capacity_require_serial")
    projected = {
        "schema_version": 1,
        "work_type": profile,
        "depth": context.get("depth", "standard"),
        "steps": PROFILES[profile],
        "mandatory_gate_checks": [f"G{i}" for i in range(8)],
        "mode": "parallel" if parallel else "single",
        "max_workers": max((len(batch) for batch in batches), default=1),
        "batches": batches,
        "units": units,
        "reasons": reasons,
        "dispatch_authorized": False,
        "adapter_recheck_required": True,
        "join_policy": "all_required_results_current_and_verified",
        "failure_policy": "preserve_valid_results_reopen_nearest_gate",
        "timeout_seconds": delegation.get("timeout_seconds"),
        "out_of_scope": "No skill promotion, tool permission, deployment, or agent spawn is implied.",
    }
    if native_development_required(context):
        projected["required_native_roles"] = list(NATIVE_DEVELOPMENT_ROLES)
    return projected
