"""Small, deterministic work-plan projection; never spawns agents or grants tools."""

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


class WorkflowError(ValueError):
    pass


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
    profile = context.get("work_type", "standard")
    if not isinstance(profile, str) or profile not in PROFILES:
        raise WorkflowError(f"unsupported work_type: {profile}")
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
        if (not isinstance(unit.get("role"), str) or unit["role"] not in ROLES
                or not isinstance(unit.get("mutation"), str)
                or unit["mutation"] not in {"none", "workspace"}):
            raise WorkflowError("invalid unit role or mutation")
        if unit["role"] in {"analyst", "designer", "reviewer", "verifier"} and unit["mutation"] != "none":
            raise WorkflowError("analysis and review personas are read-only")
        _strings(unit, "depends_on")
        _strings(unit, "evidence_ids", required=True)
        _strings(unit, "acceptance", required=True)
        _strings(unit, "allowed_tools", required=True)
        _strings(unit, "shared_resources")
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
    for key in ("max_workers", "timeout_seconds"):
        if key in delegation and (type(delegation[key]) is not int or delegation[key] < 1):
            raise WorkflowError(f"delegation.{key} must be a positive integer")
    for key in ("benefit_evidence_ids", "authorization_evidence_ids", "capability_evidence_ids"):
        _strings(delegation, key)


def validate_work_plan(plan: Any, route_status: str) -> None:
    """Validate externally supplied projections without granting dispatch authority."""
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
    limit = delegation.get("max_workers", 1) if not reasons else 1
    remaining = list(units)
    done: set[str] = set()
    batches = []
    while remaining:
        ready = [u for u in remaining if set(u.get("depends_on", [])) <= done]
        batch: list[dict] = []
        for unit in ready:
            if len(batch) < limit and not any(_conflict(unit, selected) for selected in batch):
                batch.append(unit)
        batches.append([u["id"] for u in batch])
        done.update(batches[-1])
        remaining = [u for u in remaining if u["id"] not in done]
    parallel = any(len(batch) > 1 for batch in batches)
    if not parallel and not reasons:
        reasons.append("dependencies_ownership_or_capacity_require_serial")
    return {
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
