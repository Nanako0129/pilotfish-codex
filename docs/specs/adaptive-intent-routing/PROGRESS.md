# PROGRESS — adaptive-intent-routing

## Status

- Overall: Q1-Q5 initial implementation complete; release evidence pending
- Current phase: Phase 4 follow-up — documentation and release evidence
- Implementation: Approved by Miyago; source changes are bounded by SPEC.md
- Last updated: 2026-08-05

## Phase tracking

| Phase | Status | Exit evidence |
|---|---|---|
| Batch 0 — specification review | Completed | Approved SPEC, resolved open questions, confirmed scope |
| Phase 1 — Pilotfish policy contract | Completed | Updated policy and verifier contracts |
| Phase 2 — Offline route evaluation | Completed | Versioned route fixtures and passing targeted tests |
| Phase 3 — Direction checkpoints and recovery | Completed | Checkpoint fixtures, safety validation, and passing tests |
| Phase 4 — Documentation and release evidence | Pending | Reviewed report and synchronized user documentation |

## Review boundary

The review boundary was explicitly cleared by Miyago on 2026-08-05. Current
implementation changes are limited to the policy template, the existing
verifier contract, offline evaluator, fixtures, tests, and supporting docs.
Hooks, installed Codex state, the role manifest, and native dispatch transport
remain unchanged.

## Q1-Q5 initial completion evidence

- Q1: upstream-style descriptive route names retained.
- Q2: five qualitative impact bands cover the initial examples and future
  distinctions without pseudo-precise scoring.
- Q3: four discovery budgets enforce a grounding floor and stopping ceiling;
  exhausted insufficient evidence must abstain at a discovery or approval gate.
- Q4: the existing `verifier` role supports the explicit
  `direction_checkpoint` contract and `CONTINUE`/`PIVOT`/`ROLLBACK` outcomes.
- Q5: material choices use an adaptive AskUserQuestion-style decision card;
  low-risk work can omit it.
- Targeted verification: 177 tests passed, including route, checkpoint,
  template, policy, dispatch, benchmark, hook, and smoke coverage.

## Initial qualitative experiment

The first A/B smoke run is recorded in `EXPERIMENT-RESULTS.md`. The adaptive
candidate selected the expected interaction shape for all three representative
prompts and kept release approval separate from route selection. The control
arm over-planned the clear release and migration prompts and used generic
advice for the product idea. This is directional evidence only; it is not a
statistical significance or live dispatch claim.
