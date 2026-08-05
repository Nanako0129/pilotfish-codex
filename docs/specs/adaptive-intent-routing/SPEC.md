# SPEC — Adaptive intent routing

- **ID:** `spec-adaptive-intent-routing`
- **Status:** Approved for implementation
- **Owner:** Miyago
- **Created:** 2026-08-05
- **Implementation approval:** Granted by Miyago on 2026-08-05

## Goal

Make Pilotfish choose an orchestration shape that matches the user's current
intent and the work's risk, rather than forcing every request through either a
full Plan or immediate execution. The system shall preserve user flexibility,
reduce unnecessary model time and cost, and detect direction drift before a
large amount of work becomes difficult to recover.

The feature belongs to Pilotfish's orchestration policy and routing evaluation.
It is not a standalone requirements-analysis agent or a generic thinking skill.

## Problem

The current policy already owns task framing, Plan synthesis, ambiguity
resolution, delegation, approval, and verification, but it does not explicitly
route among three different interaction shapes:

1. A clear, bounded execution request.
2. A clear but broad or high-impact change that needs discovery before a formal
   Plan.
3. An exploratory or underspecified request where the user and agent must
   jointly define the problem before planning.

Without this distinction, a complete Plan may be produced too early, users may
be asked to review details they did not yet decide, or a vague direction may be
treated as authorization for a large implementation.

## Scope

- Add an orchestration-level route decision with three initial modes:
  `execute`, `explore_then_plan`, and `co_discover`.
- Base the decision on semantic intent confidence, change impact, and
  reversibility, with rationale and unresolved decisions visible to the main
  session.
- Keep the full working Plan internally, while presenting concise user-facing
  decision cards at material product, authority, risk, or irreversible choices.
- Support provisional Plans that cover the next safe, testable slice without
  pretending that later details are already known.
- Bound discovery by risk and information value; do not require multi-agent
  debate or multiple alternatives for every task.
- Add slice-level direction checks with `CONTINUE`, `PIVOT`, and `ROLLBACK`
  dispositions.
- Reuse the existing main session, `scout`, `plan-verifier`, and `verifier`
  roles. Do not add a new universal requirements role or custom role.
- Extend offline route evaluation and fixtures so behavior claims are measured
  separately from native runtime dispatch evidence.

## Non-goals

- A deterministic keyword classifier such as routing every Nuxt request to one
  mode or every release request to another.
- A complete product-requirements engine that autonomously decides user intent.
- A requirement that users read or approve every line of an internal spec.
- An unconditional exploration phase, alternative generation, or repeated user
  questioning for routine work.
- A guarantee that the selected direction is always correct.
- A hook that tries to enforce semantic correctness before execution. Hooks and
  dispatch verifiers remain evidence and transport-boundary controls.
- Changing the installed role set, model bindings, native typed dispatch
  contract, or existing security and external-mutation approval boundaries.

## Terminology and route signals

The route decision is a policy-level judgment, not required to be a public
runtime JSON schema in the first implementation. It should expose these logical
fields:

| Signal | Values | Meaning |
|---|---|---|
| `task_mode` | `execute`, `explore_then_plan`, `co_discover` | Interaction and delegation shape |
| `intent_confidence` | `clear`, `partial`, `unclear` | How much product intent is actually determined |
| `change_impact` | `trivial`, `low`, `material`, `high`, `critical` | Expected blast radius and decision density |
| `discovery_budget` | `none`, `minimum`, `bounded`, `deep` | Grounding floor and exploration ceiling |
| `budget_exhausted` | `yes`, `no` | Whether the selected discovery ceiling was reached |
| `evidence_sufficient` | `yes`, `no` | Whether evidence supports the next gate |
| `reversible` | `yes`, `no`, `partial` | Whether the next action can be safely undone |
| `blocking_decisions` | bounded list | User choices that materially change the result |
| `next_gate` | discovery, approval, execution, direction_check | The next required control point |

Semantic ambiguity, technical uncertainty, and authority/risk uncertainty must
remain separate. The agent handles technical uncertainty through repository
inspection and bounded experiments; it surfaces product or authority choices
when no safe default exists.

The first implementation uses the three route modes as representative cases,
not an exhaustive classifier. `change_impact` uses five qualitative bands:
`trivial` for direct answers or no-write tasks, `low` for isolated reversible
work, `material` for module or user-behavior boundaries, `high` for migration,
release, or expensive-to-reverse work, and `critical` for destructive,
external, security-sensitive, or otherwise irreversible work.

