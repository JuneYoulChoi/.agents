"""Focused regression tests for the minimal reference runtime."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT / "scripts"))

from harness_runner import RunnerError, start, submit  # noqa: E402
from harness_router import _load_manifest, route  # noqa: E402
from harness_state import StateError, StateStore  # noqa: E402
from harness_validator import (  # noqa: E402
    ContractError,
    validate_intake,
    validate_implementation_quality,
    validate_pattern_review,
    write_object,
)


def intake() -> dict:
    return {
        "schema_version": 1,
        "request_id": "REQ-RUNTIME-TEST",
        "target": "project",
        "scope": "software_engineering",
        "project_state": "brownfield",
        "action": "review",
        "risk": "medium",
        "depth": "standard",
        "confidence": "high",
        "intent": {
            "goal": "Review and externalize the service port",
            "success_criteria": ["Architecture is checked before implementation"],
            "constraints": ["Preserve existing behavior"],
        },
        "enforcement_mode": "hook",
        "architecture_status": "accepted",
        "fields": ["backend", "configuration", "testing"],
        "languages": ["python"],
        "technologies": [],
        "configuration_candidates": [
            {"name": "listen_port", "kind": "port", "source": "yaml", "default": 8080}
        ],
        "evidence_ids": ["EV-RUNTIME-TEST"],
        "artifacts": [],
        "feedback": [],
    }


def execution_resolution(reasoning: str, status: str = "exact") -> dict:
    return {
        "adapter": "codex",
        "model": "test-model",
        "reasoning": reasoning,
        "native_reasoning": reasoning,
        "status": status,
        "evidence_ids": ["EV-EXECUTION-PROFILE"],
    }


def undecided_pattern_review() -> dict:
    return {
        "schema_version": 1,
        "pattern_id": "PATTERN-TEST-001",
        "scopes": ["architecture"],
        "drivers": ["QAS-TEST-001"],
        "candidates": [
            {
                "candidate_id": "PATTERN-OPTION-MODULAR",
                "name": "modular_monolith",
                "status": "candidate",
                "decision_scope": "service deployment boundary",
                "fit": "keeps one deployment while preserving module ownership",
                "recommendation_reason": "matches the current team and operations constraints",
                "benefits": ["lower operational complexity"],
                "liabilities": ["limited independent deployment"],
                "quality_attribute_effects": ["improves operability"],
                "affected_artifact_ids": ["ADR-TEST-001"],
                "migration_and_rollback": ["retain the current deployment unit"],
                "verification_ids": ["TEST-PATTERN-001"],
            },
            {
                "candidate_id": "PATTERN-OPTION-SERVICES",
                "name": "microservices",
                "status": "candidate",
                "decision_scope": "service deployment boundary",
                "fit": "supports independent deployment and scaling",
                "recommendation_reason": "becomes preferable with independent team ownership",
                "benefits": ["independent deployment"],
                "liabilities": ["distributed operational complexity"],
                "quality_attribute_effects": ["improves independent scalability"],
                "affected_artifact_ids": ["ADR-TEST-001"],
                "migration_and_rollback": ["extract one boundary and retain a rollback route"],
                "verification_ids": ["TEST-PATTERN-002"],
            },
        ],
        "decision": {
            "status": "user_decision_required",
            "decision_scope": "service deployment boundary",
            "recommended_candidate_id": "PATTERN-OPTION-MODULAR",
            "recommendation_reason": "current QAS prioritizes operational simplicity",
            "conditions_that_change_recommendation": ["teams require independent release ownership"],
            "selected_candidate_id": None,
            "decision_evidence_ids": [],
        },
        "open_issue_ids": ["ISSUE-PATTERN-001"],
    }


def implementation_quality_result() -> dict:
    return {
        "schema_version": 1,
        "status": "completed",
        "authored_boundaries": ["src/service"],
        "activated_profiles": [
            {
                "id": "core",
                "depth": "light",
                "authored_boundaries": ["src/service"],
                "evidence_ids": ["EV-CODE-001"],
                "expected_outcomes": ["errors remain explicit"],
                "verification_ids": ["TEST-CODE-001"],
            }
        ],
        "suppressed_profiles": [
            {"id": "performance", "reason": "no performance QAS or hotspot"}
        ],
        "findings": [],
        "changes_or_recommendations": [],
        "residual_risks": [],
        "open_points": [],
    }


class RuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_owner = tempfile.TemporaryDirectory(prefix="harness-runtime-test-")
        self.target = Path(self.temp_owner.name)
        self.registry = HARNESS_ROOT / "registry" / "active-skills.json"
        self.taxonomy = HARNESS_ROOT / "registry" / "taxonomy.json"
        self.manifest = HARNESS_ROOT / "registry" / "routing-gates.json"

    def tearDown(self) -> None:
        self.temp_owner.cleanup()

    def start_task(self) -> dict:
        intake_path = self.target / "intake.json"
        write_object(intake_path, intake())
        return start(
            self.target,
            "TASK-RUNTIME",
            intake_path,
            "codex",
            "test-revision",
            HARNESS_ROOT,
            self.registry,
            self.taxonomy,
            self.manifest,
        )

    def test_runner_starts_at_architecture_and_advances_in_order(self) -> None:
        started = self.start_task()
        self.assertEqual("active", started["status"])
        self.assertEqual("core.architecture-baseline-and-design", started["next"]["skill_id"])
        self.assertEqual("architect", started["next"]["execution_profile"]["role"])
        self.assertEqual("medium", started["next"]["execution_profile"]["reasoning"])
        state = StateStore(self.target).read("TASK-RUNTIME")
        self.assertEqual(
            intake().get("change_characteristics", []),
            state["classification"]["change_characteristics"],
        )
        self.assertEqual("authored_in_scope", state["classification"]["language_scope"])
        result_path = self.target / "skill-result.json"
        write_object(
            result_path,
            {
                "schema_version": 1,
                "skill_id": "core.architecture-baseline-and-design",
                "status": "completed",
                "artifact_ids": ["ARCH-001"],
                "evidence_ids": ["EV-ARCH-001"],
                "transition": {"next_stage": "impact"},
                "execution_resolution": execution_resolution("medium"),
                "error": None,
            },
        )
        advanced = submit(
            self.target,
            "TASK-RUNTIME",
            1,
            result_path,
            HARNESS_ROOT,
            self.registry,
        )
        self.assertEqual(2, advanced["revision"])
        self.assertEqual("core.brownfield-impact-analysis", advanced["next"]["skill_id"])

    def test_completion_requires_successful_verification_and_writes_handoff(self) -> None:
        response = self.start_task()
        result_path = self.target / "skill-result.json"
        for _ in range(30):
            next_item = response.get("next")
            if next_item is None:
                break
            skill_id = next_item["skill_id"]
            write_object(
                result_path,
                {
                    "schema_version": 1,
                    "skill_id": skill_id,
                    "status": "completed",
                    "artifact_ids": [f"ART-{next_item['position']:03d}"],
                    "evidence_ids": [f"EV-{next_item['position']:03d}"],
                    "transition": {
                        "next_stage": "handoff"
                        if skill_id == "core.verify-and-handoff"
                        else next_item["stage"]
                    },
                    "execution_resolution": execution_resolution(
                        next_item["execution_profile"]["reasoning"]
                    ),
                    "error": None,
                },
            )
            response = submit(
                self.target,
                "TASK-RUNTIME",
                response["revision"],
                result_path,
                HARNESS_ROOT,
                self.registry,
            )
        self.assertEqual("complete", response["status"])
        state = StateStore(self.target).read("TASK-RUNTIME")
        self.assertEqual("passed", state["validation_status"])
        handoff = self.target / ".agents" / "state" / "TASK-RUNTIME" / "handoff.md"
        self.assertTrue(handoff.is_file())

    def test_runner_rejects_inconsistent_execution_resolution(self) -> None:
        started = self.start_task()
        result_path = self.target / "skill-result.json"
        write_object(
            result_path,
            {
                "schema_version": 1,
                "skill_id": started["next"]["skill_id"],
                "status": "completed",
                "artifact_ids": [],
                "evidence_ids": [],
                "transition": {"next_stage": "impact"},
                "execution_resolution": execution_resolution("low", "upgraded"),
                "error": None,
            },
        )
        with self.assertRaises(RunnerError):
            submit(
                self.target,
                "TASK-RUNTIME",
                started["revision"],
                result_path,
                HARNESS_ROOT,
                self.registry,
            )

    def test_revision_conflict_preserves_current_state(self) -> None:
        self.start_task()
        store = StateStore(self.target)
        before = store.read("TASK-RUNTIME")
        with self.assertRaises(StateError):
            store.update("TASK-RUNTIME", 99, "invalid_update", lambda state: state.update(status="failed"))
        after = store.read("TASK-RUNTIME")
        self.assertEqual(before, after)

    def test_unreadable_state_is_not_rewritten(self) -> None:
        self.start_task()
        state_path = self.target / ".agents" / "state" / "TASK-RUNTIME" / "state.json"
        broken = '{"schema_version": 1, "revision":'
        state_path.write_text(broken, encoding="utf-8")
        with self.assertRaises(StateError):
            StateStore(self.target).read("TASK-RUNTIME")
        self.assertEqual(broken, state_path.read_text(encoding="utf-8"))

    def test_secret_candidate_requires_redaction_and_no_value(self) -> None:
        value = intake()
        value["configuration_candidates"] = [
            {
                "name": "api_token",
                "kind": "secret_reference",
                "source": "secret_provider",
                "value": "not-allowed",
            }
        ]
        with self.assertRaises(ContractError):
            validate_intake(value, self.taxonomy)

    def test_port_default_rejects_out_of_range_value(self) -> None:
        value = intake()
        value["configuration_candidates"][0]["default"] = 70000
        with self.assertRaises(ContractError):
            validate_intake(value, self.taxonomy)

    def test_structural_change_routes_through_scoped_pattern_review(self) -> None:
        value = intake()
        value["action"] = "change"
        value["change_characteristics"] = [
            "authored_code",
            "architecture_structure",
            "design_interaction",
        ]
        result = route(value, _load_manifest(self.manifest))
        gates = {gate["gate_id"]: gate for gate in result["gate_results"]}
        self.assertIn("core.architecture-and-design-patterns", result["activated_skills"])
        self.assertLess(
            result["activated_skills"].index("core.architecture-and-design-patterns"),
            result["activated_skills"].index("core.language-engineering"),
        )
        self.assertIn("pattern:architecture", gates["G5"]["activated_branches"])
        self.assertIn("pattern:design", gates["G5"]["activated_branches"])

    def test_local_code_change_suppresses_pattern_review_and_loads_core_quality(self) -> None:
        value = intake()
        value.update(
            action="change",
            risk="low",
            depth="light",
            change_characteristics=["authored_code"],
            language_scope="authored_in_scope",
        )
        result = route(value, _load_manifest(self.manifest))
        gates = {gate["gate_id"]: gate for gate in result["gate_results"]}
        self.assertNotIn("core.architecture-and-design-patterns", result["activated_skills"])
        self.assertIn("core.language-engineering", result["activated_skills"])
        self.assertIn("core.implementation-quality", result["activated_skills"])
        self.assertIn(
            {
                "skill_id": "core.architecture-and-design-patterns",
                "reason": "no_structural_or_interaction_pattern_signal",
            },
            result["suppressed_skills"],
        )
        self.assertEqual(
            ["implementation_quality:core"], gates["G6"]["activated_branches"]
        )
        self.assertEqual(
            "light", gates["G6"]["application_depths"]["core.implementation-quality"]
        )

    def test_detected_only_language_does_not_activate_implementation_skills(self) -> None:
        value = intake()
        value.update(
            action="document",
            fields=["documentation"],
            language_scope="detected_only",
            change_characteristics=["documentation_only"],
            configuration_candidates=[],
        )
        result = route(value, _load_manifest(self.manifest))
        self.assertNotIn("core.language-engineering", result["activated_skills"])
        self.assertNotIn("core.implementation-quality", result["activated_skills"])

    def test_implementation_quality_requires_core_evidence_and_verification(self) -> None:
        value = implementation_quality_result()
        self.assertIs(validate_implementation_quality(value), value)
        value["activated_profiles"][0]["verification_ids"] = []
        with self.assertRaises(ContractError):
            validate_implementation_quality(value)
        value = implementation_quality_result()
        value["activated_profiles"][0]["authored_boundaries"] = ["src/unrelated"]
        with self.assertRaises(ContractError):
            validate_implementation_quality(value)

    def test_not_applicable_implementation_quality_has_no_authored_scope(self) -> None:
        value = implementation_quality_result()
        value.update(status="not_applicable", authored_boundaries=[], activated_profiles=[])
        self.assertIs(validate_implementation_quality(value), value)

    def test_multiple_viable_patterns_require_a_user_decision(self) -> None:
        value = undecided_pattern_review()
        self.assertIs(validate_pattern_review(value), value)

    def test_pending_pattern_decision_cannot_preselect_an_option(self) -> None:
        value = undecided_pattern_review()
        value["candidates"][0]["status"] = "selected"
        value["decision"]["selected_candidate_id"] = "PATTERN-OPTION-MODULAR"
        with self.assertRaises(ContractError):
            validate_pattern_review(value)

    def test_user_selected_pattern_requires_evidence_and_tradeoffs(self) -> None:
        value = undecided_pattern_review()
        value["candidates"][0]["status"] = "selected"
        value["decision"].update(
            status="user_selected",
            selected_candidate_id="PATTERN-OPTION-MODULAR",
            decision_evidence_ids=["EVD-USER-PATTERN-001"],
        )
        value["open_issue_ids"] = []
        self.assertIs(validate_pattern_review(value), value)

        missing_tradeoff = json.loads(json.dumps(value))
        missing_tradeoff["candidates"][1]["liabilities"] = []
        with self.assertRaises(ContractError):
            validate_pattern_review(missing_tradeoff)

    def test_conformance_without_authorized_source_blocks_g2(self) -> None:
        value = intake()
        value.update(
            standards=["ISO 42010"],
            conformance_intent="conformance",
            authorized_standard_evidence_ids=[],
        )
        result = route(value, _load_manifest(self.manifest))
        gate = next(gate for gate in result["gate_results"] if gate["gate_id"] == "G2")
        self.assertEqual("blocked", result["status"])
        self.assertIn(
            {"reason": "authorized_standard_evidence_required"},
            gate["blocked"],
        )
        value["standards"] = []
        value["authorized_standard_evidence_ids"] = ["EV-AUTHORIZED-STANDARD"]
        result = route(value, _load_manifest(self.manifest))
        gate = next(gate for gate in result["gate_results"] if gate["gate_id"] == "G2")
        self.assertIn({"reason": "conformance_standard_required"}, gate["blocked"])

    def test_legacy_accepted_architecture_status_is_canonicalized(self) -> None:
        result = route(intake(), _load_manifest(self.manifest))
        gate = next(gate for gate in result["gate_results"] if gate["gate_id"] == "G2")
        self.assertIn("confirmed", gate["activated_branches"])
        self.assertNotIn("accepted", gate["activated_branches"])


if __name__ == "__main__":
    unittest.main()
