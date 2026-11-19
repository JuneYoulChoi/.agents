#!/usr/bin/env python3
"""
모듈: 하네스 런타임 (scripts)
컴포넌트: 개요 스탬프
역할: HTML 개요가 설명하는 소스(plan 문서, 라우팅 매니페스트, 활성 스킬 목록)의 지문을
      계산해 개요에 기록하거나, 기록된 지문과 비교해 개요가 오래됐는지 알려준다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

OVERVIEW = "docs/harness/index.html"
META_NAME = "harness-overview-sources"
META_PATTERN = re.compile(r'<meta name="%s" content="([0-9a-f]*)">' % META_NAME)


def source_fingerprint(root: Path) -> str:
    """
    역할: 개요가 요약하는 소스들의 내용 지문을 계산한다.

    입력:
        root: 하네스 소스 루트
    출력:
        plan 문서들, 라우팅 매니페스트, 활성 스킬 ID 목록을 합친 SHA-256 16진 문자열
    """
    records = [(path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())
               for path in sorted([*(root / "plan").glob("*.md"), root / "registry/routing-gates.json"])]
    registry = json.loads((root / "registry/active-skills.json").read_text(encoding="utf-8"))
    records.append(("skills", ",".join(sorted(skill["id"] for skill in registry["skills"]))))
    return hashlib.sha256(json.dumps(records, ensure_ascii=False).encode("utf-8")).hexdigest()


def recorded_fingerprint(root: Path) -> str | None:
    """
    역할: 개요 HTML에 기록된 소스 지문을 읽는다.

    입력:
        root: 하네스 소스 루트
    출력:
        기록된 지문. 스탬프가 없으면 None
    """
    match = META_PATTERN.search((root / OVERVIEW).read_text(encoding="utf-8"))
    return match.group(1) if match else None


def is_current(root: Path) -> bool:
    """
    역할: 개요에 기록된 지문이 현재 소스와 같은지 판단한다.

    입력:
        root: 하네스 소스 루트
    출력:
        같으면 True. 스탬프가 없거나 다르면 False
    """
    return recorded_fingerprint(root) == source_fingerprint(root)


def write_stamp(root: Path) -> str:
    """
    역할: 개요를 검토·갱신한 뒤 현재 소스 지문을 개요 HTML에 기록한다.

    입력:
        root: 하네스 소스 루트
    출력:
        기록한 지문
    예외:
        ValueError: 개요에 <head>가 없어 스탬프를 넣을 수 없는 경우
    """
    path = root / OVERVIEW
    text = path.read_text(encoding="utf-8")
    fingerprint = source_fingerprint(root)
    tag = f'<meta name="{META_NAME}" content="{fingerprint}">'
    if META_PATTERN.search(text):
        text = META_PATTERN.sub(tag, text, count=1)
    elif "<head>" in text:
        text = text.replace("<head>", "<head>" + tag, 1)
    else:
        raise ValueError("overview has no <head> element")
    path.write_text(text, encoding="utf-8")
    return fingerprint


def main(argv: list[str] | None = None) -> int:
    """
    역할: 명령줄에서 개요 스탬프를 확인하거나 기록한다.

    입력:
        argv: 명령줄 인자 목록(테스트용). None이면 sys.argv 사용
    출력:
        종료 코드. 최신이거나 기록 성공 0, 오래됨 1, 사용 오류 2
    """
    parser = argparse.ArgumentParser(description="Check or record the overview's source fingerprint.")
    parser.add_argument("action", choices=["check", "write"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        if args.action == "write":
            sys.stdout.write(write_stamp(args.root) + "\n")
            return 0
        current = is_current(args.root)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"harness_overview: {exc}\n")
        return 2
    sys.stdout.write("current\n" if current else "stale: review docs/harness/index.html, then run write\n")
    return 0 if current else 1


if __name__ == "__main__":
    raise SystemExit(main())