Discovery has a grounding floor and a stopping ceiling. One logical discovery
unit is one targeted inspection, search, or reversible probe. The default
budgets are `none` (zero units), `minimum` (at least one grounding check and
up to two units), `bounded` (up to six units and one cheap probe), and `deep`
(up to ten units and two cheap probes). The agent may stop earlier when new
evidence no longer changes the decision. It must narrow, pause, or ask when
the floor cannot be met or the ceiling is exhausted.

## Route behavior

### `execute`

Use when the desired outcome and scope are clear. The next move may be a
bounded local action or an approval-gated external action; a clear release
request does not become an exploration route merely because authority is still
required. The main session may use a lightweight internal Plan and dispatch the
least expensive matching role. External writes, destructive operations,
release actions, and other existing approval gates remain mandatory; intent
clarity does not grant authority.

### `explore_then_plan`

Use when the direction is clear but the change is broad, migration-heavy,
cross-component, high-impact, or expensive to reverse. The main session first
creates an intent sketch, inspects the repository, records assumptions and
risks, and produces a bounded decision card. It then forms a provisional Plan
for the next slice. Bulk implementation waits until material product choices,
scope boundaries, and required approvals are resolved.

### `co_discover`

Use when the request describes an idea or broad outcome but not a stable
product problem, target user, MVP, or acceptance boundary. The main session
leads a divide-and-conquer conversation, may perform low-cost reconnaissance,
and progressively narrows the outcome, non-goals, and first experiment. It must
not convert an exploratory sentence into a large implementation contract.

## Progressive planning contract

Pilotfish shall maintain two views of planning:

- **Internal Plan:** assumptions, evidence, candidate interpretations,
  dependencies, risks, slices, acceptance, rollback, and open decisions.
- **User decision card:** an interactive, AskUserQuestion-style checkpoint with
  the current interpretation, proposed default, included and excluded scope,
  relevant material risk, a small set of questions with options and a
  recommendation, and the next reversible slice. Low-risk work may omit the
  card; material product, authority, risk, irreversible-cost, or unresolved
  direction choices require it.

The next executable slice must have a falsifiable outcome, exclusive ownership,
constraints, acceptance evidence, rollback or containment, and a stop
condition. Future slices may remain provisional. A Plan is not required to
resolve unknown implementation details that cannot affect the next gate.

Discovery is time- and value-bounded. Continue exploring when the result could
change the chosen route, product outcome, architecture boundary, safety,
irreversible cost, or acceptance. Stop exploring when a safe reversible probe
can answer the question more cheaply, when new evidence no longer changes the
decision, or when the declared discovery budget is exhausted. Exhaustion is a
reason to narrow, pause, or ask—not permission to silently guess.

## Direction checkpoints and recovery

At each stable integration boundary, the main session shall compare the current
state against the original outcome, non-negotiable constraints, and slice
acceptance. The check is behavior- and evidence-oriented, not a line-count or
diff-size review.

- `CONTINUE`: current evidence supports the intent and next slice.
- `PIVOT`: the user outcome still stands, but the current path or assumption
  should change; preserve useful evidence and re-plan from the checkpoint.
- `ROLLBACK`: a required invariant or acceptance condition was broken; stop new
  writes and return to the latest verified good checkpoint before salvaging
  isolated useful changes.

Direction review shall trigger early when the outcome is silently rewritten,
new assumptions accumulate without evidence, validation shifts to internal
structure instead of user behavior, repeated repairs do not improve the
acceptance signal, or the next step cannot be stated as a falsifiable test.

Recovery shall preserve the current evidence, identify the last verified good
checkpoint, classify whether the failure is intent, assumption, implementation,
or environment, and then choose rollback, pivot, or a bounded re-plan. It must
not continue repairing a large drift in place merely because substantial work
has already been invested.

## Architecture boundary

The orchestration policy owns route selection, budgets, delegation topology,
approval gates, checkpoints, and recovery semantics. Role instructions own the
quality and format of discovery, review, and verification evidence. The route
evaluator owns offline behavioral fixtures and abstention scoring. Native
dispatch and hooks prove transport and installed-role evidence only.

The main session remains the synthesis and accountability owner. `scout` is for
bounded evidence, `plan-verifier` challenges readiness and material direction
assumptions, and `verifier` can independently check a completed slice against
its exact outcome and acceptance. No role may silently turn an unclear product
request into write authorization.

## Architecture decisions

### ADR-1: Adaptive routing instead of one universal Plan flow

**Decision:** Select `execute`, `explore_then_plan`, or `co_discover` using
intent, impact, and reversibility.

