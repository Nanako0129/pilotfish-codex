# TASKS — adaptive-intent-routing

> Approved by Miyago on 2026-08-05. Implementation remains bounded by
> `SPEC.md` and must not change the installed Codex home or native dispatch
> contract.

## Batch 0 — specification review

- [x] Review the three-mode routing contract and retain upstream-style names.
- [x] Resolve the five-band impact rubric, four-band discovery-budget policy,
      and checkpoint contract.
- [x] Confirm that no new custom role is required.
- [x] Approve the scope and acceptance conditions before source changes.

## Phase 1 — Pilotfish policy contract

- [x] Add route-mode decision cues and the
      intent/impact/reversibility signals to
      `templates/agents-md.orchestration.md`.
- [x] Define the boundary between internal Plan content and user-facing decision
      cards in the policy.
- [x] Add provisional-plan, discovery-budget, and direction-checkpoint rules.
- [x] Update the existing role instructions only where their evidence contract
      needs to support the selected mode; do not add a universal requirements
      role.

## Phase 2 — Offline route evaluation

- [x] Extend `install/evaluate_dispatch.py` with mode-aware decision validation,
      abstention, rationale, and role/approval expectations.
- [x] Add fixtures for clear bounded execution, broad framework migration,
      underspecified product discovery, irreversible release work, and
      misleading keyword/context pairs.
- [x] Keep route-choice evaluation separate from native typed-dispatch receipts
      and live quota-spending probes.
- [x] Add unit tests for route decisions, discovery budget exhaustion, and
      invalid or overconfident classifications.

## Phase 3 — Direction checkpoints and recovery

- [x] Specify the exact checkpoint input and `CONTINUE`/`PIVOT`/`ROLLBACK`
      disposition mapping using existing verifier boundaries.
- [x] Add offline fixtures for silent goal rewrite, unsupported assumption,
      repeated repair failure, and last-known-good recovery.
- [x] Verify that external or irreversible operations retain existing approval
      and containment rules.

## Phase 4 — Documentation and release evidence

- [x] Update `docs/design.md` with the adaptive routing boundary and its limits.
- [ ] Update README behavior claims only after reviewed evaluator results.
- [ ] Record cost, latency, abstention, false-direct-execution, and
      false-overexploration results in a versioned report.
- [ ] Run the full offline test suite and any explicitly approved live smoke;
      do not run quota-spending probes in CI.
