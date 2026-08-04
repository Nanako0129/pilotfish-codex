"""Offline native installer tests; all homes are temporary."""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
import tomllib
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
import install as installer  # noqa: E402
import stage_smoke_home  # noqa: E402
from install import InstallAbort, install, merge_config_text, parse_codex_version  # noqa: E402


class NativeConfigMergeTests(unittest.TestCase):
    def test_empty_config_renders_exact_native_table(self) -> None:
        rendered, _ = merge_config_text("")
        data = tomllib.loads(rendered)
        self.assertEqual(data["model"], "gpt-5.6-luna")
        self.assertEqual(data["model_reasoning_effort"], "medium")
        self.assertEqual(data["plan_mode_reasoning_effort"], "xhigh")
        self.assertEqual(data["agents"], {"enabled": True, "max_concurrent_threads_per_session": 3})
        self.assertNotIn("multi_agent_v2", data.get("features", {}))

    def test_existing_root_model_and_effort_are_preserved(self) -> None:
        rendered, _ = merge_config_text(
            'model = "custom-model"\n'
            'model_reasoning_effort = "high"\n'
            'plan_mode_reasoning_effort = "max"\n'
        )
        data = tomllib.loads(rendered)
        self.assertEqual(data["model"], "custom-model")
        self.assertEqual(data["model_reasoning_effort"], "high")
        self.assertEqual(data["plan_mode_reasoning_effort"], "max")

    def test_legacy_v2_requires_provenance_and_disabled_aborts(self) -> None:
        old = "[features.multi_agent_v2]\nenabled = true\nmax_concurrent_threads_per_session = 4\n"
        with self.assertRaisesRegex(InstallAbort, "provenance"):
            merge_config_text(old)
        migrated, _ = merge_config_text(old, migration_proven=True)
        self.assertEqual(tomllib.loads(migrated)["agents"], {"enabled": True, "max_concurrent_threads_per_session": 3})
        for text in ("[features]\nmulti_agent_v2 = false\n", "[features.multi_agent_v2]\nenabled = false\n", "[features]\nmulti_agent_v2 = true\n"):
            with self.subTest(text=text):
                with self.assertRaises(InstallAbort):
                    merge_config_text(text)

    def test_normalizes_child_domain_and_rejects_conflicts(self) -> None:
        for value in (0, 8, 9, '"4"'):
            with self.subTest(value=value):
                with self.assertRaises(InstallAbort):
                    merge_config_text(f"[agents]\nenabled = true\nmax_concurrent_threads_per_session = {value}\n")
        with self.assertRaises(InstallAbort):
            merge_config_text("[agents]\nenabled = true\nmax_concurrent_threads_per_session = 2\n")

    def test_agents_table_is_exact_and_rejects_legacy_or_unknown_keys(self) -> None:
        for text in (
            "[agents]\nenabled = true\nmax_concurrent_threads_per_session = 3\nmax_depth = 1\n",
            "[agents]\nenabled = true\nmax_concurrent_threads_per_session = 3\ncustom = true\n",
            "[agents]\nenabled = false\nmax_concurrent_threads_per_session = 3\n",
            "[agents]\nenabled = \"true\"\nmax_concurrent_threads_per_session = 3\n",
        ):
            with self.subTest(text=text):
                with self.assertRaises(InstallAbort):
                    merge_config_text(text)

    def test_unowned_legacy_key_is_preserved(self) -> None:
        original = "custom = true\n"
        rendered, _ = merge_config_text(original)
        self.assertTrue(tomllib.loads(rendered)["custom"])

    def test_owned_legacy_key_is_removed(self) -> None:
        original = "[features]\nmulti_agent = true\n"
        rendered, _ = merge_config_text(original, owned_legacy=frozenset({"features.multi_agent"}))
        data = tomllib.loads(rendered)
        self.assertNotIn("multi_agent", data["features"])
        self.assertEqual(data["agents"]["max_concurrent_threads_per_session"], 3)

    def test_exact_version_parser(self) -> None:
        self.assertEqual(parse_codex_version("codex 0.146.0"), (0, 146, 0))
        for output in ("0.146.0-beta", "0.146.0 0.146.1", "none"):
            with self.subTest(output=output):
                self.assertIsNone(parse_codex_version(output))


