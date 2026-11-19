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
