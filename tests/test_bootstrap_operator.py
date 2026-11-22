"""
모듈: 하네스 테스트 (tests)
컴포넌트: 설치기 회귀 테스트
역할: 명시적 설치 갱신, 사용자 파일 보존, 원본 무결성 확인을 검증한다.
"""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from harness_bootstrap import (  # noqa: E402
    BootstrapError,
    CLAUDE_ROLE_SOURCE,
    CONFIG_PATH,
    JYDLC_TEMPLATE,
    MANAGED_TEMPLATES,
    _atomic_bytes,
    check,
    install,
    source_tree_hash,
)
from harness_validator import (  # noqa: E402
    CLAUDE_ROLE_ASSETS,
    ContractError,
    JYDLC_LAUNCHERS,
    canonical_json_bytes,
    read_object,
    sha256_bytes,
    sha256_file,
    write_object,
)


class BootstrapOperatorTests(unittest.TestCase):
    def setUp(self):
        """역할: 독립된 임시 원본과 설치 대상을 만들고 검증용 원본 지문을 기록한다."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name).resolve()
        self.harness = base / "source"
        self.target = base / "target"
        self.target.mkdir()
        source_roles = [f"{CLAUDE_ROLE_SOURCE}/{Path(name).name}" for name in CLAUDE_ROLE_ASSETS]
        for relative in (*MANAGED_TEMPLATES.values(), JYDLC_TEMPLATE, *source_roles):
            destination = self.harness / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / relative).read_bytes())
        (self.harness / "registry").mkdir()
        self.manifest_path = self.harness / "registry/adapter-manifest.json"
        digest = source_tree_hash(self.harness)
        adapter = read_object(ROOT / "registry/adapter-manifest.json")
        adapter["source_revision"] = "source-fixture"
        adapter["source_tree_sha256"] = digest
        for item in adapter["templates"]:
            item["sha256"] = sha256_file(self.harness / item["path"])
        adapter["manual_gate_skill"]["sha256"] = sha256_file(self.harness / JYDLC_TEMPLATE)
        adapter["claude_native_assets"]["role_sha256"] = {
            Path(name).name: sha256_file(self.harness / name) for name in source_roles
        }
        write_object(self.manifest_path, adapter)
        pin = {"manifest_revision": adapter["source_revision"]}
        registry = {"integrity_policy": pin}
        pin["manifest_sha256"] = sha256_bytes(canonical_json_bytes(registry))
        write_object(self.harness / "registry/active-skills.json", registry)
        fixture_revision = patch("harness_bootstrap._git_revision", return_value="f" * 40)
        fixture_revision.start()
        self.addCleanup(fixture_revision.stop)

    def legacy_config(self, *, launchers=False):
        """
        역할: 사용자 관리 설정이 있는 이전 설치를 준비한다.
        입력: launchers는 과거 설치에 jydlc 런처가 이미 포함된 경우 True다.
        """
        self.assertEqual(install(self.target, self.harness, "claude")["status"], "installed")
        config_path = self.target / CONFIG_PATH
        config = read_object(config_path)
        config["x-local-preference"] = "keep"
        config["harness_source"]["sha256"] = "1" * 64
        removed = CLAUDE_ROLE_ASSETS if launchers else (*JYDLC_LAUNCHERS, *CLAUDE_ROLE_ASSETS)
        for name in removed:
            (self.target / name).unlink()
            config["bootstrap"]["managed_files"].remove(name)
            config["bootstrap"]["file_hashes"].pop(name)
        wrapper = self.target / "AGENTS.md"
        wrapper.write_text("Previously managed wrapper\n", encoding="utf-8")
        wrapper.chmod(0o600)
        config["bootstrap"]["file_hashes"]["AGENTS.md"] = sha256_file(wrapper)
        config["bootstrap"].pop("config_hash")
        config["bootstrap"]["config_hash"] = sha256_bytes(canonical_json_bytes(config))
        write_object(config_path, config)

    def test_explicit_upgrade_migrates_legacy_without_switching_default_adapter(self):
        """역할: 기존 설정의 사용자 필드와 권한을 보존하며 두 런처를 추가하는지 검증한다."""
        self.legacy_config()
        self.assertEqual(check(self.target)["status"], "valid")
        with self.assertRaisesRegex(BootstrapError, "project harness source pin does not match"):
            check(self.target, self.harness)
        self.assertEqual(install(self.target, self.harness, "claude")["status"], "conflict")
        self.assertEqual(install(self.target, self.harness, None, upgrade=True)["status"], "upgraded")
        self.assertEqual(check(self.target, self.harness)["status"], "valid")
        config = read_object(self.target / CONFIG_PATH)
        self.assertEqual(config["x-default-adapter"], "claude")
        self.assertEqual(config["x-local-preference"], "keep")
        for name in JYDLC_LAUNCHERS:
            self.assertEqual((self.target / name).read_bytes(), (self.harness / JYDLC_TEMPLATE).read_bytes())
        for name in CLAUDE_ROLE_ASSETS:
            self.assertEqual(
                (self.target / name).read_bytes(),
                (self.harness / CLAUDE_ROLE_SOURCE / Path(name).name).read_bytes(),
            )
        self.assertEqual((self.target / "AGENTS.md").stat().st_mode & 0o777, 0o600)
        self.assertEqual(install(self.target, self.harness, None, upgrade=True)["status"], "idempotent")

    def test_upgrade_adds_roles_to_prior_launcher_install(self):
        """역할: 기존 런처 설치에 검증된 Claude 역할 파일도 추가하는지 확인한다."""
        self.legacy_config(launchers=True)
        result = install(self.target, self.harness, None, upgrade=True)
        self.assertEqual(result["status"], "upgraded")
        self.assertTrue(set(CLAUDE_ROLE_ASSETS) <= set(result["written"]))
        self.assertFalse(set(JYDLC_LAUNCHERS) & set(result["written"]))
        self.assertEqual(check(self.target, self.harness)["status"], "valid")

    def test_handled_upgrade_failure_restores_previous_files(self):
        """역할: 설정을 쓰기 전에 실패하면 이전 원본을 복구하고 신규 파일을 제거하는지 검증한다."""
        self.legacy_config()
        wrapper = self.target / "AGENTS.md"
        original = wrapper.read_bytes()
        config_path = self.target / CONFIG_PATH
        config_before = config_path.read_bytes()

        def fail_saving_config(path, content, mode):
            """
            역할: 설정 파일에만 쓰기 오류를 주입하고 나머지는 실제 설치 쓰기를 수행한다.
            입력: path·content·mode는 쓰기 대상과 내용, 권한이다.
            """
            if path == config_path:
                raise BootstrapError("fixture write failure")
            _atomic_bytes(path, content, mode)

        with patch("harness_bootstrap._atomic_bytes", side_effect=fail_saving_config):
            with self.assertRaisesRegex(BootstrapError, "fixture write failure"):
                install(self.target, self.harness, None, upgrade=True)

        self.assertEqual(wrapper.read_bytes(), original)
        self.assertEqual(config_path.read_bytes(), config_before)
        self.assertTrue(all(not (self.target / name).exists() for name in (*JYDLC_LAUNCHERS, *CLAUDE_ROLE_ASSETS)))
        journal = read_object(self.target / ".agents/bootstrap-transaction.json")
        self.assertEqual(journal["status"], "interrupted")
        self.assertIn("AGENTS.md", journal["rolled_back"])

    def test_upgrade_refuses_edited_managed_wrapper(self):
        """역할: 이전 설정 해시와 다른 사용자 수정은 업그레이드에서도 보존하는지 검증한다."""
        self.legacy_config()
        wrapper = self.target / "AGENTS.md"
        wrapper.write_text("User's edit\n", encoding="utf-8")
        self.assertEqual(install(self.target, self.harness, None, upgrade=True)["status"], "conflict")
        self.assertEqual(wrapper.read_text(encoding="utf-8"), "User's edit\n")
        self.assertTrue(all(not (self.target / name).exists() for name in JYDLC_LAUNCHERS))

    def test_install_rejects_launcher_pin_mismatch_before_writing(self):
        """역할: 실행용 스킬 해시가 매니페스트와 다르면 설치 대상 쓰기를 거부하는지 검증한다."""
        manifest = read_object(self.manifest_path)
        manifest["manual_gate_skill"]["sha256"] = "0" * 64
        write_object(self.manifest_path, manifest)
        with self.assertRaisesRegex(BootstrapError, "template integrity mismatch"):
            install(self.target, self.harness, "codex")
        self.assertEqual(list(self.target.iterdir()), [])

    def test_workspace_detection_preserves_each_installed_launcher(self):
        """역할: 양쪽 런처의 시작 확인이 읽기 전용이며 설치된 런처의 변경을 감지하는지 검증한다."""
        self.assertEqual(install(self.target, self.harness, "codex")["status"], "installed")
        config = self.target / CONFIG_PATH
        before = config.read_bytes()
        self.assertEqual(check(self.target, self.harness)["status"], "valid")
        for name in JYDLC_LAUNCHERS:
            with self.subTest(launcher=name):
                launcher = self.target / name
                original = launcher.read_bytes()
                edited = original + b"\nUser edit\n"
                launcher.write_bytes(edited)
                with self.assertRaisesRegex(ContractError, "managed file hash mismatch"):
                    check(self.target, self.harness)
                self.assertEqual(launcher.read_bytes(), edited)
                launcher.write_bytes(original)
        self.assertEqual(config.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
