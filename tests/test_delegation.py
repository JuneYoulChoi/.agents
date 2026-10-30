"""Real Runner joins and bounded worker admission, without spawning providers."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from harness_delegation import prepare, record, require_join, usage_summary
from harness_runner import start, submit, work_event
from harness_state import StateStore
from harness_validator import ContractError


class DelegationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name)
        self.registry = ROOT / 'registry/active-skills.json'
        self.ctx = json.loads((ROOT / 'templates/workflow-intake.json.example').read_text())
        for unit in self.ctx['work_units']:
            unit['skill_id'] = 'core.architecture-baseline-and-design'
        f = self.target / 'intake.json'
        f.write_text(json.dumps(self.ctx))
        self.response = start(self.target, 'TASK-RECEIPTS', f, 'codex', 'test', ROOT,
                              self.registry, ROOT / 'registry/taxonomy.json', ROOT / 'registry/routing-gates.json')
        self.store = StateStore(self.target, harness_root=ROOT)
        self.state = self.store.read('TASK-RECEIPTS')

    def request(self, unit='a', mode='native'):
        return {'unit_id': unit, 'input_revision': 'source-001', 'mode': mode,
                'checks': dict.fromkeys(['authority', 'capability', 'revision', 'ownership', 'tools'], True),
                'evidence_ids': ['EVD-CHECK']}

    def result(self, packet, unit='a', usage=None):
        return {'unit_id': unit, 'input_revision': 'source-001', 'packet_hash': packet['packet_hash'],
                'status': 'completed', 'worker_stopped': True, 'acceptance_verified': True, 'artifact_ids': ['ART-1'],
                'evidence_ids': ['EVD-1'], 'usage': usage or {'status': 'unavailable'}}

    def test_dependencies_capacity_and_verified_join(self):
        a = prepare(self.state, self.request(), self.target, 0)
        b = prepare(self.state, self.request('b'), self.target, 0)
        with self.assertRaises(ContractError):
            prepare(self.state, self.request('join'), self.target, 1)
        with self.assertRaises(ContractError):
            require_join(self.state, 'core.architecture-baseline-and-design')
        record(self.state, self.result(a), 1)
        record(self.state, self.result(b, 'b'), 1)
        join = prepare(self.state, self.request('join'), self.target, 2)
        record(self.state, self.result(join, 'join'), 3)
        require_join(self.state, 'core.verify-and-handoff')

    def test_missing_checks_future_skill_and_no_delegation(self):
        for key in ['authority', 'capability', 'revision', 'ownership', 'tools']:
            req = self.request(); req['checks'][key] = False
            with self.assertRaises(ContractError):
                prepare(copy.deepcopy(self.state), req, self.target)
        self.state['route']['work_plan']['units'][0]['skill_id'] = 'core.verify-and-handoff'
        with self.assertRaises(ContractError):
            prepare(self.state, self.request(), self.target)
        self.state['route']['work_plan']['units'][0]['skill_id'] = 'core.architecture-baseline-and-design'
        self.state['intake']['delegation']['authorized'] = False
        with self.assertRaises(ContractError):
            prepare(self.state, self.request(), self.target)
        prepare(self.state, self.request(mode='serial'), self.target)
        with self.assertRaises(ContractError):
            prepare(self.state, self.request('b', mode='serial'), self.target)

    def test_late_completion_is_timeout_not_success(self):
        a = prepare(self.state, self.request(), self.target, 0)
        record(self.state, self.result(a), 301)
        self.assertEqual(self.state['execution']['work_records']['a']['status'], 'timed_out')
        with self.assertRaises(ContractError):
            require_join(self.state, 'core.architecture-baseline-and-design')
        with self.assertRaises(ContractError):
            record(self.state, self.result(a), 302)

    def test_stale_duplicate_and_unverified_results_rejected(self):
        a = prepare(self.state, self.request(), self.target, 0)
        for key, value in [('packet_hash', 'old'), ('input_revision', 'old'),
                           ('acceptance_verified', False), ('worker_stopped', False), ('artifact_ids', []), ('evidence_ids', [])]:
            result = self.result(a); result[key] = value
            with self.assertRaises(ContractError):
                record(self.state, result, 1)
        record(self.state, self.result(a), 1)
        with self.assertRaises(ContractError):
            record(self.state, self.result(a), 2)

    def test_context_is_focused_bounded_and_does_not_silently_truncate(self):
        self.state['intake']['conversation'] = 'history' * 100000
        a = prepare(self.state, self.request(), self.target, 0)
        self.assertNotIn('conversation', json.dumps(a))
        self.assertNotIn('work_plan', a['packet'])
        self.assertLess(len(json.dumps(a).encode()), 3000)
        self.state['intent']['constraints'] = ['required constraint' * 2000]
        with self.assertRaises(ContractError):
            prepare(self.state, self.request('b'), self.target, 0)

    def test_reported_usage_and_admission_budget(self):
        self.state['intake']['delegation']['worker_token_budget'] = 100
        a = prepare(self.state, self.request(), self.target, 0)
        with self.assertRaises(ContractError):
            prepare(self.state, self.request('b'), self.target, 1)
        record(self.state, self.result(a, usage={'status': 'reported', 'input_tokens': 70,
                   'output_tokens': 30, 'source': 'provider receipt'}), 2)
        self.assertEqual(usage_summary(self.state)['reported']['input_tokens'], 70)
        with self.assertRaises(ContractError):
            prepare(self.state, self.request('b'), self.target, 3)

    def test_unavailable_usage_is_not_zero(self):
        a = prepare(self.state, self.request(), self.target, 0)
        bad = self.result(a, usage={'status': 'unavailable', 'input_tokens': 0})
        with self.assertRaises(ContractError):
            record(self.state, bad, 1)
        record(self.state, self.result(a), 1)
        self.assertEqual(usage_summary(self.state)['unavailable_or_pending'], 1)
        self.assertEqual(usage_summary(self.state)['savings'], 'not_measured')

    def test_symlink_aliases_and_escapes_rejected(self):
        (self.target / 'src').mkdir()
        (self.target / 'actual').mkdir()
        (self.target / 'src/a').symlink_to(self.target / 'actual', target_is_directory=True)
        with self.assertRaises(ContractError):
            prepare(self.state, self.request(), self.target)

    def test_runner_rejects_missing_joins_without_advancing(self):
        item = self.response['next']
        result = {'schema_version': 1, 'skill_id': item['skill_id'], 'status': 'completed',
                  'artifact_ids': ['ART'], 'evidence_ids': ['EVD'], 'transition': {'next_stage': 'impact'},
                  'execution_resolution': {'adapter': 'codex', 'model': 'test', 'reasoning': 'unknown',
                  'native_reasoning': 'unknown', 'status': 'platform_default', 'evidence_ids': []}}
        f = self.target / 'skill-result.json'; f.write_text(json.dumps(result))
        with self.assertRaises(ContractError):
            submit(self.target, 'TASK-RECEIPTS', 1, f, ROOT, self.registry)
        self.assertEqual(self.store.read('TASK-RECEIPTS')['revision'], 1)

    def test_work_events_persist_and_stale_writes_fail(self):
        f = self.target / 'work.json'; f.write_text(json.dumps(self.request()))
        first = work_event(self.target, 'TASK-RECEIPTS', 1, f, 'prepare-work', ROOT, self.registry)
        with self.assertRaises(ContractError):
            work_event(self.target, 'TASK-RECEIPTS', 1, f, 'prepare-work', ROOT, self.registry)
        f.write_text(json.dumps(self.result(first)))
        final = work_event(self.target, 'TASK-RECEIPTS', 2, f, 'record-work', ROOT, self.registry)
        self.assertEqual(final['revision'], 3)
        self.assertEqual(self.store.read('TASK-RECEIPTS')['execution']['work_records']['a']['status'], 'completed')

    def test_terminal_status_requires_stopped_worker_and_blocks_skill_transition(self):
        packet = prepare(self.state, self.request(), self.target, 0)
        result = self.result(packet); result['worker_stopped'] = False
        with self.assertRaises(ContractError):
            record(self.state, result, 301)
        self.assertEqual(self.state['execution']['work_records']['a']['status'], 'running')
        with self.assertRaises(ContractError):
            prepare(self.state, self.request('b'), self.target, 302)

    def test_unreachable_bindings_are_rejected(self):
        from harness_delegation import validate_bindings
        plan = self.state['route']['work_plan']; queue = self.state['execution']['queue']
        with self.assertRaises(ContractError):
            validate_bindings(plan, queue, 1)
        plan['units'][0]['skill_id'] = 'core.nonexistent'
        with self.assertRaises(ContractError):
            validate_bindings(plan, queue)
        del plan['units'][0]['skill_id']
        validate_bindings(plan, queue, allow_unbound=True)
        with self.assertRaises(ContractError):
            validate_bindings(plan, queue)

    def test_g7_rejects_unbound_or_missing_results(self):
        for u in self.state['route']['work_plan']['units']:
            u.pop('skill_id')
        with self.assertRaises(ContractError):
            require_join(self.state, 'core.verify-and-handoff')

    def test_budget_configuration_and_unknown_coverage(self):
        from harness_workflow import validate_workflow_input, WorkflowError
        for value in (0, -1, True, '100'):
            self.ctx['delegation']['worker_token_budget'] = value
            with self.assertRaises(WorkflowError):
                validate_workflow_input(self.ctx)
        packet = prepare(self.state, self.request(), self.target, 0)
        record(self.state, self.result(packet), 1)
        self.assertIsNone(usage_summary(self.state)['total_worker_tokens'])
        self.assertEqual(usage_summary(self.state)['reported_units'], 0)

    def test_running_worker_blocks_waiting_transition_until_cleanup(self):
        f = self.target / 'work.json'; f.write_text(json.dumps(self.request()))
        response = work_event(self.target, 'TASK-RECEIPTS', 1, f, 'prepare-work', ROOT, self.registry)
        item = response['next']
        result = {'schema_version': 1, 'skill_id': item['skill_id'], 'status': 'waiting_user',
                  'artifact_ids': [], 'evidence_ids': [], 'transition': {'next_stage': 'clarification'},
                  'execution_resolution': {'adapter': 'codex', 'model': 'test', 'reasoning': 'unknown',
                  'native_reasoning': 'unknown', 'status': 'platform_default', 'evidence_ids': []}}
        f.write_text(json.dumps(result))
        with self.assertRaises(ContractError):
            submit(self.target, 'TASK-RECEIPTS', 2, f, ROOT, self.registry)
        self.assertEqual(self.store.read('TASK-RECEIPTS')['status'], 'active')