**Reason:** A release operation, a framework migration, and an undeveloped
product idea have different uncertainty and cost profiles. A universal flow is
either wasteful or unsafe.

### ADR-2: Keep the feature in Pilotfish policy, not a new universal skill/role

**Decision:** Implement the routing contract in Pilotfish's policy and offline
evaluator, and use existing roles for evidence and gates.

**Reason:** A standalone thinking skill cannot control delegation, approval,
checkpoint, or recovery behavior. A new role would add coordination and make
the router less self-directed.

The existing `verifier` role also owns the narrowly named
`direction_checkpoint` contract; no new checkpoint role is added.

### ADR-3: Internal full Plan, external decision cards

**Decision:** Maintain complete internal planning evidence, but expose only
material decisions and the next slice to the user through an
AskUserQuestion-style interactive card.

**Reason:** Users should not need to review an exhaustive spec to collaborate,
but they must see decisions that change product outcome, authority, or
irreversible cost.

### ADR-4: Provisional Plans and progressive commitment

**Decision:** Require a complete contract only for the next executable slice;
keep later work provisional until evidence warrants commitment.

**Reason:** Early certainty is often unavailable, and forcing a perfect full
  spec makes vague requests unusable.

### ADR-5: Evidence-based checkpoints, not diff-size review

**Decision:** Direction checks compare observable outcomes and invariants, with
explicit `CONTINUE`, `PIVOT`, and `ROLLBACK` dispositions.

**Reason:** Large or small diffs can both be right or wrong; behavioral evidence
is closer to the user's actual goal.

### ADR-6: Adaptive, bounded discovery

**Decision:** Spend exploration effort according to likely decision impact and
reversibility, with explicit stop conditions and no unconditional debate.

**Reason:** More exploration can reduce error but can also dominate latency and
cost. The system must stop when additional information is not decision-relevant.

## Alternatives considered

| Alternative | Decision | Reason |
|---|---|---|
| Always require a complete Plan first | Rejected | Over-constrains vague ideas and creates false precision |
| Always execute the first clear interpretation | Rejected | Unsafe for migrations and product ambiguity |
| Add a universal requirements agent | Rejected | Adds a new role and does not solve authority or routing gates |
| Route by keywords | Rejected | Context and repository state determine risk and intent |
| Always generate multiple competing plans | Rejected | Excessive cost; alternatives are needed only when decision-relevant |
| Make it a standalone thinking skill | Rejected | Does not control dispatch, approval, or recovery |
| Use hooks to enforce semantic correctness | Rejected | Hooks cannot reliably infer product intent and would overclaim enforcement |

## Rabbit holes and safeguards

- Do not turn `intent_confidence` into pseudo-precise numeric scoring without
  calibration evidence.
- Do not create an infinite clarification loop; every discovery turn needs a
  decision purpose, budget, and next gate.
- Do not let a user who skips the spec accidentally approve hidden product
  decisions; surface them as concise cards.
- Do not treat a provisional Plan as permission for future slices.
- Do not promise rollback for external actions that are inherently irreversible;
  require approval and compensating recovery steps instead.
- Do not claim that offline route evaluation proves live model behavior or that
  a successful dispatch receipt proves semantic route quality.

## Resolved review decisions

1. Keep the upstream-style descriptive mode names `execute`,
   `explore_then_plan`, and `co_discover`. They are the first implementation
   examples, not an exhaustive scenario list.
2. Use five qualitative impact bands: `trivial`, `low`, `material`, `high`,
   and `critical`, with explicit examples instead of pseudo-precise scoring.
3. Use four bounded discovery budgets: `none`, `minimum`, `bounded`, and
   `deep`. Each has a grounding floor and a default ceiling measured in
   logical discovery units and cheap reversible probes.
4. Keep the existing `verifier` role and add the explicit
   `direction_checkpoint` contract with `CONTINUE`, `PIVOT`, and `ROLLBACK`.
   Insufficient evidence remains `INCONCLUSIVE` under the calibrated verifier
   boundary.
5. Use an AskUserQuestion-style decision card. Always show the current
   interpretation, proposed default, included and excluded scope, questions
   with options and a recommendation, and the next reversible slice when the
   card is required. Show material risk and authority or approval details only
   when relevant; omit the card for low-risk work with no blocking decision.

Miyago approved these decisions and the implementation scope on 2026-08-05.

## Approval gate

The review gate is complete. Implementation may update the source policy,
existing verifier contract, offline evaluator, fixtures, tests, and supporting
documentation within this specification. It must not change the installed
Codex home, the role manifest, native typed dispatch contract, or existing
security and external-mutation approval boundaries.
