---
id: spec-role-fitness-benchmark
title: Role Fitness Benchmark
status: proposed
created: 2026-08-04
updated: 2026-08-04
author: Miyago
approved_by: Miyago (planning only)
tags: [benchmark, routing, evaluation]
priority: high
---

## Requirements

- Measure why Sol/high is reserved for risk-triggered Plan review while
  Luna/low-medium remains the mechanical default.
- Measure role-relevant capability, not generic model intelligence. The
  existing exact artifact contract remains a transport and usage metric only.
- Publish separate planning-quality, mechanical-reliability, usage, and time
  values; no aggregate score may hide a failed quality gate.
- Keep Miyago's priority order: usage first, time second, quality sufficient
  for the role. Sol must demonstrate a material planning benefit before its
  added usage or latency is accepted.
- Reuse only the existing native receipt and rollout-ledger semantics. The new
  runner must replace the current broad environment, auth-copy, raw-session,
  and report-publication paths with the security gates below.

## Architecture / Plan

### Decisions

- **Decision:** Create a new `role-fitness-v1` cohort rather than extend the
  existing `usage-routing-v1` acceptance metric.
  - **Reason:** The current fixture accepts only byte-equivalent artifacts;
    it does not contain a plan, risk ledger, ownership decision, or downstream
    execution result to score.
  - **By:** Miyago (2026-08-04)

- **Decision:** Compare the installed roles in their actual jobs.
  - **Reason:** Planning cases compare Luna/xhigh and Sol/high through the
    `plan-verifier` contract. Mechanical cases compare Luna/medium and
    Sol/high through `mech-executor`. Terra is out of scope because it has no
    active binding.
  - **By:** Miyago (2026-08-04)

- **Decision:** The benchmark has three matched cohorts, capped at 60 scenario
  arms and 108 paid Codex process calls.
  - **Reason:** It yields role-specific evidence without treating a cheap
    routing decision as an open-ended model study.
  - **By:** Miyago (2026-08-04)

- **Decision:** No live role-fitness run may use the current benchmark auth and
  session-retention flow unchanged.
  - **Reason:** Security review found broad host-environment inheritance,
    readable auth placement, unbounded raw-session retention, and no enforced
    public-report projection.
  - **By:** Miyago (2026-08-04)

| Cohort | Cases × arms | Scenario arms | Paid stages | Purpose |
| --- | ---: | ---: | --- | --- |
| Plan review | 12 × Luna/xhigh, Sol/high | 24 | reviewer | Planning Quality Score |
| Mechanical execution | 12 × Luna/medium, Sol/high | 24 | executor → verifier | Execution Reliability Score |
| Split workflow | 6 × Luna/xhigh, Sol/high review | 12 | reviewer → executor → verifier | Sol escalation value |

### Security findings and dispositions

The following security-review findings are accepted as implementation gates.
None is accepted as a live-run exception. Their acceptance checks must pass
before the execution-approval request.

| Finding | Disposition | Required before live execution |
| --- | --- | --- |
| Auth file and inherited host secrets can reach a workspace-write trial | Fix | minimal environment allowlist, auth isolation proof, and outbound boundary test |
| Private ledgers and raw session material lack retention controls | Fix | `0700` encrypted private root, TTL audit, crash cleanup, and deletion-error failure |
| Public benchmark artifact has no allowlist-only projection | Fix | separate raw/public schemas, unknown-field rejection, and secret/path scanner |
| Hidden ledger has no tamper-evident precommitment | Fix | salted commitment, timestamped freeze record, and mutation rejection |
| Split handoff and stage attribution are underspecified | Fix | fresh homes, identity-free handoff schema, per-stage receipts, and reconciliation |

### Scorecards

Each plan fixture contains a hidden, frozen risk ledger. It assigns P0/P1/P2
weights of `5 / 3 / 1`, source evidence, minimum revision, and acceptance
check. The ledger is not shown to the model. The scorer runs before candidate
identity is joined to the result. It only accepts a source-anchored rubric
match; an ambiguous match is `inconclusive`, never a pass.

