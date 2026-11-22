"""
모듈: 하네스 런타임 (scripts)
컴포넌트: 게이트 증거 검증기
역할: 승인된 요구사항과 시험 계획을 G6·G7의 관찰 및 대상 파일 증거에 연결한다.
"""

from __future__ import annotations

import math
import operator
from pathlib import Path
from typing import Any

from harness_validator import ContractError, _require_string, read_object, validate_evidence_files

COMPARISONS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "==": operator.eq}
METHODS = {"inspection", "test", "tdd", "measurement"}
MEASUREMENT_KINDS = {"performance_measurement", "deadline_measurement"}


def evidence_record(value: Any, target: Path, label: str) -> dict:
    """
    역할: 구조화된 산출물과 실제 근거 파일을 확인한다.
    입력: value는 산출물, target은 프로젝트, label은 진단 이름이다.
    출력: 확인된 산출물
    """
    if not isinstance(value, dict):
        raise ContractError(f"{label} record is required")
    validate_evidence_files(value.get("evidence"), target)
    return value


def requirements(value: Any, criteria: list[str], target: Path) -> dict[str, dict]:
    """
    역할: 수용 기준과 요구사항 ID 및 검증 방법을 일대일로 연결한다.
    입력: value는 요구사항 레코드, criteria는 승인된 수용 기준, target은 프로젝트다.
    출력: 요구사항 ID로 찾을 수 있는 요구사항
    """
    entries = evidence_record(value, target, "requirements").get("items")
    if not isinstance(entries, list) or len(entries) != len(criteria):
        raise ContractError("requirements must cover every intake criterion")
    by_id = {}
    covered = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ContractError("requirement entries must be objects")
        requirement_id = _require_string(entry, "id")
        criterion = _require_string(entry, "criterion")
        _require_string(entry, "method", METHODS)
        if not requirement_id.startswith(("REQ-", "QAS-")) or requirement_id in by_id:
            raise ContractError("requirements need unique REQ- or QAS- IDs")
        if criterion not in criteria or criterion in covered:
            raise ContractError("requirement criterion is unknown or repeated")
        by_id[requirement_id] = entry
        covered.add(criterion)
    return by_id


def finite(value: Any) -> bool:
    """
    역할: 측정값과 한계값에 사용 가능한 유한한 수인지 판단한다.
    입력: value는 측정값 또는 한계값이다.
    출력: 유한한 JSON 수인 경우 참
    """
    return type(value) in {float, int} and (type(value) is int or math.isfinite(value))


def test_plan(value: Any, by_requirement: dict[str, dict], required_kinds: set[str], target: Path,
              routed: dict | None = None) -> dict[str, dict]:
    """
    역할: 요구사항·판정 기준·도구·환경·라우팅된 검증 종류를 시험 계획에 연결한다.
    입력: value는 시험 계획, by_requirement는 요구사항, required_kinds는 필수 종류,
          target은 프로젝트, routed는 라우팅이 정한 도구 능력·환경이다.
    출력: 시험 ID로 찾을 수 있는 검사 계획
    """
    entries = evidence_record(value, target, "test_plan").get("checks")
    routed = routed or {}
    if not isinstance(entries, list) or not entries:
        raise ContractError("test_plan requires checks")
    by_id = {}
    covered = set()
    kinds = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ContractError("test plan checks must be objects")
        check_id = _require_string(entry, "id")
        requirement_id = _require_string(entry, "requirement_id")
        kind = _require_string(entry, "kind")
        method = _require_string(entry, "method", METHODS)
        for key in ("command", "tool_version", "environment"):
            _require_string(entry, key)
        if not check_id.startswith("TEST-") or check_id in by_id:
            raise ContractError("test plan needs unique TEST- IDs")
        if requirement_id not in by_requirement:
            raise ContractError("test plan check must link an accepted requirement")
        if kind in MEASUREMENT_KINDS and method != "measurement":
            raise ContractError("performance and deadline checks require a numeric measurement")
        if kind in {"behavior_test", "reliability_scenario", "control_verification", "operations_recovery"} and method == "inspection":
            raise ContractError("routed behavioral and operational checks require executable evidence")
        capabilities = routed.get("capabilities_by_check", {}).get(kind, [])
        if capabilities:
            available = entry.get("capabilities")
            if not isinstance(available, list) or any(not isinstance(item, str) for item in available) or not set(capabilities) <= set(available):
                raise ContractError("test plan must record the routed tool capabilities")
        environment = routed.get("environment")
        if environment and kind in {"deadline_measurement", "control_verification"} and entry["environment"] != environment:
            raise ContractError("test plan must use the routed execution environment")
        if method == "measurement":
            threshold = entry.get("threshold")
            if not isinstance(threshold, dict) or not finite(threshold.get("value")):
                raise ContractError("measurement checks need a numeric threshold")
            _require_string(threshold, "comparison", set(COMPARISONS))
            _require_string(threshold, "unit")
        if method == by_requirement[requirement_id]["method"]:
            covered.add(requirement_id)
        kinds.add(kind)
        by_id[check_id] = entry
    if covered != set(by_requirement) or not required_kinds <= kinds:
        raise ContractError("test plan must cover each requirement method and every routed check kind")
    return by_id


