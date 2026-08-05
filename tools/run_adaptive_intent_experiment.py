#!/usr/bin/env python3
"""Run the offline adaptive-intent routing tunnel experiment.

This runner compares a reference candidate arm with a reference pre-adaptive
control arm. It makes no model calls, does not inspect a repository, and does
not perform writes beyond optional stdout capture by the caller. The output is
behavioral design evidence, not live model evidence.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = (
    ROOT / "docs" / "specs" / "adaptive-intent-routing" / "experiment-matrix.json"
)
SCENARIOS = {
    "clear_bounded": "execute",
    "broad_migration": "explore_then_plan",
    "open_ended_idea": "co_discover",
}
MODES = frozenset({"execute", "explore_then_plan", "co_discover", "full_plan", "generic_advice"})
CONFIDENCE = frozenset({"clear", "partial", "unclear"})
IMPACTS = frozenset({"trivial", "low", "material", "high", "critical"})
GROUNDING = ("none", "minimum", "bounded", "deep")
CHECKPOINTS = frozenset({"CONTINUE", "PIVOT", "ROLLBACK", "INCONCLUSIVE"})
FAILURE_TAGS = frozenset(
    {
        "premature_execution",
        "approval_boundary_loss",
        "overplanning",
        "runaway_discovery",
        "missing_checkpoint",
        "unsupported_guess",
        "generic_advice",
    }
)
EXPECTED_FIELDS = frozenset(
    {
        "mode",
        "intent_confidence",
        "change_impact",
        "first_move",
        "grounding_floor",
        "grounding_target",
        "grounding_ceiling",
        "direction_checkpoint",
        "approval_required",
        "stopping_rule",
    }
)
CONTROL_FIELDS = frozenset(
    {
        "mode",
        "first_move",
        "grounding",
        "direction_checkpoint",
        "approval_required",
        "failure_tags",
    }
)


class ExperimentError(ValueError):
    """Raised when the experiment matrix violates its contract."""


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentError(f"cannot load matrix: {path}: {exc}") from exc


def validate_matrix(matrix: Any) -> dict[str, Any]:
    if not isinstance(matrix, dict) or matrix.get("version") != 1:
        raise ExperimentError("matrix must be a version 1 object")
    if not _is_text(matrix.get("question")):
        raise ExperimentError("matrix question must be non-empty")
    scenarios = matrix.get("scenarios")
    if not isinstance(scenarios, list) or {item.get("id") for item in scenarios} != set(SCENARIOS):
        raise ExperimentError("matrix must declare all three experiment scenarios")
    minimums = {}
    for item in scenarios:
        if not isinstance(item, dict) or item.get("id") not in SCENARIOS:
            raise ExperimentError("invalid scenario declaration")
        if type(item.get("minimum_groups")) is not int or item["minimum_groups"] < 20:
            raise ExperimentError(f"scenario {item.get('id')} must require at least 20 groups")
        if item.get("expected_mode") != SCENARIOS[item["id"]]:
            raise ExperimentError(f"scenario {item['id']} has the wrong expected mode")
        minimums[item["id"]] = item["minimum_groups"]

    cases = matrix.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ExperimentError("matrix cases must be a non-empty list")
    ids: set[str] = set()
    counts = Counter()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "id",
            "scenario",
            "variant",
            "prompt",
            "expected",
            "control",
        }:
            raise ExperimentError("each case must contain id, scenario, variant, prompt, expected, control")
        case_id = case["id"]
        if not _is_text(case_id) or case_id in ids:
            raise ExperimentError(f"invalid or duplicate case id: {case_id}")
        ids.add(case_id)
        scenario = case["scenario"]
        if scenario not in SCENARIOS:
            raise ExperimentError(f"case {case_id}: unknown scenario")
        if not _is_text(case["variant"]) or not _is_text(case["prompt"]):
            raise ExperimentError(f"case {case_id}: variant and prompt must be non-empty")
        expected = case["expected"]
        if not isinstance(expected, dict) or set(expected) != EXPECTED_FIELDS:
            raise ExperimentError(f"case {case_id}: invalid expected shape")
        if expected["mode"] != SCENARIOS[scenario] or expected["intent_confidence"] not in CONFIDENCE:
            raise ExperimentError(f"case {case_id}: invalid route expectation")
        if expected["change_impact"] not in IMPACTS or not _is_text(expected["first_move"]):
            raise ExperimentError(f"case {case_id}: invalid impact or first move")
        floor = expected["grounding_floor"]
        target = expected["grounding_target"]
        ceiling = expected["grounding_ceiling"]
        if floor not in GROUNDING or target not in GROUNDING or ceiling not in GROUNDING:
            raise ExperimentError(f"case {case_id}: invalid grounding level")
        if not (GROUNDING.index(floor) <= GROUNDING.index(target) <= GROUNDING.index(ceiling)):
            raise ExperimentError(f"case {case_id}: grounding floor/target/ceiling are out of order")
        if expected["direction_checkpoint"] not in CHECKPOINTS:
            raise ExperimentError(f"case {case_id}: invalid direction checkpoint")
        if type(expected["approval_required"]) is not bool or not _is_text(expected["stopping_rule"]):
            raise ExperimentError(f"case {case_id}: invalid approval or stopping rule")

        control = case["control"]
        if not isinstance(control, dict) or set(control) != CONTROL_FIELDS:
            raise ExperimentError(f"case {case_id}: invalid control shape")
        if control["mode"] not in MODES or not _is_text(control["first_move"]):
            raise ExperimentError(f"case {case_id}: invalid control route")
        if control["grounding"] not in GROUNDING or control["direction_checkpoint"] not in CHECKPOINTS:
            raise ExperimentError(f"case {case_id}: invalid control boundary signal")
        if type(control["approval_required"]) is not bool or not isinstance(control["failure_tags"], list):
            raise ExperimentError(f"case {case_id}: invalid control approval or failure tags")
        if not all(tag in FAILURE_TAGS for tag in control["failure_tags"]):
            raise ExperimentError(f"case {case_id}: unknown control failure tag")
        counts[scenario] += 1

    for scenario, minimum in minimums.items():
        if counts[scenario] < minimum:
            raise ExperimentError(f"scenario {scenario} has {counts[scenario]} groups; expected at least {minimum}")
    if set(case["expected"]["direction_checkpoint"] for case in cases) != set(CHECKPOINTS):
        raise ExperimentError("matrix must exercise all direction checkpoints")
    return matrix


def _candidate_observation(case: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    return {
        "mode": expected["mode"],
        "first_move": expected["first_move"],
        "grounding": expected["grounding_target"],
        "direction_checkpoint": expected["direction_checkpoint"],
        "approval_required": expected["approval_required"],
        "failure_tags": [],
    }


def _score_case(case: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    checks = {
        "route_fit": observation["mode"] == expected["mode"],
        "first_move_fit": observation["first_move"] == expected["first_move"],
        "grounding_floor": GROUNDING.index(observation["grounding"])
        >= GROUNDING.index(expected["grounding_floor"]),
        "grounding_ceiling": GROUNDING.index(observation["grounding"])
        <= GROUNDING.index(expected["grounding_ceiling"]),
        "direction_checkpoint_fit": observation["direction_checkpoint"]
        == expected["direction_checkpoint"],
        "approval_boundary": observation["approval_required"] == expected["approval_required"],
    }
    failures = set(observation.get("failure_tags", []))
    if not checks["route_fit"]:
        failures.add("premature_execution" if observation["mode"] == "execute" else "overplanning")
    if not checks["first_move_fit"] and observation["mode"] == "generic_advice":
        failures.add("generic_advice")
    if not checks["grounding_floor"]:
        failures.add("unsupported_guess")
    if not checks["grounding_ceiling"]:
        failures.add("runaway_discovery")
    if not checks["direction_checkpoint_fit"]:
        failures.add("missing_checkpoint")
    if not checks["approval_boundary"] and expected["approval_required"]:
        failures.add("approval_boundary_loss")
    return {
        "id": case["id"],
        "scenario": case["scenario"],
        "checks": checks,
        "passed": all(checks.values()) and not failures,
        "failures": sorted(failures),
    }


def _score_arm(matrix: dict[str, Any], arm: str) -> dict[str, Any]:
    results = []
    for case in matrix["cases"]:
        observation = _candidate_observation(case) if arm == "candidate" else case["control"]
        results.append(_score_case(case, observation))
    check_names = (
        "route_fit",
        "first_move_fit",
        "grounding_floor",
        "grounding_ceiling",
        "direction_checkpoint_fit",
        "approval_boundary",
    )
    checks = {
        name: sum(result["checks"][name] for result in results) for name in check_names
    }
    by_scenario = {}
    for scenario in SCENARIOS:
        subset = [result for result in results if result["scenario"] == scenario]
        by_scenario[scenario] = {
            "groups": len(subset),
            "passed": sum(result["passed"] for result in subset),
            "failure_counts": dict(Counter(tag for result in subset for tag in result["failures"])),
        }
    return {
        "groups": len(results),
        "passed": sum(result["passed"] for result in results),
        "pass_rate": sum(result["passed"] for result in results) / len(results),
        "checks": {name: {"correct": count, "total": len(results), "rate": count / len(results)} for name, count in checks.items()},
        "failure_counts": dict(Counter(tag for result in results for tag in result["failures"])),
        "by_scenario": by_scenario,
        "case_results": results,
    }


def run(matrix: dict[str, Any]) -> dict[str, Any]:
    validate_matrix(matrix)
    candidate = _score_arm(matrix, "candidate")
    control = _score_arm(matrix, "control")
    return {
        "experiment": "adaptive-intent-routing-tunnel-v1",
        "evidence_type": "offline-reference-policy-contrast",
        "live_model_calls": 0,
        "tools_or_writes": 0,
        "matrix": {
            "version": matrix["version"],
            "groups": len(matrix["cases"]),
            "paired_observations": len(matrix["cases"]) * 2,
            "scenario_counts": dict(Counter(case["scenario"] for case in matrix["cases"])),
        },
        "arms": {"candidate": candidate, "control": control},
        "delta": {
            "pass_rate": candidate["pass_rate"] - control["pass_rate"],
            "passed_groups": candidate["passed"] - control["passed"],
        },
        "limitations": [
            "Candidate and control observations are reference policies generated from the matrix, not model transcripts.",
            "The result tests rubric coverage and an expected contrast; it does not estimate live compliance or a population rate.",
            "A live follow-up must randomize arm order, hold model/session settings constant, and blind the reviewer to arm labels.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    args = parser.parse_args(argv)
    report = run(_load_json(args.matrix))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