| Score | Formula | What it answers |
| --- | --- | --- |
| Risk coverage | caught ledger weight / total ledger weight | Did the review find the important problems? |
| Critical precision | supported P0/P1 findings / all claimed P0/P1 findings | Does it cry wolf? |
| Actionable revision rate | true findings with evidence, minimum revision, and acceptance check / true findings | Can the review be acted on? |
| Planning Quality Score | `100 × (0.50 × coverage + 0.25 × precision + 0.25 × actionable revision)` | Is this reviewer better for high-risk Plans? |
| Verified first-pass rate | mechanical cases accepted by the independent verifier on first submission / cases | Does the worker finish the job? |
| Rework-free rate | accepted cases requiring no repair pass / cases | How often is a result immediately usable? |
| Execution Reliability Score | `100 × (0.70 × first-pass + 0.30 × rework-free)` | Is this worker dependable for mechanical work? |

Usage fields remain raw input/output/cache tokens, weighted tokens, equivalent
cost, median wall time, and p95 wall time. They are displayed beside quality;
they are not mixed into either quality score.

### Scoring edge cases and aggregation

- The plan-review decision cohort must include at least four P0/P1 ledger
  entries and exactly four matched clean-control cases. It otherwise fails
  before a live run.
- Risk coverage and actionable revision aggregate micro-style across all
  ledger weights. Clean controls contribute no coverage denominator.
- Critical precision aggregates all claimed P0/P1 findings. A zero denominator
  is `1.0` only when the corresponding ledger contains no P0/P1 entry;
  otherwise it is `0.0`.
- Missing output, invalid structured verdict, missing source evidence, failed
  receipt, or unresolved scorer match yields `inconclusive`. Inconclusive
  outputs receive no quality credit and block automatic routing claims.
- Paired model deltas use case-level scores and a fixed-seed 10,000-resample
  percentile bootstrap. Risk-coverage inference resamples only the matched
  risk-bearing cases; every resample recomputes the micro weighted ratio.
  Clean controls are excluded from this denominator and reported separately as
  false escalations. Reports include the delta and 95% interval; no result is
  rounded before the gate is evaluated.
- A clean-control false escalation is any `REVISE`, invalid verdict, or
  inconclusive score on a fixture with an empty ledger. The fixed-seed paired
  bootstrap resamples all four clean controls and reports
  `false_escalation(Sol) - false_escalation(Luna)`. Invalid or inconclusive
  controls count as false escalations and cannot improve either candidate.

### Routing decision rule

Sol remains an automatic risk-triggered Plan-review tier only when all gates
pass against Luna/xhigh on the matched plan-review cohort:

1. Risk coverage improves by at least 10 points and the paired bootstrap 95%
   interval excludes zero.
2. Critical precision is not more than 10 points lower than Luna.
3. The split workflow's verifier-confirmed completion rate is no lower than
   Luna-review → Luna-executor by more than one of six matched cases.
4. Sol's clean-control false-escalation rate is at most 25% and no higher than
   Luna's; any additional Sol-only false escalation fails the automatic route.
5. The added Sol cost and p95 time are published as a premium, not hidden.

Luna remains the mechanical default only if its verified first-pass rate is at
least 90% and is not more than one of 12 matched cases below Sol. Once that
quality gate passes, lower weighted-token usage decides first and lower p95
wall time breaks a usage tie within 5%.

The README also reports the human-readable marginal result:

```text
critical-risk yield = additional supported P0/P1 findings per 100k extra weighted tokens
```

If any quality result is inconclusive, the automatic route fails closed. Sol
may still be manually requested, but the benchmark cannot claim it is justified
as a default escalation.

### Data and scoring boundary

- Plan-review fixtures are realistic Plan documents with predeclared source
  context, risks, dependencies, acceptance evidence, and stop conditions.
- Mechanical fixtures are isolated worktrees with allowed paths and an
  acceptance script. They must test a useful change, not exact prose.
- The split cohort sends the reviewed Plan to the same Luna/medium executor;
  only the reviewer model differs.
- Every split fixture provides an original Plan plus pre-frozen, ledger-bound
  revision fragments. The runner applies fragments mechanically; no reviewer
  or executor authors a Plan revision.