class NativeInstallTests(unittest.TestCase):
    def run_install(self, home: Path, **kwargs: object) -> int:
        return install(source_root=ROOT, codex_home=home, dry_run=False, check_codex=False, **kwargs)

    def _legacy_home(self, home: Path) -> Path:
        self.assertEqual(self.run_install(home), 0)
        config = home / "config.toml"
        legacy = (
            'model = "gpt-5.6-luna"\nmodel_reasoning_effort = "medium"\n'
            'plan_mode_reasoning_effort = "xhigh"\n\n'
            '[features.multi_agent_v2]\nenabled = true\n'
            'max_concurrent_threads_per_session = 4\n'
        )
        config.write_text(legacy)
        state_path = home.with_name(f"{home.name}.pilotfish-install-state.json")
        state = json.loads(state_path.read_text())
        state["target_fingerprints"]["config.toml"] = hashlib.sha256(legacy.encode()).hexdigest()
        state["original_targets"]["config.toml"] = {
            "present": True,
            "sha256": hashlib.sha256(legacy.encode()).hexdigest(),
            "bytes_b64": installer.base64.b64encode(legacy.encode()).decode(),
        }
        state_path.write_text(json.dumps(state, sort_keys=True) + "\n")
        return state_path

    def test_exact_legacy_v2_migration_and_dry_run_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            state_path = self._legacy_home(home)
            before = (home / "config.toml").read_bytes()
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(install(source_root=ROOT, codex_home=home, dry_run=True, check_codex=False), 0)
            self.assertIn("would change primary: config.toml", output.getvalue())
            self.assertIn(f"allowed transaction artifact: {state_path.name}.pending", output.getvalue())
            self.assertEqual((home / "config.toml").read_bytes(), before)
            self.assertEqual(self.run_install(home), 0)
            data = tomllib.loads((home / "config.toml").read_text())
            self.assertEqual(data["agents"], {"enabled": True, "max_concurrent_threads_per_session": 3})

    def test_legacy_v2_migration_allows_canonical_security_reviewer_upgrade(self) -> None:
        previous = ROOT / "install" / "previous" / "v1.3.0" / "agents" / "security-reviewer.toml"
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            state_path = self._legacy_home(home)
            target = home / "agents" / "security-reviewer.toml"
            target.write_bytes(previous.read_bytes())
            state = json.loads(state_path.read_text())
            state["target_fingerprints"]["agents/security-reviewer.toml"] = hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            state_path.write_text(json.dumps(state, sort_keys=True) + "\n")

            self.assertEqual(self.run_install(home), 0)
            self.assertEqual(
                target.read_bytes(),
                (ROOT / "templates" / "agents" / "security-reviewer.toml").read_bytes(),
            )

    def test_legacy_v2_extra_state_entry_aborts_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            state_path = self._legacy_home(home)
            state = json.loads(state_path.read_text())
            state["target_fingerprints"]["extra.toml"] = "0" * 64
            state_path.write_text(json.dumps(state))
            before = (home / "config.toml").read_bytes()
            with self.assertRaisesRegex(InstallAbort, "manifest"):
                self.run_install(home)
            self.assertEqual((home / "config.toml").read_bytes(), before)

    def test_install_is_atomic_idempotent_and_records_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            self.assertEqual(self.run_install(home), 0)
            config = tomllib.loads((home / "config.toml").read_text())
            self.assertEqual(config["agents"]["max_concurrent_threads_per_session"], 3)
            self.assertEqual({p.stem for p in (home / "agents").glob("*.toml")}, {"executor", "mech-executor", "plan-verifier", "scout", "security-executor", "security-reviewer", "verifier"})
            state = home.with_name(f"{home.name}.pilotfish-install-state.json")
            recorded = json.loads(state.read_text())
            self.assertEqual(recorded["status"], "committed")
            self.assertIn("config.toml", recorded["target_fingerprints"])
            self.assertEqual(
                (home / "hooks.json").read_bytes(),
                (ROOT / "templates" / "hooks.json").read_bytes(),
            )
            self.assertEqual(
                (home / "hooks" / "pilotfish_autoroute_gate.py").read_bytes(),
                (ROOT / "hooks" / "pilotfish_autoroute_gate.py").read_bytes(),
            )
            self.assertIn("hooks.json", recorded["target_fingerprints"])
            self.assertIn(
                "hooks/pilotfish_autoroute_gate.py",
                recorded["target_fingerprints"],
            )
            self.assertIn("config.toml", recorded["original_targets"])
            first = {p.relative_to(home): p.read_bytes() for p in home.rglob("*") if p.is_file()}
            self.assertEqual(self.run_install(home), 0)
            second = {p.relative_to(home): p.read_bytes() for p in home.rglob("*") if p.is_file()}
            self.assertEqual(first, second)

    def test_codex_hooks_state_append_is_accepted_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            self.assertEqual(self.run_install(home), 0)
            config = home / "config.toml"
            config.write_bytes(
                config.read_bytes()
                + b'\n[hooks.state]\npilotfish_autoroute_gate = "trusted"\n'
            )
            expected = config.read_bytes()

            self.assertEqual(self.run_install(home), 0)
            self.assertEqual(self.run_install(home), 0)
            self.assertEqual(config.read_bytes(), expected)

    def test_owned_routing_drift_aborts_without_installer_writes(self) -> None:
        mutations = {
            "model": lambda text: text.replace(
                'model = "gpt-5.6-luna"', 'model = "unapproved-model"'
            ),
            "agents": lambda text: text.replace(
                "max_concurrent_threads_per_session = 3",
                "max_concurrent_threads_per_session = 2",
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                home = Path(directory) / "home"
                self.assertEqual(self.run_install(home), 0)
                config = home / "config.toml"
                config.write_text(mutate(config.read_text()))
                before = {
                    path.relative_to(home): path.read_bytes()
                    for path in home.rglob("*")
                    if path.is_file()
                }

                with self.assertRaisesRegex(InstallAbort, "routing projection"):
                    self.run_install(home)

                after = {
                    path.relative_to(home): path.read_bytes()
                    for path in home.rglob("*")
                    if path.is_file()
                }
                self.assertEqual(after, before)
                self.assertFalse(
                    home.with_name(f"{home.name}.pilotfish-install-state.json.pending").exists()
                )

    def test_config_snapshot_change_during_state_validation_aborts_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            self.assertEqual(self.run_install(home), 0)
            config = home / "config.toml"
            before = {
                path.relative_to(home): path.read_bytes()
                for path in home.rglob("*")
                if path.is_file() and path != config
            }
            original_load_state = installer._load_state

            def load_state_with_race(target_home: Path) -> dict | None:
                state = original_load_state(target_home)
                config.write_bytes(config.read_bytes() + b"\n[hooks.state]\nrace = true\n")
                return state

            with mock.patch.object(installer, "_load_state", side_effect=load_state_with_race):
                with self.assertRaisesRegex(InstallAbort, "changed during state validation"):
                    self.run_install(home)

            after = {
                path.relative_to(home): path.read_bytes()
                for path in home.rglob("*")
                if path.is_file() and path != config
            }
            self.assertEqual(after, before)
            self.assertFalse(
                home.with_name(f"{home.name}.pilotfish-install-state.json.pending").exists()
            )

    def test_legacy_v2_provenance_allows_hooks_state_but_rejects_legacy_deviation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            self._legacy_home(home)
            config = home / "config.toml"
            config.write_bytes(config.read_bytes() + b"\n[hooks.state]\nlegacy = true\n")
            self.assertEqual(self.run_install(home), 0)
            migrated = tomllib.loads(config.read_text())
            self.assertEqual(migrated["hooks"]["state"], {"legacy": True})
            self.assertNotIn("multi_agent_v2", migrated.get("features", {}))

            config.write_bytes(
                config.read_bytes()
                + b"\n[features.multi_agent_v2]\nenabled = true\n"
                + b"max_concurrent_threads_per_session = 5\n"
            )
            before = config.read_bytes()
            with self.assertRaisesRegex(InstallAbort, "routing projection"):
                self.run_install(home)
            self.assertEqual(config.read_bytes(), before)

    def test_unowned_hooks_json_collision_aborts_before_any_primary_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            home.mkdir()
            hooks = home / "hooks.json"
            hooks.write_bytes(b'{"hooks":{"Stop":[]}}\n')

            with self.assertRaisesRegex(InstallAbort, "unowned hooks.json collision"):
                self.run_install(home)

            self.assertEqual(hooks.read_bytes(), b'{"hooks":{"Stop":[]}}\n')
            self.assertFalse((home / "config.toml").exists())
            self.assertFalse((home / "agents").exists())
            self.assertFalse((home / "AGENTS.md").exists())
            self.assertFalse(
                home.with_name(f"{home.name}.pilotfish-install-state.json").exists()
            )

    def test_committed_state_binds_registration_and_hook_script_bytes(self) -> None:
        for relative in (
            Path("hooks.json"),
            Path("hooks/pilotfish_autoroute_gate.py"),
        ):
            with self.subTest(relative=relative.as_posix()), tempfile.TemporaryDirectory() as directory:
                home = Path(directory) / "home"
                self.assertEqual(self.run_install(home), 0)
                target = home / relative
                target.write_bytes(target.read_bytes() + b"\n")

                with self.assertRaisesRegex(InstallAbort, "committed install state is stale"):
                    self.run_install(home)

    def test_staged_layout_requires_exact_owned_hook_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            self.assertEqual(self.run_install(home), 0)
            self.assertIsNone(
                stage_smoke_home.explicit_layout_error(
                    home,
                    allow_rollback_backups=True,
                    project_active_root=True,
                )
            )
            projection = stage_smoke_home._required_input_projection(home.resolve())
            self.assertEqual(len(projection), 6)

            extra = home / "hooks" / "unowned.py"
            extra.write_text("pass\n")
            self.assertIn(
                "unapproved entry",
                stage_smoke_home.explicit_layout_error(
                    home,
                    allow_rollback_backups=True,
                    project_active_root=True,
                ),
            )

    def test_pending_state_and_role_drift_abort_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            home.mkdir()
            pending = home.with_name(f"{home.name}.pilotfish-install-state.json.pending")
            pending.write_text("{}")
            with self.assertRaises(InstallAbort):
                self.run_install(home)

            pending.unlink()
            agents = home / "agents"; agents.mkdir()
            (agents / "scout.toml").write_text('name = "scout"\n')
            with self.assertRaises(InstallAbort):
                self.run_install(home)

    def test_unowned_agents_key_aborts_before_any_target_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            home.mkdir()
            config = home / "config.toml"
            original = '[custom]\nkeep = "yes"\n\n[agents]\nenabled = true\nmax_concurrent_threads_per_session = 3\nmax_depth = 1\n'
            config.write_text(original)
            with self.assertRaisesRegex(InstallAbort, "agents table"):
                self.run_install(home)
            self.assertEqual(config.read_text(), original)
            self.assertFalse((home / "agents").exists())
            self.assertFalse((home / "AGENTS.md").exists())
            self.assertFalse(home.with_name(f"{home.name}.pilotfish-install-state.json").exists())

    def test_release_pinned_v130_roles_upgrade_but_custom_bytes_abort(self) -> None:
        previous = ROOT / "install" / "previous" / "v1.3.0" / "agents"
        expected = installer.CANONICAL_ROLE_UPGRADE_DIGESTS
        for role in ("plan-verifier", "security-reviewer"):
            payload = (previous / f"{role}.toml").read_bytes()
            self.assertIn(hashlib.sha256(payload).hexdigest(), expected[role])

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            agents = home / "agents"
            agents.mkdir(parents=True)
            for role in installer.ROLES:
                source = ROOT / "templates" / "agents" / f"{role}.toml"
                prior = previous / f"{role}.toml"
                (agents / f"{role}.toml").write_bytes(
                    prior.read_bytes() if prior.exists() else source.read_bytes()
                )

            self.assertEqual(self.run_install(home), 0)
            for role in ("plan-verifier", "security-reviewer"):
                self.assertEqual(
                    (agents / f"{role}.toml").read_bytes(),
                    (ROOT / "templates" / "agents" / f"{role}.toml").read_bytes(),
                )

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            agents = home / "agents"
            agents.mkdir(parents=True)
            payload = (previous / "plan-verifier.toml").read_bytes() + b"# custom\n"
            (agents / "plan-verifier.toml").write_bytes(payload)
            with self.assertRaisesRegex(InstallAbort, "installed_role_drift"):
                self.run_install(home)

    def test_dry_run_names_canonical_role_upgrades_without_writes(self) -> None:
        previous = ROOT / "install" / "previous" / "v1.3.0" / "agents"
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            agents = home / "agents"
            agents.mkdir(parents=True)
            for role in installer.ROLES:
                source = ROOT / "templates" / "agents" / f"{role}.toml"
                prior = previous / f"{role}.toml"
                (agents / f"{role}.toml").write_bytes(
                    prior.read_bytes() if prior.exists() else source.read_bytes()
                )
            before = {
                path.relative_to(home): path.read_bytes()
                for path in home.rglob("*")
                if path.is_file()
            }
            state = home.with_name(f"{home.name}.pilotfish-install-state.json")
            pending = state.with_suffix(".json.pending")
            self.assertFalse(state.exists())
            self.assertFalse(pending.exists())

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = install(
                    source_root=ROOT, codex_home=home, dry_run=True, check_codex=False
                )
            stdout = buffer.getvalue()

            self.assertEqual(code, 0)
            self.assertIn("note: upgraded canonical role plan-verifier", stdout)
            self.assertIn("note: upgraded canonical role security-reviewer", stdout)
            self.assertIn("would change", stdout)
            after = {
                path.relative_to(home): path.read_bytes()
                for path in home.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, before)
            self.assertFalse(state.exists())
            self.assertFalse(pending.exists())

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            agents = home / "agents"
            agents.mkdir(parents=True)
            (agents / "plan-verifier.toml").write_bytes(
                (previous / "plan-verifier.toml").read_bytes() + b"# custom\n"
            )
            with self.assertRaisesRegex(InstallAbort, "installed_role_drift"):
                install(source_root=ROOT, codex_home=home, dry_run=True, check_codex=False)

    def test_release_pinned_v131_roles_upgrade_but_custom_bytes_abort(self) -> None:
        previous = ROOT / "install" / "previous" / "v1.3.1" / "agents"
        for role in ("plan-verifier", "verifier"):
            digest = hashlib.sha256((previous / f"{role}.toml").read_bytes()).hexdigest()
            self.assertIn(digest, installer.CANONICAL_ROLE_UPGRADE_DIGESTS[role])

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            agents = home / "agents"
            agents.mkdir(parents=True)
            for role in installer.ROLES:
                source = ROOT / "templates" / "agents" / f"{role}.toml"
                (agents / f"{role}.toml").write_bytes(source.read_bytes())
            for role in ("plan-verifier", "verifier"):
                (agents / f"{role}.toml").write_bytes(
                    (previous / f"{role}.toml").read_bytes()
                )

            self.assertEqual(self.run_install(home), 0)
            for role in ("plan-verifier", "verifier"):
                self.assertEqual(
                    (agents / f"{role}.toml").read_bytes(),
                    (ROOT / "templates" / "agents" / f"{role}.toml").read_bytes(),
                )

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            agents = home / "agents"
            agents.mkdir(parents=True)
            (agents / "plan-verifier.toml").write_bytes(
                (previous / "plan-verifier.toml").read_bytes() + b"# custom\n"
            )
            with self.assertRaisesRegex(InstallAbort, "installed_role_drift"):
                self.run_install(home)

        runbook = (ROOT / "install" / "AGENT-INSTALL.md").read_text()
        self.assertIn(
            "released canonical\nv1.3.1 `plan-verifier` and `verifier`",
            runbook,
        )
        self.assertIn("released canonical v1.3.3 payloads", runbook)

    def test_release_pinned_v132_security_executor_upgrades(self) -> None:
        previous = (
            ROOT
            / "install"
            / "previous"
            / "v1.3.2"
            / "agents"
            / "security-executor.toml"
        )
        digest = hashlib.sha256(previous.read_bytes()).hexdigest()
        self.assertIn(
            digest,
            installer.CANONICAL_ROLE_UPGRADE_DIGESTS["security-executor"],
        )

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            agents = home / "agents"
            agents.mkdir(parents=True)
            for role in installer.ROLES:
                source = ROOT / "templates" / "agents" / f"{role}.toml"
                (agents / f"{role}.toml").write_bytes(source.read_bytes())
            (agents / "security-executor.toml").write_bytes(previous.read_bytes())

            self.assertEqual(self.run_install(home), 0)
            installed = agents / "security-executor.toml"
            self.assertEqual(
                installed.read_bytes(),
                (ROOT / "templates" / "agents" / "security-executor.toml").read_bytes(),
            )
            state = json.loads(
                home.with_name(f"{home.name}.pilotfish-install-state.json").read_text()
            )
            self.assertEqual(
                state["target_fingerprints"]["agents/security-executor.toml"],
                hashlib.sha256(installed.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                state["original_targets"]["agents/security-executor.toml"]["sha256"],
                digest,
            )
            self.assertEqual(self.run_install(home), 0)

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            agents = home / "agents"
            agents.mkdir(parents=True)
            (agents / "security-executor.toml").write_bytes(
                previous.read_bytes() + b"# custom\n"
            )
            with self.assertRaisesRegex(InstallAbort, "installed_role_drift"):
                self.run_install(home)

    def test_release_pinned_v133_routing_roles_upgrade(self) -> None:
        previous = ROOT / "install" / "previous" / "v1.3.3" / "agents"
        roles = ("plan-verifier", "verifier")
        for role in roles:
            digest = hashlib.sha256((previous / f"{role}.toml").read_bytes()).hexdigest()
            self.assertIn(digest, installer.CANONICAL_ROLE_UPGRADE_DIGESTS[role])

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            agents = home / "agents"
            agents.mkdir(parents=True)
            for role in installer.ROLES:
                source = ROOT / "templates" / "agents" / f"{role}.toml"
                (agents / f"{role}.toml").write_bytes(source.read_bytes())
            for role in roles:
                (agents / f"{role}.toml").write_bytes(
                    (previous / f"{role}.toml").read_bytes()
                )

            self.assertEqual(self.run_install(home), 0)
            for role in roles:
                self.assertEqual(
                    (agents / f"{role}.toml").read_bytes(),
                    (ROOT / "templates" / "agents" / f"{role}.toml").read_bytes(),
                )

    def test_two_nonempty_policy_files_abort_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            home.mkdir()
            agents_policy = home / "AGENTS.md"
            override_policy = home / "AGENTS.override.md"
            agents_policy.write_bytes(b"primary policy\n")
            override_policy.write_bytes(b"override policy\n")
            before = {path.name: path.read_bytes() for path in home.iterdir()}

            with self.assertRaisesRegex(InstallAbort, "both policy files"):
                self.run_install(home)

            after = {path.name: path.read_bytes() for path in home.iterdir()}
            self.assertEqual(after, before)

    def test_policy_override_appearing_after_selection_aborts_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            home.mkdir()
            agents_policy = home / "AGENTS.md"
            override_policy = home / "AGENTS.override.md"
            pending = home.with_name(f"{home.name}.pilotfish-install-state.json.pending")
            state = home.with_name(f"{home.name}.pilotfish-install-state.json")
            agents_policy.write_bytes(b"primary policy\n")
            original_atomic_write = installer._atomic_write
            injected = False

            def atomic_write_with_policy_race(path: Path, payload: bytes, mode: int) -> None:
                nonlocal injected
                original_atomic_write(path, payload, mode)
                if path == pending and not injected:
                    override_policy.write_bytes(b"late override policy\n")
                    injected = True

            with mock.patch.object(installer, "_atomic_write", side_effect=atomic_write_with_policy_race):
                with self.assertRaisesRegex(InstallAbort, "both policy files"):
                    self.run_install(home)

            self.assertTrue(injected)
            self.assertEqual(agents_policy.read_bytes(), b"primary policy\n")
            self.assertEqual(override_policy.read_bytes(), b"late override policy\n")
            self.assertFalse((home / "config.toml").exists())
            self.assertFalse(any((home / "agents").glob("*.toml")))
            self.assertFalse(state.exists())
            aborted = json.loads(pending.read_text())
            self.assertEqual(aborted["status"], "aborted")
            self.assertEqual(aborted["error"], "InstallAbort")

    def test_extra_role_aborts_without_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"; agents = home / "agents"; agents.mkdir(parents=True)
            (agents / "Explore.toml").write_text('name = "Explore"\n')
            with self.assertRaisesRegex(InstallAbort, "invalid role"):
                self.run_install(home)
            self.assertTrue((agents / "Explore.toml").exists())

    def test_nested_malformed_or_duplicate_role_aborts_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"; nested = home / "agents" / "nested"; nested.mkdir(parents=True)
            (nested / "scout.toml").write_text('name = "scout"\n')
            with self.assertRaisesRegex(InstallAbort, "invalid role"):
                self.run_install(home)
            self.assertFalse((home / "config.toml").exists())

    def test_agents_root_symlink_is_rejected_before_role_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); home = root / "home"; home.mkdir(); outside = root / "outside"; outside.mkdir()
            os.symlink(outside, home / "agents")
            with self.assertRaisesRegex(InstallAbort, "agents root"):
                self.run_install(home)


if __name__ == "__main__":
    unittest.main()
