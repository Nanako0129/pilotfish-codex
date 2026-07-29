<!-- pilotfish-codex:begin -->
<!-- pilotfish-codex v1.3.2 -->
<!-- markdownlint-disable-next-line MD041 -->
### Orchestration

Main-session policy. If you are running as a subagent role (`scout`,
`plan-verifier`, `security-reviewer`, `mech-executor`, `executor`, `verifier`,
or `security-executor`), ignore this section and complete the task yourself
without further delegation.

Use the supplied role agents for bounded discovery, execution, and fresh-context
verification while keeping task framing, Plan synthesis, architecture,
ambiguity resolution, integration, and final judgment in the main session.
Complete small, local, already-stable work directly.

| Role | Boundary |
|---|---|
| `scout` | Broad or focused read-only repository reconnaissance |
| `plan-verifier` | Pre-approval Plan challenge; `READY` or `REVISE` |
| `security-reviewer` | Pre-approval read-only security evidence |
| `mech-executor` | Fully specified mechanical implementation |
| `executor` | Bounded implementation requiring local judgment |
| `verifier` | Calibrated completed-work falsification; `CONFIRMED`, `REFUTED`, or `INCONCLUSIVE` |
| `security-executor` | Approved security-sensitive implementation |

#### Decision cues

Treat role fit as an active delegation signal. The main session should not
wait for the user to name a subagent: classify each bounded workstream and,
when the dispatch brake passes, proactively delegate it to the least expensive
matching typed role. In particular:

- For parallel independent discovery, send bounded, read-only, independently
  scoped reconnaissance to `scout`. If two or more reconnaissance surfaces are
  independent, start them in parallel and give each child an exclusive surface
  and stop condition.
- Send a material Plan to `plan-verifier` before approval, and send
  pre-approval security evidence to `security-reviewer`.
- Send fully specified mechanical repetition to `mech-executor` under the
  qualifying default below, and send an approved, bounded implementation
  requiring judgment to `executor`.
- Send an approved security-sensitive implementation to `security-executor`.
- After a non-trivial implementation, send the integrated result to the fresh
  `verifier` for an independent refutation pass.

The parent session remains responsible and accountable throughout: it frames
the request, chooses the role(s), supplies complete briefs, reconciles findings,
integrates writes, resolves conflicts, and makes final judgment. Delegation is
not required for a small, local, already-stable edit or a tightly coupled
unknown bug; keep those in the parent when coordination would cost more than
direct work.

For large, ambiguous, architectural, risky, or explicitly plan-first work, use
this lifecycle:

| Phase | Gate | Eligible delegation |
|---|---|---|
| Discovery | Stabilize the question, allowed scope, evidence format, and stop condition. The final implementation may remain unknown. | Bounded read-only `scout` work on disjoint evidence surfaces. |
| Plan | The main session synthesizes one Plan. Large work uses a program envelope plus independent slices with stable IDs, outcome, scope, non-goals, owners, prerequisites, acceptance that proves the slice outcome, rollback, slice-local budget, and stop conditions. | A fresh `plan-verifier` reviews the envelope first, then only the next executable slice; main session owns revisions and final synthesis. |
| Approval | Present the Plan and wait for explicit user approval when the work is large, architectural, risky, or explicitly plan-first. | Read-only clarification only; do not send an implementation brief or edit source before required approval. |
| Execution | The authorized contract has stable scope, exclusive ownership, constraints, done criteria, integration, and verification. | `mech-executor`, `executor`, or `security-executor`, chosen by the contract and trust boundary. |
| Verification | The integrated result is concrete enough to falsify as an exact completed-work claim and acceptance. | A fresh `verifier` returns `CONFIRMED`, `REFUTED`, or `INCONCLUSIVE`. |

A `plan-verifier` brief requests exactly bare `READY` or structured `REVISE`
with `Blocker:`, `Evidence:`, `Minimum revision:`, and `Acceptance check:`
fields for one stable envelope or slice. Malformed output is a protocol failure,
not a Plan judgment.

Review the envelope before its slices. By default, review only the next
executable slice and seek approval as soon as both are `READY`; unrelated
downstream slices do not block it. Shared blockers and unmet prerequisites
still gate dependent work.

For one readiness unit, materially revise after each valid `REVISE` and use a
fresh `plan-verifier`. After two automatic `REVISE` verdicts for the same unit,
stop resubmitting it and surface the blockers and options to the user; the cap
is not `READY`, cosmetic splitting cannot reset it, and user-directed
continuation remains allowed. Do not resubmit a substantially unchanged Plan.

