#!/usr/bin/env python3
"""
모듈: 하네스 런타임 (scripts)
컴포넌트: 설치기
역할: 사용자 파일을 보존하면서 Codex·Claude의 프로젝트 진입 문서와 설정을 설치한다.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from harness_validator import (
    CLAUDE_ROLE_ASSETS,
    ContractError,
    JYDLC_LAUNCHERS,
    canonical_json_bytes,
    read_object,
    sha256_bytes,
    sha256_file,
    validate_config,
    write_object,
)


MAX_BOOTSTRAP_BYTES = 32768
MANAGED_TEMPLATES = {
    "AGENTS.md": "adapters/codex/AGENTS.md.tmpl",
    "CLAUDE.md": "adapters/claude/CLAUDE.md.tmpl",
}
JYDLC_TEMPLATE = "adapters/jydlc/SKILL.md"
CLAUDE_ROLE_SOURCE = "adapters/claude/agents"
CONFIG_PATH = ".agents/harness.json"
SOURCE_EXCLUDES = {
    ".git",
    "incoming",
    "state",
    ".DS_Store",
    "registry/active-skills.json",
    "registry/adapter-manifest.json",
}


class BootstrapError(ContractError):
    """Raised when target installation would be unsafe or non-idempotent."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_revision(harness_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(harness_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise BootstrapError(f"cannot resolve harness revision: {exc}") from exc
    revision = completed.stdout.strip()
    if not revision:
        raise BootstrapError("harness revision is empty")
    return revision


def _is_excluded(relative: str) -> bool:
    if relative.startswith((
        "tools/ros-mcp-server/.runtime/",
        "tools/ros-mcp-server/upstream/build/",
        "tools/ros-mcp-server/upstream/ros_mcp.egg-info/",
        "tools/ros-mcp-server/upstream/.venv/",
    )):
        return True
    parts = Path(relative).parts
    if any(part in {".DS_Store", "__pycache__", ".pytest_cache"} for part in parts):
        return True
    if parts and parts[0] in {".git", "incoming", "state"}:
        return True
    return relative in SOURCE_EXCLUDES or relative.startswith(".agents/state/")


