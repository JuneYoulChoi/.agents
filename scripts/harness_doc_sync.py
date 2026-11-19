#!/usr/bin/env python3
"""
모듈: 하네스 런타임 (scripts)
컴포넌트: 문서 동기화 검사기
역할: 코드 파일 헤더의 모듈·컴포넌트와 아키텍처 문서의 모듈 맵이 서로 일치하는지,
      문서가 가리키는 코드 경로가 실제로 있는지 검사해 JSON 보고서로 돌려준다.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from harness_code_docs import LANGUAGES, detect_language, extract_header, header_fields

DEFAULT_MAP = "docs/architecture/module-map.md"
MAP_COLUMNS = ("모듈", "컴포넌트", "코드 경로")
CODE_PATH_TOKEN = re.compile(r"`([\w.\-]+(?:/[\w.\-]+)+\.(\w+))`")


@dataclass(frozen=True)
class MapEntry:
    """
    역할: 모듈 맵 표의 한 행을 담는다.

    입력:
        module: 모듈 이름
        component: 컴포넌트 이름
        paths: 이 컴포넌트의 코드가 있는 프로젝트 기준 파일·폴더 경로들
    """

    module: str
    component: str
    paths: tuple[str, ...]


def normalize(text: str) -> str:
    """
    역할: 이름 비교를 위해 백틱과 여분의 공백을 없앤다.

    입력:
        text: 표 칸이나 헤더에서 읽은 원문
    출력:
        정규화한 문자열
    """
    return " ".join(text.replace("`", "").split())


def table_cells(line: str) -> list[str]:
    """
    역할: Markdown 표 한 줄을 칸 목록으로 나눈다.

    입력:
        line: 표의 한 줄
    출력:
        앞뒤 공백을 없앤 칸 목록. 표 줄이 아니면 빈 목록
    """
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def parse_module_map(text: str) -> list[MapEntry]:
    """
    역할: 문서에서 모듈·컴포넌트·코드 경로 열을 가진 표를 찾아 행을 읽는다.

    입력:
        text: 모듈 맵 문서 원문
    출력:
        표의 행 목록
    예외:
        ValueError: 필요한 열을 가진 표가 없거나 행의 이름·경로가 비어 있거나 중복된 경우
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        header = [normalize(cell) for cell in table_cells(line)]
        if not all(column in header for column in MAP_COLUMNS):
            continue
        positions = [header.index(column) for column in MAP_COLUMNS]
        entries: list[MapEntry] = []
        for row in lines[index + 1:]:
            cells = table_cells(row)
            if not cells:
                break
            if all(set(cell) <= set("-: ") for cell in cells):
                continue
            if len(cells) <= max(positions):
                raise ValueError(f"module map row has too few columns: {row.strip()}")
            module, component, raw_paths = (normalize(cells[p]) for p in positions)
            paths = tuple(p.strip().rstrip("/") for p in raw_paths.split(",") if p.strip())
            if not module or not component or not paths:
                raise ValueError(f"module map row needs module, component and code path: {row.strip()}")
            if any((e.module, e.component) == (module, component) for e in entries):
                raise ValueError(f"module map repeats a component: {module} / {component}")
            entries.append(MapEntry(module, component, paths))
        if not entries:
            raise ValueError("module map table has no rows")
        return entries
    raise ValueError("module map needs a table with 모듈, 컴포넌트 and 코드 경로 columns")


def covers(entry_path: str, relative: str) -> bool:
    """
    역할: 맵의 코드 경로가 주어진 파일을 포함하는지 판단한다.

    입력:
        entry_path: 맵에 적힌 파일 또는 폴더 경로
        relative: 프로젝트 기준 파일 경로
    출력:
        같은 파일이거나 그 폴더 아래에 있으면 True
    """
    return relative == entry_path or relative.startswith(entry_path + "/")


