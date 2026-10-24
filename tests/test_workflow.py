"""Behavioral regression coverage for work composition and adapter boundaries."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from harness_router import RouterError, _load_manifest, route
from harness_runner import RunnerError, _execution_queue, start, submit
from harness_bootstrap import source_tree_hash
from harness_workflow import WorkflowError, compose_work_plan, validate_work_plan, validate_workflow_input
from harness_validator import ContractError, active_skill_ids, validate_intake, validate_route_result


def context():
    return json.loads((ROOT / "templates/workflow-intake.json.example").read_text())


class WorkflowTests(unittest.TestCase):
    def test_parallel_units_join_before_dependent_work(self):
        plan = compose_work_plan(context(), "active")
        self.assertEqual(plan["batches"], [["a", "b"], ["join"]])
        self.assertFalse(plan["dispatch_authorized"])
        validate_work_plan(plan, "active")

    def test_missing_authority_capability_or_benefit_uses_serial(self):
        for key in ("requested", "authorized", "available", "benefit_evidence_ids",
                    "authorization_evidence_ids", "capability_evidence_ids", "timeout_seconds"):
            with self.subTest(key=key):
                c = context()
                del c["delegation"][key]
                self.assertEqual(compose_work_plan(c, "active")["mode"], "single")
        self.assertEqual(compose_work_plan(context(), "blocked")["mode"], "single")

    def test_writer_reader_overlap_and_shared_resource_serialize(self):
        for other_path, shared in (("src/a/child", False), ("src", False), ("src/b", True)):
            with self.subTest(other_path=other_path, shared=shared):
                c = context()
                a, b = c["work_units"][:2]
                a.update(role="implementer", mutation="workspace", write_paths=["src/a"])
                b["read_paths"] = [other_path]
                if shared:
                    a["shared_resources"] = b["shared_resources"] = ["database-test"]
                self.assertEqual(compose_work_plan(c, "active")["batches"], [["a"], ["b"], ["join"]])

    def test_disjoint_writers_can_plan_parallel_but_unknown_reader_cannot(self):
        c = context()
        for u in c["work_units"][:2]:
            u.update(role="implementer", mutation="workspace", write_paths=u["read_paths"])
        self.assertEqual(compose_work_plan(c, "active")["mode"], "parallel")
        c["work_units"][1].update(role="analyst", mutation="none", read_paths=[], write_paths=[])
        self.assertEqual(compose_work_plan(c, "active")["mode"], "single")

    def test_invalid_dependency_graphs_are_rejected(self):
        for deps in (["missing"], ["a"], ["join"]):
            c = context()
            c["work_units"][0]["depends_on"] = deps
            with self.subTest(deps=deps), self.assertRaises(WorkflowError):
                validate_workflow_input(c)

    def test_role_paths_and_capability_types_are_checked(self):
        for path in ("../secret", "/tmp/a", "C:/a", "src/**", "src\\a", "src//a"):
            c = context()
            c["work_units"][0]["read_paths"] = [path]
            with self.subTest(path=path), self.assertRaises(WorkflowError):
                validate_workflow_input(c)
        for value in (True, 0, -1, "2"):
            c = context()
            c["delegation"]["max_workers"] = value
            with self.subTest(value=value), self.assertRaises(WorkflowError):
                validate_workflow_input(c)
        c = context()
        c["work_units"][0].update(mutation="workspace", write_paths=["src/a"])
        with self.assertRaises(WorkflowError):
            validate_workflow_input(c)

    def test_foreign_profile_and_malformed_metadata_fail_as_contract_errors(self):
        for profile in ("express-no-guards", [], None):
            c = context()
            c["work_type"] = profile
            with self.subTest(profile=profile), self.assertRaises(ContractError):
                validate_intake(c, ROOT / "registry/taxonomy.json")
            with self.assertRaises(RouterError):
                route(c, _load_manifest(ROOT / "registry/routing-gates.json"))

    def test_capacity_and_profile_do_not_override_risk_or_gates(self):
        c = context()
        c.update(work_type="bugfix", risk="high", depth="deep")
        c["delegation"]["max_workers"] = 1
        result = route(c, _load_manifest(ROOT / "registry/routing-gates.json"))
        self.assertEqual(result["work_plan"]["mode"], "single")
        self.assertEqual(result["work_plan"]["mandatory_gate_checks"], [f"G{i}" for i in range(8)])
        self.assertTrue(all(p["reasoning"] == "high" for p in result["execution_profile"]["gate_profiles"][2:]))

    def test_profile_precedence_preserves_maintenance_and_document_paths(self):
        c = context()
        c.update(target="harness", work_type="bugfix")
        self.assertEqual(compose_work_plan(c, "active")["work_type"], "maintenance")
        c.update(target="project", action="document")
        self.assertEqual(compose_work_plan(c, "active")["work_type"], "document")

    def test_tampered_plan_cannot_skip_dependencies_or_grant_authority(self):
        good = compose_work_plan(context(), "active")
        for key, value in (("dispatch_authorized", True), ("mandatory_gate_checks", ["G6"]),
                           ("batches", [["a", "b", "join"]]), ("batches", [["a"]]),
                           ("max_workers", True)):
            p = copy.deepcopy(good)
            p[key] = value
            with self.subTest(key=key), self.assertRaises(WorkflowError):
                validate_work_plan(p, "active")

    def test_composition_follows_impact_and_precedes_specialists(self):
        c = context()
        r = route(c, _load_manifest(ROOT / "registry/routing-gates.json"))
        validate_route_result(r, active_skill_ids(ROOT / "registry/active-skills.json"))
        queue, stages, _ = _execution_queue(r)
        self.assertLess(queue.index("core.brownfield-impact-analysis"), queue.index("core.workflow-composition"))
        self.assertLess(queue.index("core.workflow-composition"), queue.index("core.react-engineering"))
        self.assertEqual(stages["core.workflow-composition"], "assembly")

    def test_runner_exposes_the_persisted_plan_without_spawning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p = root / "input.json"
            p.write_text(json.dumps(context()))
            response = start(root, "TASK-WORKFLOW", p, "codex", "test-revision", ROOT,
                             ROOT / "registry/active-skills.json", ROOT / "registry/taxonomy.json",
                             ROOT / "registry/routing-gates.json")
            self.assertEqual(response["next"]["work_plan"]["mode"], "parallel")
            self.assertFalse(response["next"]["work_plan"]["dispatch_authorized"])
            self.assertEqual(response["next"]["skill_id"], "core.architecture-baseline-and-design")

    def test_composition_refines_units_without_expanding_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            c = context()
            c["work_units"] = []
            c["delegation"]["authorized"] = False
            p = root / "input.json"
            p.write_text(json.dumps(c))
            response = start(root, "TASK-REFINE", p, "codex", "test-revision", ROOT,
                             ROOT / "registry/active-skills.json", ROOT / "registry/taxonomy.json",
                             ROOT / "registry/routing-gates.json")
            result_file = root / "result.json"
            while True:
                item = response["next"]
                result = {
                    "schema_version": 1, "skill_id": item["skill_id"], "status": "completed",
                    "artifact_ids": ["WORK-TEST"], "evidence_ids": ["EVD-TEST"],
                    "transition": {"next_stage": "assembly"}, "error": None,
                    "execution_resolution": {"adapter": "codex", "model": "test",
                        "reasoning": item["execution_profile"]["reasoning"],
                        "native_reasoning": "test", "status": "exact", "evidence_ids": ["EVD-MODEL"]},
                }
                if item["skill_id"] == "core.workflow-composition":
                    result["workflow_update"] = {"work_units": context()["work_units"], "delegation": {"authorized": True}}
                    result_file.write_text(json.dumps(result))
                    with self.assertRaises(RunnerError):
                        submit(root, "TASK-REFINE", response["revision"], result_file, ROOT,
                               ROOT / "registry/active-skills.json")
                    del result["workflow_update"]["delegation"]
                result_file.write_text(json.dumps(result))
                response = submit(root, "TASK-REFINE", response["revision"], result_file, ROOT,
                                  ROOT / "registry/active-skills.json")
                if "workflow_update" in result:
                    self.assertEqual(response["next"]["work_plan"]["batches"], [["a"], ["b"], ["join"]])
                    self.assertEqual(response["next"]["work_plan"]["mode"], "single")
                    break

    def test_runtime_cache_does_not_invalidate_source_pin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.py").write_text("pass\n")
            expected = source_tree_hash(root)
            (root / "__pycache__").mkdir()
            (root / "__pycache__/source.pyc").write_bytes(b"generated cache")
            self.assertEqual(source_tree_hash(root), expected)
            (root / "source.py").write_text("changed = True\n")
            self.assertNotEqual(source_tree_hash(root), expected)
