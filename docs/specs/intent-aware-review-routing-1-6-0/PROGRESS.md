# PROGRESS — intent-aware-review-routing-1-6-0

## Status

- Overall: implementation complete; security readiness pending
- Current phase: S0 — independent security review gate
- Last updated: 2026-08-06

## Evidence

- v1.5.1 is released and clean on the current branch.
- Existing adaptive routing separates `task_mode` from authority and approval.
- Existing role-fitness evidence does not promote automatic Sol switching;
  native adjudication remains cost-performance score 5/10.
- Security-reviewer delegation did not return a completed artifact before the
  implementation turn; security readiness remains an explicit gate.
- A second bounded security-reviewer attempt also timed out without findings;
  this is recorded as `INCONCLUSIVE`, not as a pass.

## Slice tracking

- [ ] S0 — security findings, dispositions, and executable slice envelope
- [x] S1 — review-intent signal and policy contract
- [x] S2 — mandatory hook contract isolation
- [x] S3 — scheduler/adjudicator adapter and receipt evidence
- [x] S4 — offline/live Matrix and scorecard extension
- [x] S5 — docs, compatibility, and release evidence

## Release evidence

- Offline Matrix: 60 cases (5 scenario families × 4 intent variants × 3 repeats).
- Local runtime Matrix: 60/60 intent accuracy, 60/60 risk-category accuracy,
  30/30 redacted-signal validation, 60/60 hook-process execution, 60/60
  Sol-trigger accuracy, and 100% cross-variant review-gate parity. This
  validates the local hook contract, not a paid model cohort.
- Directional regrade of the existing 3-case native content fixture reports
  baseline quality efficiency 96.50, switched efficiency 80.47, delta -16.03
  quality-points per weighted-token cost unit; the quality-adjusted metric does
  not promote the switch and the historical fixture is not a new formal cohort.
- Live adjudicator evidence now covers 12 cases (4 clean + 8 risk): 12/12
  accepted, 2 disagreements adjudicated by Sol, zero false escalations and
  zero inconclusive cases. Quality delta is +5.87, but CI low is 0.00,
  weighted-token premium is +101.36%, and quality-adjusted efficiency falls
  from 30.97 to 16.86 (delta -14.11); score remains 5/10.
- Targeted Python tests cover hook parsing, signal validation, scheduler
  projection, routing evaluation, Matrix generation, and scorecard metrics.
- The live report covers all 12 plan-review fixtures in the bounded run. The
  independent security-reviewer artifact is still missing, so no security-
  ready claim is made.

## Local security checks

- `classify_review_intent` abstains on quoted, negated, conflicting, oversized,
  and malformed input; the runtime Matrix covers the first three categories.
- The signal is redacted and turn-scoped; `validate_signal` rejects unknown
  fields, invalid provenance, unsorted/unknown risk categories, and mode/review
  mismatches.
- The scheduler projection rejects a false `mandatory_review` downgrade for
  security or compound-risk signals.
- Marker and transcript integrity remain covered by the existing hook test
  suite, including symlink, size, identity, duplicate-child, and wrong-task
  cases.
- These local checks do not replace the missing independent security review.
