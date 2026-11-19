"""
모듈: 하네스 테스트 (tests)
컴포넌트: 코드 문서화 검사기 테스트
역할: 한글 파일 헤더와 함수 주석 검사기가 언어별로 누락을 잡고, 변경 범위·예외 파일·잘못된
      경로를 올바르게 처리하는지 검증한다.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from harness_code_docs import check, main

PY_HEADER = '"""\n모듈: 주문\n컴포넌트: 결제\n역할: 결제를 검증한다.\n"""\n'
PY_GOOD_FUNCTION = (
    'def add(a, b):\n'
    '    """\n    역할: 더한다.\n\n    입력:\n        a: 수\n        b: 수\n    출력:\n        합계\n    """\n'
    '    return a + b\n'
)


def problems_by_name(report: dict, path: str) -> dict:
    """
    역할: 보고서에서 한 파일의 함수별 문제 목록을 이름으로 찾기 쉽게 바꾼다.

    입력:
        report: 검사기 보고서
        path: 확인할 파일 경로
    출력:
        함수 이름을 키, 문제 목록을 값으로 하는 딕셔너리
    """
    entry = next(f for f in report['files'] if f['path'] == path)
    return {item['name']: item['problems'] for item in entry['function_problems']}


class CodeDocumentationCheckTests(unittest.TestCase):
    def setUp(self):
        """
        역할: 검사 대상 파일을 만들 임시 루트를 준비한다.
        """
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()

    def write(self, name: str, text: str) -> str:
        """
        역할: 임시 루트에 검사 대상 파일을 쓴다.

        입력:
            name: 루트 기준 파일 경로
            text: 파일 내용
        출력:
            검사기에 넘길 같은 상대 경로
        """
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return name

    def test_python_requires_korean_header_and_labels_per_function(self):
        """
        역할: Python 파일에서 헤더 누락·영어 헤더와 함수별 역할·입력·출력 누락을 구분해 잡는지 확인한다.
        """
        self.write('good.py', PY_HEADER + '\n\n' + PY_GOOD_FUNCTION)
        self.write('english.py', '"""Payment checks."""\n')
        self.write('none.py', 'import os\n')
        self.write('partial.py', PY_HEADER.replace('컴포넌트: 결제\n', '') + (
            '\n\nclass Cart:\n'
            '    def add(self, item):\n        """역할: 담는다."""\n        self.items.append(item)\n\n'
            '    def total(self):\n        """역할: 합계를 구한다."""\n        return 1\n\n'
            '    def clear(self):\n        """Clears."""\n        self.items = []\n\n'
            '    def count(self, kind):\n        return 0\n'))
        report = check(self.root, ['good.py', 'english.py', 'none.py', 'partial.py'])
        headers = {f['path']: f['header'] for f in report['files']}
        self.assertEqual(headers, {'good.py': 'ok', 'english.py': 'not_korean', 'none.py': 'missing',
                                   'partial.py': 'incomplete'})
        self.assertEqual(problems_by_name(report, 'good.py'), {})
        self.assertEqual(problems_by_name(report, 'partial.py'), {
            'add': ['입력: 누락'], 'total': ['출력: 누락'],
            'clear': ['주석이 한글이 아님', '역할: 누락'], 'count': ['함수 주석 없음']})
        self.assertEqual(report['status'], 'failed')

    def test_brace_and_shell_languages_find_functions_and_comments(self):
        """
        역할: TypeScript·Java·Go·Rust·Shell에서 함수 선언과 바로 위 주석을 찾아 누락을 판정하는지 확인한다.
        """
        header = '/**\n * 모듈: 주문\n * 컴포넌트: 결제\n * 역할: 검증한다.\n */\n'
        self.write('a.ts', header + (
            '/**\n * 역할: 확인한다.\n * 입력: n 값\n * 출력: 결과\n */\n'
            'export function ok(n: number): boolean {\n  return n > 0;\n}\n\n'
            'export const bad = (n: number) => {\n  return n;\n};\n'))
        self.write('A.java', header + (
            'public class A {\n'
            '    /** 역할: 실행한다. */\n    @Override\n    public void run() {\n        go();\n    }\n\n'
            '    public int size(int x) {\n        return x;\n    }\n}\n'))
        self.write('a.go', '// 모듈: 주문\n// 컴포넌트: 결제\n// 역할: 검증한다.\npackage a\n\n'
                           '// 역할: 크기를 돌려준다.\n// 출력: 크기\nfunc (s *S) Size() int {\n\treturn 1\n}\n\n'
                           'func Bad(x int) {\n}\n')
        self.write('a.rs', '//! 모듈: 주문\n//! 컴포넌트: 결제\n//! 역할: 검증한다.\n\n'
                           '/// 역할: 더한다.\n/// 입력: a 수\n/// 출력: 합\npub fn add(&self, a: i32) -> i32 {\n    a + 1\n}\n')
        self.write('a.sh', '#!/usr/bin/env bash\n# 모듈: 배포\n# 컴포넌트: 실행\n# 역할: 시작한다.\n\n'
                           '# 역할: 포트를 출력한다.\nport() {\n  echo 1\n}\n\nstart() {\n  port\n}\n')
        report = check(self.root, ['a.ts', 'A.java', 'a.go', 'a.rs', 'a.sh'])
        self.assertTrue(all(f['header'] == 'ok' for f in report['files']))
        self.assertEqual(problems_by_name(report, 'a.ts'), {'bad': ['함수 주석 없음']})
        self.assertEqual(problems_by_name(report, 'A.java'), {'size': ['함수 주석 없음']})
        self.assertEqual(problems_by_name(report, 'a.go'), {'Bad': ['함수 주석 없음']})
        self.assertEqual(problems_by_name(report, 'a.sh'), {'port': ['출력: 누락'], 'start': ['함수 주석 없음']})
        self.assertEqual(problems_by_name(report, 'a.rs'), {})

    def test_unsupported_files_are_skipped_and_bad_paths_rejected(self):
        """
        역할: 주석 문법이 없는 파일은 건너뛰고, 루트 밖이나 없는 파일 경로는 오류로 거부하는지 확인한다.
        """
        self.write('data.json', '{"a": 1}\n')
        report = check(self.root, ['data.json'])
        self.assertEqual((report['status'], report['skipped_unsupported'], report['files']),
                         ('passed', ['data.json'], []))
        for bad in (['../x.py'], ['missing.py'], []):
            with self.assertRaises(ValueError):
                check(self.root, bad)
        self.assertEqual(main(['--target-root', str(self.root), 'missing.py']), 2)

    def test_base_revision_limits_function_checks_to_changed_functions(self):
        """
        역할: --base를 주면 기존의 주석 없는 함수는 건너뛰고, 새로 추가·수정한 함수와 헤더만 검사하는지 확인한다.
        """
        git = ['git', '-C', str(self.root), '-c', 'user.name=t', '-c', 'user.email=t@example.invalid']
        legacy = 'def old(a):\n    return a\n'
        self.write('m.py', legacy)
        subprocess.run([*git, 'init', '-q'], check=True)
        subprocess.run([*git, 'add', '.'], check=True)
        subprocess.run([*git, 'commit', '-q', '-m', 'base'], check=True)
        self.write('m.py', PY_HEADER + '\n\n' + legacy + '\n\ndef new(a):\n    return a\n')
        self.write('fresh.py', PY_HEADER + '\n\ndef undocumented():\n    pass\n')
        report = check(self.root, ['m.py', 'fresh.py'], base='HEAD')
        self.assertEqual(problems_by_name(report, 'm.py'), {'new': ['함수 주석 없음']})
        self.assertEqual(problems_by_name(report, 'fresh.py'), {'undocumented': ['함수 주석 없음']})
        full = check(self.root, ['m.py'])
        self.assertEqual(set(problems_by_name(full, 'm.py')), {'old', 'new'})
        self.assertEqual(json.loads(json.dumps(report))['base_revision'], 'HEAD')


if __name__ == '__main__':
    unittest.main()