def trial(value: Any, planned: dict, target: Path, expected_exit: str) -> dict:
    """
    역할: 실제 실행 기록이 계획된 명령·도구·환경과 기대한 종료 상태에 일치하는지 확인한다.
    입력: value는 실행 기록, planned는 시험 계획, target은 프로젝트, expected_exit는 pass 또는 fail이다.
    출력: 확인된 실행 기록
    """
    run = evidence_record(value, target, "test run")
    for key in ("command", "tool_version", "environment"):
        if run.get(key) != planned[key]:
            raise ContractError(f"test run {key} must match its approved test plan")
    _require_string(run, "target_revision")
    code = run.get("exit_code")
    if type(code) is not int or (code == 0) != (expected_exit == "pass"):
        raise ContractError(f"test run is missing the expected {expected_exit} exit code")
    summary = validate_evidence_files([run.get("observation")], target)[0]
    observed = read_object(target / summary["path"])
    keys = {"command", "tool_version", "environment", "target_revision", "exit_code"}
    keys.update(key for key in ("value", "unit", "test_revision", "failed_assertion") if key in run)
    if any(key not in observed or observed[key] != run[key] for key in keys):
        raise ContractError("recorded run data does not match its observation file")
    return run


def verify_tdd(value: Any, planned: dict[str, dict], target: Path) -> None:
    """
    역할: 계획된 각 TDD 시험의 동일 시험 Red 및 Green 실행 근거를 확인한다.
    입력: value는 TDD 기록, planned는 시험 계획, target은 프로젝트다.
    """
    required = {test_id for test_id, test in planned.items() if test["method"] == "tdd"}
    if not required:
        return
    if not isinstance(value, dict) or set(value) != required:
        raise ContractError("TDD results must cover all planned TDD checks")
    for test_id, result in value.items():
        if not isinstance(result, dict):
            raise ContractError("TDD result must be an object")
        red = trial(result.get("red"), planned[test_id], target, "fail")
        green = trial(result.get("green"), planned[test_id], target, "pass")
        _require_string(red, "failed_assertion")
        if (_require_string(red, "test_revision") != _require_string(green, "test_revision")
                or red["target_revision"] == green["target_revision"]
                or red["evidence"] == green["evidence"]):
            raise ContractError("TDD requires distinct Red and Green observations of the same test")


def verify_results(value: Any, planned: dict[str, dict], authored_files: list[str], target: Path) -> None:
    """
    역할: 실행 결과와 현재 검증 대상 파일을 고정하고 측정값을 승인된 한계값으로 판정한다.
    입력: value는 검증 레코드, planned는 시험 계획, authored_files는 변경된 소스, target은 프로젝트다.
    """
    if not isinstance(value, dict):
        raise ContractError("verified_checks record is required")
    revision = _require_string(value, "target_revision")
    subjects = validate_evidence_files(value.get("subject_files"), target)
    if not set(authored_files) <= {item["path"] for item in subjects}:
        raise ContractError("verification snapshot must include all checked authored files")
    runs = value.get("runs")
    if not isinstance(runs, dict) or set(runs) != set(planned):
        raise ContractError("verification runs must cover every approved test plan check")
    for test_id, observation in runs.items():
        plan = planned[test_id]
        run = trial(observation, plan, target, "pass")
        if run["target_revision"] != revision:
            raise ContractError("test run revision does not match the verification snapshot")
        if plan["method"] == "measurement":
            limit = plan["threshold"]
            measured = run.get("value")
            if (not finite(measured) or run.get("unit") != limit["unit"]
                    or not COMPARISONS[limit["comparison"]](measured, limit["value"])):
                raise ContractError("measured value does not satisfy the approved threshold")
