from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
import benchmark_routing as benchmark  # noqa: E402


class ManifestTests(unittest.TestCase):
    def test_manifest_is_versioned_and_exactly_twelve_cases(self) -> None:
        manifest = benchmark.load_manifest()
        self.assertEqual(manifest["version"], "usage-routing-v1")
        self.assertEqual(len(manifest["cases"]), 12)
        self.assertEqual(
            {case["cohort"] for case in manifest["cases"]}, {"routine", "judgment"}
        )
        self.assertEqual(
            sum(case["cohort"] == "routine" for case in manifest["cases"]), 6
        )
        self.assertEqual(
            sum(case["cohort"] == "judgment" for case in manifest["cases"]), 6
        )
        for case in manifest["cases"]:
            self.assertEqual(
                set(case["fixture"]), {"id", "revision", "hash", "path"}
            )

    def test_candidate_matrix_matches_contract(self) -> None:
        self.assertEqual(
            [(x.model, x.reasoning_effort) for x in benchmark.CANDIDATES["routine"]],
            [("gpt-5.6-luna", "medium"), ("gpt-5.6-terra", "high"), ("gpt-5.6-sol", "high")],
        )
        self.assertEqual(
            [(x.model, x.reasoning_effort) for x in benchmark.CANDIDATES["judgment"]],
            [("gpt-5.6-luna", "xhigh"), ("gpt-5.6-terra", "xhigh"), ("gpt-5.6-sol", "high")],
        )


