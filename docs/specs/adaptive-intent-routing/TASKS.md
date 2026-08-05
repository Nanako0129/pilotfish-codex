# TASKS — adaptive-intent-routing

> Draft only. No implementation is authorized until `SPEC.md` is reviewed and
> approved by Miyago.

## Batch 0 — specification review

- [ ] Review the three-mode routing contract and rename modes if needed.
- [ ] Resolve the impact rubric, discovery-budget policy, and checkpoint
      contract open questions.
- [ ] Confirm that no new custom role is required.
- [ ] Approve the scope and acceptance conditions before source changes.

## Phase 1 — Pilotfish policy contract

- [ ] Add route-mode decision cues and the
      intent/impact/reversibility signals to
      `templates/agents-md.orchestration.md`.
- [ ] Define the boundary between internal Plan content and user-facing decision
      cards in the policy.
- [ ] Add provisional-plan, discovery-budget, and direction-checkpoint rules.
- [ ] Update the existing role instructions only where their evidence contract
      needs to support the selected mode; do not add a universal requirements
      role.

## Phase 2 — Offline route evaluation

- [ ] Extend `install/evaluate_dispatch.py` with mode-aware decision validation,
      abstention, rationale, and role/approval expectations.
- [ ] Add fixtures for clear bounded execution, broad framework migration,
      underspecified product discovery, irreversible release work, and
      misleading keyword/context pairs.
- [ ] Keep route-choice evaluation separate from native typed-dispatch receipts
      and live quota-spending probes.
- [ ] Add unit tests for route decisions, discovery budget exhaustion, and
      invalid or overconfident classifications.

## Phase 3 — Direction checkpoints and recovery

- [ ] Specify the exact checkpoint input and `CONTINUE`/`PIVOT`/`ROLLBACK`
      disposition mapping using existing verifier boundaries.
- [ ] Add offline fixtures for silent goal rewrite, unsupported assumption,
      repeated repair failure, and last-known-good recovery.
- [ ] Verify that external or irreversible operations retain existing approval
      and containment rules.

## Phase 4 — Documentation and release evidence

- [ ] Update `docs/design.md` with the adaptive routing boundary and its limits.
- [ ] Update README behavior claims only after reviewed evaluator results.
- [ ] Record cost, latency, abstention, false-direct-execution, and
      false-overexploration results in a versioned report.
- [ ] Run the full offline test suite and any explicitly approved live smoke;
      do not run quota-spending probes in CI.
