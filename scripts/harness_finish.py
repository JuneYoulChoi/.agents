#!/usr/bin/env python3
"""
모듈: 하네스 런타임 (scripts)
컴포넌트: 마무리 검사
역할: 훅 없이 진행한 일반 변경을 끝낼 때 한 번 실행하는 검사. 한글 주석 검사와 문서 동기화
      검사를 함께 돌리고, 변경분이 큰 변경(컴포넌트·아키텍처 문서 변경)으로 보이면 임시 강제를
      요청하도록 알린다. 통과하면 한 줄만 출력해 토큰을 아낀다.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from harness_code_docs import check as check_code_docs
from harness_doc_sync import DEFAULT_MAP, changed_code_files, check as check_doc_sync, parse_module_map

EXIT_PASSED, EXIT_FAILED, EXIT_USAGE, EXIT_ESCALATE = 0, 1, 2, 3


def git_lines(root: Path, *arguments: str) -> list[str]:
    """
    역할: 대상 저장소에서 Git 명령을 실행해 출력 줄 목록을 얻는다.

    입력:
        root: Git 작업 트리인 대상 루트
        arguments: git 뒤에 붙일 인자들
    출력:
        비어 있지 않은 출력 줄 목록
    예외:
        RuntimeError: Git 명령이 실패한 경우
    """
    done = subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=off", *arguments],
                          capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(f"git {arguments[0]} failed: {done.stderr.strip()}")
    return [line for line in done.stdout.splitlines() if line]


def components_at(root: Path, revision: str, module_map: str) -> set[tuple[str, str]] | None:
    """
    역할: 기준 리비전 시점의 모듈 맵에서 (모듈, 컴포넌트) 집합을 읽는다.

    입력:
        root: Git 작업 트리인 대상 루트
        revision: Git 리비전
        module_map: 대상 기준 모듈 맵 경로
    출력:
        (모듈, 컴포넌트) 집합. 그 시점에 맵이 없거나 읽을 수 없으면 None
    """
    done = subprocess.run(["git", "-C", str(root), "show", f"{revision}:{module_map}"],
                          capture_output=True, text=True)
    if done.returncode != 0:
        return None
    try:
        return {(entry.module, entry.component) for entry in parse_module_map(done.stdout)}
    except ValueError:
        return None


def major_change_signals(root: Path, base: str, module_map: str) -> list[str]:
    """
    역할: 기준 리비전 이후 변경분에서 큰 변경의 신호를 찾는다.

    입력:
        root: Git 작업 트리인 대상 루트
        base: 비교할 Git 리비전
        module_map: 대상 기준 모듈 맵 경로
    출력:
        신호 설명 목록. 컴포넌트가 추가·삭제·이름 변경됐거나 맵 외의 아키텍처 문서가 바뀐 경우
    예외:
        RuntimeError: Git 명령이 실패한 경우
    """
    signals: list[str] = []
    before = components_at(root, base, module_map)
    map_path = root / module_map
    if before is not None and map_path.is_file():
        try:
            after = {(e.module, e.component) for e in parse_module_map(map_path.read_text(encoding="utf-8"))}
        except ValueError:
            after = before  # 형식 오류는 문서 동기화 검사가 따로 보고한다
        for module, component in sorted(after - before):
            signals.append(f"component_added: {module} / {component}")
        for module, component in sorted(before - after):
            signals.append(f"component_removed: {module} / {component}")
    documents = Path(module_map).parent.as_posix()
    changed = set(git_lines(root, "diff", "--name-only", base, "--", documents))
    changed.update(git_lines(root, "ls-files", "--others", "--exclude-standard", "--", documents))
    for path in sorted(changed - {module_map}):
        signals.append(f"architecture_document_changed: {path}")
    return signals


def enforced_task_active(root: Path) -> bool:
    """
    역할: 대상에 훅 강제 모드로 시작된 진행 중 작업이 있는지 확인한다(있으면 큰 변경도 정상 경로다).

    입력:
        root: 대상 프로젝트 루트
    출력:
        강제 모드의 active 작업이 하나라도 있으면 True
    """
    for state_file in sorted((root / ".agents" / "state").glob("*/state.json")):
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if (isinstance(state, dict) and state.get("status") == "active"
                and state.get("intake", {}).get("enforcement_mode") == "hook"):
            return True
    return False


def finish(root: Path, files: Iterable[str] = (), base: str | None = None, module_map: str = DEFAULT_MAP,
           excluded: Iterable[str] = (), acknowledged_major: str | None = None) -> dict:
    """
    역할: 일반 변경의 마무리 검사를 한 번에 수행한다.

    입력:
        root: 대상 프로젝트 루트
        files: 검사할 코드 파일 경로들(대상 기준). base 가 있으면 생략할 수 있다
        base: 변경분 기준 Git 리비전. 주면 바뀐 코드 파일·함수만 검사하고 큰 변경 신호도 찾는다
        module_map: 대상 기준 모듈 맵 경로
        excluded: 자동 수집에서 뺄 경로 접두어들(생성·외부 코드)
        acknowledged_major: 사용자가 임시 강제를 거절했을 때 그 사유. 주면 큰 변경 신호가 있어도 통과시킨다
    출력:
        status(passed/failed/escalate), 요약, 위반, 큰 변경 신호를 담은 보고서
    예외:
        ValueError: 검사할 파일을 정할 수 없거나 경로가 잘못된 경우
        RuntimeError: Git 명령이 실패한 경우
    """
    root = root.resolve(strict=True)
    excluded = tuple(prefix.rstrip("/") for prefix in excluded)
    targets = list(dict.fromkeys(files))
    if base:
        documents = Path(module_map).parent.as_posix()
        targets = list(dict.fromkeys([*targets, *changed_code_files(root, base, (*excluded, documents))]))
    elif not targets:
        raise ValueError("give the changed code files, or --base to find them")
    problems: list[dict] = []
    functions = 0
    if targets:
        code = check_code_docs(root, targets, base)
        for item in code["files"]:
            functions += item["checked_functions"]
            if item["header"] != "ok":
                problems.append({"kind": "file_header", "path": item["path"], "detail": item["header"]})
            for function in item["function_problems"]:
                problems.append({"kind": "function_comment", "path": f"{item['path']}:{function['line']}",
                                 "detail": f"{function['name']}: {', '.join(function['problems'])}"})
    problems.extend(check_doc_sync(root, targets, None, module_map, excluded)["violations"])
    signals = major_change_signals(root, base, module_map) if base else []
    if problems:
        status = "failed"
    elif signals and not acknowledged_major and not enforced_task_active(root):
        status = "escalate"
    else:
        status = "passed"
    report = {"schema_version": 1, "status": status, "code_files": len(targets), "functions_checked": functions}
    if problems:
        report["violations"] = problems
    if signals:
        report["major_change_signals"] = signals
        if status == "escalate":
            report["next"] = ("This looks like a major change: ask the user to approve temporary enforcement "
                              "and redo it as a hook-mode task, or rerun with --acknowledged-major <reason> "
                              "if the user declines.")
        elif acknowledged_major:
            report["acknowledged_major"] = acknowledged_major
    return report


def main(argv: list[str] | None = None) -> int:
    """
    역할: 명령줄 인자를 받아 마무리 검사를 실행하고 한 줄 JSON으로 결과를 출력한다.

    입력:
        argv: 명령줄 인자 목록(테스트용). None이면 sys.argv 사용
    출력:
        종료 코드. 통과 0, 위반 1, 사용 오류 2, 큰 변경으로 보여 사용자 확인 필요 3
    """
    parser = argparse.ArgumentParser(description="One finishing check for an advisory (no-hook) change.")
    parser.add_argument("--target-root", required=True, type=Path)
    parser.add_argument("--base", help="Git revision the change started from")
    parser.add_argument("--map", default=DEFAULT_MAP, help="project-relative module map document")
    parser.add_argument("--exclude", action="append", default=[], help="generated or vendored path prefix")
    parser.add_argument("--acknowledged-major", help="reason recorded when the user declined enforcement")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)
    try:
        report = finish(args.target_root, args.files, args.base, args.map, args.exclude, args.acknowledged_major)
    except (OSError, ValueError, RuntimeError) as exc:
        sys.stderr.write(f"harness_finish: {exc}\n")
        return EXIT_USAGE
    sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    return {"passed": EXIT_PASSED, "failed": EXIT_FAILED, "escalate": EXIT_ESCALATE}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