class HomeAndAuthTests(unittest.TestCase):
    def test_default_trial_home_never_changes_shared_temp_root_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            shared_root = Path(directory)
            original = benchmark._ensure_private_dir
            with mock.patch.object(
                benchmark,
                "_ensure_private_dir",
                wraps=original,
            ) as ensure_private:
                with mock.patch.object(
                    benchmark.tempfile,
                    "gettempdir",
                    return_value=str(shared_root),
                ):
                    with benchmark.temporary_trial_home(
                        "mech-executor",
                        benchmark.CANDIDATES["routine"][0],
                    ):
                        pass
            self.assertNotIn(mock.call(shared_root), ensure_private.call_args_list)

    def test_default_case_workspace_never_changes_shared_temp_root_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            shared_root = Path(directory)
            fixture = ROOT / "tests" / "fixtures" / "benchmark_routing" / "routine-01.json"
            original = benchmark._ensure_private_dir
            with mock.patch.object(
                benchmark,
                "_ensure_private_dir",
                wraps=original,
            ) as ensure_private:
                with mock.patch.object(
                    benchmark.tempfile,
                    "gettempdir",
                    return_value=str(shared_root),
                ):
                    with benchmark.disposable_case_workspace(fixture):
                        pass
            self.assertNotIn(mock.call(shared_root), ensure_private.call_args_list)

    def test_trial_home_preserves_templates_and_only_mutates_binding(self) -> None:
        candidate = benchmark.CANDIDATES["routine"][1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = (ROOT / "templates" / "agents" / "mech-executor.toml").read_bytes()
            with benchmark.temporary_trial_home("mech-executor", candidate, parent_dir=root) as trial:
                self.assertEqual((trial.home / "config.toml").read_bytes(), (ROOT / "templates" / "config.snippet.toml").read_bytes())
                for role in benchmark.ROLE_NAMES:
                    content = (trial.home / "agents" / f"{role}.toml").read_bytes()
                    if role == "mech-executor":
                        self.assertIn(b'model = "gpt-5.6-terra"', content)
                        self.assertIn(b'model_reasoning_effort = "high"', content)
                    else:
                        self.assertEqual(content, (ROOT / "templates" / "agents" / f"{role}.toml").read_bytes())
                self.assertTrue((trial.home / "agents" / "mech-executor.toml").exists())
            self.assertFalse((root / "pilotfish-benchmark-codex").exists())
            self.assertEqual(source.split(b"developer_instructions = ", 1)[1], (ROOT / "templates" / "agents" / "mech-executor.toml").read_bytes().split(b"developer_instructions = ", 1)[1])

    def test_auth_copy_rejects_symlink_and_cleans_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "auth.json"
            source.write_text('{"sentinel":"do-not-leak"}')
            source.chmod(0o600)
            destination = root / "out" / "auth.json"
            benchmark.copy_auth_secure(source, destination)
            self.assertEqual(destination.read_text(), source.read_text())
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o600)
            link = root / "link"
            link.symlink_to(source)
            with self.assertRaises(benchmark.BenchmarkError):
                benchmark.copy_auth_secure(link, root / "link-out")

    def test_manifest_acceptance_returns_a_safe_rejection_for_missing_result(self) -> None:
        case = benchmark.load_manifest()["cases"][0]
        fixture = ROOT / str(case["fixture"]["path"])
        with benchmark.disposable_case_workspace(fixture) as workspace:
            packet = benchmark.run_manifest_acceptance(case, workspace)
        self.assertEqual(
            packet,
            {"accepted": False, "reason_code": "acceptance_command_failed"},
        )

    def test_auth_is_removed_even_when_process_raises(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "auth.json"
            source.write_text('{"sentinel":"secret"}')
            source.chmod(0o600)
            with self.assertRaises(RuntimeError):
                with benchmark.temporary_trial_home(
                    "mech-executor", benchmark.CANDIDATES["routine"][0], auth_source=source, parent_dir=root
                ) as trial:
                    auth_path = trial.auth_path
                    self.assertIsNotNone(auth_path)
                    raise RuntimeError("stub")
            self.assertFalse(auth_path and auth_path.exists())


class ReceiptMetricsTests(unittest.TestCase):
    def test_receipt_requires_exactly_one_child_and_binding(self) -> None:
        candidate = benchmark.CANDIDATES["routine"][0]
        receipt = benchmark.build_binding_receipt("mech-executor", candidate)
        self.assertEqual(
            benchmark.validate_binding_receipt(
                receipt, expected_role="mech-executor", expected_candidate=candidate
            )["status"],
            "NATIVE_OK",
        )
        receipt["child_count"] = 2
        with self.assertRaises(benchmark.ReceiptError):
            benchmark.validate_binding_receipt(receipt, expected_role="mech-executor", expected_candidate=candidate)

    def test_live_receipt_is_bound_to_its_real_case_id(self) -> None:
        candidate = benchmark.CANDIDATES["routine"][0]
        observed = SimpleNamespace(
            status="NATIVE_OK",
            reason_code="native_verified",
            task_name="model_probe_mech_executor",
            parent_ref="parent",
            child_ref="child",
            fork_turns="none",
        )
        with mock.patch(
            "verify_dispatch.inspect_available_evidence",
            return_value=(observed, True),
        ):
            receipt = benchmark.parse_native_dispatch_receipt(
                Path("/tmp/benchmark-home"),
                "",
                role="mech-executor",
                candidate=candidate,
                case_id="routine-01",
            )
        self.assertEqual(receipt["case_id"], "routine-01")

    def test_codexbar_formula_and_strict_schema(self) -> None:
        metrics = benchmark.normalize_codexbar_totals(
            [{"provider": "codex", "source": "codexbar", "updatedAt": "2026-08-03T00:00:00Z", "totals": {"inputTokens": 100, "outputTokens": 20, "cacheReadTokens": 10, "cacheCreationTokens": 4, "totalTokens": 134, "totalCost": 1.2}}]
        )
        self.assertEqual(metrics.primary_usage, 1.2)
        self.assertEqual(metrics.weighted_tokens, 100 + 20 + 1 + 5)
        with self.assertRaises(benchmark.MetricsUnavailable):
            benchmark.normalize_codexbar_totals({"In": 1, "Out": 2})
        with self.assertRaises(benchmark.MetricsUnavailable):
            benchmark.normalize_codexbar_totals([{"provider": "codex", "source": "codexbar", "updatedAt": "now", "totals": {"inputTokens": 1, "outputTokens": 2, "cacheReadTokens": 0, "cacheCreationTokens": 0, "totalTokens": 3, "totalCost": None}}])
        daily = benchmark.normalize_codexbar_totals([{"provider": "codex", "source": "codexbar", "updatedAt": "now", "daily": [{"date": "2026-08-03", "totals": {"inputTokens": 100, "outputTokens": 20, "cacheReadTokens": 10, "cacheCreationTokens": 4, "totalTokens": 134, "totalCost": 1.2}}]}])
        self.assertEqual(daily.primary_usage, metrics.primary_usage)

    def test_native_rollout_usage_prices_parent_and_child_without_double_counting_reasoning(self) -> None:
        totals = [
            {
                "input_tokens": 100,
                "cached_input_tokens": 20,
                "cache_write_input_tokens": 4,
                "output_tokens": 30,
                "reasoning_output_tokens": 12,
                "total_tokens": 130,
            },
            {
                "input_tokens": 50,
                "cached_input_tokens": 10,
                "cache_write_input_tokens": 0,
                "output_tokens": 20,
                "reasoning_output_tokens": 8,
                "total_tokens": 70,
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            sessions = Path(directory) / "sessions"
            sessions.mkdir()
            for index, total in enumerate(totals):
                (sessions / f"trial-{index}.jsonl").write_text(
                    json.dumps(
                        {
                            "type": "event_msg",
                            "payload": {
                                "type": "token_count",
                                "info": {"total_token_usage": total},
                            },
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
            metrics = benchmark.collect_native_rollout_metrics(
                sessions,
                benchmark.CANDIDATES["routine"][0],
            )
        self.assertEqual(metrics.input, 116)
        self.assertEqual(metrics.cached_read, 30)
        self.assertEqual(metrics.cached_write, 4)
        self.assertEqual(metrics.output, 50)
        self.assertEqual(metrics.reasoning_output, 20)
        self.assertEqual(metrics.total, 200)
        self.assertAlmostEqual(metrics.cost, 0.000424)
        self.assertEqual(metrics.source, "native-rollout-proxy")

    def test_native_rollout_prices_fixed_luna_parent_separately_from_child(self) -> None:
        parent_total = {
            "input_tokens": 100,
            "cached_input_tokens": 20,
            "cache_write_input_tokens": 4,
            "output_tokens": 30,
            "reasoning_output_tokens": 12,
            "total_tokens": 130,
        }
        child_total = {
            "input_tokens": 50,
            "cached_input_tokens": 10,
            "cache_write_input_tokens": 0,
            "output_tokens": 20,
            "reasoning_output_tokens": 8,
            "total_tokens": 70,
        }
        with tempfile.TemporaryDirectory() as directory:
            sessions = Path(directory) / "sessions"
            sessions.mkdir()
            paths = []
            for name, total in (("parent", parent_total), ("child", child_total)):
                path = sessions / f"{name}.jsonl"
                path.write_text(
                    json.dumps(
                        {
                            "type": "event_msg",
                            "payload": {
                                "type": "token_count",
                                "info": {"total_token_usage": total},
                            },
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                paths.append(path)
            metrics = benchmark.collect_native_rollout_metrics(
                sessions,
                benchmark.CANDIDATES["routine"][1],
                parent_rollout=paths[0],
                child_rollout=paths[1],
            )
        self.assertAlmostEqual(metrics.cost, 0.0006655)

    def test_codexbar_nested_schema_drift_fails_closed(self) -> None:
        totals = {
            "inputTokens": 100,
            "outputTokens": 20,
            "cacheReadTokens": 10,
            "cacheCreationTokens": 4,
            "totalTokens": 134,
            "totalCost": 1.2,
            "schemaDriftField": 7,
        }
        with self.assertRaises(benchmark.MetricsUnavailable):
            benchmark.normalize_codexbar_totals(
                [
                    {
                        "provider": "codex",
                        "source": "codexbar",
                        "updatedAt": "now",
                        "totals": totals,
                    }
                ]
            )
        with self.assertRaises(benchmark.MetricsUnavailable):
            benchmark.normalize_codexbar_totals(
                [
                    {
                        "provider": "codex",
                        "source": "codexbar",
                        "updatedAt": "now",
                        "daily": [{"totals": totals}],
                    }
                ]
            )

    def test_metrics_deduplicate_and_quota_fails_closed(self) -> None:
        one = benchmark.normalize_codexbar_totals([{"provider": "codex", "source": "codexbar", "updatedAt": "now", "totals": {"inputTokens": 1, "outputTokens": 2, "cacheReadTokens": 3, "cacheCreationTokens": 4, "totalTokens": 10, "totalCost": 1}}])
        self.assertEqual(len(benchmark.deduplicate_codexbar_metrics([one, one])), 1)
        with self.assertRaises(benchmark.MetricsUnavailable):
            benchmark.validate_quota_snapshot({"source": "quota", "cohort": "routine", "primary_usage": 1})
        benchmark.validate_quota_snapshot({"source": "quota", "exclusive_attestation": True, "cohort": "routine", "primary_usage": 1})


class SimulationTests(unittest.TestCase):
    def _observations(self) -> dict[str, list[benchmark.TrialObservation]]:
        metrics = benchmark.normalize_codexbar_totals([{"provider": "codex", "source": "codexbar", "updatedAt": "now", "totals": {"inputTokens": 10, "outputTokens": 1, "cacheReadTokens": 0, "cacheCreationTokens": 0, "totalTokens": 11, "totalCost": 1}}])
        return {
            "routine-01": [
                benchmark.TrialObservation("routine-01", "L", "accept", metrics, 3, cohort="routine"),
                benchmark.TrialObservation("routine-01", "T", "accept", metrics, 2, cohort="routine"),
                benchmark.TrialObservation("routine-01", "S", "accept", metrics, 1, cohort="routine"),
            ],
        }

    def test_reruns_are_independent_and_recommendation_is_deterministic(self) -> None:
        results = benchmark.simulate_posthoc_reruns(self._observations())
        self.assertEqual(set(results), set(benchmark.CHAIN_ORDERS))
        recommendation = benchmark.recommend_chain(results)
        self.assertEqual(recommendation.chain, "S")
        self.assertFalse(recommendation.terra_retained)

    def test_inconclusive_review_fails_closed(self) -> None:
        self.assertFalse(benchmark.verdict_accepts({"verdict": "inconclusive", "rationale": "unclear"}))
        self.assertFalse(benchmark.verdict_accepts({"verdict": "accept", "rationale": ""}))
        with self.assertRaises(benchmark.BenchmarkError):
            benchmark.parse_review_verdict({"verdict": "reject"})

    def test_rejected_deterministic_acceptance_enters_native_chain_simulation(self) -> None:
        manifest = benchmark.load_manifest()
        reviews = []
        for case in manifest["cases"]:
            for tier, usage in (("L", 1.0), ("T", 2.0), ("S", 3.0)):
                rejected = case["id"] == "routine-01" and tier == "S"
                reviews.append(
                    {
                        "case_id": case["id"],
                        "tier": tier,
                        "verdict": "reject" if rejected else "accept",
                        "rationale": "deterministic reject" if rejected else "accepted",
                        "fixture_sha256": case["fixture"]["hash"],
                        "metric_source": "native-rollout-proxy",
                        "acceptance": (
                            {"accepted": False, "reason_code": "acceptance_command_failed"}
                            if rejected
                            else {"accepted": True, "artifact_sha256": "a" * 64}
                        ),
                        "primary_usage": usage,
                        "elapsed_seconds": usage,
                        "hard_case_success": not rejected,
                    }
                )
        report = benchmark.ingest_review_report(reviews, manifest=manifest)
        self.assertEqual(report["status"], "settled")
        self.assertEqual(report["recommendation"]["chain"], "LS")


class CliTests(unittest.TestCase):
    def test_live_codex_binary_accepts_parseable_versions(self) -> None:
        with mock.patch.object(
            benchmark.subprocess,
            "run",
            return_value=benchmark.subprocess.CompletedProcess(
                ["codex", "--version"], 0, stdout="codex-cli 0.146.0\n", stderr=""
            ),
        ):
            self.assertIsNone(benchmark.validate_live_codex_binary("codex"))
        with mock.patch.object(
            benchmark.subprocess,
            "run",
            return_value=benchmark.subprocess.CompletedProcess(
                ["codex", "--version"], 0, stdout="codex-cli 0.147.0-alpha.1.2\n", stderr=""
            ),
        ):
            self.assertIsNone(benchmark.validate_live_codex_binary("codex"))

    def test_case_prompt_matches_native_typed_dispatch_contract(self) -> None:
        case = benchmark.load_manifest()["cases"][0]
        prompt = benchmark.build_case_prompt(case, Path("/tmp/pilotfish-case"))
        self.assertIn("agent_type='mech-executor'", prompt)
        self.assertIn("task_name='model_probe_mech_executor'", prompt)
        self.assertIn("fork_turns='none'", prompt)
        self.assertIn("wait_agent exactly once with timeout_ms=30000", prompt)

    def test_benchmark_command_uses_disposable_workspace_write_access(self) -> None:
        command = benchmark.build_benchmark_codex_command(
            codex_bin="codex",
            cwd=Path("/tmp/pilotfish-benchmark"),
            role="mech-executor",
            prompt="fixture benchmark",
        )
        self.assertEqual(command[command.index("-s") + 1], "workspace-write")

    def test_live_requires_double_opt_in_and_rejects_ci_and_cap(self) -> None:
        with self.assertRaises(benchmark.BenchmarkError):
            benchmark.enforce_live_gates(live=True, yes=True, benchmark_yes=False, trials=1, environ={})
        with self.assertRaises(benchmark.BenchmarkError):
            benchmark.enforce_live_gates(live=True, yes=True, benchmark_yes=True, trials=1, environ={})
        with self.assertRaises(benchmark.BenchmarkError):
            benchmark.enforce_live_gates(live=True, yes=True, benchmark_yes=True, trials=1, environ={"CI": "true"})
        with self.assertRaises(benchmark.BenchmarkError):
            benchmark.run_live(trials=36, auth_source=Path("/tmp/auth.json"))
        with self.assertRaises(benchmark.BenchmarkError):
            benchmark.run_live(trials=36, auth_source=Path("/tmp/auth.json"), yes=True, benchmark_yes=True, environ={"CI": "true"})

    def test_dry_run_emits_three_receipts_without_network(self) -> None:
        with mock.patch.object(benchmark, "run_live") as live:
            self.assertEqual(benchmark.main(["--dry-run"]), 0)
            live.assert_not_called()

    def test_result_report_is_private_atomic_and_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "result.json"
            payload = {"version": "usage-routing-v1", "trials": []}
            benchmark.write_result_report(destination, payload)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), payload)
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o600)
            with self.assertRaises(benchmark.BenchmarkError):
                benchmark.write_result_report(destination, payload)

    def test_live_writes_a_checkpoint_after_each_completed_trial(self) -> None:
        checkpoint = Path("/tmp/pilotfish-benchmark-checkpoint.json")
        with (
            mock.patch.object(benchmark, "validate_live_codex_binary"),
            mock.patch.object(
                benchmark,
                "run_live_trial",
                return_value={
                    "metrics": {"source": "native-rollout-proxy"},
                    "model_wall_seconds": 2.5,
                },
            ),
            mock.patch.object(benchmark, "write_checkpoint_report") as writer,
        ):
            report = benchmark.run_live(
                trials=36,
                auth_source=Path("/tmp/auth.json"),
                yes=True,
                benchmark_yes=True,
                environ={},
                checkpoint_path=checkpoint,
            )
        self.assertEqual(len(report["trials"]), 36)
        self.assertEqual(writer.call_count, 36)
        self.assertEqual(writer.call_args.args[0], checkpoint)
        self.assertEqual(len(writer.call_args.args[1]["trials"]), 36)
        self.assertEqual(report["trials"][0]["model_wall_seconds"], 2.5)

    def test_live_checkpoint_records_safe_failure_context(self) -> None:
        completed = {
            "metrics": {"source": "native-rollout-proxy"},
            "model_wall_seconds": 2.5,
        }
        checkpoint = Path("/tmp/pilotfish-benchmark-failed-checkpoint.json")
        with (
            mock.patch.object(benchmark, "validate_live_codex_binary"),
            mock.patch.object(
                benchmark,
                "run_live_trial",
                side_effect=[completed, completed, benchmark.MetricsUnavailable("native usage unavailable")],
            ),
            mock.patch.object(benchmark, "write_checkpoint_report") as writer,
        ):
            with self.assertRaisesRegex(benchmark.BenchmarkError, "routine-01"):
                benchmark.run_live(
                    trials=36,
                    auth_source=Path("/tmp/auth.json"),
                    yes=True,
                    benchmark_yes=True,
                    environ={},
                    checkpoint_path=checkpoint,
                )
        failed = writer.call_args.args[1]
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(len(failed["trials"]), 2)
        self.assertEqual(failed["failure"]["case_id"], "routine-01")
        self.assertEqual(failed["failure"]["reason"], "native usage unavailable")


if __name__ == "__main__":
    unittest.main()
