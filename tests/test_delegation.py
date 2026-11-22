"""
모듈: 하네스 테스트 (tests)
컴포넌트: 기존 회귀 테스트
역할: 실제 Runner로 작업 단위의 준비·합류·워커 수용 한도를 검증한다(공급자 실행 없음).
"""
import copy
import hashlib
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
from test_runtime import fixture_hook_guard


class DelegationTests(unittest.TestCase):
    def test_jydlc_native_workers_bind_the_independent_revision(self):
        """역할: 실제 작업자 영수증과 서로 다른 컨텍스트의 구현 리비전 연결을 확인한다."""
        produce = 'core.implementation-quality'
        verify = 'core.verify-and-handoff'
        execution = self.state['execution']
        execution['queue'] = [produce, verify]
        execution['skill_gates'] = {produce: 'G6', verify: 'G7'}
        plan = self.state['route']['work_plan']
        seed = plan['units'][0]
        producer = {**seed, 'role': 'implementer', 'skill_id': produce, 'mutation': 'workspace',
                    'write_paths': ['src'], 'depends_on': []}
        verifier = {**seed, 'id': 'b', 'role': 'verifier', 'skill_id': verify, 'mutation': 'none',
                    'write_paths': [], 'depends_on': ['a'], 'input_revision': 'after_implementation',
                    'acceptance': self.state['intent']['success_criteria']}
        plan.update(units=[producer, verifier], required_native_roles=['implementer', 'verifier'], max_workers=1)

        def evidence_for(packet, unit, worker_id, output=None):
            """
            역할: 호스트가 반환한 형식의 모의 작업자 결과와 영수증을 임시 파일로 작성한다.
            입력: packet은 준비 결과, unit과 worker_id는 역할 식별자, output은 통합 리비전이다.
            출력: 기록 테스트용 종료 결과
            """
            result = self.result(packet, unit)
            result['input_revision'] = packet['packet']['unit']['input_revision']
            receipt = {key: result[key] for key in ('unit_id', 'packet_hash', 'input_revision', 'status')}
            receipt.update(adapter='codex', task_id=self.state['task_id'], worker_id=worker_id,
                           host_completion='synthetic host return for schema test')
            native = {'worker_id': worker_id}
            if output is not None:
                native['output_revision'] = receipt['output_revision'] = output
            path = self.target / f'{unit}.receipt.json'
            path.write_text(json.dumps(receipt))
            native['receipt'] = {'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            result['native_execution'] = native
            return result

        with self.assertRaisesRegex(ContractError, 'native worker'):
            prepare(self.state, self.request(mode='serial'), self.target, 0)
        a = prepare(self.state, self.request(), self.target, 0)
        with self.assertRaisesRegex(ContractError, 'native execution receipt'):
            self.record(self.result(a), 1)
        self.record(evidence_for(a, 'a', 'worker-A', 'joined-2'), 1)
        require_join(self.state, produce, self.target)
        execution['cursor'] = 1
        with self.assertRaisesRegex(ContractError, 'input revision mismatch'):
            prepare(self.state, self.request('b'), self.target, 2)
        b = prepare(self.state, {**self.request('b'), 'input_revision': 'joined-2'}, self.target, 2)
        with self.assertRaisesRegex(ContractError, 'different host worker'):
            self.record(evidence_for(b, 'b', 'worker-A'), 3)
        self.record(evidence_for(b, 'b', 'worker-B'), 3)
        require_join(self.state, verify, self.target)

    def test_lenses_reach_worker_without_changing_acceptance_or_authority(self):
        packets = []
        for lens in ('meticulous', 'minimal_sufficient'):
            state = copy.deepcopy(self.state)
            unit = state['route']['work_plan']['units'][0]
            unit['reasoning_lens'] = lens
            packet = prepare(state, self.request(), self.target, 0)['packet']
            self.assertEqual(packet['unit']['acceptance'], unit['acceptance'])
            self.assertEqual(packet['unit']['mutation'], 'none')
            self.assertEqual(packet['unit']['allowed_tools'], unit['allowed_tools'])
            self.assertTrue(packet['skill_context']['lens_guidance'])
            packets.append(packet)
        self.assertNotEqual(packets[0]['skill_context']['lens_guidance'],
                            packets[1]['skill_context']['lens_guidance'])
        self.assertEqual(packets[0]['skill_context']['execution_profile'],
                         packets[1]['skill_context']['execution_profile'])

    def test_legacy_units_keep_role_without_invented_lens(self):
        packet = prepare(self.state, self.request(), self.target, 0)['packet']
        self.assertIsNone(packet['skill_context']['lens_guidance'])
        self.assertNotIn('reasoning_lens', packet['unit'])

    def setUp(self):
        """역할: 실제 Runner의 위임 테스트에 필요한 임시 작업과 가드 관찰을 준비한다."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name)
        self.registry = ROOT / 'registry/active-skills.json'
        self.ctx = json.loads((ROOT / 'templates/workflow-intake.json.example').read_text())
        context_file = self.target / 'context.md'
        context_file.write_text('Synthetic baseline: bounded review; no product or external authority. Input snapshot and acceptance are fixture-only.')
        self.context_file = {'path': 'context.md', 'sha256': hashlib.sha256(context_file.read_bytes()).hexdigest()}
        self.proof = self.target / 'proof.md'
        self.proof.write_text('Fixture evidence for contract tests; does not claim product correctness.')
        for unit in self.ctx['work_units']:
            unit['context_artifacts'] = [self.context_file]
            unit['skill_id'] = 'core.architecture-baseline-and-design'
        f = self.target / 'intake.json'
        f.write_text(json.dumps({**self.ctx, 'hook_guard': fixture_hook_guard(self.target, 'TASK-RECEIPTS')}))
        self.response = start(self.target, 'TASK-RECEIPTS', f, 'codex', 'test', ROOT,
                              self.registry, ROOT / 'registry/taxonomy.json', ROOT / 'registry/routing-gates.json')
        self.store = StateStore(self.target, harness_root=ROOT)
        self.state = self.store.read('TASK-RECEIPTS')

    def request(self, unit='a', mode='native'):
        return {'unit_id': unit, 'input_revision': 'source-001', 'mode': mode, 'native_worker_capacity': 3,
                'checks': dict.fromkeys(['authority', 'capability', 'revision', 'ownership', 'tools'], True),
                'evidence_ids': ['EVD-CHECK']}

    def record(self, result, now):
        return record(self.state, result, now, target=self.target)

    def result(self, packet, unit='a', usage=None):
        context = packet['packet']['skill_context']
        return {'unit_id': unit, 'input_revision': 'source-001', 'packet_hash': packet['packet_hash'],
                'status': 'completed', 'worker_stopped': True, 'acceptance_verified': True, 'artifact_ids': ['ART-1'],
                'evidence_ids': ['EVD-1'], 'usage': usage or {'status': 'unavailable'},
                'verification': [{'criterion': c, 'status': 'passed', 'evidence': [
                    {'path': 'proof.md', 'sha256': hashlib.sha256(self.proof.read_bytes()).hexdigest()}]}
                    for c in packet['packet']['unit']['acceptance']],
                'instruction_evidence': {'instruction_hash': context['sha256'],
                    'reference_hashes': [r['sha256'] for r in context['references']]},
                'execution_resolution': {'adapter': 'codex', 'model': 'fixture', 'reasoning': 'unknown',
                    'native_reasoning': 'unknown', 'status': 'platform_default', 'evidence_ids': ['EVD-fixture']}}

    def test_dependencies_capacity_and_verified_join(self):
        a = prepare(self.state, self.request(), self.target, 0)
        b = prepare(self.state, self.request('b'), self.target, 0)
        with self.assertRaises(ContractError):
            prepare(self.state, self.request('join'), self.target, 1)
        with self.assertRaises(ContractError):
            require_join(self.state, 'core.architecture-baseline-and-design')
        self.record(self.result(a), 1)
        self.record(self.result(b, 'b'), 1)
        join = prepare(self.state, self.request('join'), self.target, 2)
        self.record(self.result(join, 'join'), 3)
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
        self.record(self.result(a), 301)
        self.assertEqual(self.state['execution']['work_records']['a']['status'], 'timed_out')
        with self.assertRaises(ContractError):
            require_join(self.state, 'core.architecture-baseline-and-design')
        with self.assertRaises(ContractError):
            self.record(self.result(a), 302)

    def test_stale_duplicate_and_unverified_results_rejected(self):
        a = prepare(self.state, self.request(), self.target, 0)
        for key, value in [('packet_hash', 'old'), ('input_revision', 'old'),
                           ('acceptance_verified', False), ('worker_stopped', False), ('artifact_ids', []), ('evidence_ids', [])]:
            result = self.result(a); result[key] = value
            with self.assertRaises(ContractError):
                self.record(result, 1)
        self.record(self.result(a), 1)
        with self.assertRaises(ContractError):
            self.record(self.result(a), 2)

    def test_context_is_focused_bounded_and_does_not_silently_truncate(self):
        self.state['intake']['conversation'] = 'history' * 100000
        a = prepare(self.state, self.request(), self.target, 0)
        self.assertNotIn('conversation', json.dumps(a))
        self.assertNotIn('work_plan', a['packet'])
        self.assertLess(len(json.dumps(a).encode()), 16384)
        self.state['intent']['constraints'] = ['required constraint' * 2000]
        with self.assertRaises(ContractError):
            prepare(self.state, self.request('b'), self.target, 0)

    def test_reported_usage_and_admission_budget(self):
        self.state['intake']['delegation']['worker_token_budget'] = 100
        a = prepare(self.state, self.request(), self.target, 0)
        with self.assertRaises(ContractError):
            prepare(self.state, self.request('b'), self.target, 1)
        self.record(self.result(a, usage={'status': 'reported', 'input_tokens': 70,
                   'output_tokens': 30, 'source': 'provider receipt'}), 2)
        self.assertEqual(usage_summary(self.state)['reported']['input_tokens'], 70)
        with self.assertRaises(ContractError):
            prepare(self.state, self.request('b'), self.target, 3)

    def test_unavailable_usage_is_not_zero(self):
        a = prepare(self.state, self.request(), self.target, 0)
        bad = self.result(a, usage={'status': 'unavailable', 'input_tokens': 0})
        with self.assertRaises(ContractError):
            self.record(bad, 1)
        self.record(self.result(a), 1)
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
            self.record(result, 301)
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
        self.record(self.result(packet), 1)
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

    def test_packet_contains_current_skill_body_profile_and_persona(self):
        """
        역할: 워커 패킷이 현재 스킬 본문·적용 깊이·실행 프로파일·역할 지침과, 스킬의 필수 참조 문서만 담는지 확인한다.
        """
        packet = prepare(self.state, self.request(), self.target, 0)['packet']
        context = packet['skill_context']
        self.assertEqual(context['instructions'], (ROOT / context['entry']).read_text())
        self.assertEqual(context['application_depth'], self.response['next']['application_depth'])
        self.assertEqual(context['execution_profile'], self.response['next']['execution_profile'])
        self.assertIn('hypotheses', context['role_guidance'])
        self.assertEqual([Path(r['path']).name for r in context['references']], ['doc-code-sync.md'])

    def test_only_selected_current_skill_references_are_allowed(self):
        unit = self.state['route']['work_plan']['units'][0]
        refs = list((ROOT / 'skills/architecture-baseline-and-design/references').rglob('*.md'))
        self.assertTrue(refs)
        unit['skill_references'] = [str(refs[0].relative_to(ROOT))]
        packet = prepare(copy.deepcopy(self.state), self.request(), self.target, 0)['packet']
        self.assertEqual(len(packet['skill_context']['references']), 1)
        unit['skill_references'] = ['skills/react-engineering/SKILL.md']
        with self.assertRaisesRegex(ContractError, 'current skill'):
            prepare(self.state, self.request(), self.target, 0)

    def test_unapproved_worker_skill_is_not_loaded(self):
        registry = json.loads(self.registry.read_text())
        for skill in registry['skills']:
            if skill['id'] == 'core.architecture-baseline-and-design':
                skill['trust'] = 'unverified'
        path = self.target / 'registry.json'; path.write_text(json.dumps(registry))
        with self.assertRaises(ContractError):
            prepare(self.state, self.request(), self.target, 0, registry_path=path)
        self.assertFalse(self.state['execution']['work_records'])

    def test_current_host_capacity_is_required_and_can_shrink(self):
        for value in (None, True, -1, '3', 0):
            req = self.request(); req['native_worker_capacity'] = value
            with self.subTest(value=value), self.assertRaises(ContractError):
                prepare(copy.deepcopy(self.state), req, self.target, 0)
        prepare(self.state, self.request(), self.target, 0)
        req = self.request('b'); req['native_worker_capacity'] = 1
        with self.assertRaisesRegex(ContractError, 'capacity'):
            prepare(self.state, req, self.target, 1)

    def test_worker_counters_never_imply_total_task_savings(self):
        packet = prepare(self.state, self.request(), self.target, 0)
        self.record(self.result(packet, usage={'status': 'reported', 'input_tokens': 20,
               'output_tokens': 10, 'source': 'fixture provider receipt'}), 1)
        summary = usage_summary(self.state)
        self.assertEqual(summary['total_worker_tokens'], 30)
        self.assertIsNone(summary['total_task_tokens'])
        self.assertEqual(summary['parent_usage'], 'unavailable')
        self.assertEqual(summary['savings'], 'not_measured')

    def test_missing_or_changed_context_blocks_preparation(self):
        unit = self.state['route']['work_plan']['units'][0]
        unit.pop('context_artifacts')
        with self.assertRaisesRegex(ContractError, 'evidence files'):
            prepare(self.state, self.request(), self.target, 0)
        unit['context_artifacts'] = [self.context_file]
        (self.target/'context.md').write_text('changed baseline')
        with self.assertRaisesRegex(ContractError, 'hash mismatch'):
            prepare(self.state, self.request(), self.target, 0)

    def test_worker_completion_requires_instruction_resolution_and_acceptance_evidence(self):
        packet = prepare(self.state, self.request(), self.target, 0)
        for key in ('instruction_evidence', 'execution_resolution', 'verification'):
            result = self.result(packet); result.pop(key)
            with self.subTest(key=key), self.assertRaises(ContractError): self.record(result, 1)
        self.record(self.result(packet), 1)

    def test_unconditional_references_are_included_even_when_omitted(self):
        state = copy.deepcopy(self.state)
        skill = 'core.react-engineering'
        state['execution']['cursor'] = state['execution']['queue'].index(skill)
        state['route']['work_plan']['units'][0]['skill_id'] = skill
        packet = prepare(state, self.request(), self.target, 0)['packet']
        self.assertEqual(len(packet['skill_context']['references']), 1)
        self.assertTrue(packet['skill_context']['references'][0]['path'].endswith('references/engineering-practices.md'))
