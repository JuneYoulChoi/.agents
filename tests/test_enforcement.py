"""
모듈: 하네스 테스트 (tests)
컴포넌트: 강제 수준 테스트
역할: 큰 변경에만 임시 강제(훅)를 요청하고 일반 변경은 권고 모드로 진행하는 라우팅,
      작업에 묶여 자동으로 풀리는 편집 가드 훅, 한 번에 끝내는 마무리 검사를 검증한다.
"""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'adapters/claude/hooks'))
from harness_finish import finish, main as finish_main
from harness_guard import decide
from harness_router import route, _load_manifest
from harness_runner import start
from harness_state import StateError, StateStore

REGISTRY = ROOT / 'registry/active-skills.json'
TAXONOMY = ROOT / 'registry/taxonomy.json'
MANIFEST = ROOT / 'registry/routing-gates.json'
MAP_HEADER = '| 모듈 | 컴포넌트 | 책임 | 코드 경로 |\n| --- | --- | --- | --- |\n'
PAYMENT_ROW = '| 주문 | 결제 | 결제를 검증한다 | `src/payment` |\n'
SOURCE = ('"""\n모듈: 주문\n컴포넌트: 결제\n역할: 결제를 검증한다.\n"""\n\n\n'
          'def check(amount):\n    """\n    역할: 금액을 확인한다.\n\n    입력:\n        amount: 금액\n'
          '    출력:\n        유효 여부\n    """\n    return amount > 0\n')


def intake(**changes) -> dict:
    """
    역할: 수동 모드의 기본 Brownfield 변경 intake에 주어진 값을 덮어쓴 기록을 만든다.

    입력:
        changes: 덮어쓸 intake 항목
    출력:
        intake 딕셔너리
    """
    value = json.loads((ROOT / 'templates/workflow-intake.json.example').read_text())
    value.update(work_units=[], delegation={}, technologies=[], languages=['python'], fields=['implementation'],
                 project_state='brownfield', action='change', risk='low', depth='standard', work_type='standard',
                 change_characteristics=['authored_code'], enforcement_mode='manual')
    value.update(changes)
    return value


class EnforcementRoutingTests(unittest.TestCase):
    def setUp(self):
        """
        역할: 라우팅 매니페스트를 한 번 읽어 둔다.
        """
        self.manifest = _load_manifest(MANIFEST)

    def test_ordinary_change_is_advisory_and_only_major_change_requests_enforcement(self):
        """
        역할: 수동 모드에서 일반 변경은 권고 모드로 통과하고, 유즈케이스·인터페이스·컨셉·구조 변경과 고위험만 훅을 요청하는지 확인한다.
        """
        ordinary = route(intake(), self.manifest)
        self.assertEqual((ordinary['status'], ordinary['enforcement']['level']), ('active', 'advisory'))
        self.assertTrue(ordinary['enforcement']['finish_check_required'])
        for signal in ('use_case_change', 'interface_change', 'concept_change', 'architecture_structure'):
            major = route(intake(change_characteristics=['authored_code', signal]), self.manifest)
            self.assertEqual((major['status'], major['enforcement']['level']), ('waiting_user', 'requested'), signal)
            blocked = next(g for g in major['gate_results'] if g['gate_id'] == 'G0')['blocked']
            self.assertEqual(blocked, [{'reason': 'temporary_enforcement_requested', 'signals': [signal]}])
        risky = route(intake(risk='high', approval_evidence_ids=['EVD-approval']), self.manifest)
        self.assertEqual(risky['enforcement']['major_change_signals'], ['high_risk'])
        self.assertEqual(risky['status'], 'waiting_user')

    def test_user_can_approve_enforcement_or_waive_it(self):
        """
        역할: 큰 변경이 훅 모드에서는 강제 수준으로 진행되고, 사용자가 거절해 면제 증거를 남기면 권고 모드로 진행되는지 확인한다.
        """
        major = dict(change_characteristics=['authored_code', 'use_case_change'])
        enforced = route(intake(enforcement_mode='hook', **major), self.manifest)
        self.assertEqual((enforced['status'], enforced['enforcement']['level']), ('active', 'enforced'))
        waived = route(intake(enforcement_waiver_evidence_ids=['EVD-user-declined'], **major), self.manifest)
        self.assertEqual((waived['status'], waived['enforcement']['level']), ('active', 'advisory'))
        review = route(intake(action='review', **major), self.manifest)
        self.assertEqual(review['status'], 'active')  # 읽기 전용 작업은 요청하지 않는다
        unsupported = route(intake(enforcement_mode='unsupported'), self.manifest)
        self.assertEqual((unsupported['status'], unsupported['enforcement']['level']), ('blocked', 'read_only'))

    def test_advisory_start_is_not_durable_and_returns_a_compact_summary(self):
        """
        역할: 권고 모드의 Runner start가 상태를 저장하지 않고, 전체 라우팅 대신 짧은 요약과 다음 행동을 돌려주는지 확인한다.
        """
        with tempfile.TemporaryDirectory() as name:
            target = Path(name)
            path = target / 'intake.json'
            path.write_text(json.dumps(intake(intent={'goal': 'g', 'success_criteria': ['works'], 'constraints': []})))
            result = start(target, 'TASK-ADVISORY', path, 'claude', 'label', ROOT, REGISTRY, TAXONOMY, MANIFEST)
            self.assertEqual((result['durable'], result['status']), (False, 'active'))
            self.assertEqual(result['reason'], 'advisory_route_follow_skills_then_run_harness_finish')
            self.assertIn('core.implementation-quality', result['activated_skills'])
            self.assertNotIn('route', result)
            self.assertLess(len(json.dumps(result)), 1500)
            self.assertFalse((target / '.agents').exists())

    def test_task_state_is_never_stored_inside_the_shared_harness(self):
        """
        역할: 대상 루트의 .agents 가 공용 하네스 폴더 자체이면 상태 저장소가 거부하는지 확인한다.
        """
        with self.assertRaises(StateError):
            StateStore(ROOT.parent, harness_root=ROOT)