- A valid `READY` hands off the original Plan only for a clean-control fixture.
  A valid `REVISE` creates an execution-approved Plan by applying exactly the
  matched revision fragments in stable order. Executor admission after
  `REVISE` requires one or more unambiguous supported ledger matches, nonempty
  `revision_ids`, a derived Plan hash distinct from the original, and a passed
  Plan validator. Any unsupported or ambiguous finding, including P2, makes a
  mixed `REVISE` terminal. A risky fixture with `READY`, an invalid or
  inconclusive verdict, or a failed Plan validation is terminal and never
  starts execution.
- The execution-approved handoff has exactly `scenario_id`, `fixture_hash`,
  `original_plan_hash`, `approved_plan_hash`, `ledger_commitment`,
  `revision_ids`, and `review_score_hash`. The runner owns creation; the
  validator owns schema and hash checks before executor admission.
- Fixture hashes, model binding, prompts, receipt correlation, usage ledgers,
  and scorecard versions are retained in the sanitized report.
- The private risk ledger and raw trial material live in a Miyago-owned,
  explicit, mode-`0700`, non-symlink root on an encrypted local volume. The
  runner never creates a default persistent location. Miyago retains the ledger
  and audit index through result approval; their hashes, not contents, enter
  the sanitized report.
- Raw stdout and session JSONL exist only in a per-stage private directory long
  enough to derive native metrics. The runner must then remove them, check every
  deletion result, and turn cleanup failure into a failed scenario.
- The private root has a 30-day TTL. Startup runs a permission and expiry audit;
  stale material is reported and blocks a run until Miyago explicitly resolves
  it. The benchmark never silently ignores a cleanup failure.
- Before a dry run, the scorer writes a timestamped commitment for each fixture:
  `HMAC-SHA256(salt, fixture_hash || ledger_bytes || rubric_bytes)`. The private
  salt, ledger, and rubric are immutable for the run; any later mismatch
  invalidates all affected scores.
- The public report is an allowlist-only `role-fitness-public-v1` projection.
  It may contain cohort aggregates, rubric and commitment hashes, metric
  versions, and limits. It rejects free text, prompts, fixture contents,
  source snippets, absolute paths, identities, unknown fields, and secret-like
  values before writing under `docs/benchmarks`.

### Ownership and freeze points

| Surface | Exclusive owner | Freeze point |
| --- | --- | --- |
| Fixture and hidden ledger | Miyago | signed manifest before any dry run |
| Runner, validator, and receipt accounting | main-session implementer | offline suite before execution approval |
| Deterministic source-rubric scorer | main-session implementer | scorecard hash before any live call |
| Ambiguous score disposition | Miyago | before aggregate approval; unresolved is inconclusive |
| Sanitized aggregate and README publication | Miyago | after reviewed report approval |

No model sees a ledger or candidate identity. The scorer receives an anonymous
output packet and source-rubric IDs only. A local audit index maps anonymized
packet hashes to candidate bindings and remains in Miyago's private root.

The runner uses a minimal environment allowlist and rejects inherited cloud,
SSH, API-key, token, password, proxy, and credential-path variables. Runtime
authentication and inference traffic may originate only from the parent Codex
client, via TLS on port 443 to an operator-pinned official Codex endpoint
allowlist. Model-accessible tool subprocesses have no outbound egress and no
read path to `auth.json` or the private root. A sentinel fixture before any
paid call proves that auth, sentinel environment values, and private-root files
are unreadable from tools and absent from stdout, session material, reports,
and permitted parent requests. If the native runtime cannot enforce either the
parent allowlist or zero tool egress, the live benchmark is blocked.

### Stage accounting, budgets, and stops

Each stage executes as one fresh parent plus exactly one named child in an
isolated home. A scenario arm receives a stable ID; every stage receipt and
native parent/child ledger binds to that ID. The scenario's usage and wall time
are the deduplicated sum of all of its stages. Credential-free, hash-bound
handoff artifacts are the only data copied between stages. The handoff has an
allowlisted, identity-free schema, rejects model names and extra fields, and is
validated and hashed before the next fresh stage starts. Each stage reports its
usage separately; the scenario report reconciles the exact parent and child
rollout IDs before summing them.

The split-workflow branch is deterministic: `READY` on a clean control starts
the executor with the original Plan; a valid `REVISE` starts it only with the
validated derived Plan; every other verdict terminates before execution. The
fresh outcome verifier runs only after an executor stage and records whether
the approved Plan produced a verified completion. Offline tests cover every
branch and prove no executor starts from an unapproved handoff.

