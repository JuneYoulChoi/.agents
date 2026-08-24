#!/usr/bin/env python3
"""Dependency-free reference provider for the portable gated Router contract."""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any


SELECTED_TECH_STATUSES = {"required_by_user", "detected_existing", "selected"}
ARCHITECTURE_STATUS_ALIASES = {"accepted": "confirmed"}
CONFORMANCE_INTENTS = {"guidance", "alignment", "conformance"}
PATTERN_SCOPES = {"architecture", "design"}
LANGUAGE_SCOPES = {"authored_in_scope", "detected_only", "generated_only", "none"}
CHANGE_CHARACTERISTICS = {
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
CODE_SCOPE_ACTIONS = {"investigate", "design", "implement", "change", "verify", "review"}


class RouterError(ValueError):
    """Raised when the portable input or manifest contract is invalid."""


def _read_json(path: Path | None) -> dict[str, Any]:
    try:
        if path is None:
            value = json.load(sys.stdin)
        else:
            value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RouterError(f"cannot read JSON input: {exc}") from exc
    if not isinstance(value, dict):
        raise RouterError("input must be a JSON object")
    return value


def _write_json(value: dict[str, Any], path: Path | None) -> None:
    data = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path is None:
        sys.stdout.write(data)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(data)


def _normalize_token(value: str, aliases: dict[str, str]) -> str:
    token = value.strip().lower().replace("-", "_")
    return aliases.get(token, aliases.get(value.strip().lower(), token))


def _require_string(context: dict[str, Any], key: str, allowed: set[str] | None = None) -> str:
    value = context.get(key)
    if not isinstance(value, str) or not value:
        raise RouterError(f"{key} must be a non-empty string")
    if allowed is not None and value not in allowed:
        raise RouterError(f"{key} has unsupported value: {value}")
    return value


def _string_list(context: dict[str, Any], key: str) -> list[str]:
    value = context.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise RouterError(f"{key} must be an array of strings")
    return list(dict.fromkeys(value))


def _load_manifest(path: Path) -> dict[str, Any]:
    manifest = _read_json(path)
    gates = manifest.get("gates")
    edges = manifest.get("forward_edges")
    if manifest.get("model") != "layered_gated_skill_graph":
        raise RouterError("routing manifest model is unsupported")
    if not isinstance(gates, list) or {g.get("id") for g in gates if isinstance(g, dict)} != {
        f"G{i}" for i in range(8)
    }:
        raise RouterError("routing manifest must define G0 through G7 exactly once")
    if not isinstance(edges, list):
        raise RouterError("routing manifest forward_edges must be an array")
    expected = [[f"G{i}", f"G{i + 1}"] for i in range(7)]
    if edges != expected:
        raise RouterError("reference provider requires the canonical G0 through G7 forward chain")
    if manifest.get("evaluation", {}).get("learned_weights") is not False:
        raise RouterError("learned routing weights are not permitted")
    execution_policy = manifest.get("execution_policy")
    if not isinstance(execution_policy, dict) or execution_policy.get("policy_id") != "adaptive_v1":
        raise RouterError("routing manifest execution policy is unsupported")
    if execution_policy.get("specific_model_binding") is not False:
        raise RouterError("portable execution policy cannot bind a specific model")
    if execution_policy.get("reasoning_levels") != ["low", "medium", "high"]:
        raise RouterError("execution policy reasoning levels are invalid")
    defaults = execution_policy.get("depth_defaults")
    roles = execution_policy.get("gate_roles")
    if not isinstance(defaults, dict) or set(defaults) != {"light", "standard", "deep"}:
        raise RouterError("execution policy must define light, standard, and deep defaults")
    if not isinstance(roles, dict) or set(roles) != {f"G{i}" for i in range(8)}:
        raise RouterError("execution policy must define one role per gate")
    for depth, levels in defaults.items():
        if not isinstance(levels, list) or len(levels) != 8 or any(
            level not in {"low", "medium", "high"} for level in levels
        ):
            raise RouterError(f"execution policy depth defaults are invalid: {depth}")
    selectors = manifest.get("selectors")
    if not isinstance(selectors, dict):
        raise RouterError("routing manifest selectors must be an object")
    for key in (
        "technology_aliases",
        "technology_skills",
        "adjacent_technologies",
        "standard_aliases",
        "standard_profiles",
        "pattern_characteristic_scopes",
        "implementation_quality_profiles",
    ):
        if not isinstance(selectors.get(key), dict):
            raise RouterError(f"routing manifest selector {key} must be an object")
    aliases = selectors["standard_aliases"]
    profiles = selectors["standard_profiles"]
    if any(not isinstance(key, str) or not isinstance(value, str) for key, value in aliases.items()):
        raise RouterError("standard aliases must map strings to strings")
    if set(aliases.values()) - set(profiles):
        raise RouterError("standard aliases reference unknown profiles")
    for standard_id, profile_path in profiles.items():
        if not isinstance(standard_id, str) or not isinstance(profile_path, str):
            raise RouterError("standard profiles must map strings to strings")
        path = Path(profile_path)
        if path.is_absolute() or ".." in path.parts or path.parts[:3] != (
            "skills",
            "architecture-baseline-and-design",
            "references",
        ):
            raise RouterError(f"standard profile path is outside the approved architecture skill: {standard_id}")
    pattern_characteristics = selectors["pattern_characteristic_scopes"]
    if any(
        key not in CHANGE_CHARACTERISTICS or value not in PATTERN_SCOPES
        for key, value in pattern_characteristics.items()
    ):
        raise RouterError("pattern characteristic scopes contain unsupported values")
    quality_profiles = selectors["implementation_quality_profiles"]
    allowed_quality_profiles = {
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
    if any(
        key not in CHANGE_CHARACTERISTICS or value not in allowed_quality_profiles
        for key, value in quality_profiles.items()
    ):
        raise RouterError("implementation quality profile selectors contain unsupported values")
    backward_routes = manifest.get("backward_routes")
    if not isinstance(backward_routes, list):
        raise RouterError("routing manifest backward_routes must be an array")
    signals: set[str] = set()
    for item in backward_routes:
        if not isinstance(item, dict):
            raise RouterError("each backward route must be an object")
        signal = item.get("signal")
        target = item.get("target_gate")
        if not isinstance(signal, str) or target not in {f"G{i}" for i in range(7)}:
            raise RouterError("each backward route requires a unique signal and G0 through G6 target")
        if signal in signals:
            raise RouterError(f"duplicate backward route signal: {signal}")
        signals.add(signal)
    return manifest


def _gate_result(
    gate_id: str,
    revision: int,
    activated: list[str] | None = None,
    branches: list[str] | None = None,
    suppressed: list[dict[str, Any]] | None = None,
    blocked: list[dict[str, Any]] | None = None,
    evidence: list[str] | None = None,
    candidates: list[str] | None = None,
    application_depths: dict[str, str] | None = None,
) -> dict[str, Any]:
    blocked = blocked or []
    return {
        "gate_id": gate_id,
        "forward_revision": revision,
        "activated_skills": activated or [],
        "activated_branches": branches or [],
        "candidate_branches": candidates or [],
        "suppressed": suppressed or [],
        "blocked": blocked,
        "evidence_ids": evidence or [],
        "application_depths": application_depths or {},
        "status": "blocked" if blocked else "passed",
    }


def _depths_for_skills(
    skills: list[str],
    default_depth: str,
    architecture_status: str,
    characteristics: set[str],
    implementation_profiles: list[str] | None = None,
    risk: str = "medium",
) -> dict[str, str]:
    depths = {skill_id: default_depth for skill_id in skills}
    if "core.intake-and-route" in depths:
        depths["core.intake-and-route"] = "light"
    architecture_signals = {
        "architecture_structure",
        "design_interaction",
        "api_data_contract",
        "distributed",
        "security",
        "realtime_embedded",
    }
    if (
        "core.architecture-baseline-and-design" in depths
        and architecture_status == "confirmed"
        and not characteristics & architecture_signals
    ):
        depths["core.architecture-baseline-and-design"] = "light"
    if (
        "core.implementation-quality" in depths
        and implementation_profiles == ["core"]
        and risk == "low"
    ):
        depths["core.implementation-quality"] = "light"
    return depths


def _technology_selection(
    context: dict[str, Any], manifest: dict[str, Any]
) -> tuple[set[str], list[dict[str, Any]]]:
    selectors = manifest.get("selectors", {})
    aliases = selectors.get("technology_aliases", {})
    skill_map = selectors.get("technology_skills", {})
    adjacent = selectors.get("adjacent_technologies", {})
    if not all(isinstance(value, dict) for value in (aliases, skill_map, adjacent)):
        raise RouterError("routing manifest selectors must be objects")
    raw = context.get("technologies", [])
    if not isinstance(raw, list):
        raise RouterError("technologies must be an array")
    selected: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise RouterError("each technology must be an object")
        name = item.get("name")
        status = item.get("status")
        if not isinstance(name, str) or not isinstance(status, str):
            raise RouterError("technology name and status must be strings")
        normalized = _normalize_token(name, aliases)
        if status in SELECTED_TECH_STATUSES and item.get("material", True):
            selected.add(normalized)

    suppressed_names: set[str] = set()
    for name in selected:
        neighbors = adjacent.get(name, [])
        if not isinstance(neighbors, list) or any(not isinstance(x, str) for x in neighbors):
            raise RouterError(f"adjacent technology selector for {name} must be an array of strings")
        suppressed_names.update(set(neighbors) - selected)
    suppressed = [
        {
            "skill_id": skill_map[name],
            "reason": "adjacent_technology_not_evidenced",
            "technology": name,
        }
        for name in sorted(suppressed_names)
        if name in skill_map
    ]
    return selected, suppressed


def _artifact_invalidation(context: dict[str, Any], roots: list[str]) -> tuple[list[str], list[str]]:
    artifacts = context.get("artifacts", [])
    if not isinstance(artifacts, list):
        raise RouterError("artifacts must be an array")
    all_ids: set[str] = set()
    children: dict[str, set[str]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not isinstance(artifact.get("id"), str):
            raise RouterError("each artifact requires a string id")
        artifact_id = artifact["id"]
        all_ids.add(artifact_id)
        depends_on = artifact.get("depends_on", [])
        if not isinstance(depends_on, list) or any(not isinstance(x, str) for x in depends_on):
            raise RouterError("artifact depends_on must be an array of strings")
        for parent in depends_on:
            children.setdefault(parent, set()).add(artifact_id)
    unknown = set(roots) - all_ids
    if unknown:
        raise RouterError(f"feedback roots reference unknown artifacts: {sorted(unknown)}")
    invalidated: set[str] = set(roots)
    queue: deque[str] = deque(roots)
    while queue:
        parent = queue.popleft()
        for child in children.get(parent, set()):
            if child not in invalidated:
                invalidated.add(child)
                queue.append(child)
    return sorted(invalidated), sorted(all_ids - invalidated)


def _feedback_results(
    context: dict[str, Any], manifest: dict[str, Any], start_revision: int
) -> tuple[list[dict[str, Any]], int, bool]:
    feedback = context.get("feedback", [])
    if not isinstance(feedback, list):
        raise RouterError("feedback must be an array")
    route_map = {item["signal"]: item["target_gate"] for item in manifest["backward_routes"]}
    results: list[dict[str, Any]] = []
    revision = start_revision
    requires_user = False
    for index, item in enumerate(feedback, start=1):
        if not isinstance(item, dict):
            raise RouterError("each feedback item must be an object")
        kind = item.get("kind")
        attempt = item.get("attempt", 1)
        if not isinstance(kind, str) or not isinstance(attempt, int) or attempt < 1:
            raise RouterError("feedback kind must be a string and attempt a positive integer")
        target = route_map.get(kind)
        item_requires_user = target is None or attempt >= 3 or bool(item.get("requires_user", False))
        roots = item.get("invalidated_root_artifact_ids", [])
        if not isinstance(roots, list) or any(not isinstance(x, str) for x in roots):
            raise RouterError("invalidated_root_artifact_ids must be an array of strings")
        invalidated, preserved = _artifact_invalidation(context, roots) if roots else ([], sorted(
            a["id"] for a in context.get("artifacts", []) if isinstance(a, dict) and isinstance(a.get("id"), str)
        ))
        next_revision = revision if item_requires_user else revision + 1
        result = {
            "feedback_id": item.get("feedback_id", f"FDB-{index:03d}"),
            "source_gate": item.get("source_gate", "G7"),
            "target_gate": target,
            "kind": kind,
            "expected": item.get("expected", ""),
            "actual": item.get("actual", ""),
            "evidence_ids": item.get("evidence_ids", []),
            "invalidated_artifact_ids": invalidated,
            "preserved_artifact_ids": preserved,
            "attempt": attempt,
            "requires_user": item_requires_user,
            "next_forward_revision": next_revision,
        }
        results.append(result)
        revision = next_revision
        requires_user = requires_user or item_requires_user
    return results, revision, requires_user


def _execution_profile(
    context: dict[str, Any],
    manifest: dict[str, Any],
    architecture_status: str,
    feedback: list[dict[str, Any]],
) -> dict[str, Any]:
    policy = manifest["execution_policy"]
    depth = context.get("depth", "standard")
    risk = context.get("risk", "medium")
    if depth not in {"light", "standard", "deep"}:
        raise RouterError(f"depth has unsupported value: {depth}")
    if risk not in {"low", "medium", "high"}:
        raise RouterError(f"risk has unsupported value: {risk}")
    rank = {"low": 0, "medium": 1, "high": 2}
    levels = list(policy["depth_defaults"][depth])
    reasons: dict[str, list[str]] = {
        f"G{index}": [f"depth_{depth}"] for index in range(8)
    }
    triggers: list[str] = []

    def raise_to(gate_id: str, level: str, reason: str) -> None:
        index = int(gate_id[1:])
        if rank[level] > rank[levels[index]]:
            levels[index] = level
        if reason not in reasons[gate_id]:
            reasons[gate_id].append(reason)

    if risk == "high":
        triggers.append("high_risk")
        for gate_id in policy["escalation_rules"]["high_risk"]:
            raise_to(gate_id, "high", "high_risk")
    if architecture_status == "conflicted":
        triggers.append("architecture_conflict")
        for gate_id in policy["escalation_rules"]["architecture_conflict"]:
            raise_to(gate_id, "high", "architecture_conflict")
    for item in feedback:
        target_gate = item.get("target_gate")
        if item.get("attempt", 1) >= 2 and target_gate is not None:
            trigger = f"repeated_feedback:{target_gate}"
            triggers.append(trigger)
            raise_to(target_gate, "high", "repeated_feedback")
            raise_to("G7", "high", "repeated_feedback")

    return {
        "policy_id": policy["policy_id"],
        "specific_model": None,
        "depth": depth,
        "risk": risk,
        "adapter_resolution_required": True,
        "escalation_triggers": list(dict.fromkeys(triggers)),
        "gate_profiles": [
            {
                "gate_id": f"G{index}",
                "role": policy["gate_roles"][f"G{index}"],
                "reasoning": levels[index],
                "independent_context": depth == "deep" and index == 7,
                "reasons": reasons[f"G{index}"],
            }
            for index in range(8)
        ],
    }


def route(context: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one structured routing context and return a portable result."""

    if context.get("schema_version") != 1:
        raise RouterError("schema_version must be 1")
    request_id = _require_string(context, "request_id")
    target = _require_string(context, "target", {"project", "harness", "harness_overview"})
    scope = _require_string(
        context,
        "scope",
        {
            "software_engineering",
            "software_related",
            "general_information",
            "decision_support",
            "creative",
            "non_engineering",
        },
    )
    project_state = _require_string(
        context, "project_state", {"greenfield", "brownfield", "hybrid", "unknown", "not_applicable"}
    )
    action = _require_string(
        context,
        "action",
        {"investigate", "define", "plan", "design", "implement", "change", "verify", "review", "document", "approve", "handoff"},
    )
    fields = set(_string_list(context, "fields"))
    languages = _string_list(context, "languages")
    evidence = _string_list(context, "evidence_ids")
    requested_standards = _string_list(context, "standards")
    authorized_standard_evidence = _string_list(context, "authorized_standard_evidence_ids")
    conformance_intent = context.get("conformance_intent", "guidance")
    if conformance_intent not in CONFORMANCE_INTENTS:
        raise RouterError(f"conformance_intent has unsupported value: {conformance_intent}")
    conformance_scope = context.get("conformance_scope")
    conformance_owner = context.get("conformance_owner")
    for key, value in (
        ("conformance_scope", conformance_scope),
        ("conformance_owner", conformance_owner),
    ):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise RouterError(f"{key} must be a non-empty string when provided")
    pattern_scopes = set(_string_list(context, "pattern_scopes"))
    unknown_pattern_scopes = pattern_scopes - PATTERN_SCOPES
    if unknown_pattern_scopes:
        raise RouterError(f"pattern_scopes has unsupported values: {sorted(unknown_pattern_scopes)}")
    characteristics = set(_string_list(context, "change_characteristics"))
    unknown_characteristics = characteristics - CHANGE_CHARACTERISTICS
    if unknown_characteristics:
        raise RouterError(
            f"change_characteristics has unsupported values: {sorted(unknown_characteristics)}"
        )
    language_scope = context.get("language_scope", "authored_in_scope" if languages else "none")
    if language_scope not in LANGUAGE_SCOPES:
        raise RouterError(f"language_scope has unsupported value: {language_scope}")
    if not languages and language_scope != "none":
        raise RouterError("language_scope must be none when languages is empty")
    enforcement = context.get("enforcement_mode", "manual")
    if enforcement not in {"hook", "manual", "unsupported"}:
        raise RouterError("enforcement_mode must be hook, manual, or unsupported")

    is_software = scope in {"software_engineering", "software_related"}
    revision = 1
    gate_results: list[dict[str, Any]] = []
    all_activated: list[str] = []

    g0_blocked = []
    if enforcement == "unsupported" and action in {"implement", "change", "approve"}:
        g0_blocked.append({"reason": "unsupported_enforcement_is_read_only"})
    if enforcement == "manual" and action in {"implement", "change", "approve"} and not context.get(
        "manual_guard_valid", False
    ):
        g0_blocked.append({"reason": "manual_guard_required_for_mutation"})
    gate_results.append(_gate_result("G0", revision, branches=[enforcement], blocked=g0_blocked, evidence=evidence))

    intake_skill = "core.intake-and-route"
    all_activated.append(intake_skill)
    g1_blocked = []
    if context.get("material_ambiguity", False):
        g1_blocked.append({"reason": "material_clarification_required"})
    gate_results.append(_gate_result(
        "G1",
        revision,
        [intake_skill],
        sorted(fields),
        blocked=g1_blocked,
        evidence=evidence,
        application_depths=_depths_for_skills(
            [intake_skill], context.get("depth", "standard"), "not_applicable", characteristics
        ),
    ))

    g2_skills: list[str] = []
    g2_blocked: list[dict[str, Any]] = []
    architecture_status = context.get("architecture_status", "not_applicable" if not is_software else "draft")
    architecture_status = ARCHITECTURE_STATUS_ALIASES.get(str(architecture_status), str(architecture_status))
    if architecture_status not in {"not_applicable", "missing", "draft", "confirmed", "stale", "conflicted"}:
        raise RouterError(f"architecture_status has unsupported value: {architecture_status}")
    standard_aliases = manifest["selectors"]["standard_aliases"]
    standard_profiles = manifest["selectors"]["standard_profiles"]
    normalized_standards = [
        _normalize_token(standard, standard_aliases) for standard in requested_standards
    ]
    unsupported_standards = sorted(set(normalized_standards) - set(standard_profiles))
    g2_branches: list[str] = []
    if is_software and target == "project":
        g2_skills.append("core.architecture-baseline-and-design")
        g2_branches.append("standards_applicability")
        if architecture_status == "conflicted":
            g2_blocked.append({"reason": "architecture_baseline_conflicted"})
        for standard in sorted(set(normalized_standards) & set(standard_profiles)):
            g2_branches.append(f"standard:{standard}")
        for standard in unsupported_standards:
            g2_blocked.append({"reason": "unsupported_standard_profile", "standard": standard})
        if conformance_intent == "conformance" and not normalized_standards:
            g2_blocked.append({"reason": "conformance_standard_required"})
        if conformance_intent == "conformance" and not authorized_standard_evidence:
            g2_blocked.append({"reason": "authorized_standard_evidence_required"})
        if conformance_intent == "conformance" and not conformance_scope:
            g2_blocked.append({"reason": "conformance_scope_required"})
        if conformance_intent == "conformance" and not conformance_owner:
            g2_blocked.append({"reason": "conformance_owner_required"})
    all_activated.extend(g2_skills)
    gate_results.append(_gate_result(
        "G2",
        revision,
        g2_skills,
        [str(architecture_status), f"conformance_intent:{conformance_intent}", *g2_branches],
        blocked=g2_blocked,
        evidence=[*evidence, *authorized_standard_evidence],
        application_depths=_depths_for_skills(
            g2_skills,
            context.get("depth", "standard"),
            str(architecture_status),
            characteristics,
            risk=context.get("risk", "medium"),
        ),
    ))

    g3_skills: list[str] = []
    if target == "harness":
        g3_skills.append("core.harness-upgrade-analysis")
    elif target == "project" and is_software:
        if project_state == "greenfield":
            g3_skills.append("core.greenfield-planning")
        elif project_state == "brownfield":
            g3_skills.append("core.brownfield-impact-analysis")
        elif project_state == "hybrid":
            g3_skills.extend(["core.brownfield-impact-analysis", "core.greenfield-planning"])
    if action == "document" or "documentation" in fields:
        g3_skills.append("core.document-purpose")
    g3_skills = list(dict.fromkeys(g3_skills))
    all_activated.extend(g3_skills)
    gate_results.append(_gate_result(
        "G3",
        revision,
        g3_skills,
        [project_state],
        evidence=evidence,
        application_depths=_depths_for_skills(
            g3_skills,
            context.get("depth", "standard"),
            str(architecture_status),
            characteristics,
            risk=context.get("risk", "medium"),
        ),
    ))

    tech_selected, suppressed = _technology_selection(context, manifest)
    config_candidates = context.get("configuration_candidates", [])
    if not isinstance(config_candidates, list):
        raise RouterError("configuration_candidates must be an array")
    g4_skills: list[str] = []
    g4_branches = sorted(fields & {
        "testing",
        "documentation",
        "security",
        "performance",
        "operations",
        "devops_release",
        "compliance",
        "quality_attributes",
    })
    if tech_selected or "technology_selection" in fields:
        g4_skills.append("core.technology-selection-and-integration")
        g4_branches.append("technology_selection")
    if config_candidates or "configuration" in fields:
        g4_skills.append("core.configuration-and-environment-management")
        g4_branches.append("configuration")
    g4_branches = sorted(set(g4_branches))
    all_activated.extend(g4_skills)
    gate_results.append(_gate_result(
        "G4",
        revision,
        g4_skills,
        g4_branches,
        evidence=evidence,
        application_depths=_depths_for_skills(
            g4_skills,
            context.get("depth", "standard"),
            str(architecture_status),
            characteristics,
            risk=context.get("risk", "medium"),
        ),
    ))

    technology_skills = manifest["selectors"]["technology_skills"]
    g5_skills = [technology_skills[name] for name in sorted(tech_selected) if name in technology_skills]
    pattern_scope_map = manifest["selectors"]["pattern_characteristic_scopes"]
    pattern_scopes.update(
        pattern_scope_map[item] for item in sorted(characteristics) if item in pattern_scope_map
    )
    if "design_patterns" in fields:
        pattern_scopes.add("design")
    if "architecture" in fields and action in {"design", "review"}:
        pattern_scopes.add("architecture")

    pattern_suppressed: list[dict[str, Any]] = []
    if target == "project" and is_software and pattern_scopes:
        g5_skills.insert(0, "core.architecture-and-design-patterns")
    elif target == "project" and is_software and action in {"design", "implement", "change", "review"}:
        pattern_suppressed.append({
            "skill_id": "core.architecture-and-design-patterns",
            "reason": "no_structural_or_interaction_pattern_signal",
        })

    language_in_scope = (
        bool(languages)
        and language_scope == "authored_in_scope"
        and action in CODE_SCOPE_ACTIONS
        and not characteristics & {"documentation_only", "generated_code_only"}
    )
    language_suppressed: list[dict[str, Any]] = []
    if language_in_scope:
        g5_skills.append("core.language-engineering")
    elif languages:
        if characteristics & {"documentation_only", "generated_code_only"}:
            language_suppression_reason = "non_authored_content_only"
        elif language_scope != "authored_in_scope":
            language_suppression_reason = f"language_scope_{language_scope}"
        else:
            language_suppression_reason = f"action_{action}_has_no_authored_code_work"
        language_suppressed.append({
            "skill_id": "core.language-engineering",
            "reason": language_suppression_reason,
        })
    g5_branches = [f"pattern:{scope}" for scope in sorted(pattern_scopes)]
    if language_in_scope:
        g5_branches.extend(sorted(languages))
    g5_suppressed = [*suppressed, *pattern_suppressed, *language_suppressed]
    all_activated.extend(g5_skills)
    gate_results.append(_gate_result(
        "G5",
        revision,
        g5_skills,
        g5_branches,
        suppressed=g5_suppressed,
        evidence=evidence,
        application_depths=_depths_for_skills(
            g5_skills,
            context.get("depth", "standard"),
            str(architecture_status),
            characteristics,
            risk=context.get("risk", "medium"),
        ),
    ))

    implementation_profiles: list[str] = []
    g6_suppressed: list[dict[str, Any]] = []
    if language_in_scope:
        implementation_profiles.append("core")
        profile_map = manifest["selectors"]["implementation_quality_profiles"]
        implementation_profiles.extend(
            profile_map[item]
            for item in sorted(characteristics)
            if item in profile_map
        )
        implementation_profiles = list(dict.fromkeys(implementation_profiles))
    elif target == "project" and is_software and action in CODE_SCOPE_ACTIONS:
        g6_suppressed.append({
            "skill_id": "core.implementation-quality",
            "reason": "no_authored_code_boundary_in_scope",
        })
    g6_skills = []
    if implementation_profiles:
        g6_skills.append("core.implementation-quality")
    if target == "harness_overview":
        g6_skills.append("core.harness-overview-html")
    all_activated.extend(g6_skills)
    g6_branches = [f"implementation_quality:{profile}" for profile in implementation_profiles]
    if not g6_branches:
        g6_branches = ["execution"]
    gate_results.append(_gate_result(
        "G6",
        revision,
        g6_skills,
        g6_branches,
        suppressed=g6_suppressed,
        evidence=evidence,
        application_depths=_depths_for_skills(
            g6_skills,
            context.get("depth", "standard"),
            str(architecture_status),
            characteristics,
            implementation_profiles,
            context.get("risk", "medium"),
        ),
    ))

    verify_skill = "core.verify-and-handoff"
    all_activated.append(verify_skill)
    gate_results.append(_gate_result(
        "G7",
        revision,
        [verify_skill],
        ["verification", "handoff"],
        evidence=evidence,
        application_depths=_depths_for_skills(
            [verify_skill],
            context.get("depth", "standard"),
            str(architecture_status),
            characteristics,
            risk=context.get("risk", "medium"),
        ),
    ))

    feedback, final_revision, feedback_requires_user = _feedback_results(context, manifest, revision)
    execution_profile = _execution_profile(context, manifest, str(architecture_status), feedback)
    blocked = any(result["blocked"] for result in gate_results)
    if g0_blocked or (blocked and not g1_blocked):
        status = "blocked"
    elif feedback_requires_user or g1_blocked:
        status = "waiting_user"
    else:
        status = "active"
    events = [
        {"type": "gate_evaluated", "gate_id": result["gate_id"], "forward_revision": result["forward_revision"]}
        for result in gate_results
    ]
    for item in feedback:
        events.append({"type": "feedback_emitted", "feedback_id": item["feedback_id"], "target_gate": item["target_gate"]})
        if item["target_gate"] is not None and not item["requires_user"]:
            events.extend(
                [
                    {"type": "artifact_invalidated", "artifact_id": artifact_id, "feedback_id": item["feedback_id"]}
                    for artifact_id in item["invalidated_artifact_ids"]
                ]
            )
            events.append({"type": "gate_reopened", "gate_id": item["target_gate"], "forward_revision": item["next_forward_revision"]})

    return {
        "schema_version": 1,
        "request_id": request_id,
        "model": manifest["model"],
        "status": status,
        "forward_revision": final_revision,
        "execution_profile": execution_profile,
        "gate_results": gate_results,
        "activated_skills": list(dict.fromkeys(all_activated)),
        "suppressed_skills": [*g5_suppressed, *g6_suppressed],
        "feedback_results": feedback,
        "events": events,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Router JSON input; defaults to stdin")
    parser.add_argument("--output", type=Path, help="Router JSON output; defaults to stdout")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "registry" / "routing-gates.json",
    )
    args = parser.parse_args(argv)
    try:
        result = route(_read_json(args.input), _load_manifest(args.manifest))
        _write_json(result, args.output)
    except RouterError as exc:
        error = {"schema_version": 1, "status": "failed", "error": str(exc)}
        _write_json(error, args.output)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
