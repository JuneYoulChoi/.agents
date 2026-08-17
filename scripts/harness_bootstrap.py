#!/usr/bin/env python3
"""Conflict-safe local bootstrap installer for Codex and Claude target projects."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from harness_validator import (
    ContractError,
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
    parts = Path(relative).parts
    if any(part == ".DS_Store" for part in parts):
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


def _template_content(harness_root: Path, relative: str) -> str:
    path = harness_root / relative
    try:
        if path.is_symlink() or not path.is_file():
            raise BootstrapError(f"bootstrap template is not a regular file: {relative}")
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise BootstrapError(f"cannot read bootstrap template {relative}: {exc}") from exc
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    encoded = content.encode("utf-8")
    if len(encoded) > MAX_BOOTSTRAP_BYTES:
        raise BootstrapError(f"bootstrap template exceeds {MAX_BOOTSTRAP_BYTES} bytes: {relative}")
    if "*** Begin Patch" in content or "*** Delete File" in content or "PIN_REQUIRED" in content:
        raise BootstrapError(f"bootstrap template contains a forbidden marker: {relative}")
    return content


def _render_config(
    target_mode: str,
    default_adapter: str,
    harness_root: Path,
    rendered: dict[str, str],
) -> dict[str, Any]:
    revision = _git_revision(harness_root)
    tree_hash = source_tree_hash(harness_root)
    template_records = []
    for name, relative in MANAGED_TEMPLATES.items():
        template_records.append(
            {
                "id": "codex.bootstrap" if name == "AGENTS.md" else "claude.bootstrap",
                "path": relative,
                "sha256": sha256_file(harness_root / relative),
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
            "managed_files": ["AGENTS.md", "CLAUDE.md"],
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


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
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


def install(target_root: Path, harness_root: Path, adapter: str) -> dict[str, Any]:
    target, harness = _validate_roots(target_root, harness_root)
    rendered = {
        name: _template_content(harness, relative) for name, relative in MANAGED_TEMPLATES.items()
    }
    config = _render_config("explicit", adapter, harness, rendered)
    config_path = target / ".agents" / "harness.json"
    journal_path = target / ".agents" / "bootstrap-transaction.json"
    conflicts: list[dict[str, str]] = []
    writes: list[str] = []
    for name, expected in rendered.items():
        path = target / name
        if path.is_symlink():
            conflicts.append({"path": name, "reason": "symlink_not_managed"})
        elif path.exists():
            try:
                actual = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                conflicts.append({"path": name, "reason": "unreadable_existing_file"})
            else:
                if actual != expected:
                    conflicts.append({"path": name, "reason": "user_or_divergent_file_preserved"})
        else:
            writes.append(name)
    existing_config: dict[str, Any] | None = None
    if config_path.is_symlink():
        conflicts.append({"path": ".agents/harness.json", "reason": "symlink_not_managed"})
    elif config_path.exists():
        try:
            existing_config = read_object(config_path)
            validate_config(existing_config, target)
        except ContractError as exc:
            conflicts.append({"path": ".agents/harness.json", "reason": f"invalid_existing_config: {exc}"})
        else:
            if _config_identity(existing_config) != _config_identity(config):
                conflicts.append(
                    {"path": ".agents/harness.json", "reason": "managed_config_requires_explicit_upgrade"}
                )
    else:
        writes.append(".agents/harness.json")
    if journal_path.exists():
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
    if not writes:
        return {
            "schema_version": 1,
            "status": "idempotent",
            "target_root": str(target),
            "written": [],
            "preserved": [],
            "conflicts": [],
        }
    journal = {
        "schema_version": 1,
        "status": "prepared",
        "target_root": str(target),
        "planned_writes": writes,
        "created_at": utc_now(),
    }
    _create_journal(journal_path, journal)
    completed: list[str] = []
    try:
        for name in ("AGENTS.md", "CLAUDE.md"):
            if name in writes:
                _atomic_text(target / name, rendered[name])
                completed.append(name)
        if ".agents/harness.json" in writes:
            _atomic_text(
                config_path,
                json.dumps(config, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            )
            completed.append(".agents/harness.json")
        validate_config(read_object(config_path), target)
    except (BootstrapError, ContractError, OSError) as exc:
        expected_content = {
            **rendered,
            ".agents/harness.json": json.dumps(
                config, indent=2, sort_keys=True, ensure_ascii=False
            )
            + "\n",
        }
        rolled_back: list[str] = []
        rollback_preserved: list[str] = []
        for name in reversed(completed):
            path = target / name
            try:
                unchanged = (
                    not path.is_symlink()
                    and path.is_file()
                    and path.read_text(encoding="utf-8") == expected_content[name]
                )
            except (OSError, UnicodeError):
                unchanged = False
            if unchanged:
                path.unlink()
                rolled_back.append(name)
            else:
                rollback_preserved.append(name)
        journal["status"] = "interrupted"
        journal["completed_writes"] = completed
        journal["rolled_back"] = rolled_back
        journal["rollback_preserved"] = rollback_preserved
        journal["error"] = str(exc)
        _record_journal(journal_path, journal)
        raise BootstrapError(
            f"bootstrap interrupted after {completed}; journal preserved at {journal_path}: {exc}"
        ) from exc
    journal_path.unlink()
    return {
        "schema_version": 1,
        "status": "installed",
        "target_root": str(target),
        "written": completed,
        "preserved": [],
        "conflicts": [],
        "config_hash": config["bootstrap"]["config_hash"],
    }


def check(target_root: Path) -> dict[str, Any]:
    target = target_root.resolve(strict=True)
    config_path = target / ".agents" / "harness.json"
    validate_config(read_object(config_path), target)
    return {
        "schema_version": 1,
        "status": "valid",
        "target_root": str(target),
        "config": str(config_path),
    }


def main(argv: Iterable[str] | None = None) -> int:
    default_harness_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    install_parser = subparsers.add_parser("install")
    install_parser.add_argument("--target-root", required=True, type=Path)
    install_parser.add_argument("--harness-root", type=Path, default=default_harness_root)
    install_parser.add_argument("--adapter", required=True, choices=["codex", "claude"])
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--target-root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "install":
            result = install(args.target_root, args.harness_root, args.adapter)
        else:
            result = check(args.target_root)
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
