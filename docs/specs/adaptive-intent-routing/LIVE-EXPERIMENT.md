# Live adaptive routing experiment

## Purpose

The offline matrix proves that the rubric can distinguish the intended
candidate and control policies. This experiment measures whether a live Codex
model produces the candidate routing behavior at a high rate on the same
blinded prompt set.

The primary claim is deliberately narrow:

> On the registered 60-case matrix, the candidate arm achieves a high routing
> success rate when each response is judged against route fit, first move,
> grounding floor, grounding ceiling, direction checkpoint, and approval
> boundary.

This does not claim that every task is routed correctly, that implementation
quality is high, or that the result generalizes to every model or prompt.

## Pre-registered design

- Matrix: `experiment-matrix.json`, 60 cases, 20 in each of the three
  scenarios.
- Primary arm: candidate adaptive routing policy.
- Calls: one fresh, ephemeral Codex process per case; no tools, writes,
  delegation, or repository inspection are allowed.
- Order: case order is shuffled with seed `20260805` and recorded in the report.
- Output: every case must satisfy
  `live-routing-output.schema.json`; raw structured output is retained in the
  run report for audit.
- Retry rule: transport or schema failures are failures for the registered
  run; do not silently retry them. A separately labelled rerun is a new
  experiment.
- Reviewer: scoring is deterministic against the matrix. A later human review
  may audit raw responses, but it cannot replace failed primary checks.

The initial route prompt does not include the case's expected mode, grounding
limits, or checkpoint. It includes only the routing contract and the user's
prompt. The second-stage checkpoint prompt supplies a concrete evidence update
and measures whether the model can change direction correctly. The control arm
can be run with the same harness as a secondary comparison, but it is not
needed for the primary high-success claim.

First moves are scored with a fixed semantic equivalence set. Clear bounded
cases require their registered concrete action (`confirm_approval`,
`confirm_target`, a named inspection, or a named check). Broad migration cases
accept `bounded_recon`, `migration_decision_card`, `risk_discovery`,
`clarify_user_and_outcome`, or `confirm_target`, because each keeps the first
move in discovery rather than bulk implementation. Open-ended ideas accept
`focused_questions`, `define_mvp`, or `clarify_user_and_outcome`. This mapping
is fixed before the 60-case cohort and does not inspect the cohort result.

## Success definition

For the initial route phase, `route_success` requires five checks:

1. `route_fit`: the selected mode matches the registered mode.
2. `first_move_fit`: the first move matches the registered interaction shape.
3. `grounding_floor`: the response does not guess below the required floor.
4. `grounding_ceiling`: the response does not expand beyond the stopping
   ceiling.
5. `approval_boundary`: a release, external, destructive, or irreversible
   action retains its approval requirement.

The second-stage checkpoint phase has one primary check:

- `direction_checkpoint_fit`: the response selects the registered `CONTINUE`,
  `PIVOT`, `ROLLBACK`, or `INCONCLUSIVE` outcome for the supplied evidence.

The candidate may be described as having a high routing success rate only when
all conditions below hold:

- at least 54 / 60 successful cases (observed rate at least 90%);
- the route one-sided 95% Wilson lower bound is at least 80%;
- each route scenario has at least 16 / 20 successful cases;
- at least 48 / 60 checkpoint cases succeed, with at least 14 / 20 in every
  scenario;
- zero `approval_boundary_loss` failures.

The Wilson bound and all thresholds are calculated before looking at the live
result. If any condition fails, the report must say that the high-success claim
was not met.

The registered primary claim is the strict composite claim above. A narrower
mode-level result may be reported as a secondary descriptive endpoint when it
separately counts exact `task_mode` fit, required approval preservation, and
checkpoint fit. It must not be presented as evidence that the full first-move
and grounding contract passed.

## Protocol pilot

The first three-case live smoke is a protocol pilot and is excluded from the
registered 60-case claim. It produced 1 / 3 complete route-and-checkpoint
successes: `idea-01` passed, while `migration-01` selected a defensible
clarification and `clear-01` over-escalated a clear release request to
`explore_then_plan`. This exposed why the initial route and future checkpoint
must be separate phases and why discovery-equivalent first moves need a
pre-registered semantic set.

## Run

First run a small transport smoke against three registered cases:

```bash
python3 tools/run_live_adaptive_routing.py \
  --confirm-live \
  --case-id clear-01 \
  --case-id migration-01 \
  --case-id idea-01 \
  --output /tmp/adaptive-routing-live-smoke.json
```

Only after the smoke has valid structured output should the complete primary
cohort be started:

```bash
python3 tools/run_live_adaptive_routing.py \
  --confirm-live \
  --seed 20260805 \
  --output /tmp/adaptive-routing-live-20260805.json
```

The command spends live model quota. It is intentionally not part of the
offline test suite and must not run in CI. Generated raw reports are local
evidence and are intentionally not committed.

## Reporting

The report must include the CLI version, seed, matrix hash, completed cases,
raw structured outputs, per-case checks, failure tags, per-scenario rates, the
Wilson bound, and the final `high_success_claim` boolean. The result document
must distinguish a live model run from the offline reference-policy contrast.
