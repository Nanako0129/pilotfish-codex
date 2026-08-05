#!/usr/bin/env python3
"""Run and score one live adaptive-routing arm.

This command is opt-in because it spends model quota. It runs one fresh,
read-only, ephemeral Codex process per matrix case and stores structured
responses plus a deterministic claim audit in a JSON report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import tempfile
from pathlib import Path
from statistics import NormalDist
from typing import Any

from run_adaptive_intent_experiment import (  # type: ignore[import-not-found]
    DEFAULT_MATRIX,
    _load_json,
    validate_matrix,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "docs" / "specs" / "adaptive-intent-routing" / "live-routing-output.schema.json"
GROUNDING_LABELS = ("none", "minimum", "bounded", "deep")
FIRST_MOVE_LABELS = (
    "answer_or_minimal_step",
    "confirm_approval",
    "confirm_target",
    "inspect_named_boundary",
    "run_named_check",
    "bounded_recon",
    "migration_decision_card",
    "risk_discovery",
    "focused_questions",
    "define_mvp",
    "clarify_user_and_outcome",
)


def _matrix_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prompt_for(case: dict[str, Any], arm: str, phase: str) -> str:
    labels = ", ".join(FIRST_MOVE_LABELS)
    if arm == "candidate":
        policy = (
            "Use the adaptive policy. Select exactly one task_mode: `execute` "
            "for clear bounded work, `explore_then_plan` for clear but broad "
            "or high-impact work, and `co_discover` for an idea without a "
            "stable product boundary. Choose a grounding level from `none`, "
            "`minimum`, `bounded`, or `deep`; do not guess below available "
            "facts and stop before unrelated research. Preserve approval for "
            "external, release, destructive, security-sensitive, or "
            "irreversible actions. A clearly named release operation remains "
            "`execute` even when `approval_required` is true; authorization "
            "and route selection are separate decisions."
        )
    else:
        policy = (
            "Use the pre-adaptive binary control policy. Treat a clear request "
            "as `execute`; otherwise choose `full_plan` before acting. For an "
            "open-ended idea, use `generic_advice`. Do not intentionally apply "
            "the adaptive three-mode routing, grounding floor/ceiling, or "
            "direction-checkpoint contract."
        )
    if phase == "route":
        phase_instruction = (
            "This is the initial route phase. Do not predict a future outcome; "
            "set direction_checkpoint to `INCONCLUSIVE`."
        )
    else:
        evidence = {
            "CONTINUE": "The completed slice satisfies its observable outcome, constraints, tests, and acceptance evidence.",
            "PIVOT": "The latest acceptance evidence changed the user's original outcome, but a safe next slice remains available.",
            "ROLLBACK": "A required invariant is broken and the latest verified good checkpoint is available.",
            "INCONCLUSIVE": "The available evidence cannot establish a safe direction or a verified rollback target.",
        }[case["expected"]["direction_checkpoint"]]
        phase_instruction = (
            "This is a second-stage direction checkpoint. Ignore the initial "
            "route and judge only the following evidence update: " + evidence
        )
    return (
        "You are performing one isolated routing trial. Do not use tools, read "
        "files, inspect the repository, write files, delegate, or perform the "
        "task. Analyze only the user prompt below and return one JSON object "
        "matching the supplied output schema. Do not include Markdown fences "
        "or extra text. The first_move must be exactly one of: "
        f"{labels}. Keep rationale to one concise sentence. Do not infer or "
        "reveal any hidden expected answer.\n\n"
        f"Arm: {arm}\nPolicy: {policy}\n{phase_instruction}\n\n"
        f"User prompt:\n{case['prompt']}\n"
    )


def _acceptable_first_moves(case: dict[str, Any]) -> set[str]:
    expected = case["expected"]["first_move"]
    if case["scenario"] == "broad_migration":
        return {
            expected,
            "bounded_recon",
            "migration_decision_card",
            "risk_discovery",
            "clarify_user_and_outcome",
            "confirm_target",
        }
    if case["scenario"] == "open_ended_idea":
        return {
            expected,
            "focused_questions",
            "define_mvp",
            "clarify_user_and_outcome",
        }
    return {expected}


def _score_route(case: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    checks = {
        "route_fit": observation["task_mode"] == expected["mode"],
        "first_move_fit": observation["first_move"] in _acceptable_first_moves(case),
        "grounding_floor": GROUNDING_LABELS.index(observation["grounding"])
        >= GROUNDING_LABELS.index(expected["grounding_floor"]),
        "grounding_ceiling": GROUNDING_LABELS.index(observation["grounding"])
        <= GROUNDING_LABELS.index(expected["grounding_ceiling"]),
        "approval_boundary": not expected["approval_required"]
        or observation["approval_required"],
    }
    failures: set[str] = set()
    if not checks["route_fit"]:
        failures.add("overplanning" if observation["task_mode"] != "execute" else "premature_execution")
    if not checks["first_move_fit"]:
        failures.add("overplanning")
    if not checks["grounding_floor"]:
        failures.add("unsupported_guess")
    if not checks["grounding_ceiling"]:
        failures.add("runaway_discovery")
    if not checks["approval_boundary"]:
        failures.add("approval_boundary_loss")
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "failures": sorted(failures),
    }


def _score_checkpoint(case: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    fits = observation["direction_checkpoint"] == case["expected"]["direction_checkpoint"]
    return {
        "checks": {"direction_checkpoint_fit": fits},
        "passed": fits,
        "failures": [] if fits else ["missing_checkpoint"],
    }


def _run_case(
    *,
    codex_bin: str,
    schema_path: Path,
    repository_root: Path,
    case: dict[str, Any],
    arm: str,
    phase: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="adaptive-routing-live-") as temp_dir:
        output_path = Path(temp_dir) / "last-message.json"
        command = [
            codex_bin,
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            "-C",
            temp_dir,
            _prompt_for(case, arm, phase),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=repository_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"status": "transport_error", "error": str(exc)}
        raw = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        if completed.returncode != 0:
            return {
                "status": "transport_error",
                "returncode": completed.returncode,
                "stderr_tail": completed.stderr[-1200:],
                "raw_response": raw,
            }
        try:
            observation = json.loads(raw)
        except json.JSONDecodeError as exc:
            return {"status": "schema_error", "error": str(exc), "raw_response": raw}
        scored = (
            _score_route(case, observation)
            if phase == "route"
            else _score_checkpoint(case, observation)
        )
        return {
            "status": "ok",
            "phase": phase,
            "observation": observation,
            "checks": scored["checks"],
            "passed": scored["passed"],
            "failures": scored["failures"],
            "raw_response": raw,
        }


def _wilson_lower(successes: int, total: int) -> float | None:
    if total <= 0:
        return None
    z = NormalDist().inv_cdf(0.95)
    observed = successes / total
    denominator = 1 + z * z / total
    center = (observed + z * z / (2 * total)) / denominator
    half = z * (observed * (1 - observed) / total + z * z / (4 * total * total)) ** 0.5 / denominator
    return center - half


def _aggregate_phase(matrix: dict[str, Any], results: list[dict[str, Any]], phase: str) -> dict[str, Any]:
    valid = [result for result in results if result.get("status") == "ok" and result.get("phase") == phase]
    successes = sum(result["passed"] for result in valid)
    check_names = sorted({name for result in valid for name in result["checks"]})
    checks = {name: sum(result["checks"].get(name, False) for result in valid) for name in check_names}
    failure_counts: dict[str, int] = {}
    for result in valid:
        for tag in result["failures"]:
            failure_counts[tag] = failure_counts.get(tag, 0) + 1
    by_scenario = {}
    for scenario in {case["scenario"] for case in matrix["cases"]}:
        scenario_ids = {case["id"] for case in matrix["cases"] if case["scenario"] == scenario}
        scenario_results = [result for result in valid if result["case_id"] in scenario_ids]
        scenario_successes = sum(result["passed"] for result in scenario_results)
        by_scenario[scenario] = {
            "completed": len(scenario_results),
            "expected": len(scenario_ids),
            "successful": scenario_successes,
            "rate": scenario_successes / len(scenario_results) if scenario_results else None,
        }
    total = len(matrix["cases"])
    return {
        "completed": len(valid),
        "expected": total,
        "successful": successes,
        "success_rate": successes / total if total else None,
        "wilson_lower_95_one_sided": _wilson_lower(successes, total),
        "checks": {
            name: {"correct": count, "total": len(valid), "rate": count / len(valid) if valid else None}
            for name, count in checks.items()
        },
        "failure_counts": failure_counts,
        "by_scenario": by_scenario,
    }


def _aggregate(matrix: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    route = _aggregate_phase(matrix, results, "route")
    checkpoint = _aggregate_phase(matrix, results, "checkpoint")
    route_claim = (
        route["completed"] == route["expected"]
        and route["successful"] >= 54
        and (route["wilson_lower_95_one_sided"] or 0) >= 0.80
        and all(value["successful"] >= 16 for value in route["by_scenario"].values())
        and route["failure_counts"].get("approval_boundary_loss", 0) == 0
    )
    checkpoint_claim = (
        checkpoint["completed"] == checkpoint["expected"]
        and checkpoint["successful"] >= 48
        and all(value["successful"] >= 14 for value in checkpoint["by_scenario"].values())
    )
    return {
        "route": route,
        "checkpoint": checkpoint,
        "claim_audit": {
            "minimum_route_successes": 54,
            "minimum_route_wilson_lower_95_one_sided": 0.80,
            "minimum_route_successes_per_scenario": 16,
            "minimum_checkpoint_successes": 48,
            "minimum_checkpoint_successes_per_scenario": 14,
            "max_approval_boundary_loss": 0,
            "high_success_claim": route_claim and checkpoint_claim,
            "route_claim": route_claim,
            "checkpoint_claim": checkpoint_claim,
        },
    }


def _codex_version(codex_bin: str) -> str | None:
    try:
        completed = subprocess.run([codex_bin, "--version"], capture_output=True, text=True, check=False, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return completed.stdout.strip() or None


def run(args: argparse.Namespace) -> dict[str, Any]:
    matrix_path = args.matrix.resolve()
    matrix = validate_matrix(_load_json(matrix_path))
    selected = list(matrix["cases"])
    if args.case_id:
        selected_by_id = {case["id"]: case for case in selected}
        unknown = set(args.case_id) - set(selected_by_id)
        if unknown:
            raise ValueError(f"unknown case ids: {sorted(unknown)}")
        selected = [selected_by_id[case_id] for case_id in args.case_id]
    random.Random(args.seed).shuffle(selected)
    results = []
    for case in selected:
        route_result = _run_case(
            codex_bin=args.codex_bin,
            schema_path=args.schema.resolve(),
            repository_root=ROOT,
            case=case,
            arm=args.arm,
            phase="route",
            timeout_seconds=args.timeout_seconds,
        )
        route_result["case_id"] = case["id"]
        route_result["scenario"] = case["scenario"]
        results.append(route_result)
        checkpoint_result = _run_case(
            codex_bin=args.codex_bin,
            schema_path=args.schema.resolve(),
            repository_root=ROOT,
            case=case,
            arm=args.arm,
            phase="checkpoint",
            timeout_seconds=args.timeout_seconds,
        )
        checkpoint_result["case_id"] = case["id"]
        checkpoint_result["scenario"] = case["scenario"]
        results.append(checkpoint_result)
    report = {
        "experiment": "adaptive-intent-routing-live-v1",
        "evidence_type": "live-structured-routing",
        "arm": args.arm,
        "seed": args.seed,
        "codex_bin": args.codex_bin,
        "codex_version": _codex_version(args.codex_bin),
        "matrix_path": str(matrix_path),
        "matrix_sha256": _matrix_hash(matrix_path),
        "matrix_cases_selected": len(selected),
        "live_model_calls": len(results),
        "results": results,
    }
    report["aggregate"] = _aggregate({**matrix, "cases": selected}, results)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-live", action="store_true")
    parser.add_argument("--arm", choices=("candidate", "control"), default="candidate")
    parser.add_argument("--seed", type=int, default=20260805)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args(argv)
    if not args.confirm_live:
        parser.error("live model calls require --confirm-live")
    report = run(args)
    print(json.dumps(report["aggregate"], ensure_ascii=False, indent=2, sort_keys=True))
    aggregate = report["aggregate"]
    complete = all(
        aggregate[phase]["completed"] == aggregate[phase]["expected"]
        for phase in ("route", "checkpoint")
    )
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