class EditGuardTests(unittest.TestCase):
    def setUp(self):
        """
        역할: 대상 폴더 app 을 가진 임시 프로젝트 루트를 준비한다.
        """
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        (self.root / 'app/src').mkdir(parents=True)
        (self.root / '.claude').mkdir()

    def edit(self, relative: str) -> dict:
        """
        역할: 프로젝트 기준 경로를 편집하는 훅 이벤트를 만든다.

        입력:
            relative: 프로젝트 기준 파일 경로
        출력:
            훅 이벤트 딕셔너리
        """
        return {'tool_name': 'Edit', 'tool_input': {'file_path': str(self.root / relative)}}

    def configure(self, value) -> None:
        """
        역할: 가드 설정 파일을 쓴다.

        입력:
            value: JSON으로 쓸 설정 값, 또는 그대로 쓸 문자열
        """
        text = value if isinstance(value, str) else json.dumps(value)
        (self.root / '.claude/harness-guard.json').write_text(text)

    def set_status(self, status: str) -> None:
        """
        역할: 강제에 묶인 작업의 상태 파일을 주어진 상태로 쓴다.

        입력:
            status: 작업 상태 문자열
        """
        task = self.root / 'app/.agents/state/TASK-1'
        task.mkdir(parents=True, exist_ok=True)
        (task / 'state.json').write_text(json.dumps({'task_id': 'TASK-1', 'status': status}))

    def allowed(self, relative: str) -> bool:
        """
        역할: 프로젝트 기준 경로의 편집이 허용되는지 묻는다.

        입력:
            relative: 프로젝트 기준 파일 경로
        출력:
            허용이면 True
        """
        return decide(self.edit(relative), self.root)[0]

    def test_guard_is_dormant_until_a_task_is_bound(self):
        """
        역할: 설정이 없거나 enforce 항목이 없으면 모든 편집과 설정 파일 수정이 통과하는지 확인한다.
        """
        self.assertTrue(self.allowed('app/src/a.py'))
        self.configure({'exempt_paths': ['legacy']})
        self.assertTrue(self.allowed('app/src/a.py'))
        self.assertTrue(self.allowed('.claude/harness-guard.json'))
        self.assertTrue(decide({'tool_name': 'Read', 'tool_input': {}}, self.root)[0])

    def test_bound_task_controls_target_edits_and_expires_when_finished(self):
        """
        역할: 작업이 묶이면 대상 폴더 편집이 작업 상태를 따르고, 완료·취소되면 저절로 휴면으로 돌아가는지 확인한다.
        """
        self.configure({'exempt_paths': ['app/vendor'], 'enforce': {'task_id': 'TASK-1', 'target_root': 'app'}})
        self.assertFalse(self.allowed('app/src/a.py'))            # 아직 시작 전
        self.assertTrue(self.allowed('app/.agents/state/TASK-1/intake.json'))
        self.assertTrue(self.allowed('other/b.py'))               # 대상 밖
        self.assertTrue(self.allowed('app/vendor/lib.py'))        # 예외 경로
        self.assertFalse(self.allowed('.claude/harness-guard.json'))
        self.assertFalse(decide({'tool_name': 'Write', 'tool_input': {}}, self.root)[0])
        self.set_status('active')
        self.assertTrue(self.allowed('app/src/a.py'))
        for status in ('waiting_user', 'blocked', 'failed'):
            self.set_status(status)
            self.assertFalse(self.allowed('app/src/a.py'), status)
        for status in ('complete', 'cancelled'):
            self.set_status(status)
            self.assertTrue(self.allowed('app/src/a.py'), status)
            self.assertTrue(self.allowed('.claude/harness-guard.json'), status)

    def test_broken_configuration_denies_instead_of_allowing(self):
        """
        역할: 설정이 깨졌거나 형식·경로가 틀리면 편집을 허용하지 않고 거부하는지 확인한다.
        """
        for bad in ('{broken', {'exempt_paths': 'all'}, {'exempt_paths': ['../x']}, {'enforce': {'task_id': 'T'}},
                    {'enforce': {'task_id': 'bad id', 'target_root': 'app'}},
                    {'enforce': {'task_id': 'TASK-1', 'target_root': '../outside'}}, []):
            self.configure(bad)
            self.assertFalse(self.allowed('app/src/a.py'), bad)


