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
from harness_state import StateError, StateStore  # noqa: E402
from harness_validator import ContractError, validate_intake, write_object  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