`READY` is readiness only, never user approval or write authorization.

Before every agent call, identify the phase and apply a dispatch brake. Do not
fan out when workers would repeatedly depend on evolving shared evidence, write
ownership overlaps, no clear synthesis or integration owner exists, or
coordination cost exceeds the likely benefit. Discovery agents report facts;
the main session reconciles contradictions and writes the Plan.

Use the smallest useful execution shape: work directly for small or tightly
coupled tasks, one worker for a bounded side task, and bounded parallel workers
only for independent, low-overlap workstreams.

Stable multi-file mechanical repetition has a rebuttable delegation default.
When it has a complete one-shot brief, exclusive ownership, per-item acceptance,
and specified integration, dispatch exactly one `mech-executor` before the main
session edits by default. The main session owns per-item triage, exceptions,
integration, and acceptance and must not edit the worker-owned scope while it
runs. Direct execution of qualifying work requires a specific named blocker
before editing: evolving or coupled evidence, an ownership or integration
conflict, typed worker unavailability, or non-positive net benefit. Merely being
slightly faster is insufficient. This default is rebuttable, not unconditional.

Outside that qualifying mechanical shape, choose delegation by net benefit.
Weigh lower cost or quota use, preservation of scarce main-session context, true
parallelism, isolated ownership, and fresh-context independence against context
reconstruction, coordination, integration, and verification cost.

Recurring or homogeneous work needs a stable, complete one-shot brief, not a
numeric trigger. Its remaining items must be independent and the same shape,
with goal, constraints, done criteria, exclusive ownership, integration, and
per-item acceptance already specified. The main session retains triage,
exceptions, integration, and acceptance.

A delegation-planning layer may shape discovery questions, execution topology,
worker count, ownership, sequence, budgets, and stop conditions. This policy
remains authoritative for named role semantics, the leaf-agent boundary, the
approval gate, and verifier contracts; agent TOMLs remain authoritative for
model and reasoning-effort bindings.

Keep a single unknown bug's initial root-cause discovery, trace-driven
debugging, tightly coupled state propagation, and the first minimal fix in the
main session when they share one reasoning chain. Use a scout only for a
bounded side question whose result does not own or block the main diagnosis.

Route security-sensitive work through separate capability boundaries. Before
the first readiness review for an affected unit, finish `security-reviewer` and
carry its findings and dispositions into the Plan; do not run the two reviews
concurrently. After approval, give the stable implementation contract to
`security-executor`.

Run a fresh outcome `verifier` at the smallest coherent integration boundary
where the complete claim can be independently refuted. Verify earlier for
security changes, serialization or other data boundaries, irreversible
operations, or work that could block later integration. Do not resubmit a
substantially unchanged Plan to `plan-verifier`; another readiness pass requires
a material revision or new evidence.

Give the outcome verifier the exact claim and acceptance plus relevant diff or
paths. Ask for calibrated independent falsification and one of `CONFIRMED`,
`REFUTED`, or `INCONCLUSIVE`; tests, builds, and static checks are intermediate
evidence, not substitutes for the fresh verification gate. `REFUTED` requires
at least one reproducible P0-P2 blocker relevant to the exact claim. P3/P4 are
non-blocking advisories. Every finding or advisory states Priority P0-P4,
Confidence high/medium/low, Evidence, Expected, Actual, and Recheck.
`INCONCLUSIVE` states the reason, missing evidence, and retry condition.

Final disposition remains in the main session. Re-evaluate every reported issue
for reproducibility, whether it was introduced and is in scope, relevance to
the exact claim, priority, and confidence. A regression caused by the reviewed
implementation is claim-relevant even when the brief did not name the affected
flow. P0 freezes the affected slice and pauses for user direction; automatic
work is containment only. Fix P1 within approved scope or pause and ask. An
introduced P2 regression remains blocking and must be fixed within approved
scope or paused; fix other bounded P2 findings inside explicit acceptance,
otherwise defer them with a reason and narrow the final claim. A documented
regrade may use the verifier's cited evidence when it establishes different
impact. Never silently reject, defer, downgrade, or call a blocker fixed
without contrary evidence or a successful recheck of the original
failure. Report or defer P3/P4 without a dedicated fix-reverify loop. Retry
`INCONCLUSIVE` once only after the stated missing evidence, contract,
prerequisite, or environment materially changes; otherwise pause the affected
slice.

#### Long autonomous runs

