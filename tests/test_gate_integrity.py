"""
모듈: 하네스 테스트 (tests)
컴포넌트: 게이트 무결성 회귀 테스트
역할: 게이트 완료·건너뛰기·재개·되돌림·라우팅 진입 규칙과 코드 문서화 검사 연결을 검증한다.
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
from harness_router import route, _load_manifest, RouterError
from harness_runner import resume, start, submit
from harness_state import StateStore
from harness_validator import ContractError

REGISTRY = ROOT / 'registry/active-skills.json'
TAXONOMY = ROOT / 'registry/taxonomy.json'
MANIFEST = ROOT / 'registry/routing-gates.json'
PATTERNS = 'core.architecture-and-design-patterns'
QUALITY = 'core.implementation-quality'
VERIFY = 'core.verify-and-handoff'


def base_intake():
    value = json.loads((ROOT / 'templates/workflow-intake.json.example').read_text())
    value.update(work_units=[], delegation={}, technologies=[], languages=['python'], fields=['implementation'],
                 project_state='brownfield', action='change', risk='low', depth='standard', work_type='standard',
                 change_characteristics=['authored_code'], enforcement_mode='hook')
    return value


def option(candidate_id, status='candidate'):
    return {'candidate_id': candidate_id, 'name': candidate_id, 'status': status, 'decision_scope': 'storage boundary',
            'fit': 'fits', 'recommendation_reason': 'evidence', 'benefits': ['isolation'], 'liabilities': ['mapping'],
            'quality_attribute_effects': [], 'affected_artifact_ids': [], 'migration_and_rollback': [],
            'verification_ids': []}


def pattern_review(decision_status):
    selected = decision_status == 'user_selected'
    return {'schema_version': 1, 'pattern_id': 'PATTERN-001', 'scopes': ['architecture'], 'drivers': ['QAS-1'],
            'open_issue_ids': [] if selected else ['ISSUE-1'],
            'candidates': [option('OPT-A', 'selected' if selected else 'candidate'), option('OPT-B')],
            'decision': {'status': decision_status, 'decision_scope': 'storage boundary',
                         'recommended_candidate_id': 'OPT-A', 'recommendation_reason': 'lower coupling',
                         'conditions_that_change_recommendation': ['team split'],
                         'selected_candidate_id': 'OPT-A' if selected else None,
                         'decision_evidence_ids': ['EVD-user-choice'] if selected else []}}


SAMPLE_SOURCE = (
    '"""\n모듈: 테스트 대상\n컴포넌트: 샘플\n역할: 문서화 규칙을 만족하는 예시 파일.\n"""\n\n\n'
    'def add(a, b):\n'
    '    """\n    역할: 두 수를 더한다.\n\n    입력:\n        a: 첫 번째 수\n        b: 두 번째 수\n'
    '    출력:\n        합계\n    """\n'
    '    return a + b\n'
)
DOCUMENTATION_CHECK = {'files': ['src/sample.py']}
MODULE_MAP = ('| 모듈 | 컴포넌트 | 책임 | 코드 경로 |\n| --- | --- | --- | --- |\n'
              '| 테스트 대상 | 샘플 | 예시 | `src` |\n')
QUALITY_RECORD = {'schema_version': 1, 'status': 'completed', 'authored_boundaries': ['src'],
    'activated_profiles': [{'id': 'core', 'depth': 'light', 'authored_boundaries': ['src'],
        'evidence_ids': ['EVD-q'], 'expected_outcomes': ['behavior preserved'], 'verification_ids': ['VER-q']}],
    'suppressed_profiles': [], 'findings': [], 'changes_or_recommendations': [], 'residual_risks': [], 'open_points': [],
    'readability_standard': 'PEP 8', 'documentation_check': DOCUMENTATION_CHECK}


