#!/usr/bin/env python3
"""Run portable harness fixtures against a replaceable Router adapter command."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from harness_validator import ContractError, validate_intake


class FixtureError(ValueError):
    """Raised when a fixture or adapter result violates the runner contract."""


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FixtureError(f"{path} must contain a JSON object")
    return value


def _contains(actual: list[Any], expected_items: list[Any]) -> bool:
    return all(item in actual for item in expected_items)


def _gate_map(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    gates = result.get("gate_results", [])
    if not isinstance(gates, list):
        raise FixtureError("adapter gate_results must be an array")
    return {g["gate_id"]: g for g in gates if isinstance(g, dict) and isinstance(g.get("gate_id"), str)}


def _compare(fixture: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    expected = fixture.get("expected")
    if not isinstance(expected, dict):
        raise FixtureError("fixture expected must be an object")
    failures: list[str] = []

    for key in ("status", "forward_revision"):
        if key in expected and actual.get(key) != expected[key]:
            failures.append(f"{key}: expected {expected[key]!r}, actual {actual.get(key)!r}")

    if "activated_skills_exact" in expected:
        wanted = expected["activated_skills_exact"]
        got = actual.get("activated_skills", [])
        if not isinstance(wanted, list) or sorted(got) != sorted(wanted):
            failures.append(f"activated_skills_exact: expected {sorted(wanted)!r}, actual {sorted(got)!r}")

    if "activated_skills_contains" in expected:
        wanted = expected["activated_skills_contains"]
        got = actual.get("activated_skills", [])
        if not isinstance(wanted, list) or not _contains(got, wanted):
            failures.append(f"activated_skills_contains: missing {sorted(set(wanted) - set(got))!r}")

    suppressed = {
        item.get("skill_id")
        for item in actual.get("suppressed_skills", [])
        if isinstance(item, dict)
    }
    wanted_suppressed = expected.get("suppressed_skills_contains", [])
    if not isinstance(wanted_suppressed, list) or not set(wanted_suppressed) <= suppressed:
        failures.append(f"suppressed_skills_contains: missing {sorted(set(wanted_suppressed) - suppressed)!r}")

    gates = _gate_map(actual)
    for gate_id, gate_expected in expected.get("gates", {}).items():
        gate = gates.get(gate_id)
        if gate is None:
            failures.append(f"gate {gate_id}: missing")
            continue
        for key in ("status",):
            if key in gate_expected and gate.get(key) != gate_expected[key]:
                failures.append(f"gate {gate_id}.{key}: expected {gate_expected[key]!r}, actual {gate.get(key)!r}")
        for key in ("activated_skills", "activated_branches"):
            contains_key = f"{key}_contains"
            if contains_key in gate_expected:
                wanted = gate_expected[contains_key]
                got = gate.get(key, [])
                if not _contains(got, wanted):
                    failures.append(f"gate {gate_id}.{contains_key}: missing {sorted(set(wanted) - set(got))!r}")

    feedback = actual.get("feedback_results", [])
    if not isinstance(feedback, list):
        failures.append("feedback_results must be an array")
        feedback = []
    for index, feedback_expected in enumerate(expected.get("feedback", [])):
        if index >= len(feedback):
            failures.append(f"feedback[{index}]: missing")
            continue
        item = feedback[index]
        for key in ("target_gate", "requires_user", "next_forward_revision"):
            if key in feedback_expected and item.get(key) != feedback_expected[key]:
                failures.append(
                    f"feedback[{index}].{key}: expected {feedback_expected[key]!r}, actual {item.get(key)!r}"
                )
        for key in ("invalidated_artifact_ids", "preserved_artifact_ids"):
            contains_key = f"{key}_contains"
            if contains_key in feedback_expected:
                wanted = feedback_expected[contains_key]
                got = item.get(key, [])
                if not _contains(got, wanted):
                    failures.append(f"feedback[{index}].{contains_key}: missing {sorted(set(wanted) - set(got))!r}")

    if "event_types_contains" in expected:
        actual_types = [event.get("type") for event in actual.get("events", []) if isinstance(event, dict)]
        wanted = expected["event_types_contains"]
        if not _contains(actual_types, wanted):
            failures.append(f"event_types_contains: missing {sorted(set(wanted) - set(actual_types))!r}")
    profile_expected = expected.get("execution_profile")
    if profile_expected is not None:
        profile = actual.get("execution_profile")
        if not isinstance(profile_expected, dict) or not isinstance(profile, dict):
            failures.append("execution_profile: expected and actual must be objects")
        else:
            for key in ("policy_id", "depth", "risk"):
                if key in profile_expected and profile.get(key) != profile_expected[key]:
                    failures.append(
                        f"execution_profile.{key}: expected {profile_expected[key]!r}, "
                        f"actual {profile.get(key)!r}"
                    )
            if "escalation_triggers_exact" in profile_expected:
                wanted = profile_expected["escalation_triggers_exact"]
                got = profile.get("escalation_triggers", [])
                if sorted(got) != sorted(wanted):
                    failures.append(
                        f"execution_profile.escalation_triggers_exact: expected {wanted!r}, actual {got!r}"
                    )
            gate_profiles = {
                item.get("gate_id"): item
                for item in profile.get("gate_profiles", [])
                if isinstance(item, dict)
            }
            for gate_id, reasoning in profile_expected.get("gate_reasoning", {}).items():
                if gate_profiles.get(gate_id, {}).get("reasoning") != reasoning:
                    failures.append(
                        f"execution_profile.{gate_id}.reasoning: expected {reasoning!r}, "
                        f"actual {gate_profiles.get(gate_id, {}).get('reasoning')!r}"
                    )
    return failures


def _compare_bootstrap(fixture: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    expected = fixture.get("expected")
    if not isinstance(expected, dict):
        raise FixtureError("bootstrap fixture expected must be an object")
    failures: list[str] = []
    wanted_statuses = expected.get("bootstrap_statuses", [])
    actual_statuses = actual.get("bootstrap_statuses", [])
    if wanted_statuses != actual_statuses:
        failures.append(
            f"bootstrap_statuses: expected {wanted_statuses!r}, actual {actual_statuses!r}"
        )
    final_files = actual.get("final_files", {})
    for name, content in expected.get("preserved_files", {}).items():
        if final_files.get(name) != content:
            failures.append(f"preserved file changed: {name}")
    for name in expected.get("files_present", []):
        if name not in final_files:
            failures.append(f"expected installed file is missing: {name}")
    return failures


def _invoke_adapter(
    command: list[str], context: dict[str, Any], artifact_path: Path, timeout_seconds: float
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="harness-fixture-") as temp_dir:
        input_path = Path(temp_dir) / "input.json"
        output_path = Path(temp_dir) / "output.json"
        with input_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(context, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        try:
            completed = subprocess.run(
                [*command, "--input", str(input_path), "--output", str(output_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise FixtureError(f"adapter timed out after {timeout_seconds:g} seconds") from exc
        if not output_path.exists():
            raise FixtureError(
                f"adapter produced no output (exit={completed.returncode}, stderr={completed.stderr.strip()!r})"
            )
        actual = _read_object(output_path)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        with artifact_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(actual, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        if completed.returncode != 0 and actual.get("status") != "failed":
            raise FixtureError(
                f"adapter exited {completed.returncode} without a failed result: {completed.stderr.strip()}"
            )
        return actual


def _invoke_bootstrap_fixture(
    command: list[str], fixture: dict[str, Any], artifact_path: Path, timeout_seconds: float
) -> dict[str, Any]:
    allowed_files = {"AGENTS.md", "CLAUDE.md"}
    setup_files = fixture.get("setup_files", {})
    setup_symlinks = fixture.get("setup_symlinks", [])
    attempts = fixture.get("attempts", [])
    modifications = fixture.get("modify_after_attempt", {})
    if not isinstance(setup_files, dict) or any(
        name not in allowed_files or not isinstance(content, str)
        for name, content in setup_files.items()
    ):
        raise FixtureError("bootstrap setup_files supports only managed text files")
    if not isinstance(setup_symlinks, list) or any(name not in allowed_files for name in setup_symlinks):
        raise FixtureError("bootstrap setup_symlinks supports only managed file names")
    if not isinstance(attempts, list) or not attempts:
        raise FixtureError("bootstrap fixture requires at least one attempt")
    if not isinstance(modifications, dict):
        raise FixtureError("modify_after_attempt must be an object")
    with tempfile.TemporaryDirectory(prefix="harness-bootstrap-fixture-") as temp_dir:
        target = Path(temp_dir) / "target"
        target.mkdir()
        for name, content in setup_files.items():
            with (target / name).open("w", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
        for name in setup_symlinks:
            source = target / f".{name}.source"
            source.write_text("symlink-owned\n", encoding="utf-8")
            (target / name).symlink_to(source.name)
        statuses: list[str] = []
        results: list[dict[str, Any]] = []
        for attempt_number, attempt in enumerate(attempts, start=1):
            if not isinstance(attempt, dict) or attempt.get("adapter") not in {"codex", "claude"}:
                raise FixtureError("each bootstrap attempt requires a Codex or Claude adapter")
            try:
                completed = subprocess.run(
                    [
                        *command,
                        "install",
                        "--target-root",
                        str(target),
                        "--adapter",
                        attempt["adapter"],
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                raise FixtureError(f"bootstrap timed out after {timeout_seconds:g} seconds") from exc
            try:
                result = json.loads(completed.stdout)
            except json.JSONDecodeError as exc:
                raise FixtureError(
                    f"bootstrap produced invalid JSON (exit={completed.returncode}): {completed.stderr.strip()}"
                ) from exc
            if not isinstance(result, dict):
                raise FixtureError("bootstrap result must be an object")
            statuses.append(str(result.get("status")))
            results.append(result)
            changes = modifications.get(str(attempt_number), {})
            if not isinstance(changes, dict) or any(
                name not in allowed_files or not isinstance(content, str)
                for name, content in changes.items()
            ):
                raise FixtureError("bootstrap modifications support only managed text files")
            for name, content in changes.items():
                path = target / name
                if path.is_symlink():
                    path.unlink()
                with path.open("w", encoding="utf-8", newline="\n") as stream:
                    stream.write(content)
        final_files: dict[str, str] = {}
        for relative in ("AGENTS.md", "CLAUDE.md", ".agents/harness.json"):
            path = target / relative
            if path.is_file() and not path.is_symlink():
                final_files[relative] = path.read_text(encoding="utf-8")
            elif path.is_symlink():
                final_files[relative] = "<symlink>"
        actual = {
            "schema_version": 1,
            "status": "completed",
            "bootstrap_statuses": statuses,
            "results": results,
            "final_files": final_files,
        }
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        with artifact_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(actual, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        return actual


def _discover(paths: list[Path], root: Path) -> list[Path]:
    if paths:
        discovered = paths
    else:
        discovered = sorted(root.rglob("*.json"))
    return [path for path in discovered if path.is_file()]


def main(argv: list[str] | None = None) -> int:
    harness_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixtures", nargs="*", type=Path)
    parser.add_argument("--fixture-root", type=Path, default=harness_root / "fixtures")
    parser.add_argument(
        "--adapter-command",
        default=f"{shlex.quote(sys.executable)} {shlex.quote(str(harness_root / 'scripts' / 'harness_router.py'))}",
        help="Command implementing --input/--output portable Router JSON contract",
    )
    parser.add_argument(
        "--bootstrap-command",
        default=f"{shlex.quote(sys.executable)} {shlex.quote(str(harness_root / 'scripts' / 'harness_bootstrap.py'))}",
        help="Command implementing the portable bootstrap install subcommand",
    )
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args(argv)
    command = shlex.split(args.adapter_command)
    bootstrap_command = shlex.split(args.bootstrap_command)
    if not command:
        parser.error("--adapter-command cannot be empty")
    if not bootstrap_command:
        parser.error("--bootstrap-command cannot be empty")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    fixtures = _discover(args.fixtures, args.fixture_root)
    if not fixtures:
        print("No fixture files found", file=sys.stderr)
        return 2

    if args.artifact_dir is None:
        artifact_dir = Path(tempfile.mkdtemp(prefix="harness-fixture-results-"))
    else:
        artifact_dir = args.artifact_dir

    passed = 0
    failed = 0
    for path in fixtures:
        fixture: dict[str, Any] = {}
        fixture_id = path.stem
        artifact_path = artifact_dir / f"{fixture_id}.actual.json"
        try:
            fixture = _read_object(path)
            fixture_id = str(fixture.get("id", fixture_id))
            context = fixture.get("context")
            if fixture.get("fixture_type", "router") == "bootstrap":
                actual = _invoke_bootstrap_fixture(
                    bootstrap_command, fixture, artifact_path, args.timeout_seconds
                )
                failures = _compare_bootstrap(fixture, actual)
            else:
                if not isinstance(context, dict):
                    raise FixtureError("fixture context must be an object")
                validate_intake(context, harness_root / "registry" / "taxonomy.json")
                actual = _invoke_adapter(command, context, artifact_path, args.timeout_seconds)
                failures = _compare(fixture, actual)
        except (FixtureError, ContractError, OSError) as exc:
            failures = [str(exc)]
            actual = {"status": "runner_error", "error": str(exc)}
        if failures:
            failed += 1
            print(f"{fixture_id} FAIL")
            print(f"  expected_state={fixture.get('expected', {})}")
            print(f"  actual_state={actual}")
            print(f"  artifact_path={artifact_path}")
            for failure in failures:
                print(f"  assertion={failure}")
        else:
            passed += 1
            print(f"{fixture_id} PASS")
            print(f"  expected_state={fixture['expected']}")
            if fixture.get("fixture_type", "router") == "bootstrap":
                print(f"  actual_state={{'bootstrap_statuses': {actual.get('bootstrap_statuses')!r}}}")
            else:
                print(
                    f"  actual_state={{'status': {actual.get('status')!r}, "
                    f"'forward_revision': {actual.get('forward_revision')!r}}}"
                )
            print(f"  artifact_path={artifact_path}")
    print(f"SUMMARY pass={passed} fail={failed} total={passed + failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
