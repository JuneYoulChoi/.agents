"""ROS MCP selection stays conditional and never authorizes tool execution."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from harness_router import RouterError, _load_manifest, route
from harness_runner import start, submit
from harness_validator import write_object
from harness_bootstrap import source_tree_hash


def intake():
    return {
        "schema_version": 1, "request_id": "REQ-ROS-MCP", "target": "project",
        "scope": "software_engineering", "project_state": "brownfield",
        "action": "investigate", "risk": "medium", "depth": "standard",
        "confidence": "high", "enforcement_mode": "hook",
        "architecture_status": "confirmed", "fields": ["robotics"],
        "language_scope": "none", "languages": [],
        "intent": {"goal": "Inspect the selected ROS2 graph", "success_criteria":
                   ["Report observations and failed queries separately"], "constraints": []},
        "technologies": [{"name": name, "status": "selected", "material": True}
                         for name in ("ros2", "ros-mcp-server")],
        "evidence_ids": ["EVD-ROS-MCP-SCOPE"], "artifacts": [], "feedback": [],
    }


class RosMcpRoutingTests(unittest.TestCase):
    def setUp(self):
        self.manifest = _load_manifest(ROOT / "registry/routing-gates.json")

    def test_selected_pair_loads_only_ros_profile_without_tool_authority(self):
        result = route(intake(), self.manifest)
        profile = result["ros2_mcp_profile"]
        self.assertTrue(profile["applicable"])
        self.assertFalse(profile["execution_authorized"])
        self.assertTrue((ROOT / profile["reference"]).is_file())
        g5 = next(g for g in result["gate_results"] if g["gate_id"] == "G5")
        self.assertIn("tool_profile:ros2_mcp_inspection", g5["activated_branches"])
        self.assertEqual(result["activated_skills"].count("core.ros2-engineering"), 1)
        for unrelated in ("moveit", "isaac-sim", "isaac-lab", "colcon-workspace"):
            self.assertNotIn("core." + unrelated + "-engineering", result["activated_skills"])
        self.assertNotIn("core.language-engineering", result["activated_skills"])

    def test_unrelated_missing_candidate_and_detected_unaffected_are_suppressed(self):
        for technologies in (
            [], [{"name": "ros2", "status": "selected"}],
            [{"name": "ros-mcp-server", "status": "selected"}],
            [{"name": "ros2", "status": "selected"}, {"name": "blender-mcp", "status": "selected"}],
            [{"name": "ros2", "status": "selected"}, {"name": "context-mode", "status": "selected"}],
            [{"name": "ros2", "status": "selected"}, {"name": "ros-mcp-server", "status": "candidate"}],
            [{"name": "ros2", "status": "selected"}, {"name": "ros-mcp-server", "status": "detected_existing", "material": False}],
        ):
            with self.subTest(technologies=technologies):
                context = intake()
                context["technologies"] = technologies
                profile = route(context, self.manifest)["ros2_mcp_profile"]
                self.assertFalse(profile["applicable"])
                self.assertIsNone(profile["reference"])

    def test_blocked_and_maintenance_routes_do_not_offer_profile(self):
        for delta in ({"enforcement_mode": "unsupported", "action": "change"}, {"target": "harness"},
                      {"project_state": "unknown"}, {"architecture_status": "conflicted"}):
            with self.subTest(delta=delta):
                context = intake()
                context.update(delta)
                self.assertFalse(route(context, self.manifest)["ros2_mcp_profile"]["applicable"])

    def test_non_mcp_route_retains_prior_gates_and_skills(self):
        old = copy.deepcopy(self.manifest)
        old.pop("ros2_mcp_reference")
        old["selectors"]["technology_aliases"].pop("ros-mcp-server")
        for technologies in ([{"name": "ros2", "status": "selected"}],
                             [{"name": "react", "status": "selected"}]):
            context = intake()
            context["technologies"] = technologies
            before, after = route(context, old), route(context, self.manifest)
            self.assertEqual(before["gate_results"], after["gate_results"])
            self.assertEqual(before["activated_skills"], after["activated_skills"])

    def test_quarantined_or_malformed_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for value in ("incoming/robotics/skill/SKILL.md", "../../outside.md", {"path": "x"}):
                manifest = copy.deepcopy(self.manifest)
                manifest["ros2_mcp_reference"] = value
                path = Path(directory) / "manifest.json"
                write_object(path, manifest)
                with self.assertRaises(RouterError):
                    _load_manifest(path)

    def test_runner_exposes_profile_only_at_ros_skill_and_preserves_it_on_disk(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            path = target / "intake.json"
            write_object(path, intake())
            response = start(target, "TASK-ROS-MCP", path, "codex", "test", ROOT,
                             ROOT / "registry/active-skills.json", ROOT / "registry/taxonomy.json",
                             ROOT / "registry/routing-gates.json")
            while response["next"]["skill_id"] != "core.ros2-engineering":
                step = response["next"]
                self.assertIsNone(step["tool_profile"])
                result = {"schema_version": 1, "skill_id": step["skill_id"], "status": "completed",
                          "artifact_ids": ["ART-ROS-BASELINE"], "evidence_ids": ["EVD-ROS-BASELINE"],
                          "transition": {"next_stage": step["stage"]}, "error": None,
                          "execution_resolution": {"adapter": "codex", "model": "test", "reasoning":
                          step["execution_profile"]["reasoning"], "native_reasoning": "test",
                          "status": "platform_default", "evidence_ids": ["EVD-TEST"]}}
                result_path = target / "result.json"
                write_object(result_path, result)
                response = submit(target, "TASK-ROS-MCP", response["revision"], result_path,
                                  ROOT, ROOT / "registry/active-skills.json")
            self.assertTrue(response["next"]["tool_profile"]["applicable"])
            state = json.loads((target / ".agents/state/TASK-ROS-MCP/state.json").read_text())
            self.assertEqual(state["route"]["ros2_mcp_profile"], response["next"]["tool_profile"])

    def test_optional_runtime_does_not_change_source_pin_but_adapter_does(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "tools/ros-mcp-server/inspect_server.py"
            source.parent.mkdir(parents=True)
            source.write_text("source-v1")
            before = source_tree_hash(root)
            for path in (".runtime/cache/data", "upstream/build/generated.py", "upstream/ros_mcp.egg-info/PKG-INFO"):
                generated = source.parent / path
                generated.parent.mkdir(parents=True, exist_ok=True)
                generated.write_text("generated")
            self.assertEqual(source_tree_hash(root), before)
            source.write_text("source-v2")
            self.assertNotEqual(source_tree_hash(root), before)

    def test_vendored_runtime_matches_pinned_original_files(self):
        import hashlib
        tool = ROOT / "tools/ros-mcp-server"
        provenance = json.loads((tool / "provenance.json").read_text())
        for name, digest in provenance["files"].items():
            self.assertEqual(hashlib.sha256((tool / "upstream" / name).read_bytes()).hexdigest(), digest, name)
