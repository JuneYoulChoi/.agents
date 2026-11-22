"""Calendar scenario regressions for minimal clarification and serial defaults.

These are annotated structured inputs, not a natural-language classifier test.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from harness_router import RouterError, _load_manifest, route
from harness_runner import start
from harness_validator import ContractError, validate_intake


class IntakeDecisionTests(unittest.TestCase):
    def calendar(self):
        context = json.loads((ROOT / 'templates/workflow-intake.json.example').read_text())
        context.update(request_id='REQ-CALENDAR', project_state='greenfield', action='plan',
                       architecture_status='draft', fields=['requirements', 'frontend', 'testing'],
                       languages=[], language_scope='none', change_characteristics=['documentation_only'],
                       technologies=[], work_type='feature', work_units=[], delegation={})
        context['intent']['goal'] = '첫 진입 인사말과 캘린더 할 일 조회/추가/수정/삭제'
        context['open_decisions'] = ['자체 캘린더 또는 외부 연동', '개인/다중 사용자와 저장 범위',
                                     '종일/시간 지정과 시간대', '인사말 표시 주기']
        return context

    def test_recorded_calendar_decisions_wait_without_legacy_ambiguity_flag(self):
        context = self.calendar()
        self.assertNotIn('material_ambiguity', context)
        result = route(context, _load_manifest(ROOT / 'registry/routing-gates.json'))
        self.assertEqual(result['status'], 'waiting_user')
        g1 = next(g for g in result['gate_results'] if g['gate_id'] == 'G1')
        self.assertEqual(g1['blocked'][0]['open_decisions'], context['open_decisions'])
        self.assertEqual(result['work_plan']['mode'], 'single')
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory); intake = target / 'intake.json'
            intake.write_text(json.dumps(context))
            response = start(target, 'TASK-CALENDAR-OPEN', intake, 'codex', 'test', ROOT,
                             ROOT / 'registry/active-skills.json', ROOT / 'registry/taxonomy.json',
                             ROOT / 'registry/routing-gates.json')
            self.assertEqual(response['status'], 'waiting_user')
            self.assertIsNone(response['next'])

    def test_false_legacy_flag_cannot_override_recorded_open_decisions(self):
        context = self.calendar(); context['material_ambiguity'] = False
        self.assertEqual(route(context, _load_manifest(ROOT / 'registry/routing-gates.json'))['status'],
                         'waiting_user')

    def test_scoped_calendar_is_active_single_without_speculative_skills(self):
        context = self.calendar(); context['open_decisions'] = []
        context['architecture_status'] = 'confirmed'
        context['intent']['constraints'] = [
            '테스트용 확정 범위: 개인용 자체 달력, 같은 브라우저에 종일 날짜 저장, 매 진입 인사말',
            '외부 연동/로그인/서버는 제외. 실제 사용자 승인으로 간주하지 않음']
        result = route(context, _load_manifest(ROOT / 'registry/routing-gates.json'))
        self.assertEqual(result['status'], 'active')
        self.assertEqual(result['work_plan']['mode'], 'single')
        self.assertEqual(result['work_plan']['max_workers'], 1)
        self.assertIn('core.greenfield-planning', result['activated_skills'])
        for skill in ['core.react-engineering', 'core.nodejs-engineering', 'core.language-engineering']:
            self.assertNotIn(skill, result['activated_skills'])

    def test_local_greeting_change_does_not_require_full_product_questionnaire(self):
        context = self.calendar()
        context.update(project_state='brownfield', action='change', architecture_status='confirmed',
                       open_decisions=[], work_type='bugfix')
        context['intent']['goal'] = '기존 인사말 문구만 안녕하세요에서 반갑습니다로 변경'
        result = route(context, _load_manifest(ROOT / 'registry/routing-gates.json'))
        self.assertEqual(result['status'], 'active')
        self.assertEqual(result['work_plan']['mode'], 'single')
        self.assertIn('core.brownfield-impact-analysis', result['activated_skills'])

    def test_malformed_decisions_rejected_by_both_input_paths(self):
        for value in ['calendar?', None, [False], ['   ']]:
            context = self.calendar(); context['open_decisions'] = value
            with self.subTest(value=value):
                with self.assertRaises(RouterError):
                    route(context, _load_manifest(ROOT / 'registry/routing-gates.json'))
                with self.assertRaises(ContractError):
                    validate_intake(context, ROOT / 'registry/taxonomy.json')

    def test_legacy_inputs_without_open_decisions_remain_supported(self):
        context = self.calendar(); del context['open_decisions']
        context['material_ambiguity'] = True
        self.assertEqual(route(context, _load_manifest(ROOT / 'registry/routing-gates.json'))['status'],
                         'waiting_user')

    def test_preview_and_intake_reject_the_same_invalid_fields(self):
        """역할: 잘못된 분류에 미리보기와 실행 검증이 같은 진단을 반환하는지 확인한다."""
        manifest = _load_manifest(ROOT / 'registry/routing-gates.json')
        taxonomy = ROOT / 'registry/taxonomy.json'
        for fields in (['backend', 'reliability'], ['frontend', 'frontend'], [''], [False]):
            with self.subTest(fields=fields):
                context = {**self.calendar(), 'fields': fields}
                with self.assertRaises(ContractError) as intake_error:
                    validate_intake(context, taxonomy)
                with self.assertRaises(RouterError) as route_error:
                    route(context, manifest)
                self.assertEqual(str(route_error.exception), str(intake_error.exception))

    def test_evidenced_control_routes_g4_checks_and_only_evidenced_g6_profiles(self):
        """역할: 제어·데드라인·신뢰성 근거가 필요한 시험 능력과 실시간 품질로 이어지는지 확인한다."""
        manifest = _load_manifest(ROOT / 'registry/routing-gates.json')
        context = {
            **self.calendar(), 'fields': ['industrial_integration', 'testing'],
            'project_state': 'brownfield', 'architecture_status': 'confirmed', 'action': 'change',
            'languages': ['cpp'], 'language_scope': 'authored_in_scope',
            'change_characteristics': ['authored_code'], 'open_decisions': [],
            'evidence_ids': ['EVD-control-qas'],
        }
        kind = {'evidence_ids': ['EVD-control-qas'], 'timing': 'hard', 'control': 'actuation',
                'environment': 'hardware_in_the_loop', 'reliability': ['recoverability']}
        ordinary = route(context, manifest)
        evidenced = route({**context, 'quality_context': kind}, manifest)
        observation = route({**context, 'fields': ['operations', 'testing']}, manifest)
        plan = evidenced['verification_plan']
        self.assertEqual(ordinary['verification_plan']['required_checks'], ['behavior_test'])
        self.assertEqual(observation['verification_plan']['required_checks'], ['behavior_test'])
        self.assertEqual(plan['required_checks'],
                         ['behavior_test', 'reliability_scenario', 'deadline_measurement', 'control_verification'])
        self.assertEqual(plan['capabilities_by_check']['deadline_measurement'], 'target_timing_measurement')
        self.assertEqual(plan['environment'], 'hardware_in_the_loop')
        self.assertFalse(plan['execution_authorized'])
        legacy_gate = next(gate for gate in ordinary['gate_results'] if gate['gate_id'] == 'G6')
        active_gate = next(gate for gate in evidenced['gate_results'] if gate['gate_id'] == 'G6')
        self.assertEqual(legacy_gate['activated_branches'], ['implementation_quality:core'])
        self.assertEqual(active_gate['activated_branches'],
                         ['implementation_quality:core', 'implementation_quality:realtime_embedded'])
        with self.assertRaisesRegex(RouterError, 'registered intake evidence'):
            route({**context, 'quality_context': {**kind, 'evidence_ids': ['EVD-unknown']}}, manifest)
