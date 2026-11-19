"""
모듈: 하네스 테스트 (tests)
컴포넌트: 문서 동기화 테스트
역할: 문서 동기화 검사기가 코드 헤더와 모듈 맵의 불일치·삭제된 경로·문서의 끊어진 인용을
      잡는지 검증하고, 하네스 자신의 코드·모듈 맵·HTML 개요가 서로 맞는지 확인한다.
"""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from harness_code_docs import extract_header, header_fields
from harness_doc_sync import check, main, parse_module_map
from harness_overview import is_current, source_fingerprint

MAP = ('# 모듈 맵\n\n| 모듈 | 컴포넌트 | 책임 | 코드 경로 |\n| --- | --- | --- | --- |\n'
       '| 주문 (order) | 결제 | 결제를 검증한다 | `src/order/payment` |\n'
       '| 주문 (order) | 저장소 | 주문을 저장한다 | `src/order/repo.py`, `src/order/schema.py` |\n')


def source(component: str) -> str:
    """
    역할: 주어진 컴포넌트를 가리키는 헤더만 가진 Python 소스를 만든다.

    입력:
        component: 헤더의 컴포넌트 이름
    출력:
        파일 내용 문자열
    """
    return f'"""\n모듈: 주문 (order)\n컴포넌트: {component}\n역할: 예시.\n"""\n'


def kinds(report: dict) -> list[tuple[str, str]]:
    """
    역할: 보고서의 위반을 (종류, 경로) 쌍 목록으로 줄여 비교하기 쉽게 만든다.

    입력:
        report: 검사기 보고서
    출력:
        정렬된 (종류, 경로) 목록
    """
    return sorted((v['kind'], v['path']) for v in report['violations'])


class DocumentSyncCheckTests(unittest.TestCase):
    def setUp(self):
        """
        역할: 모듈 맵과 그에 맞는 코드 파일 세 개를 가진 임시 프로젝트를 준비한다.
        """
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.write('docs/architecture/module-map.md', MAP)
        self.write('src/order/payment/check.py', source('결제'))
        self.write('src/order/repo.py', source('저장소'))
        self.write('src/order/schema.py', source('저장소'))

    def write(self, name: str, text: str) -> str:
        """
        역할: 임시 프로젝트에 파일을 쓴다.

        입력:
            name: 프로젝트 기준 파일 경로
            text: 파일 내용
        출력:
            같은 상대 경로
        """
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return name

    def test_matching_headers_and_map_pass_without_document_edits(self):
        """
        역할: 헤더가 맵의 행과 같고 그 경로 안에 있으면 통과하고, 같은 폴더에 파일이 늘어도 맵 수정이 필요 없는지 확인한다.
        """
        files = ['src/order/payment/check.py', 'src/order/repo.py', 'src/order/schema.py']
        self.assertEqual(check(self.root, files)['status'], 'passed')
        files.append(self.write('src/order/payment/limit.py', source('결제')))
        self.assertEqual(check(self.root, files)['violations'], [])

    def test_header_and_map_disagreements_are_reported(self):
        """
        역할: 맵에 없는 이름, 컴포넌트 경로 밖의 파일, 라벨 없는 헤더를 서로 다른 위반으로 잡는지 확인한다.
        """
        unknown = self.write('src/order/payment/new.py', source('환불'))
        outside = self.write('src/billing/pay.py', source('결제'))
        bare = self.write('src/order/payment/bare.py', 'import os\n')
        self.assertEqual(kinds(check(self.root, [unknown, outside, bare])), [
            ('header_missing_labels', bare), ('path_not_covered', outside), ('unknown_component', unknown)])

    def test_removed_code_and_dangling_document_references_are_reported(self):
        """
        역할: 맵이 가리키는 파일이 삭제되거나 문서가 없는 코드 경로를 인용하면, 파일 목록 없이도 잡는지 확인한다.
        """
        (self.root / 'src/order/schema.py').unlink()
        self.write('docs/architecture/hld.md', '결제는 `src/order/payment/check.py` 와 `src/order/old.py` 를 쓴다.\n'
                                               '예시 `other/place/x.py` 와 설정 `src/order/config.json` 은 대상이 아니다.\n')
        self.assertEqual(kinds(check(self.root)), [
            ('dangling_doc_reference', 'docs/architecture/hld.md'), ('missing_code_path', 'src/order/schema.py')])

    def test_missing_or_malformed_map_fails_closed(self):
        """
        역할: 모듈 맵이 없거나 표 형식이 틀리면 통과가 아니라 실패로 보고하는지 확인한다.
        """
        self.assertEqual(kinds(check(self.root, module_map='docs/none.md')), [('map_missing', 'docs/none.md')])
        for bad in ('표 없음\n', '| 모듈 | 컴포넌트 | 코드 경로 |\n| --- | --- | --- |\n',
                    '| 모듈 | 컴포넌트 | 코드 경로 |\n| --- | --- | --- |\n| a | b | |\n',
                    '| 모듈 | 컴포넌트 | 코드 경로 |\n| --- | --- | --- |\n| a | b | `x` |\n| a | b | `y` |\n'):
            self.write('docs/architecture/module-map.md', bad)
            self.assertEqual([k for k, _ in kinds(check(self.root))], ['map_invalid'], bad)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--target-root', str(self.root), 'missing.py']), 1)
            self.write('docs/architecture/module-map.md', MAP)
            self.assertEqual(main(['--target-root', str(self.root), 'missing.py']), 2)

    def test_base_revision_finds_new_code_that_was_not_listed(self):
        """
        역할: --base를 주면 목록에 넣지 않은 새 코드 파일도 찾아 검사하고, 제외 경로는 건너뛰는지 확인한다.
        """
        git = ['git', '-C', str(self.root), '-c', 'user.name=t', '-c', 'user.email=t@example.invalid']
        subprocess.run([*git, 'init', '-q'], check=True)
        subprocess.run([*git, 'add', '.'], check=True)
        subprocess.run([*git, 'commit', '-q', '-m', 'base'], check=True)
        added = self.write('src/shipping/track.py', source('배송'))
        self.write('vendor/lib/x.py', 'x = 1\n')
        self.write('docs/architecture/overview.html', '<html></html>\n')  # 문서 폴더의 HTML은 코드가 아님
        self.write('src/order/repo.py', source('저장소') + 'VALUE = 1\n')
        report = check(self.root, base='HEAD', excluded=['vendor'])
        self.assertEqual(report['checked_files'], ['src/order/repo.py', added])
        self.assertEqual(kinds(report), [('unknown_component', added)])
        self.assertIn(('header_missing_labels', 'vendor/lib/x.py'), kinds(check(self.root, base='HEAD')))


