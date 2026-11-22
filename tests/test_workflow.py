"""
모듈: 하네스 테스트 (tests)
컴포넌트: 기존 회귀 테스트
역할: 작업 구성과 어댑터 실행 경계의 동작을 검증한다.
"""

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from harness_router import RouterError, _load_manifest, route
from harness_runner import RunnerError, _execution_queue, start, submit, work_event
from harness_state import StateStore
from harness_bootstrap import source_tree_hash
from harness_workflow import WorkflowError, compose_work_plan, validate_work_plan, validate_workflow_input
from harness_validator import ContractError, active_skill_ids, validate_intake, validate_route_result
from test_runtime import fixture_hook_guard


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
        """역할: Runner가 워커 실행 없이 저장된 작업 계획을 반환하는지 확인한다."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p = root / "input.json"
            p.write_text(json.dumps({**context(), "hook_guard": fixture_hook_guard(root, "TASK-WORKFLOW")}))
            response = start(root, "TASK-WORKFLOW", p, "codex", "test-revision", ROOT,
                             ROOT / "registry/active-skills.json", ROOT / "registry/taxonomy.json",
                             ROOT / "registry/routing-gates.json")
            self.assertEqual(response["next"]["work_plan"]["mode"], "parallel")
            self.assertFalse(response["next"]["work_plan"]["dispatch_authorized"])
            self.assertEqual(response["next"]["skill_id"], "core.architecture-baseline-and-design")

    def test_composition_refines_units_without_expanding_authority(self):
        """역할: 작업 구성 스킬이 기존 권한 안에서 작업 단위를 보완하는지 확인한다."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            c = context()
            c["work_units"] = []
            c["delegation"]["authorized"] = False
            p = root / "input.json"
            p.write_text(json.dumps({**c, "hook_guard": fixture_hook_guard(root, "TASK-REFINE")}))
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

    def test_observed_capacity_clamps_requested_workers(self):
        c = context(); c['delegation'].update(max_workers=20, native_worker_capacity=1)
        self.assertEqual(compose_work_plan(c, 'active')['max_workers'], 1)
        for capacity in (0, None):
            if capacity is None:
                c['delegation'].pop('native_worker_capacity', None)
            else:
                c['delegation']['native_worker_capacity'] = capacity
            self.assertEqual(compose_work_plan(c, 'active')['mode'], 'single')

    def test_mixed_or_unbound_owners_cannot_project_parallel_execution(self):
        for owner in ('core.nodejs-engineering', None):
            c = context()
            if owner is None:
                for u in c['work_units']:
                    u.pop('skill_id')
            else:
                c['work_units'][1]['skill_id'] = owner
            plan = compose_work_plan(c, 'active')
            self.assertEqual(plan['batches'], [['a'], ['b'], ['join']])
            validate_work_plan(plan, 'active')
            plan['batches'] = [['a', 'b'], ['join']]; plan['max_workers'] = 2; plan['mode'] = 'parallel'
            with self.assertRaises(WorkflowError):
                validate_work_plan(plan, 'active')

    def test_small_fullstack_and_document_work_default_to_one_agent(self):
        for fields in (['frontend', 'backend', 'ui_ux'], ['documentation'], ['implementation']):
            c = context(); c.update(fields=fields, work_units=[], delegation={})
            plan = compose_work_plan(c, 'active')
            self.assertEqual(plan['mode'], 'single')
            self.assertEqual(plan['batches'], [])
            self.assertEqual(plan['mandatory_gate_checks'], [f'G{i}' for i in range(8)])

    def test_six_same_owner_units_queue_three_at_a_time(self):
        c = context(); original = c['work_units'][0]
        c['work_units'] = [{**original, 'id': str(i), 'read_paths': [f'src/{i}']} for i in range(6)]
        c['delegation'].update(max_workers=10, native_worker_capacity=3)
        self.assertEqual(compose_work_plan(c, 'active')['batches'], [['0','1','2'], ['3','4','5']])
        for u in c['work_units']:
            u['shared_resources'] = ['physical-robot']
        self.assertEqual(compose_work_plan(c, 'active')['max_workers'], 1)


