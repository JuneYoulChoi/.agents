#!/usr/bin/env python3
"""
모듈: 하네스 런타임 (scripts)
컴포넌트: 코드 문서화 검사기
역할: 작성·수정된 코드 파일에 한글 파일 헤더(모듈·컴포넌트·역할)와 함수별 한글 주석
      (역할·입력·출력)이 있는지 검사하고, 결과를 JSON 보고서로 돌려준다.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

HEADER_LABELS = ("모듈:", "컴포넌트:", "역할:")
ROLE_LABEL, INPUT_LABEL, OUTPUT_LABEL = "역할:", "입력:", "출력:"
HANGUL = re.compile(r"[\uac00-\ud7a3]")
HEADER_SCAN_LINES = 40

LANGUAGES = {
    ".py": "python",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".mts": "typescript", ".cts": "typescript",
    ".java": "java", ".cs": "csharp",
    ".c": "c", ".h": "c", ".cc": "cpp", ".cpp": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".hh": "cpp",
    ".go": "go", ".rs": "rust",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell",
    ".html": "html", ".htm": "html", ".css": "css",
}
BRACE_LANGUAGES = {"javascript", "typescript", "java", "csharp", "c", "cpp", "go", "rust"}
HEADER_ONLY_LANGUAGES = {"html", "css"}
CONTROL_WORDS = {"if", "for", "while", "switch", "catch", "return", "sizeof", "foreach", "using",
                 "lock", "fixed", "elif", "else", "do", "new", "throw", "typeof", "await", "match"}

FUNCTION_PATTERNS = {
    "javascript": [
        re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(\w+)\s*\(([^)]*)\)"),
        re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function\s*\w*\s*)?\(([^)]*)\)\s*(?:=>|\{)"),
        re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(\w+)\s*=>"),
        re.compile(r"^\s*(?:static\s+)?(?:async\s+)?(?:get\s+|set\s+)?\*?(\w+)\s*\(([^)]*)\)\s*\{"),
    ],
    "go": [re.compile(r"^func\s+(?:\([^)]*\)\s*)?(\w+)\s*(?:\[[^\]]*\])?\s*\(([^)]*)\)")],
    "rust": [re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:const\s+)?(?:async\s+)?(?:unsafe\s+)?(?:extern\s+\"[^\"]*\"\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)")],
    "shell": [re.compile(r"^\s*(?:function\s+)?([A-Za-z_][\w-]*)\s*\(\s*\)\s*\{?"),
              re.compile(r"^\s*function\s+([A-Za-z_][\w-]*)\s*\{")],
    "c_family": [re.compile(r"^\s*(?:[\w:<>,\[\]\*&~]+\s+)+\**&?\s*([~\w:]+)\s*\(([^;{}]*)\)\s*(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?(?:throws\s+[\w.,\s]+)?\s*\{?\s*$")],
}
FUNCTION_PATTERNS["typescript"] = [
    re.compile(p.pattern.replace(r"\(([^)]*)\)\s*(?:=>|\{)", r"\(([^)]*)\)\s*(?::\s*[^=]+)?\s*(?:=>|\{)"))
    for p in FUNCTION_PATTERNS["javascript"]
] + [re.compile(r"^\s*(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:readonly\s+)?(?:async\s+)?(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)\s*(?::\s*[^{]+)?\{")]
for language in ("java", "csharp", "c", "cpp"):
    FUNCTION_PATTERNS[language] = FUNCTION_PATTERNS["c_family"]

COMMENT_PREFIXES = {
    "python": ("#",), "shell": ("#",),
    "go": ("//",), "rust": ("///", "//!", "//"),
    "html": ("<!--",), "css": ("/*",),
}
SKIPPABLE_ABOVE = re.compile(r"^\s*(@[\w.]+|#\[.*\]|\[[\w.]+.*\])")


@dataclass
class FunctionInfo:
    """
    역할: 검사 대상 함수 하나의 위치와 주석 판단에 필요한 정보를 담는다.

    입력:
        name: 함수 이름
        line: 함수 선언이 시작하는 줄 번호(1부터)
        end_line: 함수 본문이 끝나는 줄 번호
        has_inputs: self/cls를 제외한 매개변수가 있는지
        has_output: 값을 반환하거나 내보내는지
        doc: 함수에 붙은 주석 원문(없으면 빈 문자열)
    """

    name: str
    line: int
    end_line: int
    has_inputs: bool
    has_output: bool
    doc: str


@dataclass
class FileReport:
    """
    역할: 파일 하나의 검사 결과(헤더 상태와 함수별 문제)를 담는다.

    입력:
        path: 대상 루트 기준 파일 경로
        language: 판정한 언어 이름
        header: 헤더 상태(ok, missing, incomplete, not_korean)
        functions: 문제가 있는 함수별 결과 목록
        checked_functions: 검사한 함수 수
    """

    path: str
    language: str
    header: str = "ok"
    functions: list[dict] = field(default_factory=list)
    checked_functions: int = 0

    def passed(self) -> bool:
        """
        역할: 이 파일이 헤더와 함수 주석 규칙을 모두 만족하는지 판단한다.

        출력:
            헤더가 정상이고 문제 함수가 없으면 True
        """
        return self.header == "ok" and not self.functions


def detect_language(path: Path) -> str | None:
    """
    역할: 파일 확장자로 검사할 언어를 정한다.

    입력:
        path: 검사할 파일 경로
    출력:
        언어 이름. 지원하지 않는 확장자면 None
    """
    return LANGUAGES.get(path.suffix.lower())


def header_status(text: str) -> str:
    """
    역할: 헤더 주석 원문이 세 가지 한글 라벨을 모두 갖췄는지 판정한다.

    입력:
        text: 파일 맨 위에서 추출한 헤더 주석 원문
    출력:
        ok, missing(주석 없음), not_korean(한글 없음), incomplete(라벨 누락) 중 하나
    """
    if not text.strip():
        return "missing"
    if not HANGUL.search(text):
        return "not_korean"
    if any(label not in text for label in HEADER_LABELS):
        return "incomplete"
    return "ok"


def function_problems(info: FunctionInfo) -> list[str]:
    """
    역할: 함수 주석에서 빠진 항목을 찾는다.

    입력:
        info: 검사할 함수 정보
    출력:
        문제 설명 목록. 비어 있으면 규칙을 만족한다.
    """
    if not info.doc.strip():
        return ["함수 주석 없음"]
    problems = []
    if not HANGUL.search(info.doc):
        problems.append("주석이 한글이 아님")
    if ROLE_LABEL not in info.doc:
        problems.append("역할: 누락")
    if info.has_inputs and INPUT_LABEL not in info.doc:
        problems.append("입력: 누락")
    if info.has_output and OUTPUT_LABEL not in info.doc:
        problems.append("출력: 누락")
    return problems


# ---------- Python: 표준 ast로 정확하게 분석 ----------

def python_header(source: str, tree: ast.Module) -> str:
    """
    역할: Python 파일의 모듈 docstring 또는 맨 앞 # 주석 블록을 헤더로 추출한다.

    입력:
        source: 파일 원문
        tree: 파싱된 모듈 트리
    출력:
        헤더 원문. 없으면 빈 문자열
    """
    docstring = ast.get_docstring(tree, clean=False)
    if docstring:
        return docstring
    lines = []
    for line in source.splitlines()[:HEADER_SCAN_LINES]:
        stripped = line.strip()
        if stripped.startswith("#!") or re.match(r"#.*coding[:=]", stripped):
            continue
        if stripped.startswith("#"):
            lines.append(stripped.lstrip("#").strip())
        elif stripped or lines:
            break
    return "\n".join(lines)


def python_returns_value(node: ast.AST) -> bool:
    """
    역할: 함수 본문이 값을 반환하거나 yield 하는지 확인한다. 중첩 함수 안은 보지 않는다.

    입력:
        node: 함수 정의 노드
    출력:
        값을 내보내면 True
    """
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(child, ast.Return) and child.value is not None:
            if not (isinstance(child.value, ast.Constant) and child.value.value is None):
                return True
        if isinstance(child, (ast.Yield, ast.YieldFrom)):
            return True
        stack.extend(ast.iter_child_nodes(child))
    return False


def python_functions(tree: ast.Module) -> list[FunctionInfo]:
    """
    역할: Python 모듈 안의 모든 이름 있는 함수와 메서드를 찾는다.

    입력:
        tree: 파싱된 모듈 트리
    출력:
        함수 정보 목록
    """
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = node.args
        names = [a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]]
        names += [a.arg for a in (args.vararg, args.kwarg) if a is not None]
        inputs = [n for n in names if n not in {"self", "cls"}]
        found.append(FunctionInfo(node.name, node.lineno, node.end_lineno or node.lineno, bool(inputs),
                                  python_returns_value(node), ast.get_docstring(node, clean=False) or ""))
    return found


# ---------- 그 밖의 언어: 가벼운 줄 단위 분석 ----------

def leading_comment(lines: list[str], language: str) -> str:
    """
    역할: 파일 맨 앞(셰뱅 등 허용 줄 다음)의 첫 주석 블록을 헤더로 추출한다.

    입력:
        lines: 파일의 줄 목록
        language: 언어 이름
    출력:
        헤더 원문. 첫 코드 줄 전에 주석이 없으면 빈 문자열
    """
    collected: list[str] = []
    in_block = False
    for raw in lines[:HEADER_SCAN_LINES]:
        line = raw.strip()
        if not collected and not in_block:
            if not line or line.startswith("#!") or line in {"'use strict';", '"use strict";'} \
                    or line.lower().startswith("<!doctype"):
                continue
        if in_block:
            collected.append(line)
            if "*/" in line or "-->" in line:
                break
            continue
        if line.startswith("/*") or line.startswith("<!--"):
            collected.append(line)
            in_block = not ("*/" in line[2:] or "-->" in line[4:])
            if not in_block:
                break
            continue
        if line.startswith("//") or (line.startswith("#") and language == "shell"):
            collected.append(line)
            continue
        break
    return "\n".join(collected)


def comment_above(lines: list[str], index: int, language: str) -> str:
    """
    역할: 함수 선언 바로 위에 붙은 주석 블록을 찾는다. 데코레이터·어노테이션 줄은 건너뛴다.

    입력:
        lines: 파일의 줄 목록
        index: 함수 선언 줄의 0부터 시작하는 위치
        language: 언어 이름
    출력:
        주석 원문. 바로 위에 주석이 없으면 빈 문자열
    """
    position = index - 1
    while position >= 0 and SKIPPABLE_ABOVE.match(lines[position]):
        position -= 1
    if position < 0:
        return ""
    if lines[position].strip().endswith("*/"):
        block = []
        while position >= 0:
            block.append(lines[position])
            if "/*" in lines[position]:
                return "\n".join(reversed(block))
            position -= 1
        return ""
    prefixes = ("#",) if language == "shell" else ("//",)
    block = []
    while position >= 0 and lines[position].strip().startswith(prefixes) \
            and not lines[position].strip().startswith("#!"):
        block.append(lines[position])
        position -= 1
    return "\n".join(reversed(block))


def strip_strings(line: str) -> str:
    """
    역할: 중괄호 짝 맞추기를 방해하지 않도록 줄에서 문자열 리터럴과 // 주석을 지운다.

    입력:
        line: 원본 코드 한 줄
    출력:
        문자열과 줄 주석을 제거한 줄
    """
    line = re.sub(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`", '""', line)
    return line.split("//", 1)[0]


def block_end(lines: list[str], index: int) -> int:
    """
    역할: 함수 선언 줄부터 중괄호 짝을 맞춰 본문이 끝나는 줄을 찾는다.

    입력:
        lines: 파일의 줄 목록
        index: 함수 선언 줄의 0부터 시작하는 위치
    출력:
        본문 마지막 줄의 0부터 시작하는 위치. 본문이 없으면 선언 줄 위치
    """
    depth, opened = 0, False
    for position in range(index, len(lines)):
        text = strip_strings(lines[position])
        if not opened and position > index and text.strip().endswith(";") and "{" not in text:
            return position  # 선언만 있는 프로토타입
        for char in text:
            if char == "{":
                depth, opened = depth + 1, True
            elif char == "}":
                depth -= 1
                if opened and depth == 0:
                    return position
        if not opened and position - index > 5:
            return index
    return len(lines) - 1


def shell_end(lines: list[str], index: int) -> int:
    """
    역할: 셸 함수의 본문이 끝나는 줄(맨 앞의 닫는 중괄호)을 찾는다.

    입력:
        lines: 파일의 줄 목록
        index: 함수 선언 줄의 0부터 시작하는 위치
    출력:
        본문 마지막 줄의 0부터 시작하는 위치
    """
    for position in range(index + 1, len(lines)):
        if lines[position].strip() == "}":
            return position
    return len(lines) - 1


def body_has_output(body: str, language: str) -> bool:
    """
    역할: 함수 본문이 값을 반환하거나(셸은 표준 출력으로) 결과를 내보내는지 추정한다.

    입력:
        body: 함수 선언부터 끝까지의 원문
        language: 언어 이름
    출력:
        출력이 있다고 판단되면 True
    """
    if language == "shell":
        return bool(re.search(r"\b(echo|printf|return\s+\S)", body))
    return bool(re.search(r"\breturn\s+[^;\s}]", body)) or bool(re.search(r"\byield\b", body))


def has_parameters(params: str) -> bool:
    """
    역할: 선언된 매개변수 목록에 실제 입력이 있는지 판단한다. 리시버·void·this는 제외한다.

    입력:
        params: 괄호 안의 매개변수 원문
    출력:
        입력 매개변수가 하나 이상이면 True
    """
    text = re.sub(r"&?\s*(mut\s+)?self\b,?|\bthis\s*:[^,]*,?", "", params).strip()
    return bool(text) and text not in {"void", ","}


def generic_functions(lines: list[str], language: str) -> list[FunctionInfo]:
    """
    역할: Python 이외 언어에서 정규식으로 이름 있는 함수와 메서드 선언을 찾는다.

    입력:
        lines: 파일의 줄 목록
        language: 언어 이름
    출력:
        함수 정보 목록
    """
    found = []
    for index, line in enumerate(lines):
        if line.lstrip().startswith(("//", "/*", "*", "#")):
            continue
        for pattern in FUNCTION_PATTERNS.get(language, []):
            match = pattern.match(line)
            if not match:
                continue
            name = match.group(1).split("::")[-1]
            if name in CONTROL_WORDS:
                break
            params = match.group(2) if match.lastindex and match.lastindex >= 2 else ""
            end = shell_end(lines, index) if language == "shell" else block_end(lines, index)
            if language != "shell" and end == index and not line.rstrip().endswith(("{", ")")):
                break
            body = "\n".join(lines[index:end + 1])
            found.append(FunctionInfo(name, index + 1, end + 1, has_parameters(params),
                                      body_has_output(body, language), comment_above(lines, index, language)))
            break
    return found


def extract_header(source: str, language: str) -> str:
    """
    역할: 언어에 맞는 방법으로 파일 맨 위의 헤더 주석 원문을 추출한다.

    입력:
        source: 파일 원문
        language: 언어 이름
    출력:
        헤더 원문. 헤더가 없거나 Python 문법 오류면 빈 문자열
    """
    if language == "python":
        try:
            return python_header(source, ast.parse(source))
        except SyntaxError:
            return ""
    return leading_comment(source.splitlines(), language)


def header_fields(header: str) -> dict[str, str]:
    """
    역할: 헤더 주석에서 모듈·컴포넌트·역할 라벨의 값을 뽑는다.

    입력:
        header: 헤더 주석 원문
    출력:
        라벨(콜론 제외)을 키로, 그 줄의 값을 값으로 하는 딕셔너리. 없는 라벨은 빠진다.
    """
    fields: dict[str, str] = {}
    for raw in header.splitlines():
        line = raw.strip().lstrip("/*#!<-").strip()
        for label in HEADER_LABELS:
            if line.startswith(label) and label[:-1] not in fields:
                fields[label[:-1]] = " ".join(line[len(label):].replace("*/", "").replace("-->", "").split())
    return fields


# ---------- 변경 범위 ----------

def changed_lines(root: Path, relative: str, base: str) -> set[int] | None:
    """
    역할: 기준 리비전 이후 이 파일에서 바뀐(추가·수정된) 줄 번호를 구한다.

    입력:
        root: Git 작업 트리인 대상 루트
        relative: 루트 기준 파일 경로
        base: 비교할 Git 리비전
    출력:
        바뀐 줄 번호 집합. 추적되지 않는 새 파일이면 None(전체가 변경)
    예외:
        RuntimeError: Git 명령이 실패한 경우
    """
    tracked = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{base}:{relative}"],
                             capture_output=True)
    if tracked.returncode != 0:
        return None
    diff = subprocess.run(["git", "-C", str(root), "diff", "-U0", base, "--", relative],
                          capture_output=True, text=True)
    if diff.returncode != 0:
        raise RuntimeError(f"git diff failed for {relative}: {diff.stderr.strip()}")
    lines: set[int] = set()
    for match in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff.stdout, re.M):
        start, count = int(match.group(1)), int(match.group(2) or 1)
        lines.update(range(start, start + count))
    return lines


# ---------- 진입점 ----------

def check_file(root: Path, relative: str, base: str | None) -> FileReport | None:
    """
    역할: 파일 하나의 헤더와 (변경된) 함수 주석을 검사한다.

    입력:
        root: 대상 프로젝트 루트
        relative: 루트 기준 파일 경로
        base: 함수 검사를 변경분으로 한정할 Git 리비전. None이면 전체 함수 검사
    출력:
        검사 결과. 지원하지 않는 언어면 None
    예외:
        ValueError: 경로가 루트를 벗어나거나 파일이 없을 때
    """
    path = (root / relative).resolve()
    if root not in path.parents or not path.is_file():
        raise ValueError(f"file must exist inside the target root: {relative}")
    language = detect_language(path)
    if language is None:
        return None
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    report = FileReport(relative, language)
    if language == "python":
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            report.header = f"unparsable: {exc.msg} (line {exc.lineno})"
            return report
        report.header = header_status(python_header(source, tree))
        functions = python_functions(tree)
    else:
        report.header = header_status(leading_comment(lines, language))
        functions = [] if language in HEADER_ONLY_LANGUAGES else generic_functions(lines, language)
    scope = changed_lines(root, relative, base) if base else None
    for info in functions:
        if scope is not None and not scope & set(range(info.line, info.end_line + 1)):
            continue
        report.checked_functions += 1
        problems = function_problems(info)
        if problems:
            report.functions.append({"name": info.name, "line": info.line, "problems": problems})
    return report


def check(root: Path, files: Iterable[str], base: str | None = None) -> dict:
    """
    역할: 여러 파일을 검사해 하나의 보고서로 묶는다.

    입력:
        root: 대상 프로젝트 루트
        files: 루트 기준 파일 경로 목록
        base: 함수 검사를 변경분으로 한정할 Git 리비전(선택)
    출력:
        status(passed/failed), 파일별 결과, 건너뛴 파일을 담은 보고서 딕셔너리
    예외:
        ValueError: 파일 목록이 비었거나 경로가 잘못된 경우
    """
    files = list(dict.fromkeys(files))
    if not files:
        raise ValueError("at least one file is required")
    root = root.resolve(strict=True)
    reports, skipped = [], []
    for relative in files:
        report = check_file(root, relative, base)
        if report is None:
            skipped.append(relative)
        else:
            reports.append(report)
    failed = [r for r in reports if not r.passed()]
    return {
        "schema_version": 1,
        "status": "failed" if failed else "passed",
        "base_revision": base,
        "files": [{"path": r.path, "language": r.language, "header": r.header,
                   "checked_functions": r.checked_functions, "function_problems": r.functions}
                  for r in reports],
        "skipped_unsupported": skipped,
    }


def main(argv: list[str] | None = None) -> int:
    """
    역할: 명령줄 인자를 받아 검사를 실행하고 보고서를 출력한다.

    입력:
        argv: 명령줄 인자 목록(테스트용). None이면 sys.argv 사용
    출력:
        종료 코드. 통과 0, 규칙 위반 1, 사용 오류 2
    """
    parser = argparse.ArgumentParser(description="Check Korean file headers and function comments.")
    parser.add_argument("--target-root", required=True, type=Path)
    parser.add_argument("--base", help="Git revision; limit function checks to changed functions")
    parser.add_argument("files", nargs="+")
    args = parser.parse_args(argv)
    try:
        result = check(args.target_root, args.files, args.base)
    except (OSError, ValueError, RuntimeError) as exc:
        sys.stderr.write(f"harness_code_docs: {exc}\n")
        return 2
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
