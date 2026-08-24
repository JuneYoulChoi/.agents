#!/usr/bin/env python3
"""Small standard-library validators for the portable harness contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCOPES = {
    "software_engineering",
    "software_related",
    "general_information",
    "decision_support",
    "creative",
    "non_engineering",
}
PROJECT_STATES = {"greenfield", "brownfield", "hybrid", "unknown", "not_applicable"}
ACTIONS = {
    "investigate",
    "define",
    "plan",
    "design",
    "implement",
    "change",
    "verify",
    "review",
    "document",
    "approve",
    "handoff",
}
TASK_STATUSES = {"active", "waiting_user", "blocked", "failed", "cancelled", "complete"}
STAGES = {
    "intake",
    "clarification",
    "discovery",
    "architecture",
    "impact",
    "assembly",
    "deliberation",
    "design",
    "execution",
    "verification",
    "handoff",
}
SKILL_RESULT_STATUSES = {"completed", "not_applicable", "waiting_user", "blocked", "failed"}
REASONING_LEVELS = {"low", "medium", "high"}
PATTERN_CANDIDATE_STATUSES = {
    "existing",
    "candidate",
    "selected",
    "rejected",
    "not_applicable",
}
PATTERN_DECISION_STATUSES = {
    "not_applicable",
    "single_viable",
    "user_decision_required",
    "user_selected",
    "existing_decision",
}
EXECUTION_ROLES = {
    "guard",
    "classifier",
    "architect",
    "analyst",
    "planner",
    "specialist",
    "implementer",
    "verifier",
}
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ContractError(ValueError):
    """Raised when a portable harness object violates a required invariant."""


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path} must contain a JSON object")
    return value


def write_object(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(data)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ContractError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def root_fingerprint(root: Path) -> str:
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise ContractError(f"target root cannot be resolved: {exc}") from exc
    if not resolved.is_dir():
        raise ContractError("target root must be an existing directory")
    return "sha256:" + sha256_bytes(str(resolved).encode("utf-8"))


def validate_identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ContractError(f"{name} must be a portable identifier")
    return value


def safe_relative_path(value: Any, name: str) -> Path:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise ContractError(f"{name} must be a non-empty POSIX-style relative path")
    candidate = Path(value)
    if candidate.is_absolute() or re.match(r"^[A-Za-z]:", value):
        raise ContractError(f"{name} must not be absolute")
    if any(part in {"", ".", ".."} for part in candidate.parts):
        raise ContractError(f"{name} must not contain empty, current, or parent segments")
    return candidate


def contained_path(root: Path, relative: Any, name: str, must_exist: bool = False) -> Path:
    rel = safe_relative_path(relative, name)
    root_resolved = root.resolve(strict=True)
    path = root_resolved.joinpath(rel)
    try:
        resolved = path.resolve(strict=must_exist)
    except OSError as exc:
        raise ContractError(f"{name} cannot be resolved: {exc}") from exc
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ContractError(f"{name} escapes the selected root")
    return resolved


def _require_string(value: dict[str, Any], key: str, allowed: set[str] | None = None) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ContractError(f"{key} must be a non-empty string")
    if allowed is not None and item not in allowed:
        raise ContractError(f"{key} has unsupported value: {item}")
    return item


def _string_array(value: dict[str, Any], key: str) -> list[str]:
    items = value.get(key, [])
    if not isinstance(items, list) or any(not isinstance(item, str) or not item for item in items):
        raise ContractError(f"{key} must be an array of non-empty strings")
    if len(items) != len(set(items)):
        raise ContractError(f"{key} must not contain duplicates")
    return items


def field_ids(taxonomy_path: Path) -> set[str]:
    taxonomy = read_object(taxonomy_path)
    fields = taxonomy.get("fields")
    if not isinstance(fields, list):
        raise ContractError("field taxonomy must contain a fields array")
    result = {
        item.get("id")
        for item in fields
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if len(result) != len(fields):
        raise ContractError("field taxonomy contains a missing or duplicate id")
    return result


def active_skill_ids(registry_path: Path) -> set[str]:
    registry = read_object(registry_path)
    skills = registry.get("skills")
    if not isinstance(skills, list):
        raise ContractError("active registry must contain a skills array")
    result: set[str] = set()
    for skill in skills:
        if not isinstance(skill, dict):
            raise ContractError("each active skill entry must be an object")
        skill_id = validate_identifier(skill.get("id"), "skill.id")
        if skill_id in result:
            raise ContractError(f"duplicate active skill id: {skill_id}")
        if skill.get("trust") != "approved":
            raise ContractError(f"active skill is not approved: {skill_id}")
        entry = safe_relative_path(skill.get("entry"), f"{skill_id}.entry")
        if "incoming" in entry.parts:
            raise ContractError(f"active skill points to quarantine: {skill_id}")
        result.add(skill_id)
    return result


def _validate_artifact_graph(artifacts: Any) -> None:
    if not isinstance(artifacts, list):
        raise ContractError("artifacts must be an array")
    dependencies: dict[str, list[str]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ContractError("each artifact must be an object")
        artifact_id = validate_identifier(artifact.get("id"), "artifact.id")
        if artifact_id in dependencies:
            raise ContractError(f"duplicate artifact id: {artifact_id}")
        depends_on = artifact.get("depends_on", [])
        if not isinstance(depends_on, list) or any(not isinstance(item, str) for item in depends_on):
            raise ContractError("artifact.depends_on must be an array of strings")
        dependencies[artifact_id] = depends_on
    for artifact_id, parents in dependencies.items():
        unknown = set(parents) - dependencies.keys()
        if unknown:
            raise ContractError(f"artifact {artifact_id} has unknown dependencies: {sorted(unknown)}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(artifact_id: str) -> None:
        if artifact_id in visiting:
            raise ContractError("artifact dependency graph must be acyclic")
        if artifact_id in visited:
            return
        visiting.add(artifact_id)
        for parent in dependencies[artifact_id]:
            visit(parent)
        visiting.remove(artifact_id)
        visited.add(artifact_id)

    for artifact_id in dependencies:
        visit(artifact_id)


def validate_intake(
    value: dict[str, Any], taxonomy_path: Path, require_intent: bool = False
) -> dict[str, Any]:
    if value.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")
    validate_identifier(value.get("request_id"), "request_id")
    _require_string(value, "target", {"project", "harness", "harness_overview"})
    _require_string(value, "scope", SCOPES)
    _require_string(value, "project_state", PROJECT_STATES)
    _require_string(value, "action", ACTIONS)
    if require_intent:
        _require_string(value, "risk", {"low", "medium", "high"})
        _require_string(value, "depth", {"light", "standard", "deep"})
        _require_string(value, "confidence", {"low", "medium", "high"})
        intent = value.get("intent")
        if not isinstance(intent, dict):
            raise ContractError("durable intake requires an intent object")
        _require_string(intent, "goal")
        _string_array(intent, "success_criteria")
        _string_array(intent, "constraints")
    fields = _string_array(value, "fields")
    unknown_fields = set(fields) - field_ids(taxonomy_path)
    if unknown_fields:
        raise ContractError(f"unknown classification fields: {sorted(unknown_fields)}")
    _string_array(value, "languages")
    _string_array(value, "evidence_ids")
    _string_array(value, "standards")
    _string_array(value, "authorized_standard_evidence_ids")
    _require_string(
        value,
        "conformance_intent",
        {"guidance", "alignment", "conformance"},
    ) if "conformance_intent" in value else None
    _require_string(value, "conformance_scope") if "conformance_scope" in value else None
    _require_string(value, "conformance_owner") if "conformance_owner" in value else None
    pattern_scopes = _string_array(value, "pattern_scopes")
    unknown_pattern_scopes = set(pattern_scopes) - {"architecture", "design"}
    if unknown_pattern_scopes:
        raise ContractError(
            f"unsupported pattern scopes: {sorted(unknown_pattern_scopes)}"
        )
    characteristics = _string_array(value, "change_characteristics")
    allowed_characteristics = {
        "authored_code",
        "architecture_structure",
        "design_interaction",
        "object_oriented",
        "functional",
        "data_oriented",
        "api_data_contract",
        "concurrency",
        "distributed",
        "security",
        "performance",
        "realtime_embedded",
        "configuration",
        "documentation_only",
        "generated_code_only",
    }
    unknown_characteristics = set(characteristics) - allowed_characteristics
    if unknown_characteristics:
        raise ContractError(
            f"unsupported change characteristics: {sorted(unknown_characteristics)}"
        )
    language_scope = value.get(
        "language_scope", "authored_in_scope" if value.get("languages") else "none"
    )
    if language_scope not in {"authored_in_scope", "detected_only", "generated_only", "none"}:
        raise ContractError(f"unsupported language_scope: {language_scope}")
    if not value.get("languages") and language_scope != "none":
        raise ContractError("language_scope must be none when languages is empty")
    enforcement = value.get("enforcement_mode", "manual")
    if enforcement not in {"hook", "manual", "unsupported"}:
        raise ContractError("enforcement_mode must be hook, manual, or unsupported")
    if require_intent and enforcement == "manual" and value.get("manual_guard_valid") is True:
        guard = value.get("manual_guard")
        if not isinstance(guard, dict):
            raise ContractError("manual_guard_valid requires a manual_guard object")
        for key in ("approval_id", "action_id", "actor", "at", "expires_at", "rollback_plan", "verifier"):
            _require_string(guard, key)
        allowed_paths = _string_array(guard, "allowed_paths")
        allowed_actions = _string_array(guard, "allowed_actions")
        for index, path in enumerate(allowed_paths):
            safe_relative_path(path, f"manual_guard.allowed_paths[{index}]")
        if value["action"] not in allowed_actions:
            raise ContractError("manual guard does not allow the requested action")
        try:
            expires = datetime.fromisoformat(guard["expires_at"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ContractError("manual_guard.expires_at must be an ISO-8601 timestamp") from exc
        if expires.tzinfo is None or expires <= datetime.now(timezone.utc):
            raise ContractError("manual guard is expired or has no timezone")
    technologies = value.get("technologies", [])
    if not isinstance(technologies, list):
        raise ContractError("technologies must be an array")
    technology_names: set[str] = set()
    for technology in technologies:
        if not isinstance(technology, dict):
            raise ContractError("each technology candidate must be an object")
        name = technology.get("name")
        status = technology.get("status")
        if not isinstance(name, str) or not name.strip():
            raise ContractError("technology.name must be a non-empty string")
        normalized = name.strip().lower()
        if normalized in technology_names:
            raise ContractError(f"duplicate technology candidate: {name}")
        technology_names.add(normalized)
        if status not in {
            "required_by_user",
            "detected_existing",
            "candidate",
            "selected",
            "rejected",
            "not_applicable",
        }:
            raise ContractError(f"technology.status is unsupported: {status}")
        if "material" in technology and not isinstance(technology["material"], bool):
            raise ContractError("technology.material must be boolean")
    configuration_candidates = value.get("configuration_candidates", [])
    if not isinstance(configuration_candidates, list):
        raise ContractError("configuration_candidates must be an array")
    configuration_names: set[str] = set()
    for candidate in configuration_candidates:
        if not isinstance(candidate, dict):
            raise ContractError("each configuration candidate must be an object")
        name = candidate.get("name")
        kind = candidate.get("kind")
        source = candidate.get("source")
        if not all(isinstance(item, str) and item for item in (name, kind, source)):
            raise ContractError("configuration candidate requires string name, kind, and source")
        if name in configuration_names:
            raise ContractError(f"duplicate configuration candidate: {name}")
        configuration_names.add(name)
        if kind == "port" and "default" in candidate:
            default = candidate["default"]
            if not isinstance(default, int) or isinstance(default, bool) or not 1 <= default <= 65535:
                raise ContractError(f"port default is outside 1..65535: {name}")
        secret_candidate = "secret" in kind or source == "secret_provider"
        if secret_candidate:
            if candidate.get("redacted") is not True:
                raise ContractError(f"secret candidate must be marked redacted: {name}")
            if any(key in candidate for key in ("value", "default", "example")):
                raise ContractError(f"secret candidate must not embed a value: {name}")
    _validate_artifact_graph(value.get("artifacts", []))
    if not isinstance(value.get("feedback", []), list):
        raise ContractError("feedback must be an array")
    return value


def validate_route_result(value: dict[str, Any], approved_skills: set[str]) -> dict[str, Any]:
    if value.get("schema_version") != 1:
        raise ContractError("route result schema_version must be 1")
    validate_identifier(value.get("request_id"), "request_id")
    if value.get("status") not in {"active", "waiting_user", "blocked", "failed"}:
        raise ContractError("route result has unsupported status")
    if not isinstance(value.get("forward_revision"), int) or value["forward_revision"] < 1:
        raise ContractError("forward_revision must be a positive integer")
    gates = value.get("gate_results")
    if not isinstance(gates, list) or [gate.get("gate_id") for gate in gates if isinstance(gate, dict)] != [
        f"G{i}" for i in range(8)
    ]:
        raise ContractError("route result must contain ordered G0 through G7 results")
    activated = value.get("activated_skills")
    if not isinstance(activated, list) or any(not isinstance(item, str) for item in activated):
        raise ContractError("activated_skills must be an array of strings")
    if len(activated) != len(set(activated)):
        raise ContractError("activated_skills must not contain duplicates")
    unknown = set(activated) - approved_skills
    if unknown:
        raise ContractError(f"route selected unapproved skills: {sorted(unknown)}")
    for gate in gates:
        depths = gate.get("application_depths", {})
        if not isinstance(depths, dict):
            raise ContractError("gate application_depths must be an object")
        if set(depths) != set(gate.get("activated_skills", [])):
            raise ContractError("gate application_depths must cover exactly its activated skills")
        if any(depth not in {"light", "standard", "deep"} for depth in depths.values()):
            raise ContractError("gate application_depths contains an unsupported depth")
    validate_execution_profile(value.get("execution_profile"))
    return value


def validate_execution_profile(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("policy_id") != "adaptive_v1":
        raise ContractError("execution_profile requires adaptive_v1")
    if value.get("specific_model") is not None:
        raise ContractError("portable execution_profile cannot bind a specific model")
    _require_string(value, "depth", {"light", "standard", "deep"})
    _require_string(value, "risk", {"low", "medium", "high"})
    if value.get("adapter_resolution_required") is not True:
        raise ContractError("execution_profile requires adapter resolution")
    _string_array(value, "escalation_triggers")
    profiles = value.get("gate_profiles")
    if not isinstance(profiles, list) or [
        profile.get("gate_id") for profile in profiles if isinstance(profile, dict)
    ] != [f"G{i}" for i in range(8)]:
        raise ContractError("execution_profile must contain ordered G0 through G7 profiles")
    for profile in profiles:
        _require_string(profile, "role", EXECUTION_ROLES)
        _require_string(profile, "reasoning", REASONING_LEVELS)
        if not isinstance(profile.get("independent_context"), bool):
            raise ContractError("execution profile independent_context must be boolean")
        _string_array(profile, "reasons")
    return value


def validate_skill_result(value: dict[str, Any], approved_skills: set[str]) -> dict[str, Any]:
    if value.get("schema_version") != 1:
        raise ContractError("skill result schema_version must be 1")
    skill_id = _require_string(value, "skill_id")
    if skill_id not in approved_skills:
        raise ContractError(f"skill result references an unapproved skill: {skill_id}")
    status = _require_string(value, "status", SKILL_RESULT_STATUSES)
    _string_array(value, "artifact_ids")
    _string_array(value, "evidence_ids")
    transition = value.get("transition")
    if not isinstance(transition, dict):
        raise ContractError("skill result transition must be an object")
    _require_string(transition, "next_stage", STAGES | {"blocked", "failed", "backward_feedback"})
    error = value.get("error")
    if status in {"blocked", "failed"} and not isinstance(error, str):
        raise ContractError("blocked or failed skill result requires an error string")
    resolution = value.get("execution_resolution")
    if not isinstance(resolution, dict):
        raise ContractError("skill result requires an execution_resolution")
    _require_string(resolution, "adapter", {"codex", "claude"})
    model = _require_string(resolution, "model")
    if len(model) > 128:
        raise ContractError("execution_resolution.model is too long")
    _require_string(resolution, "reasoning", REASONING_LEVELS | {"unknown"})
    native_reasoning = _require_string(resolution, "native_reasoning")
    if len(native_reasoning) > 64:
        raise ContractError("execution_resolution.native_reasoning is too long")
    resolution_status = _require_string(
        resolution,
        "status",
        {"exact", "upgraded", "degraded", "platform_default", "unavailable"},
    )
    _string_array(resolution, "evidence_ids")
    if resolution_status == "unavailable" and status not in {"blocked", "failed"}:
        raise ContractError("unavailable execution capability requires a blocked or failed result")
    return value


def validate_pattern_review(value: dict[str, Any]) -> dict[str, Any]:
    """Validate one PATTERN-* decision scope and its user-selection boundary."""
    if value.get("schema_version") != 1:
        raise ContractError("pattern review schema_version must be 1")
    validate_identifier(value.get("pattern_id"), "pattern_id")
    scopes = _string_array(value, "scopes")
    if not scopes or set(scopes) - {"architecture", "design"}:
        raise ContractError("pattern review scopes must contain architecture or design")
    if not _string_array(value, "drivers"):
        raise ContractError("pattern review requires at least one driver")
    open_issue_ids = _string_array(value, "open_issue_ids")

    candidates = value.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ContractError("pattern review requires at least one candidate")
    candidate_ids: set[str] = set()
    candidate_by_id: dict[str, dict[str, Any]] = {}
    viable_ids: list[str] = []
    selected_ids: list[str] = []
    existing_ids: list[str] = []
    decision_scopes: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ContractError("each pattern candidate must be an object")
        candidate_id = validate_identifier(candidate.get("candidate_id"), "candidate_id")
        if candidate_id in candidate_ids:
            raise ContractError(f"duplicate pattern candidate_id: {candidate_id}")
        candidate_ids.add(candidate_id)
        candidate_by_id[candidate_id] = candidate
        _require_string(candidate, "name")
        status = _require_string(candidate, "status", PATTERN_CANDIDATE_STATUSES)
        if status in {"candidate", "selected", "existing"}:
            decision_scope = _require_string(candidate, "decision_scope")
            decision_scopes.add(decision_scope)
            _require_string(candidate, "fit")
            _require_string(candidate, "recommendation_reason")
            if not _string_array(candidate, "benefits"):
                raise ContractError(f"viable pattern candidate requires benefits: {candidate_id}")
            if not _string_array(candidate, "liabilities"):
                raise ContractError(f"viable pattern candidate requires liabilities: {candidate_id}")
            _string_array(candidate, "quality_attribute_effects")
            _string_array(candidate, "affected_artifact_ids")
            _string_array(candidate, "migration_and_rollback")
            _string_array(candidate, "verification_ids")
            viable_ids.append(candidate_id)
        if status == "selected":
            selected_ids.append(candidate_id)
        elif status == "existing":
            existing_ids.append(candidate_id)
    if len(decision_scopes) > 1:
        raise ContractError("one PATTERN record may contain only one decision scope")
    if len(selected_ids) > 1:
        raise ContractError("pattern review may select at most one candidate")

    decision = value.get("decision")
    if not isinstance(decision, dict):
        raise ContractError("pattern review requires a decision object")
    decision_status = _require_string(decision, "status", PATTERN_DECISION_STATUSES)
    decision_scope = _require_string(decision, "decision_scope")
    if decision_scopes and decision_scope not in decision_scopes:
        raise ContractError("decision scope must match every viable candidate")

    recommended_id = decision.get("recommended_candidate_id")
    selected_id = decision.get("selected_candidate_id")
    if recommended_id is not None:
        validate_identifier(recommended_id, "recommended_candidate_id")
        if recommended_id not in viable_ids:
            raise ContractError("recommended candidate must be materially viable")
    if selected_id is not None:
        validate_identifier(selected_id, "selected_candidate_id")
        if selected_id not in candidate_by_id:
            raise ContractError("selected candidate is not present in candidates")
    evidence_ids = _string_array(decision, "decision_evidence_ids")
    change_conditions = _string_array(decision, "conditions_that_change_recommendation")

    if decision_status == "not_applicable":
        if viable_ids or selected_id is not None or recommended_id is not None:
            raise ContractError("not_applicable cannot contain a viable, selected, or recommended candidate")
    elif decision_status == "single_viable":
        if len(viable_ids) != 1 or selected_ids != viable_ids or selected_id != viable_ids[0]:
            raise ContractError("single_viable requires exactly one viable selected candidate")
    elif decision_status == "user_decision_required":
        if len(viable_ids) < 2:
            raise ContractError("user_decision_required requires at least two viable candidates")
        if selected_ids or selected_id is not None:
            raise ContractError("user_decision_required cannot preselect a candidate")
        if recommended_id is None or not _require_string(decision, "recommendation_reason"):
            raise ContractError("user_decision_required requires an evidence-backed recommendation")
        if not change_conditions:
            raise ContractError("user_decision_required requires recommendation change conditions")
        if not open_issue_ids:
            raise ContractError("user_decision_required requires an open user decision issue")
    elif decision_status == "user_selected":
        if len(viable_ids) < 2 or len(selected_ids) != 1 or selected_id != selected_ids[0]:
            raise ContractError("user_selected requires one selected candidate from multiple viable options")
        if (
            recommended_id is None
            or not isinstance(decision.get("recommendation_reason"), str)
            or not decision["recommendation_reason"].strip()
            or not change_conditions
            or not evidence_ids
        ):
            raise ContractError(
                "user_selected requires recommendation rationale, change conditions, and user decision evidence"
            )
    else:  # existing_decision
        if len(existing_ids) != 1 or selected_id != existing_ids[0] or not evidence_ids:
            raise ContractError("existing_decision requires one existing candidate and decision evidence")
    return value


def validate_implementation_quality(value: dict[str, Any]) -> dict[str, Any]:
    """Validate selective G6 implementation-quality applicability evidence."""
    if value.get("schema_version") != 1:
        raise ContractError("implementation quality schema_version must be 1")
    status = _require_string(
        value,
        "status",
        {"completed", "not_applicable", "waiting_user", "blocked", "failed"},
    )
    boundaries = _string_array(value, "authored_boundaries")
    active = value.get("activated_profiles", [])
    suppressed = value.get("suppressed_profiles", [])
    if not isinstance(active, list) or not isinstance(suppressed, list):
        raise ContractError("implementation quality profiles must be arrays")

    allowed_profiles = {
        "core",
        "object_oriented",
        "functional",
        "data_oriented",
        "api_data",
        "concurrency",
        "distributed",
        "security",
        "performance",
        "realtime_embedded",
    }
    active_ids: set[str] = set()
    for profile in active:
        if not isinstance(profile, dict):
            raise ContractError("each active implementation quality profile must be an object")
        profile_id = _require_string(profile, "id", allowed_profiles)
        if profile_id in active_ids:
            raise ContractError(f"duplicate active implementation quality profile: {profile_id}")
        active_ids.add(profile_id)
        _require_string(profile, "depth", {"light", "standard", "deep"})
        profile_boundaries = _string_array(profile, "authored_boundaries")
        if not profile_boundaries:
            raise ContractError(
                f"implementation quality profile requires authored boundaries: {profile_id}"
            )
        if set(profile_boundaries) - set(boundaries):
            raise ContractError(
                f"implementation quality profile escapes the declared authored boundaries: {profile_id}"
            )
        if not _string_array(profile, "evidence_ids"):
            raise ContractError(f"implementation quality profile requires evidence: {profile_id}")
        if not _string_array(profile, "expected_outcomes"):
            raise ContractError(f"implementation quality profile requires expected outcomes: {profile_id}")
        if not _string_array(profile, "verification_ids"):
            raise ContractError(f"implementation quality profile requires verification: {profile_id}")

    suppressed_ids: set[str] = set()
    for profile in suppressed:
        if not isinstance(profile, dict):
            raise ContractError("each suppressed implementation quality profile must be an object")
        profile_id = _require_string(profile, "id", allowed_profiles)
        if profile_id in suppressed_ids or profile_id in active_ids:
            raise ContractError(f"implementation quality profile state is duplicated: {profile_id}")
        suppressed_ids.add(profile_id)
        _require_string(profile, "reason")

    for key in ("findings", "changes_or_recommendations", "residual_risks", "open_points"):
        _string_array(value, key)
    if status == "not_applicable":
        if boundaries or active:
            raise ContractError("not_applicable implementation quality cannot contain authored boundaries or active profiles")
    elif status == "completed":
        if not boundaries:
            raise ContractError("completed implementation quality requires authored boundaries")
        if "core" not in active_ids:
            raise ContractError("applicable implementation quality requires the core profile")
    return value


def validate_state(
    value: dict[str, Any], target_root: Path, harness_root: Path | None = None
) -> dict[str, Any]:
    if value.get("schema_version") != 1:
        raise ContractError("state schema_version must be 1")
    validate_identifier(value.get("task_id"), "task_id")
    validate_identifier(value.get("run_id"), "run_id")
    validate_identifier(value.get("request_id"), "request_id")
    if not isinstance(value.get("revision"), int) or value["revision"] < 1:
        raise ContractError("state revision must be a positive integer")
    if value.get("target_root_fingerprint") != root_fingerprint(target_root):
        raise ContractError("state belongs to a different target root")
    harness_fingerprint = value.get("harness_root_fingerprint")
    if not isinstance(harness_fingerprint, str) or not re.fullmatch(
        r"sha256:[A-Fa-f0-9]{64}", harness_fingerprint
    ):
        raise ContractError("state harness_root_fingerprint is invalid")
    if harness_root is not None and harness_fingerprint != root_fingerprint(harness_root):
        raise ContractError("state belongs to a different harness source root")
    _require_string(value, "selected_adapter", {"codex", "claude"})
    _require_string(value, "status", TASK_STATUSES)
    _require_string(value, "stage", STAGES)
    _require_string(value, "session_scope", SCOPES)
    _require_string(value, "project_state", PROJECT_STATES)
    if not isinstance(value.get("classification"), dict):
        raise ContractError("state classification must be an object")
    if not isinstance(value.get("intent"), dict):
        raise ContractError("state intent must be an object")
    if not isinstance(value.get("gate_network"), dict):
        raise ContractError("state gate_network must be an object")
    route = value.get("route")
    if not isinstance(route, dict):
        raise ContractError("state route must be an object")
    validate_execution_profile(route.get("execution_profile"))
    execution = value.get("execution")
    if not isinstance(execution, dict):
        raise ContractError("state execution must be an object")
    queue = execution.get("queue")
    cursor = execution.get("cursor")
    if not isinstance(queue, list) or any(not isinstance(item, str) for item in queue):
        raise ContractError("state execution.queue must be an array of strings")
    if not isinstance(cursor, int) or cursor < 0 or cursor > len(queue):
        raise ContractError("state execution.cursor is outside the queue")
    for key in ("skill_stages", "skill_gates"):
        mapping = execution.get(key)
        if not isinstance(mapping, dict) or set(mapping) != set(queue):
            raise ContractError(f"state execution.{key} must map every queued skill exactly once")
    if any(gate_id not in {f"G{i}" for i in range(2, 8)} for gate_id in execution["skill_gates"].values()):
        raise ContractError("state execution.skill_gates contains an invalid gate")
    status = value["status"]
    if status == "complete":
        if cursor != len(queue) or value.get("validation_status") != "passed":
            raise ContractError("complete requires a finished queue and passed verification")
        if value.get("open_issue_ids"):
            raise ContractError("complete requires no open issues")
    elif status == "waiting_user":
        question = value.get("pending_question")
        if not isinstance(question, dict) or not isinstance(question.get("question_id"), str):
            raise ContractError("waiting_user requires a pending question")
    elif status == "blocked":
        blocker = value.get("blocker")
        if not isinstance(blocker, dict) or not all(
            isinstance(blocker.get(key), str) and blocker[key]
            for key in ("reason", "owner", "recovery")
        ):
            raise ContractError("blocked requires reason, owner, and recovery")
    elif status == "failed":
        error = value.get("error_record")
        if not isinstance(error, dict) or not isinstance(error.get("error"), str):
            raise ContractError("failed requires an error record")
    return value


def validate_config(value: dict[str, Any], target_root: Path) -> dict[str, Any]:
    if value.get("schema_version") != 1 or value.get("protocol_version") != 1:
        raise ContractError("harness config requires schema/protocol version 1")
    if value.get("harness_root_mode") != "separate":
        raise ContractError("only separate harness roots are supported")
    source = value.get("harness_source")
    if not isinstance(source, dict) or source.get("kind") != "local_or_bundled":
        raise ContractError("harness_source must be local_or_bundled")
    locator = source.get("locator")
    if not isinstance(locator, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*", locator):
        raise ContractError("harness_source.locator must be a safe installation identifier")
    if source.get("revision") in {None, "", "PIN_REQUIRED", "PENDING_PIN_BEFORE_BOOTSTRAP"}:
        raise ContractError("harness source revision is not pinned")
    if not isinstance(source.get("sha256"), str) or not re.fullmatch(r"[A-Fa-f0-9]{64}", source["sha256"]):
        raise ContractError("harness source sha256 must be 64 hexadecimal characters")
    templates = value.get("templates")
    if not isinstance(templates, list) or {item.get("id") for item in templates if isinstance(item, dict)} != {
        "codex.bootstrap",
        "claude.bootstrap",
    } or len(templates) != 2:
        raise ContractError("templates must contain exactly one Codex and one Claude bootstrap")
    for template in templates:
        safe_relative_path(template.get("path"), f"{template.get('id')}.path")
        if not isinstance(template.get("sha256"), str) or not re.fullmatch(
            r"[A-Fa-f0-9]{64}", template["sha256"]
        ):
            raise ContractError(f"template hash is invalid: {template.get('id')}")
    if value.get("adapters") != ["codex", "claude"]:
        raise ContractError("bootstrap MVP installs the Codex and Claude adapters together")
    state_root = value.get("state_root")
    if state_root != ".agents/state":
        raise ContractError("reference MVP supports only .agents/state")
    contained_path(target_root, state_root, "state_root")
    registry = value.get("registry")
    if not isinstance(registry, dict) or registry.get("resolution_order") != [
        "project_reviewed",
        "shared_reviewed",
        "core_fallback",
    ]:
        raise ContractError("registry resolution order is invalid")
    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ContractError("registry requires at least one reviewed source")
    scopes: set[str] = set()
    for source_item in sources:
        if not isinstance(source_item, dict) or source_item.get("scope") not in {
            "project_reviewed",
            "shared_reviewed",
        }:
            raise ContractError("registry source scope is invalid")
        if source_item["scope"] in scopes:
            raise ContractError("registry source scopes must be unique")
        scopes.add(source_item["scope"])
        safe_relative_path(source_item.get("path"), f"registry.{source_item['scope']}.path")
        if not isinstance(source_item.get("sha256"), str) or not re.fullmatch(
            r"[A-Fa-f0-9]{64}", source_item["sha256"]
        ):
            raise ContractError("registry source hash is invalid")
        if source_item.get("revision") in {None, "", "PIN_REQUIRED", "PENDING_PIN_BEFORE_BOOTSTRAP"}:
            raise ContractError("registry source revision is not pinned")
    mappings = value.get("adapter_mapping")
    if not isinstance(mappings, dict) or set(mappings) != {"codex", "claude"}:
        raise ContractError("adapter_mapping must contain Codex and Claude")
    expected_mappings = {
        "codex": ("native_instruction_scope", "harness_source", "skills"),
        "claude": ("native_or_plugin", "target_project", ".claude/skills"),
    }
    for platform, (loader, scope, skill_root) in expected_mappings.items():
        mapping = mappings[platform]
        if not isinstance(mapping, dict) or (
            mapping.get("loader"),
            mapping.get("scope"),
            mapping.get("skill_root"),
            mapping.get("fallback"),
        ) != (loader, scope, skill_root, "core_procedure"):
            raise ContractError(f"adapter mapping is invalid: {platform}")
        safe_relative_path(mapping["skill_root"], f"adapter_mapping.{platform}.skill_root")
    enforcement = value.get("enforcement")
    if not isinstance(enforcement, dict) or enforcement.get("mode") not in {"hook", "manual", "unsupported"}:
        raise ContractError("enforcement mode is invalid")
    probe = enforcement.get("capability_probe")
    if not isinstance(probe, dict) or probe.get("status") not in {"recorded", "stale", "failed"}:
        raise ContractError("enforcement capability probe is invalid")
    if not isinstance(probe.get("evidence_id"), str) or not isinstance(probe.get("at"), str):
        raise ContractError("enforcement capability probe requires evidence_id and timestamp")
    if enforcement["mode"] in {"hook", "manual"} and probe["status"] != "recorded":
        raise ContractError("hook and manual modes require a recorded capability probe")
    if enforcement["mode"] in {"hook", "unsupported"} and enforcement.get("manual_guard") is not None:
        raise ContractError("hook and unsupported modes cannot carry a manual guard")
    bootstrap = value.get("bootstrap")
    if not isinstance(bootstrap, dict):
        raise ContractError("bootstrap config must be an object")
    if bootstrap.get("line_endings") != "LF" or bootstrap.get("max_bytes") != 32768:
        raise ContractError("bootstrap encoding or byte-limit policy is invalid")
    managed = bootstrap.get("managed_files")
    if sorted(managed or []) != ["AGENTS.md", "CLAUDE.md"]:
        raise ContractError("managed_files must contain AGENTS.md and CLAUDE.md")
    hashes = bootstrap.get("file_hashes")
    if not isinstance(hashes, dict) or set(hashes) != set(managed):
        raise ContractError("file_hashes must exactly match managed_files")
    for name, expected in hashes.items():
        raw_path = target_root.resolve(strict=True) / name
        if raw_path.is_symlink():
            raise ContractError(f"managed file must not be a symlink: {name}")
        path = contained_path(target_root, name, f"managed file {name}", must_exist=True)
        if not path.is_file():
            raise ContractError(f"managed file must be a regular file: {name}")
        if sha256_file(path) != expected:
            raise ContractError(f"managed file hash mismatch: {name}")
    expected_config_hash = bootstrap.get("config_hash")
    copy = json.loads(json.dumps(value))
    copy["bootstrap"].pop("config_hash", None)
    if expected_config_hash != sha256_bytes(canonical_json_bytes(copy)):
        raise ContractError("config_hash does not match canonical config content")
    return value


def _result(status: str, kind: str, input_path: Path, error: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": status,
        "kind": kind,
        "input": str(input_path),
        "error": error,
    }


def main(argv: Iterable[str] | None = None) -> int:
    harness_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "kind",
        choices=[
            "intake",
            "route",
            "skill-result",
            "pattern-review",
            "implementation-quality",
            "state",
            "harness-config",
        ],
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--target-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--registry", type=Path, default=harness_root / "registry" / "active-skills.json")
    parser.add_argument("--taxonomy", type=Path, default=harness_root / "registry" / "taxonomy.json")
    args = parser.parse_args(argv)
    try:
        value = read_object(args.input)
        if args.kind == "intake":
            validate_intake(value, args.taxonomy, require_intent=True)
        elif args.kind == "route":
            validate_route_result(value, active_skill_ids(args.registry))
        elif args.kind == "skill-result":
            validate_skill_result(value, active_skill_ids(args.registry))
        elif args.kind == "pattern-review":
            validate_pattern_review(value)
        elif args.kind == "implementation-quality":
            validate_implementation_quality(value)
        elif args.kind == "state":
            if args.target_root is None:
                raise ContractError("--target-root is required for state validation")
            validate_state(value, args.target_root, harness_root)
        else:
            if args.target_root is None:
                raise ContractError("--target-root is required for harness-config validation")
            validate_config(value, args.target_root)
        result = _result("valid", args.kind, args.input)
        exit_code = 0
    except ContractError as exc:
        result = _result("invalid", args.kind, args.input, str(exc))
        exit_code = 2
    if args.output is None:
        sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    else:
        write_object(args.output, result)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
