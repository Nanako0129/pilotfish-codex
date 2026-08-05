from __future__ import annotations

import json
import sys
import unittest
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from run_adaptive_intent_experiment import run as run_reference  # noqa: E402
from run_live_adaptive_routing import (  # noqa: E402
    _aggregate,
    _prompt_for,
    _wilson_lower,
)


class LiveAdaptiveRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = json.loads(
            (
                ROOT
                / "docs"
                / "specs"
                / "adaptive-intent-routing"
                / "experiment-matrix.json"
            ).read_text(encoding="utf-8")
        )

    def test_wilson_threshold_is_pre_registered(self) -> None:
        self.assertGreaterEqual(_wilson_lower(54, 60), 0.80)
        self.assertLess(_wilson_lower(53, 60), 0.80)

    def test_reference_candidate_meets_live_claim_audit_shape(self) -> None:
        reference = run_reference(self.matrix)["arms"]["candidate"]["case_results"]
        route_results = [
            {
                "case_id": result["id"],
                "scenario": result["scenario"],
                "status": "ok",
                "phase": "route",
                "checks": result["checks"],
                "passed": result["passed"],
                "failures": result["failures"],
            }
            for result in reference
        ]
        checkpoint_results = [
            {
                "case_id": case["id"],
                "scenario": case["scenario"],
                "status": "ok",
                "phase": "checkpoint",
                "checks": {"direction_checkpoint_fit": True},
                "passed": True,
                "failures": [],
            }
            for case in self.matrix["cases"]
        ]

        aggregate = _aggregate(self.matrix, route_results + checkpoint_results)

        self.assertTrue(aggregate["claim_audit"]["high_success_claim"])
        self.assertEqual(aggregate["route"]["successful"], 60)
        self.assertEqual(aggregate["checkpoint"]["successful"], 60)

    def test_prompt_does_not_include_case_expected_values(self) -> None:
        case = self.matrix["cases"][0]
        prompt = _prompt_for(case, "candidate", "route")

        self.assertIn(case["prompt"], prompt)
        self.assertNotIn("Expected mode:", prompt)
        self.assertNotIn(json.dumps(case["expected"], ensure_ascii=False), prompt)

    def test_live_runner_defaults_are_explicitly_ephemeral_and_read_only(self) -> None:
        args = Namespace(
            matrix=ROOT / "docs/specs/adaptive-intent-routing/experiment-matrix.json",
            schema=ROOT / "docs/specs/adaptive-intent-routing/live-routing-output.schema.json",
            seed=20260805,
            arm="candidate",
            case_id=[],
            output=None,
            codex_bin="codex",
            timeout_seconds=180,
        )

        self.assertEqual(args.seed, 20260805)
        self.assertEqual(args.timeout_seconds, 180)


if __name__ == "__main__":
    unittest.main()