| Fixture | Review result | Transition |
| --- | --- | --- |
| Clean control | exact `READY` | execute original Plan |
| Clean control | `REVISE`, invalid, or inconclusive | terminal false escalation |
| Risk-bearing | supported-only `REVISE` with nonempty fragment set | validate and execute derived Plan |
| Risk-bearing | `READY`, zero-match, unsupported, ambiguous, or mixed `REVISE` | terminal; no executor |

| Cohort | Scenario arms | Stages per arm | Maximum paid processes |
| --- | ---: | ---: | ---: |
| Plan review | 24 | 1 | 24 |
| Mechanical execution | 24 | 2 | 48 |
| Split workflow | 12 | 3 | 36 |
| Total | 60 | — | 108 |

The hard live limits are 60 scenario arms, 108 paid processes, and six hours of
cumulative wall time. Admission closes at five hours and 50 minutes, leaving a
single 10-minute stage timeout as the only permitted time overshoot. There are
no automatic retries. Equivalent cost `$30` and `8,000,000` weighted tokens are
settled stop points, not claimed hard maxima: the Codex CLI does not currently
expose a proven per-call token or cost kill switch. Before a paid run, the
implementation must either prove a per-stage upstream limit and reserve it at
admission, or keep the benchmark dry-run only. A failed binding receipt,
fixture or ledger hash mismatch, private-root violation, session redaction
failure, metric correlation failure, or invalid handoff aborts the cohort
immediately. Any additional replicate is a new, separately approved run with
its own cap.

### Reporting and chart contract

The README replaces the ambiguous contract pass-rate headline with two panels:

1. **Planning quality:** risk coverage, critical precision, actionable revision
   rate, Planning Quality Score, Sol premium, and critical-risk yield.
2. **Mechanical delivery:** verified first-pass rate, rework-free rate,
   Execution Reliability Score, weighted tokens, equivalent cost, and p95
   wall time.

The chart calls the values `planning quality` and `execution reliability`, not
`intelligence`. It labels every cohort size and states that its result is
specific to this repository's versioned fixtures.

## Tasks

- [ ] Freeze 12 plan-review, 12 mechanical, and 6 split-workflow fixtures;
      write their hidden risk ledgers, source-rubric IDs, and acceptance scripts
      before any run.
- [ ] Implement an isolated `benchmark_role_fitness.py` runner that reuses the
      native-ledger semantics without changing `usage-routing-v1`. It must use
      the new auth, environment, retention, publication, commitment, and
      handoff gates.
- [ ] Add validators and offline tests for fixture hashes, ledger schema,
      anonymous scoring, model bindings, report redaction, stage accounting,
      review-to-execution branches, resource admission, security sentinel
      behavior, cleanup recovery, bootstrap edge cases, and all decision gates.
- [ ] Run an offline dry run that proves every role binding and scorecard path.
- [ ] Obtain explicit execution approval, then run at most 60 scenario arms
      and 108 paid processes within the declared resource caps.
- [ ] Review the sanitized aggregate, fail closed on an inconclusive score, and
      decide whether the Sol escalation remains automatic.
- [ ] Generate the two-panel README SVG and update benchmark documentation only
      after Miyago approves the reviewed aggregate.

## Files

- `docs/specs/role-fitness-benchmark/SPEC.md` - approved experiment contract.
- `install/benchmark_role_fitness.py` - new isolated live and dry-run harness.
- `tests/test_benchmark_role_fitness.py` - offline contract and gate coverage.
- `docs/benchmarks/role-fitness-v1/` - sanitized manifest, aggregate, and
  metric definitions.
- `docs/assets/role-fitness-evidence.svg` - post-review README chart.
- `README.md` - role-fit evidence and limitation disclosure after results.

## Notes

- `usage-routing-v1` remains the baseline for native transport, usage, and
  latency. Its exact-artifact acceptance does not become a planning score.
- This benchmark evaluates Sol as a bounded reviewer, not a free-form Plan
  author. It therefore supports the installed orchestration contract directly.
- Sixty trials are the initial budget. A second paired replicate requires new
  approval and is allowed only if a decision gate is still statistically
  ambiguous or a fixture is invalid.