class RunnerGateClosureTests(unittest.TestCase):
    def setUp(self):
        """
        역할: 임시 대상 루트에 증거 파일과 문서화 규칙을 만족하는 샘플 소스를 준비한다.
        """
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.target = Path(temp.name)
        (self.target / 'src').mkdir()
        (self.target / 'src/sample.py').write_text(SAMPLE_SOURCE)
        (self.target / 'docs/architecture').mkdir(parents=True)
        (self.target / 'docs/architecture/module-map.md').write_text(MODULE_MAP)
        self.intake = base_intake()
        self.intake['change_characteristics'] = ['authored_code', 'architecture_structure']
        self.proof = self.target / 'proof.txt'
        self.proof.write_text('Contract fixture evidence, not product validation.')

    def begin(self, **changes):
        intake = {**self.intake, **changes}
        path = self.target / 'intake.json'; path.write_text(json.dumps(intake))
        return start(self.target, 'TASK-INTEGRITY', path, 'claude', 'label', ROOT, REGISTRY, TAXONOMY, MANIFEST)

    def result(self, response, status='completed', **extra):
        skill = response['next']['skill_id']
        value = {'schema_version': 1, 'skill_id': skill, 'status': status,
                 'artifact_ids': ['ART-1'], 'evidence_ids': ['EVD-1'],
                 'transition': {'next_stage': response['next']['stage']}, 'error': None,
                 'execution_resolution': {'adapter': 'claude', 'model': 'fixture', 'reasoning': 'unknown',
                                          'native_reasoning': 'unknown', 'status': 'platform_default',
                                          'evidence_ids': []}}
        if skill == PATTERNS and status == 'completed':
            value['pattern_review'] = pattern_review('user_selected')
        if skill == QUALITY and status == 'completed':
            value['implementation_quality'] = QUALITY_RECORD
        if skill == VERIFY and status == 'completed':
            digest = hashlib.sha256(self.proof.read_bytes()).hexdigest()
            value['verification'] = [{'criterion': c, 'status': 'passed',
                                      'evidence': [{'path': 'proof.txt', 'sha256': digest}]}
                                     for c in self.intake['intent']['success_criteria']]
        value.update(extra)
        return value

    def send(self, response, result):
        path = self.target / 'result.json'; path.write_text(json.dumps(result))
        return submit(self.target, response['task_id'], response['revision'], path, ROOT, REGISTRY)

    def advance_to(self, response, skill):
        while response['next']['skill_id'] != skill:
            response = self.send(response, self.result(response))
        return response

    def assert_rejected(self, response, result):
        with self.assertRaises(ContractError):
            self.send(response, result)
        self.assertEqual(StateStore(self.target, harness_root=ROOT).read(response['task_id'])['revision'],
                         response['revision'])

    def test_gate_cannot_close_without_outputs_or_with_a_contradicting_transition(self):
        response = self.begin()
        self.assert_rejected(response, self.result(response, artifact_ids=[]))
        self.assert_rejected(response, self.result(response, evidence_ids=[]))
        for stage in ('clarification', 'backward_feedback', 'blocked', 'failed'):
            self.assert_rejected(response, self.result(response, transition={'next_stage': stage}))
        degraded = self.result(response)
        degraded['execution_resolution'].update(reasoning='low', status='degraded')
        self.assert_rejected(response, degraded)

    def test_activated_baseline_and_impact_cannot_be_skipped_for_a_mutation(self):
        response = self.begin()
        self.assert_rejected(response, self.result(response, 'not_applicable', reason='no docs'))
        response = self.advance_to(response, 'core.workflow-composition')
        self.assert_rejected(response, self.result(response, 'not_applicable'))  # no reason
        self.assert_rejected(response, self.result(response, 'not_applicable', reason='single slice', evidence_ids=[]))
        self.assertEqual(self.send(response, self.result(response, 'not_applicable', reason='single slice'))['status'],
                         'active')

    def test_typed_records_bind_pattern_and_quality_completion(self):
        response = self.advance_to(self.begin(), PATTERNS)
        missing = self.result(response); del missing['pattern_review']
        self.assert_rejected(response, missing)
        self.assert_rejected(response, self.result(response, pattern_review=pattern_review('user_decision_required')))
        response = self.advance_to(self.send(response, self.result(response)), QUALITY)
        missing = self.result(response); del missing['implementation_quality']
        self.assert_rejected(response, missing)
        self.assert_rejected(response, self.result(
            response, implementation_quality={**QUALITY_RECORD, 'status': 'not_applicable'}))

    def test_quality_completion_requires_standard_and_passing_documentation(self):
        """
        역할: 구현 품질 완료가 가독성 기준과 Runner의 문서화 재검사 통과를 요구하는지 확인한다.
        """
        response = self.advance_to(self.begin(), QUALITY)
        for key in ('readability_standard', 'documentation_check'):
            record = dict(QUALITY_RECORD); del record[key]
            self.assert_rejected(response, self.result(response, implementation_quality=record))
        (self.target / 'src/undocumented.py').write_text('def add(a, b):\n    return a + b\n')
        for files in (['src/undocumented.py'], ['../outside.py'], ['src/missing.py']):
            record = {**QUALITY_RECORD, 'documentation_check': {'files': files}}
            self.assert_rejected(response, self.result(response, implementation_quality=record))
        (self.target / 'src/sample.py').write_text(SAMPLE_SOURCE.replace('컴포넌트: 샘플', '컴포넌트: 없는 이름'))
        self.assert_rejected(response, self.result(response))  # 헤더가 모듈 맵에 없는 컴포넌트를 가리킴
        (self.target / 'src/sample.py').write_text(SAMPLE_SOURCE)
        (self.target / 'docs/architecture/module-map.md').unlink()
        self.assert_rejected(response, self.result(response))  # 모듈 맵 문서가 없음
        (self.target / 'docs/architecture/module-map.md').write_text(MODULE_MAP)
        self.assertEqual(self.send(response, self.result(response))['next']['skill_id'], VERIFY)

    def test_user_decision_resumes_the_same_skill_without_replaying_earlier_gates(self):
        response = self.advance_to(self.begin(), PATTERNS)
        done = response['queue_progress']['completed']
        waiting = self.send(response, self.result(response, 'waiting_user', transition={'next_stage': 'clarification'},
                                                  pattern_review=pattern_review('user_decision_required'),
                                                  artifact_ids=[], evidence_ids=[]))
        self.assertEqual(waiting['status'], 'waiting_user')
        request = self.target / 'resume.json'
        request.write_text(json.dumps({'answer': 'OPT-A'}))
        with self.assertRaises(ContractError):
            resume(self.target, 'TASK-INTEGRITY', waiting['revision'], request, ROOT, REGISTRY)
        request.write_text(json.dumps({'answer': 'OPT-A', 'decision_evidence_ids': ['EVD-user-choice']}))
        resumed = resume(self.target, 'TASK-INTEGRITY', waiting['revision'], request, ROOT, REGISTRY)
        self.assertEqual((resumed['status'], resumed['next']['skill_id'], resumed['queue_progress']['completed']),
                         ('active', PATTERNS, done))
        self.assertEqual(self.send(resumed, self.result(resumed))['status'], 'active')

    def test_routing_block_is_not_resumable(self):
        blocked = self.begin(risk='high')  # no approval evidence
        self.assertEqual(blocked['status'], 'blocked')
        request = self.target / 'resume.json'
        request.write_text(json.dumps({'answer': 'go', 'decision_evidence_ids': ['EVD-x']}))
        with self.assertRaises(ContractError):
            resume(self.target, 'TASK-INTEGRITY', blocked['revision'], request, ROOT, REGISTRY)

    def test_failed_verification_reopens_only_the_responsible_gate_with_a_counted_budget(self):
        response = self.advance_to(self.begin(), VERIFY)
        queue = StateStore(self.target, harness_root=ROOT).read('TASK-INTEGRITY')['execution']['queue']
        failure = dict(status='failed', error='regression failed', transition={'next_stage': 'backward_feedback'},
                       feedback={'kind': 'implementation_or_assembly_defect', 'attempt': 99})
        for attempt in (1, 2):
            reopened = self.send(response, self.result(response, **failure))
            self.assertEqual((reopened['status'], reopened['next']['skill_id']), ('active', QUALITY))
            self.assertEqual(reopened['queue_progress']['completed'], queue.index(QUALITY))
            state = StateStore(self.target, harness_root=ROOT).read('TASK-INTEGRITY')
            self.assertEqual(state['execution']['feedback_attempts'], {'G6': attempt})
            response = self.advance_to(reopened, VERIFY)
        escalated = self.send(response, self.result(response, **failure))
        self.assertEqual(escalated['status'], 'waiting_user')

    def test_unrouted_feedback_escalates_and_plain_failure_stays_failed(self):
        response = self.advance_to(self.begin(), VERIFY)
        unknown = self.result(response, status='failed', error='x', feedback={'kind': 'not-a-signal'})
        self.assertEqual(self.send(response, unknown)['status'], 'waiting_user')

    def test_deep_route_requires_independent_verification_evidence(self):
        response = self.advance_to(self.begin(depth='deep'), VERIFY)
        self.assertTrue(response['next']['execution_profile']['independent_context'])
        self.assert_rejected(response, self.result(response))
        done = self.send(response, self.result(response, independent_verification_evidence_ids=['EVD-fresh-context']))
        self.assertEqual(done['status'], 'complete')