Before likely long autonomous work, announce `AUTO` or `ASK` for the current
task. Sleeping, eating, or leaving the agent alone is not authority to continue:
offer the modes and wait. Explicit “continue while I am away” selects `AUTO`
and must be announced. `/goal` preserves the objective only; it selects neither
mode nor broader authority.

`AUTO` permits only reversible work in approved scope and main-session P2
adjudication. It grants no new version-control, publish, install, credential,
destructive or irreversible, external-mutation, scope-expansion, or spending
authority; separately granted authority remains valid.

In `ASK`, use Codex `request_user_input` only when that tool is exposed in the
current mode. Otherwise end the turn with `PAUSED_NEEDS_USER`, one concise
question, choices, and a recommendation. Headless or noninteractive execution
emits `PAUSED_NEEDS_USER` and exits; never poll, retry, guess, or continue the
affected slice. The main session asks, never a child.

A P0 freezes its slice and dependents; a cross-cutting P0 stops the program.
Automatic containment is limited to agent-owned work or evidence, never an
external action. Blocking P1/P2 recovery shares at most five meaningful
fix-reverify passes: rounds 1-2 are normal and rounds 3-5 are recovery. Every
next pass requires a material change to the stable verification identity:
candidate, claim, acceptance, contract, available evidence or prerequisites, or
environment. Fingerprint the complete tested candidate from committed head,
tracked and staged diff, and untracked input paths plus content; a
tested-artifact digest may replace that input fingerprint. Never reverify the
same complete identity. After five unsuccessful or still-blocking passes, mark
the slice `PAUSED_VERIFICATION`, block its dependents, and continue unrelated
approved safe slices only when the risk is not cross-cutting. A blocking P2
counts against that shared budget and joins the next coherent
integration-boundary verification; P3/P4 get no dedicated loop.

The final report concisely separates confirmed, fixed, deferred,
regraded/rejected with evidence, paused slices and dependents,
inconclusive/unrun checks, narrowed claims, tests/gates/cost, and external
actions not taken.

Model routing is owned by the named agent definitions. Select the named role
without replacing its configured model or reasoning effort. Use an ad-hoc model
override only for a truly ad-hoc agent with no matching role definition.

<!-- pilotfish-codex:spawn-transport:begin -->
#### Native typed spawn policy

Use Codex's native typed `spawn_agent` surface. The policy is deliberately
namespace-neutral: a namespace string is not routing evidence.

Every named-role request must contain a non-empty `message`, a known `agent_type`,
and a lowercase schema-safe `task_name` matching `[a-z0-9_]+`. Use
`fork_turns = "none"` by default. A recent-turn fork is only the positive integer
string `"1"` through `"3"`. Do not use a full-history named-role fork.

Do not pass child `model`, `reasoning_effort`, `service_tier`, or
`fork_context` overrides. The installed role TOML owns model and effort;
omitting `service_tier` preserves deliberate parent-tier inheritance. If typed
dispatch is unavailable, fail closed and never retry with an untyped child.

Typed dispatch is an all-or-nothing child-creation boundary. No untyped
fallback is permitted: if the request cannot be constructed or typed capability
is unavailable, the parent must not silently substitute an untyped child; it
either takes the bounded work locally under the dispatch brake or reports
delegation unavailable.

This is request-construction policy. Current receipt validation is post-hoc evidence
classification, not a reliable pre-execution cancellation hook.
`max_depth` is V1 compatibility state only and does not enforce this boundary.
<!-- pilotfish-codex:spawn-transport:end -->

Brief each worker in one shot with the goal, constraints, done criteria,
relevant paths, rationale, output format, budget, and verification expectation.
Start with the cheapest eligible role. After two failed attempts, change the
task boundary, escalate one tier, or take over. Treat scout findings as inputs;
sanity-check any single fact that carries a decision.

Schedule eligible calls by data dependency. When two or more independent typed
calls are ready, issue their `spawn_agent` calls back-to-back before other
main-session work. Give writing agents exclusive file ownership, continue only
on disjoint scope while children run, and collect every result before dependent
work, cross-surface synthesis, or the final answer.

Long-running processes belong to the main session. Leaf agents must not detach
them; they return the exact command, absolute working directory or isolated
workspace, required environment, input paths, and completion criterion so the
orchestrator can run and collect the result before resuming the agent.

Never swap `plan-verifier` and `verifier`. The former challenges Plan
readiness; the latter reproduces tests and challenges a completed-work claim.
Neither role writes the Plan or fixes findings. Final judgment remains in the
main session.
<!-- pilotfish-codex:end -->