class HarnessSelfConsistencyTests(unittest.TestCase):
    def test_harness_code_headers_match_the_harness_module_map(self):
        """
        역할: 한글 헤더가 달린 하네스 코드 파일이 모두 하네스 모듈 맵과 일치하고, 맵의 경로가 모두 존재하는지 확인한다.
        """
        files = []
        for path in sorted([*ROOT.glob('scripts/*.py'), *ROOT.glob('tests/*.py'), *ROOT.glob('adapters/**/*.py')]):
            if '모듈' in header_fields(extract_header(path.read_text(encoding='utf-8'), 'python')):
                files.append(path.relative_to(ROOT).as_posix())
        self.assertGreaterEqual(len(files), 8)
        report = check(ROOT, files, module_map='docs/harness/module-map.md')
        self.assertEqual(report['violations'], [])
        mapped = {p for entry in parse_module_map((ROOT / 'docs/harness/module-map.md').read_text()) for p in entry.paths}
        code = {p.relative_to(ROOT).as_posix() for p in [*ROOT.glob('scripts/*.py'), *ROOT.glob('tests/*.py')]}
        self.assertEqual(code - mapped, set(), 'code file without a module map row')

    def test_overview_was_reviewed_against_the_current_sources(self):
        """
        역할: plan·라우팅·스킬 목록이 바뀐 뒤 HTML 개요를 검토하고 스탬프를 갱신했는지 확인한다.
        """
        self.assertEqual(len(source_fingerprint(ROOT)), 64)
        self.assertTrue(is_current(ROOT), 'plan/routing/skills changed: review docs/harness/index.html, '
                                          'then run scripts/harness_overview.py write')


if __name__ == '__main__':
    unittest.main()