class RoutingEntryTests(unittest.TestCase):
    def setUp(self):
        self.manifest = _load_manifest(MANIFEST)

    def route(self, **changes):
        return route({**base_intake(), **changes}, self.manifest)

    def gate(self, result, gate_id):
        return next(g for g in result['gate_results'] if g['gate_id'] == gate_id)

    def test_contradictory_scope_and_inapplicable_state_do_not_reach_code_work(self):
        with self.assertRaises(RouterError):
            self.route(scope='general_information')
        blocked = self.route(project_state='not_applicable')
        self.assertEqual(blocked['status'], 'blocked')
        self.assertTrue(self.gate(blocked, 'G2')['blocked'])
        self.assertEqual(self.route(project_state='not_applicable', action='investigate')['status'], 'active')

    def test_unselected_technology_candidate_activates_selection(self):
        result = self.route(technologies=[{'name': 'gRPC', 'status': 'candidate', 'material': True}])
        self.assertIn('core.technology-selection-and-integration', result['activated_skills'])
        self.assertNotIn('core.grpc-engineering', result['activated_skills'])

    def test_high_risk_and_harness_mutation_require_recorded_approval(self):
        for changes, reason in (({'risk': 'high'}, 'high_risk_approval_required'),
                                ({'target': 'harness'}, 'harness_change_approval_required')):
            blocked = self.route(**changes)
            self.assertEqual(blocked['status'], 'blocked')
            self.assertIn({'reason': reason}, self.gate(blocked, 'G0')['blocked'])
            self.assertEqual(self.route(**changes, approval_evidence_ids=['EVD-approval'])['status'], 'active')
        self.assertEqual(self.route(risk='high', action='review')['status'], 'active')

    def test_architecture_planning_and_greenfield_design_enter_pattern_review(self):
        for changes in ({'action': 'plan', 'fields': ['architecture']}, {'action': 'define', 'fields': ['architecture']},
                        {'action': 'design', 'project_state': 'greenfield'}):
            self.assertIn(PATTERNS, self.route(**changes)['activated_skills'], changes)
        self.assertNotIn(PATTERNS, self.route()['activated_skills'])
        self.assertNotIn(PATTERNS, self.route(action='implement', fields=['architecture', 'implementation'])['activated_skills'])

    def test_security_and_performance_fields_select_their_quality_profiles(self):
        branches = self.gate(self.route(fields=['implementation', 'security', 'performance']), 'G6')['activated_branches']
        self.assertIn('implementation_quality:security', branches)
        self.assertIn('implementation_quality:performance', branches)

    def test_compact_local_change_skips_only_composition(self):
        compact = self.route(depth='light', architecture_status='confirmed')
        self.assertEqual(compact['activated_skills'], [
            'core.intake-and-route', 'core.architecture-baseline-and-design', 'core.brownfield-impact-analysis',
            'core.language-engineering', QUALITY, VERIFY])
        self.assertIn({'skill_id': 'core.workflow-composition', 'reason': 'compact_local_change_single_slice'},
                      compact['suppressed_skills'])
        for changes in ({'risk': 'medium'}, {'depth': 'standard'}, {'architecture_status': 'draft'},
                        {'change_characteristics': ['authored_code', 'api_data_contract']},
                        {'fields': ['implementation', 'security']}, {'project_state': 'greenfield'}):
            full = self.route(**{'depth': 'light', 'architecture_status': 'confirmed', **changes})
            self.assertIn('core.workflow-composition', full['activated_skills'], changes)

    def test_read_only_investigation_does_not_run_the_authoring_quality_gate(self):
        result = self.route(action='investigate')
        self.assertNotIn(QUALITY, result['activated_skills'])
        self.assertIn('core.language-engineering', result['activated_skills'])


class ClaudeAdapterAssetTests(unittest.TestCase):
    def test_every_unit_role_has_a_bounded_agent_and_a_gate_binding(self):
        from harness_delegation import GATE_ROLE_UNITS, ROLE_GUIDANCE
        from harness_workflow import ROLES
        self.assertEqual(set(ROLE_GUIDANCE), ROLES)
        gate_roles = set(json.loads(MANIFEST.read_text())['execution_policy']['gate_roles'].values())
        self.assertEqual(set(GATE_ROLE_UNITS), gate_roles - {'guard', 'classifier'})
        self.assertEqual({r for roles in GATE_ROLE_UNITS.values() for r in roles}, ROLES)
        for role in ROLES:
            text = (ROOT / f'adapters/claude/agents/harness-{role}.md').read_text()
            self.assertIn(f'name: harness-{role}', text)
            tools = next(line for line in text.splitlines() if line.startswith('tools:'))
            self.assertEqual('Edit' in tools, role in {'implementer', 'documenter'}, role)



if __name__ == '__main__':
    unittest.main()
