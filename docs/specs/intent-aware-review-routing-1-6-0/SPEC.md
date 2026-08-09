---
id: spec-intent-aware-review-routing-1-6-0
title: Intent-aware review routing for Pilotfish 1.6.0
status: in_progress
created: 2026-08-06
updated: 2026-08-06
author: Miyago
priority: high
tags: [routing, intent, hook, adjudication, benchmark]
---

## Goal

Add a turn-scoped `review_intent` signal without conflating it with the
existing `task_mode`. Explicit requests for speed or strict review may change
optional review scheduling, while the existing authority, safety, approval,
and native role-binding boundaries remain intact.

## Decisions

1. `review_intent` is `fast`, `default`, or `strict` and is independent of
   `task_mode`.
2. Only clear explicit natural-language cues produce a signal. Missing,
   conflicting, negated, quoted, or ambiguous cues fall back to the existing
   risk policy.
3. The signal applies to the current turn only. No session preference is
   persisted in 1.6.0.
4. `fast` skips optional review and Sol on non-mandatory work. It never skips
   required tests, approval, permission, security, irreversible, external,
   release, typed-dispatch, or fixed-binding controls.
5. `codex-auto-review` owns optional scheduling. Pilotfish emits only a
   versioned, redacted advisory signal and keeps the existing hook as the
   mandatory review gate.
6. Existing `plan-verifier` remains Sol/high for readiness. A separate
   `semantic_adjudication` task may use the same fixed binding only after a
   fingerprinted Luna disagreement. `verifier` remains Luna/xhigh for outcome
   and direction verification.
7. No exact or maximum Codex version is introduced. Existing minimum
   compatibility remains the only version constraint.

8. The primary human-facing efficiency metric is quality-adjusted cost
   efficiency: first require candidate quality to meet the baseline quality
   floor with a non-negative paired confidence bound, then maximize quality
   points per equivalent-cost unit. A cheaper lower-quality route receives no
   efficiency credit and cannot promote automatic routing.

## Signal contract

The UserPromptSubmit signal contains only:

```json
{
  "schema": 1,
  "session_id": "...",
  "turn_id": "...",
  "review_intent": "fast|default|strict",
  "source": "explicit",
  "scope": "turn",
  "confidence": "clear",
  "risk_categories": ["security"],
  "optional_review": "skip|existing_policy|expanded"
}
```

Prompt text, model names, role names, and arbitrary scheduler instructions are
never included. A missing or malformed consumer signal must not weaken the
existing policy. A semantic adjudication child cannot satisfy the mandatory
`automatic_plan_review` gate.

## Required enforcement paths

- Host/Codex permission and approval controls remain authoritative for external,
  release, destructive, and irreversible operations.
- The orchestration policy continues to produce `approval_required` for those
  operations independently of `review_intent`.
- The Pilotfish Stop hook enforces only the existing independent Plan-review
  trigger and accepts only its exact readiness task contract.
- Optional scheduler failure is a no-op for optional review, not permission to
  claim review completion.

## Slices

- [ ] S0 — record security review findings and create the executable envelope.
- [x] S1 — add the explicit review-intent signal and policy precedence.
- [x] S2 — isolate mandatory hook evidence from optional adjudication.
- [x] S3 — add the scheduler/adjudicator contract and typed receipt checks.
- [x] S4 — add the 60-group offline and 36-observation live Matrix contract.
- [x] S5 — update release documentation and compatibility evidence.

## Acceptance

- No-intent cases preserve the 1.5.1 route corpus behavior.
- Clear intent is classified correctly in at least 95% of live observations;
  ambiguous and conflicting cases default correctly.
- Mandatory approval and review boundaries are preserved in 100% of negative
  cases, including when the optional consumer is absent or failing.
- Automatic Sol promotion uses the existing scorecard gates: positive paired
  quality and switch-value confidence intervals, no extra false escalation or
  inconclusive result, and the documented token/wall-time caps or the
  documented risk-coverage exception.
- Reports include `quality_adjusted_cost_efficiency`, its cost basis, baseline
  and candidate efficiency, quality floor, and eligibility. It is descriptive
  until the existing score-8/9 gates also pass.
- The local runtime Matrix must report intent, category, signal-contract, and
  Sol-trigger accuracy separately from model-quality and cost measurements.
- If promotion fails, intent routing may ship while automatic Sol remains
  explicit, mandatory-risk-only, or disagreement-gated.

## Quality-first cost benchmark

The live 12-case adjudicator cohort is also evaluated against the author's
quality-first value: a candidate must meet Luna's quality floor, then pass if it
is cheaper than pure Sol or pure Terra, or if it has a confidence-supported
quality win over Luna. The recorded result is
`quality-first-cost-frontier.json`; it passes the cost branch (`$0.430` versus
`$2.932` pure Sol and `$1.364` pure Terra) but not the quality-win branch because
the paired confidence lower bound is `0.00`. This is directional evidence, not
automatic Sol promotion. The evaluator records a source-consistency warning
when the sanitized summary and source reports disagree on adjudication count.

## Security gate

Before implementation is declared ready, a read-only security review must cover
intent parsing, signal redaction, downgrade resistance, marker integrity,
transcript evidence, duplicate scheduling, and fail-open/fail-closed behavior.
Every P0/P1 finding requires an explicit `FIX`, `DEFER`, or evidence-backed
`REJECT` disposition and a recheck.

Current status: local checks cover these paths and the consumer rejects a
mandatory-review downgrade, but the independent security-reviewer attempt
timed out twice and remains `INCONCLUSIVE`; this slice is not security-ready.

## Rollback

Disable the optional signal consumer or revert to the 1.5.1 hook/policy
projection. Mandatory approval and Plan-review enforcement remains active during
rollback.