class FinishCheckTests(unittest.TestCase):
    def setUp(self):
        """
        역할: 모듈 맵과 문서화된 코드 파일을 커밋해 둔 임시 Git 프로젝트를 준비한다.
        """
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.git = ['git', '-C', str(self.root), '-c', 'user.name=t', '-c', 'user.email=t@example.invalid']
        self.write('docs/architecture/module-map.md', MAP_HEADER + PAYMENT_ROW)
        self.write('src/payment/check.py', SOURCE)
        subprocess.run([*self.git, 'init', '-q'], check=True)
        subprocess.run([*self.git, 'add', '.'], check=True)
        subprocess.run([*self.git, 'commit', '-q', '-m', 'base'], check=True)

    def write(self, name: str, text: str) -> None:
        """
        역할: 임시 프로젝트에 파일을 쓴다.

        입력:
            name: 프로젝트 기준 파일 경로
            text: 파일 내용
        """
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_local_change_passes_with_one_compact_line(self):
        """
        역할: 컴포넌트 내부의 문서화된 변경은 통과하고, 출력이 짧은 한 줄인지 확인한다.
        """
        self.write('src/payment/check.py', SOURCE + '\n\nLIMIT = 10\n')
        self.write('src/payment/limit.py', SOURCE)
        report = finish(self.root, base='HEAD')
        self.assertEqual(report, {'schema_version': 1, 'status': 'passed', 'code_files': 2, 'functions_checked': 1})
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(finish_main(['--target-root', str(self.root), '--base', 'HEAD']), 0)
        self.assertEqual(len(output.getvalue().splitlines()), 1)
        self.assertLess(len(output.getvalue()), 200)

    def test_missing_comments_and_map_mismatch_fail(self):
        """
        역할: 주석 없는 새 함수와 모듈 맵에 없는 컴포넌트를 한 번의 실행에서 함께 보고하는지 확인한다.
        """
        self.write('src/payment/check.py', SOURCE + '\n\ndef undocumented(x):\n    return x\n')
        self.write('src/refund/run.py', SOURCE.replace('컴포넌트: 결제', '컴포넌트: 환불'))
        report = finish(self.root, base='HEAD')
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(sorted(v['kind'] for v in report['violations']), ['function_comment', 'unknown_component'])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(finish_main(['--target-root', str(self.root), '--base', 'HEAD']), 1)

    def test_component_or_architecture_document_change_escalates(self):
        """
        역할: 컴포넌트를 추가하거나 아키텍처 문서를 바꾼 변경은 큰 변경으로 보고 사용자 확인을 요구하며, 거절 사유를 주거나 강제 작업이 진행 중이면 통과하는지 확인한다.
        """
        self.write('docs/architecture/module-map.md',
                   MAP_HEADER + PAYMENT_ROW + '| 주문 | 환불 | 환불을 처리한다 | `src/refund` |\n')
        self.write('src/refund/run.py', SOURCE.replace('컴포넌트: 결제', '컴포넌트: 환불'))
        self.write('docs/architecture/use-cases.md', '# 유즈케이스\n\n환불 요청을 추가한다.\n')
        report = finish(self.root, base='HEAD')
        self.assertEqual(report['status'], 'escalate')
        self.assertEqual(report['major_change_signals'], [
            'component_added: 주문 / 환불', 'architecture_document_changed: docs/architecture/use-cases.md'])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(finish_main(['--target-root', str(self.root), '--base', 'HEAD']), 3)
        waived = finish(self.root, base='HEAD', acknowledged_major='사용자가 훅 없이 진행하기로 함')
        self.assertEqual((waived['status'], waived['acknowledged_major']), ('passed', '사용자가 훅 없이 진행하기로 함'))
        task = self.root / '.agents/state/TASK-1'; task.mkdir(parents=True)
        (task / 'state.json').write_text(json.dumps({'status': 'active', 'intake': {'enforcement_mode': 'hook'}}))
        self.assertEqual(finish(self.root, base='HEAD')['status'], 'passed')

    def test_files_or_base_is_required(self):
        """
        역할: 파일 목록도 기준 리비전도 없으면 사용 오류로 끝나고, 파일만 주면 Git 없이도 검사하는지 확인한다.
        """
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(finish_main(['--target-root', str(self.root)]), 2)
        self.assertEqual(finish(self.root, ['src/payment/check.py'])['status'], 'passed')


if __name__ == '__main__':
    unittest.main()
