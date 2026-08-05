from __future__ import annotations

import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from run_adaptive_intent_experiment import (  # noqa: E402
    ExperimentError,
    run,
    validate_matrix,
)


class AdaptiveExperimentTests(unittest.TestCase):
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

    def test_matrix_has_twenty_matched_groups_per_scenario(self) -> None:
        matrix = validate_matrix(self.matrix)
        counts = Counter(case["scenario"] for case in matrix["cases"])

        self.assertEqual(len(matrix["cases"]), 60)
        self.assertEqual(
            counts,
            Counter(
                {
                    "clear_bounded": 20,
                    "broad_migration": 20,
                    "open_ended_idea": 20,
                }
            ),
        )

    def test_reference_candidate_covers_all_contract_checks(self) -> None:
        report = run(self.matrix)
        candidate = report["arms"]["candidate"]

        self.assertEqual(candidate["passed"], 60)
        self.assertEqual(candidate["pass_rate"], 1.0)
        self.assertTrue(all(item["correct"] == 60 for item in candidate["checks"].values()))

    def test_reference_control_exposes_tunnel_contrast(self) -> None:
        report = run(self.matrix)
        control = report["arms"]["control"]

        self.assertEqual(control["passed"], 11)
        self.assertEqual(report["delta"], {"pass_rate": 49 / 60, "passed_groups": 49})
        self.assertEqual(control["failure_counts"]["overplanning"], 42)
        self.assertEqual(control["failure_counts"]["generic_advice"], 20)

    def test_matrix_rejects_missing_scenario_coverage(self) -> None:
        matrix = json.loads(json.dumps(self.matrix))
        matrix["cases"] = [case for case in matrix["cases"] if case["scenario"] != "open_ended_idea"]

        with self.assertRaises(ExperimentError):
            validate_matrix(matrix)


if __name__ == "__main__":
    unittest.main()