def source_tree_hash(harness_root: Path) -> str:
    records: list[dict[str, str]] = []
    for path in sorted(harness_root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(harness_root).as_posix()
        if _is_excluded(relative):
            continue
        records.append({"path": relative, "sha256": sha256_file(path)})
    if not records:
        raise BootstrapError("harness source manifest is empty")
    return sha256_bytes(canonical_json_bytes(records))


def verify_source(harness_root: Path, registry_path: Path) -> str:
    """Enforce the existing local pins at execution boundaries, without network I/O."""
    registry = read_object(registry_path)
    policy = registry.get("integrity_policy", {})
    claimed = policy.get("manifest_sha256")
    unsigned = {**registry, "integrity_policy": {k: v for k, v in policy.items() if k != "manifest_sha256"}}
    if claimed != sha256_bytes(canonical_json_bytes(unsigned)):
        raise ContractError("active registry integrity mismatch")
    adapter = read_object(harness_root / "registry/adapter-manifest.json")
    if (policy.get("manifest_revision") != adapter.get("source_revision")
            or source_tree_hash(harness_root) != adapter.get("source_tree_sha256")):
        raise ContractError("harness source integrity mismatch; approved repin required")
    # The reviewed registry is pinned separately from the self-excluded source tree.
    if registry != read_object(harness_root / "registry/active-skills.json"):
        raise ContractError("execution requires the pinned active registry")
    return adapter["source_revision"]


def _template_content(harness_root: Path, relative: str, expected_sha256: str) -> str:
    """
    역할: 고정 해시가 일치하는 템플릿을 읽어 휴대 가능한 텍스트로 정규화한다.
    입력: harness_root는 원본 루트, relative는 템플릿 경로, expected_sha256은 승인된 해시다.
    출력: 설치할 LF 텍스트
    """
    path = harness_root / relative
    try:
        if path.resolve() != path or not path.is_file():
            raise BootstrapError(f"bootstrap template is not a regular file: {relative}")
        raw = path.read_bytes()
        if sha256_bytes(raw) != expected_sha256:
            raise BootstrapError(f"bootstrap template integrity mismatch: {relative}")
        content = raw.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise BootstrapError(f"cannot read bootstrap template {relative}: {exc}") from exc
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    encoded = content.encode("utf-8")
    if len(encoded) > MAX_BOOTSTRAP_BYTES:
        raise BootstrapError(f"bootstrap template exceeds {MAX_BOOTSTRAP_BYTES} bytes: {relative}")
    if "*** Begin Patch" in content or "*** Delete File" in content or "PIN_REQUIRED" in content:
        raise BootstrapError(f"bootstrap template contains a forbidden marker: {relative}")
    return content


def _verified_templates(harness: Path) -> tuple[dict[str, str], dict[str, str]]:
    """
    역할: 승인된 원본과 설치 파일 목록을 대조하고 검증한 템플릿만 렌더링한다.
    입력: harness는 확인된 원본 루트다.
    출력: 설치 대상별 텍스트와 원본 템플릿별 해시
    """
    verify_source(harness, harness / "registry/active-skills.json")
    adapter = read_object(harness / "registry/adapter-manifest.json")
    records = adapter.get("templates", [])
    if (not isinstance(records, list) or len(records) != len(MANAGED_TEMPLATES)
            or any(not isinstance(record, dict) or not isinstance(record.get("rendered_name"), str)
                   for record in records)):
        raise BootstrapError("bootstrap template manifest is invalid")
    by_name = {record.get("rendered_name"): record for record in records}
    rendered: dict[str, str] = {}
    source_hashes: dict[str, str] = {}
    for name, relative in MANAGED_TEMPLATES.items():
        record = by_name.get(name, {})
        if record.get("path") != relative or not isinstance(record.get("sha256"), str):
            raise BootstrapError(f"bootstrap template pin missing: {name}")
        source_hashes[relative] = record["sha256"]
        rendered[name] = _template_content(harness, relative, record["sha256"])
    launcher = adapter.get("manual_gate_skill")
    destinations = dict(zip(("codex", "claude"), JYDLC_LAUNCHERS))
    if (not isinstance(launcher, dict) or launcher.get("source") != JYDLC_TEMPLATE
            or launcher.get("destinations") != destinations or not isinstance(launcher.get("sha256"), str)):
        raise BootstrapError("jydlc launcher manifest is invalid")
    launcher_text = _template_content(harness, JYDLC_TEMPLATE, launcher["sha256"])
    rendered.update(dict.fromkeys(JYDLC_LAUNCHERS, launcher_text))
    native = adapter.get("claude_native_assets")
    roles = native.get("role_sha256") if isinstance(native, dict) else None
    role_paths = {name: Path(name).name for name in CLAUDE_ROLE_ASSETS}
    if (not isinstance(roles, dict) or native.get("agents") != CLAUDE_ROLE_SOURCE
            or set(roles) != set(role_paths.values())
            or any(not isinstance(value, str) for value in roles.values())):
        raise BootstrapError("Claude role asset manifest is invalid")
    for target_path, basename in role_paths.items():
        rendered[target_path] = _template_content(harness, f"{CLAUDE_ROLE_SOURCE}/{basename}", roles[basename])
    return rendered, source_hashes


def _render_config(
    target_mode: str,
    default_adapter: str,
    harness_root: Path,
    rendered: dict[str, str],
    template_hashes: dict[str, str],
) -> dict[str, Any]:
    """
    역할: 진입 문서와 스킬에 대한 해시를 이식 가능한 설치 설정으로 묶는다.
    입력: target_mode·default_adapter는 설치 모드, harness_root는 원본 위치,
          rendered는 렌더링된 파일, template_hashes는 검증된 템플릿 해시다.
    출력: 관리 파일 해시를 포함한 설정
    """
    revision = _git_revision(harness_root)
    tree_hash = read_object(harness_root / "registry/adapter-manifest.json")["source_tree_sha256"]
    template_records = []
    for name, relative in MANAGED_TEMPLATES.items():
        template_records.append(
            {
                "id": "codex.bootstrap" if name == "AGENTS.md" else "claude.bootstrap",
                "path": relative,
                "sha256": template_hashes[relative],
            }
        )
    registry_path = harness_root / "registry" / "active-skills.json"
    config: dict[str, Any] = {
        "schema_version": 1,
        "protocol_version": 1,
        "target_root_mode": target_mode,
        "harness_root_mode": "separate",
        "harness_source": {
            "kind": "local_or_bundled",
            "locator": "shared-harness",
            "ref": "shared-harness",
            "revision": revision,
            "sha256": tree_hash,
        },
        "templates": template_records,
        "adapters": ["codex", "claude"],
        "state_root": ".agents/state",
        "registry": {
            "resolution_order": ["project_reviewed", "shared_reviewed", "core_fallback"],
            "sources": [
                {
                    "scope": "shared_reviewed",
                    "path": "registry/active-skills.json",
                    "revision": revision,
                    "sha256": sha256_file(registry_path),
                }
            ],
        },
        "adapter_mapping": {
            "codex": {
                "loader": "native_instruction_scope",
                "scope": "harness_source",
                "skill_root": "skills",
                "fallback": "core_procedure",
            },
            "claude": {
                "loader": "native_or_plugin",
                "scope": "target_project",
                "skill_root": ".claude/skills",
                "fallback": "core_procedure",
            },
        },
        "enforcement": {
            "mode": "manual",
            "capability_probe": {
                "status": "recorded",
                "evidence_id": "EVD-BOOTSTRAP-MANUAL",
                "at": utc_now(),
            },
            "manual_guard": None,
        },
        "bootstrap": {
            "managed_files": list(rendered),
            "line_endings": "LF",
            "max_bytes": MAX_BOOTSTRAP_BYTES,
            "file_hashes": {
                name: sha256_bytes(content.encode("utf-8")) for name, content in rendered.items()
            },
        },
        "x-default-adapter": default_adapter,
    }
    config["bootstrap"]["config_hash"] = sha256_bytes(canonical_json_bytes(config))
    return config


def _config_identity(config: dict[str, Any]) -> bytes:
    """Return the stable managed contract, excluding observation time and self-hash."""

    normalized = json.loads(json.dumps(config))
    normalized.get("enforcement", {}).get("capability_probe", {}).pop("at", None)
    normalized.get("bootstrap", {}).pop("config_hash", None)
    return canonical_json_bytes(normalized)


def _atomic_bytes(path: Path, content: bytes, mode: int = 0o644) -> None:
    """
    역할: 기존 파일 모드를 보존하며 설치 파일을 원자적으로 교체한다.
    입력: path는 대상 경로, content는 파일 바이트, mode는 권한 비트다.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(str(temporary), str(path))
    except OSError as exc:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise BootstrapError(f"cannot write bootstrap file {path}: {exc}") from exc


def _create_journal(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    try:
        descriptor = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise BootstrapError("another or interrupted bootstrap transaction exists") from exc
    try:
        os.write(descriptor, data.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _record_journal(path: Path, value: dict[str, Any]) -> None:
    data = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(str(temporary), str(path))
    except OSError as exc:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise BootstrapError(f"cannot record bootstrap transaction: {exc}") from exc


def _validate_roots(target_root: Path, harness_root: Path) -> tuple[Path, Path]:
    try:
        target = target_root.resolve(strict=True)
        harness = harness_root.resolve(strict=True)
    except OSError as exc:
        raise BootstrapError(f"target or harness root cannot be resolved: {exc}") from exc
    if not target.is_dir() or not harness.is_dir():
        raise BootstrapError("target and harness roots must be existing directories")
    if target == harness or target in harness.parents or harness in target.parents:
        raise BootstrapError("target and harness source roots must be separate and non-nested")
    return target, harness


def _read_target_file(path: Path) -> tuple[bytes | None, int]:
    """
    역할: 심볼릭 링크를 거부하고 대상 파일의 원본 바이트와 권한을 읽는다.
    입력: path는 확인할 관리 파일의 절대 경로다.
    출력: 바이트와 권한 비트 또는 새 파일의 기본값
    """
    if any(candidate.is_symlink() for candidate in (path, *path.parents)):
        raise BootstrapError("symlink_not_managed")
    if not path.exists():
        return None, 0o644
    if not path.is_file():
        raise BootstrapError("regular_file_required")
    return path.read_bytes(), stat.S_IMODE(path.stat().st_mode)


def _upgrade_config(existing: dict[str, Any], rendered: dict[str, Any]) -> dict[str, Any]:
    """
    역할: 설치 관리 정보만 갱신하면서 프로젝트 설정과 로컬 레지스트리를 보존한다.
    입력: existing은 검증된 기존 설정, rendered는 새 설치 설정이다.
    출력: 프로젝트 설정을 보존한 업그레이드 설정
    """
    shared = rendered["registry"]["sources"][0]
    sources = existing["registry"]["sources"]
    updated_sources = [shared if value["scope"] == "shared_reviewed" else value for value in sources]
    if shared not in updated_sources:
        updated_sources.append(shared)
    value = {
        **existing,
        "harness_source": {
            **existing["harness_source"],
            "revision": rendered["harness_source"]["revision"],
            "sha256": rendered["harness_source"]["sha256"],
        },
        "templates": rendered["templates"],
        "registry": {**existing["registry"], "sources": updated_sources},
        "bootstrap": {**existing["bootstrap"], **rendered["bootstrap"]},
        "x-default-adapter": rendered["x-default-adapter"],
    }
    value["bootstrap"].pop("config_hash")
    value["bootstrap"]["config_hash"] = sha256_bytes(canonical_json_bytes(value))
    return value


def _write_installation(
    target: Path,
    journal_path: Path,
    pending: dict[str, bytes],
    before: dict[str, tuple[bytes | None, int]],
) -> None:
    """
    역할: 감지된 사용자 수정은 보존하며 관리 파일을 설치하고 실패 시 원본을 복원한다.
    입력: target은 프로젝트 루트, journal_path는 트랜잭션 기록 경로,
          pending은 설치할 파일, before는 사전 검사 시점의 바이트와 권한이다.
    """
    journal = {
        "schema_version": 1,
        "status": "prepared",
        "target_root": str(target),
        "planned_writes": list(pending),
        "created_at": utc_now(),
    }
    _create_journal(journal_path, journal)
    completed: list[str] = []
    try:
        for name, content in pending.items():
            path = target / name
            if _read_target_file(path) != before[name]:
                raise BootstrapError(f"managed file changed during installation: {name}")
            _atomic_bytes(path, content, before[name][1])
            completed.append(name)
        validate_config(read_object(target / CONFIG_PATH), target)
    except (ContractError, OSError) as exc:
        rolled_back: list[str] = []
        rollback_preserved: list[str] = []
        for name in reversed(completed):
            path = target / name
            original, mode = before[name]
            try:
                if _read_target_file(path) != (pending[name], mode):
                    rollback_preserved.append(name)
                    continue
                if original is None:
                    path.unlink()
                else:
                    _atomic_bytes(path, original, mode)
            except (ContractError, OSError):
                rollback_preserved.append(name)
            else:
                rolled_back.append(name)
        journal.update(
            status="interrupted",
            completed_writes=completed,
            rolled_back=rolled_back,
            rollback_preserved=rollback_preserved,
            error=str(exc),
        )
        _record_journal(journal_path, journal)
        raise BootstrapError(
            f"bootstrap interrupted after {completed}; journal preserved at {journal_path}: {exc}"
        ) from exc
    journal_path.unlink()


def install(
    target_root: Path, harness_root: Path, adapter: str | None, *, upgrade: bool = False
) -> dict[str, Any]:
    """
    역할: 두 플랫폼의 진입 파일을 설치하거나 검증된 기존 설치를 명시적으로 갱신한다.
    입력: target_root·harness_root는 대상과 원본 루트, adapter는 기본 어댑터,
          upgrade는 기존 관리 파일의 명시적 갱신 여부다.
    출력: 설치·갱신·멱등·충돌 결과
    """
    target, harness = _validate_roots(target_root, harness_root)
    rendered, template_hashes = _verified_templates(harness)
    config_path = target / CONFIG_PATH
    journal_path = target / ".agents" / "bootstrap-transaction.json"
    conflicts: list[dict[str, str]] = []
    before: dict[str, tuple[bytes | None, int]] = {}
    existing: dict[str, Any] | None = None
    try:
        before[CONFIG_PATH] = _read_target_file(config_path)
        raw_config = before[CONFIG_PATH][0]
        if raw_config is not None:
            existing = json.loads(raw_config)
            if not isinstance(existing, dict):
                raise BootstrapError("existing config must be an object")
            validate_config(existing, target)
        elif upgrade:
            raise BootstrapError("upgrade_requires_existing_managed_config")
    except (OSError, ValueError) as exc:
        conflicts.append({"path": CONFIG_PATH, "reason": f"invalid_existing_config: {exc}"})
        existing = None

    selected = adapter or (existing or {}).get("x-default-adapter", "codex")
    if selected not in ("codex", "claude"):
        raise BootstrapError("default adapter must be codex or claude")
    config = _render_config("explicit", selected, harness, rendered, template_hashes)
    if upgrade and existing is not None:
        config = _upgrade_config(existing, config)
    managed = existing["bootstrap"]["file_hashes"] if existing is not None else {}
    pending: dict[str, bytes] = {}
    for name, text in rendered.items():
        content = text.encode("utf-8")
        try:
            before[name] = _read_target_file(target / name)
        except (ContractError, OSError) as exc:
            conflicts.append({"path": name, "reason": str(exc)})
            continue
        current, _ = before[name]
        if current == content:
            continue
        if current is not None and (not upgrade or managed.get(name) != sha256_bytes(current)):
            conflicts.append({"path": name, "reason": "user_or_divergent_file_preserved"})
            continue
        pending[name] = content

    if existing is None or _config_identity(existing) != _config_identity(config):
        if not upgrade and existing is not None:
            conflicts.append({"path": CONFIG_PATH, "reason": "managed_config_requires_explicit_upgrade"})
        else:
            config_text = json.dumps(config, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            pending[CONFIG_PATH] = config_text.encode("utf-8")
    if journal_path.exists() or journal_path.is_symlink():
        conflicts.append({"path": ".agents/bootstrap-transaction.json", "reason": "unfinished_transaction"})
    if conflicts:
        return {
            "schema_version": 1,
            "status": "conflict",
            "target_root": str(target),
            "written": [],
            "preserved": [item["path"] for item in conflicts],
            "conflicts": conflicts,
        }
    if not pending:
        return {
            "schema_version": 1,
            "status": "idempotent",
            "target_root": str(target),
            "written": [],
            "preserved": [],
            "conflicts": [],
        }
    _write_installation(target, journal_path, pending, before)
    return {
        "schema_version": 1,
        "status": "upgraded" if upgrade else "installed",
        "target_root": str(target),
        "written": list(pending),
        "preserved": [],
        "conflicts": [],
        "config_hash": config["bootstrap"]["config_hash"],
    }


def check(target_root: Path, harness_root: Path | None = None) -> dict[str, Any]:
    """
    역할: 대상 설정을 읽고 원본 경로가 주어지면 실제 원본과 레지스트리 고정 정보도 확인한다.
    입력: target_root는 프로젝트 루트, harness_root는 선택적으로 지정하는 원본 루트다.
    출력: 검증 결과와 설정 경로
    """
    target = target_root.resolve(strict=True)
    config_path = target / CONFIG_PATH
    if config_path.resolve() != config_path:
        raise BootstrapError("symlink_not_managed")
    config = validate_config(read_object(config_path), target)
    if harness_root is not None:
        _, harness = _validate_roots(target, harness_root)
        registry_path = harness / "registry/active-skills.json"
        _verified_templates(harness)
        source_pin = read_object(harness / "registry/adapter-manifest.json")
        if config["harness_source"]["sha256"] != source_pin["source_tree_sha256"]:
            raise BootstrapError("project harness source pin does not match; use an approved upgrade")
        shared = next((value for value in config["registry"]["sources"] if value["scope"] == "shared_reviewed"), None)
        if (shared is None or shared["path"] != "registry/active-skills.json"
                or shared["sha256"] != sha256_file(registry_path)):
            raise BootstrapError("project active registry pin does not match; use an approved upgrade")
    return {
        "schema_version": 1,
        "status": "valid",
        "target_root": str(target),
        "config": str(config_path),
    }


def main(argv: Iterable[str] | None = None) -> int:
    """
    역할: 설치·업그레이드·설정 확인 요청을 실행하고 JSON 결과를 반환한다.
    입력: argv는 테스트에서 지정할 수 있는 명령행 인자다.
    출력: 명령의 종료 코드
    """
    default_harness_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    install_parser = subparsers.add_parser("install")
    install_parser.add_argument("--target-root", required=True, type=Path)
    install_parser.add_argument("--harness-root", type=Path, default=default_harness_root)
    install_parser.add_argument("--adapter", required=True, choices=["codex", "claude"])
    upgrade_parser = subparsers.add_parser("upgrade")
    upgrade_parser.add_argument("--target-root", required=True, type=Path)
    upgrade_parser.add_argument("--harness-root", type=Path, default=default_harness_root)
    upgrade_parser.add_argument("--adapter", choices=["codex", "claude"])
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--target-root", required=True, type=Path)
    check_parser.add_argument("--harness-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command in {"install", "upgrade"}:
            result = install(args.target_root, args.harness_root, args.adapter, upgrade=args.command == "upgrade")
        else:
            result = check(args.target_root, args.harness_root)
        exit_code = 3 if result["status"] == "conflict" else 0
    except (BootstrapError, ContractError, OSError) as exc:
        result = {"schema_version": 1, "status": "failed", "error": str(exc)}
        exit_code = 2
    if args.output:
        write_object(args.output, result)
    else:
        sys.stdout.write(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