def changed_code_files(root: Path, base: str, excluded: tuple[str, ...]) -> list[str]:
    """
    역할: 기준 리비전 이후 추가·수정된 코드 파일(추적되지 않는 새 파일 포함)을 찾는다.

    입력:
        root: Git 작업 트리인 프로젝트 루트
        base: 비교할 Git 리비전
        excluded: 검사에서 제외할 경로 접두어들
    출력:
        지원하는 언어의 프로젝트 기준 파일 경로 목록(정렬됨)
    예외:
        RuntimeError: Git 명령이 실패한 경우
    """
    commands = (["diff", "--name-only", "--diff-filter=AMR", base], ["ls-files", "--others", "--exclude-standard"])
    found: set[str] = set()
    for command in commands:
        done = subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=off", *command],
                              capture_output=True, text=True)
        if done.returncode != 0:
            raise RuntimeError(f"git {command[0]} failed: {done.stderr.strip()}")
        found.update(line for line in done.stdout.splitlines() if line)
    return sorted(path for path in found
                  if Path(path).suffix.lower() in LANGUAGES and (root / path).is_file()
                  and not any(covers(prefix, path) for prefix in excluded))


def header_violations(root: Path, relative: str, entries: list[MapEntry]) -> list[dict]:
    """
    역할: 코드 파일 하나의 헤더가 모듈 맵의 행과 일치하고 그 경로 안에 있는지 확인한다.

    입력:
        root: 프로젝트 루트
        relative: 프로젝트 기준 코드 파일 경로
        entries: 모듈 맵의 행 목록
    출력:
        위반 목록. 비어 있으면 일치한다.
    예외:
        ValueError: 경로가 루트를 벗어나거나 파일이 없을 때
    """
    path = (root / relative).resolve()
    if root not in path.parents or not path.is_file():
        raise ValueError(f"file must exist inside the target root: {relative}")
    language = detect_language(path)
    if language is None:
        return []
    fields = header_fields(extract_header(path.read_text(encoding="utf-8"), language))
    module, component = normalize(fields.get("모듈", "")), normalize(fields.get("컴포넌트", ""))
    if not module or not component:
        return [{"kind": "header_missing_labels", "path": relative,
                 "detail": "파일 헤더에 모듈: 또는 컴포넌트: 가 없음"}]
    entry = next((e for e in entries if (e.module, e.component) == (module, component)), None)
    if entry is None:
        return [{"kind": "unknown_component", "path": relative,
                 "detail": f"모듈 맵에 없는 이름: {module} / {component}"}]
    if not any(covers(p, relative) for p in entry.paths):
        return [{"kind": "path_not_covered", "path": relative,
                 "detail": f"{module} / {component} 의 코드 경로 밖에 있음: {', '.join(entry.paths)}"}]
    return []


def map_violations(root: Path, entries: list[MapEntry]) -> list[dict]:
    """
    역할: 모듈 맵이 가리키는 코드 경로가 모두 실제로 있는지 확인한다(삭제·이동 감지).

    입력:
        root: 프로젝트 루트
        entries: 모듈 맵의 행 목록
    출력:
        없는 경로마다 하나씩의 위반 목록
    """
    return [{"kind": "missing_code_path", "path": path,
             "detail": f"{entry.module} / {entry.component} 의 코드 경로가 없음"}
            for entry in entries for path in entry.paths if not (root / path).exists()]


def reference_violations(root: Path, documents: Path, module_map: Path) -> list[dict]:
    """
    역할: 모듈 맵 옆 문서들이 백틱으로 인용한 코드 파일 경로가 실제로 있는지 확인한다.

    입력:
        root: 프로젝트 루트
        documents: 모듈 맵이 있는 문서 폴더
        module_map: 모듈 맵 문서의 절대 경로(중복 보고를 피하려고 건너뛴다)
    출력:
        없는 코드 경로를 인용한 문서와 경로의 위반 목록
    """
    violations = []
    for document in sorted(documents.rglob("*.md")):
        if document == module_map:
            continue  # 맵의 경로는 map_violations 가 이미 확인한다
        seen: set[str] = set()
        for match in CODE_PATH_TOKEN.finditer(document.read_text(encoding="utf-8")):
            reference, extension = match.group(1), "." + match.group(2).lower()
            first = reference.split("/", 1)[0]
            if extension not in LANGUAGES or reference in seen or not (root / first).exists():
                continue
            seen.add(reference)
            if not (root / reference).exists():
                violations.append({"kind": "dangling_doc_reference",
                                   "path": document.relative_to(root).as_posix(),
                                   "detail": f"문서가 없는 코드 경로를 인용함: {reference}"})
    return violations