class WorkflowRefinementTests(unittest.TestCase):
    """Refine future work through real Runner transitions and durable receipts."""

    def setUp(self):
        """역할: 작업 단위 보완 테스트에 필요한 임시 프로젝트와 Runner 상태를 준비한다."""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.registry = ROOT / 'registry/active-skills.json'
        self.task = 'TASK-FUTURE-REFINEMENT'
        self.file = self.root / 'request.json'
        proof = self.root / 'proof.md'
        proof.write_text('Synthetic current baseline, impact and acceptance evidence.')
        self.proof = {'path': 'proof.md', 'sha256': hashlib.sha256(proof.read_bytes()).hexdigest()}
        self.ctx = context()
        a, b, future = self.ctx['work_units']
        a['skill_id'] = 'core.architecture-baseline-and-design'
        b.update(skill_id='core.brownfield-impact-analysis', depends_on=['a'])
        future.pop('skill_id')  # Composition binds provisional future work.
        for unit in self.ctx['work_units']:
            unit['context_artifacts'] = [self.proof]
        self.file.write_text(json.dumps({**self.ctx, 'hook_guard': fixture_hook_guard(self.root, self.task)}))
        self.response = start(self.root, self.task, self.file, 'codex', 'test', ROOT,
                              self.registry, ROOT / 'registry/taxonomy.json', ROOT / 'registry/routing-gates.json')
        self.store = StateStore(self.root, harness_root=ROOT)

    def skill_result(self):
        item = self.response['next']
        return {'schema_version': 1, 'skill_id': item['skill_id'], 'status': 'completed',
                'artifact_ids': ['WORK-TEST'], 'evidence_ids': ['EVD-TEST'],
                'transition': {'next_stage': 'assembly'}, 'error': None,
                'execution_resolution': {'adapter': 'codex', 'model': 'fixture',
                    'reasoning': item['execution_profile']['reasoning'], 'native_reasoning': 'fixture',
                    'status': 'exact', 'evidence_ids': ['EVD-MODEL']}}

    def submit_result(self, result):
        self.file.write_text(json.dumps(result))
        self.response = submit(self.root, self.task, self.response['revision'], self.file, ROOT, self.registry)

    def run_unit(self, unit_id, status='completed'):
        request = {'unit_id': unit_id, 'input_revision': 'source-001', 'mode': 'serial',
                   'checks': dict.fromkeys(['authority', 'capability', 'revision', 'ownership', 'tools'], True),
                   'evidence_ids': ['EVD-CHECK']}
        self.file.write_text(json.dumps(request))
        prepared = work_event(self.root, self.task, self.response['revision'], self.file,
                              'prepare-work', ROOT, self.registry)
        packet = prepared['packet']
        instruction = packet['skill_context']
        result = {'unit_id': unit_id, 'input_revision': 'source-001', 'packet_hash': prepared['packet_hash'],
                  'status': status, 'worker_stopped': True, 'acceptance_verified': True,
                  'artifact_ids': ['ART-UNIT'], 'evidence_ids': ['EVD-UNIT'],
                  'usage': {'status': 'reported', 'input_tokens': 10, 'output_tokens': 5, 'source': 'fixture'},
                  'verification': [{'criterion': c, 'status': 'passed', 'evidence': [self.proof]}
                                   for c in packet['unit']['acceptance']],
                  'instruction_evidence': {'instruction_hash': instruction['sha256'],
                      'reference_hashes': [r['sha256'] for r in instruction['references']]},
                  'execution_resolution': self.skill_result()['execution_resolution']}
        self.file.write_text(json.dumps(result))
        self.response = work_event(self.root, self.task, prepared['revision'], self.file,
                                   'record-work', ROOT, self.registry)

    def reach_composition(self):
        for unit_id in ('a', 'b'):
            self.run_unit(unit_id)
            self.submit_result(self.skill_result())
        self.assertEqual(self.response['next']['skill_id'], 'core.workflow-composition')

    def refinement(self):
        units = copy.deepcopy(self.ctx['work_units'])
        units[-1].update(skill_id='core.react-engineering', goal='Review impact-informed React behavior')
        return {**self.skill_result(), 'workflow_update': {'work_units': units}}

    def test_completed_early_work_preserves_receipts_and_allows_future_refinement(self):
        self.reach_composition()
        before = self.store.read(self.task)
        result = self.refinement()
        extra = {**copy.deepcopy(result['workflow_update']['work_units'][-1]), 'id': 'extra', 'depends_on': ['join']}
        result['workflow_update']['work_units'].append(extra)
        self.submit_result(result)
        after = self.store.read(self.task)
        self.assertEqual(after['execution']['work_records'], before['execution']['work_records'])
        self.assertEqual(after['intake']['delegation'], before['intake']['delegation'])
        self.assertEqual(after['route']['work_plan']['units'], result['workflow_update']['work_units'])
        self.assertEqual(after['intake']['work_units'], result['workflow_update']['work_units'])
        self.assertEqual(after['route']['work_plan']['batches'], [['a'], ['b'], ['join'], ['extra']])

    def test_prepared_unit_removal_or_change_does_not_advance_state(self):
        self.reach_composition()
        before = self.store.read(self.task)
        for change in ('remove', 'goal', 'skill_id', 'acceptance', 'context_artifacts'):
            with self.subTest(change=change):
                result = self.refinement()
                units = result['workflow_update']['work_units']
                if change == 'remove':
                    units.pop(0)
                    for unit in units:
                        unit['depends_on'] = [d for d in unit['depends_on'] if d != 'a']
                else:
                    units[0][change] = {'goal': 'Changed goal', 'skill_id': 'core.react-engineering',
                                       'acceptance': ['Different acceptance'], 'context_artifacts': []}[change]
                with self.assertRaisesRegex(RunnerError, 'preserve every prepared'):
                    self.submit_result(result)
                self.assertEqual(self.store.read(self.task), before)

    def test_pending_owner_must_still_be_subsequent(self):
        self.reach_composition()
        before = self.store.read(self.task)
        for owner in ('core.architecture-baseline-and-design', 'core.workflow-composition', 'core.nonexistent'):
            with self.subTest(owner=owner):
                result = self.refinement()
                result['workflow_update']['work_units'][-1]['skill_id'] = owner
                with self.assertRaisesRegex(ContractError, 'reachable pending skill'):
                    self.submit_result(result)
                self.assertEqual(self.store.read(self.task), before)

    def test_unsuccessful_prior_work_cannot_be_laundered_by_refinement(self):
        self.reach_composition()
        for status in ('failed', 'cancelled', 'timed_out'):
            with self.subTest(status=status):
                # Defensive persisted-state fixture: normal owner joins already prevent
                # advancing this far after failure. Exercise submit's recovery boundary too.
                def retain_failure(state):
                    receipt = state['execution']['work_records']['a']
                    receipt['status'] = receipt['result']['status'] = status
                state = self.store.update(self.task, self.response['revision'], 'fixture_failure', retain_failure)
                self.response['revision'] = state['revision']
                with self.assertRaisesRegex(RunnerError, 'unsuccessful receipts'):
                    self.submit_result(self.refinement())
                self.assertEqual(self.store.read(self.task), state)

    def test_real_failed_worker_blocks_its_owner_before_composition(self):
        self.run_unit('a', 'failed')
        before = self.store.read(self.task)
        with self.assertRaisesRegex(ContractError, 'successfully joined'):
            self.submit_result(self.skill_result())
        self.assertEqual(self.store.read(self.task), before)