def check(root: Path, files: Iterable[str] = (), base: str | None = None,
          module_map: str = DEFAULT_MAP, excluded: Iterable[str] = ()) -> dict:
    """
    역할: 모듈 맵과 코드 헤더, 문서의 코드 경로 인용을 대조해 하나의 보고서로 묶는다.

    입력:
        root: 프로젝트 루트
        files: 헤더를 확인할 프로젝트 기준 코드 파일 경로들
        base: 주면 이 Git 리비전 이후 추가·수정된 코드 파일도 함께 확인한다
        module_map: 프로젝트 기준 모듈 맵 문서 경로
        excluded: base 로 찾은 파일 중 제외할 경로 접두어들(생성·외부 코드)
    출력:
        status(passed/failed), 확인한 파일, 위반 목록을 담은 보고서 딕셔너리
    예외:
        ValueError: 파일 경로가 잘못된 경우
        RuntimeError: Git 명령이 실패한 경우
    """
    root = root.resolve(strict=True)
    excluded = tuple(prefix.rstrip("/") for prefix in excluded)
    map_path = (root / module_map).resolve()
    report = {"schema_version": 1, "module_map": module_map, "base_revision": base}
    if root not in map_path.parents or not map_path.is_file():
        return {**report, "status": "failed", "checked_files": [],
                "violations": [{"kind": "map_missing", "path": module_map,
                                "detail": "모듈 맵 문서가 없음. G2에서 먼저 만든다"}]}
    try:
        entries = parse_module_map(map_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return {**report, "status": "failed", "checked_files": [],
                "violations": [{"kind": "map_invalid", "path": module_map, "detail": str(exc)}]}
    targets = list(dict.fromkeys(files))
    if base:
        # 맵이 있는 문서 폴더의 HTML 등은 코드가 아니라 문서이므로 자동 수집에서 뺀다.
        documents = map_path.parent.relative_to(root).as_posix()
        targets = list(dict.fromkeys([*targets, *changed_code_files(root, base, (*excluded, documents))]))
    violations: list[dict] = []
    for relative in targets:
        violations.extend(header_violations(root, relative, entries))
    violations.extend(map_violations(root, entries))
    violations.extend(reference_violations(root, map_path.parent, map_path))
    return {**report, "status": "failed" if violations else "passed",
            "checked_files": targets, "violations": violations}


def main(argv: list[str] | None = None) -> int:
    """
    역할: 명령줄 인자를 받아 문서 동기화 검사를 실행하고 보고서를 출력한다.

    입력:
        argv: 명령줄 인자 목록(테스트용). None이면 sys.argv 사용
    출력:
        종료 코드. 통과 0, 불일치 1, 사용 오류 2
    """
    parser = argparse.ArgumentParser(description="Check that code headers and the module map agree.")
    parser.add_argument("--target-root", required=True, type=Path)
    parser.add_argument("--map", default=DEFAULT_MAP, help="project-relative module map document")
    parser.add_argument("--base", help="Git revision; also check code files added or modified since it")
    parser.add_argument("--exclude", action="append", default=[], help="path prefix to skip with --base")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)
    try:
        result = check(args.target_root, args.files, args.base, args.map, args.exclude)
    except (OSError, ValueError, RuntimeError) as exc:
        sys.stderr.write(f"harness_doc_sync: {exc}\n")
        return 2
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
