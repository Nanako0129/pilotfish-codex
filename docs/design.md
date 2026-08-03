# Pilotfish-Codex design rationale

Pilotfish-Codex preserves Pilotfish's role routing, approval boundaries, leaf
workers, and fresh-context verification while using Codex-native TOML roles and
global `AGENTS.md` policy. Claude-specific worktrees, task dashboards, agent
IDs, resume commands, and `Explore` shadowing are not Codex runtime claims.

## Native Multi-Agent V2 boundary

The active target is exactly Codex `rust-v0.145.0` and one explicit feature
table:

```toml
[features.multi_agent_v2]
enabled = true
max_concurrent_threads_per_session = 4
```

The value is total concurrency including the root. Native defaults retain
namespace, metadata visibility, and child override exposure decisions; the
configuration does not force an adapter namespace or legacy `[agents]`
concurrency fallback.

The role manifest is seven recursively discovered TOMLs. Pilotfish validates a
single approved staged manifest and rejects duplicate names, filename/name
mismatches, extra roles, path escape, and role drift. Only release-pinned prior
canonical bytes may upgrade automatically; customized same-name roles still
fail closed. This local validation does not claim to duplicate Codex's layered
loader, which may merge role data across layers. The native smoke instead
requires a one-user-layer staged home.

## Policy and evidence

Policy constructs typed named-role requests with a non-empty message, installed
`agent_type`, lowercase schema-safe task name, and `fork_turns = "none"` or
`"1"` through `"3"`. It forbids full history for named roles, untyped retries,
and child model, reasoning-effort, service-tier, and context overrides.

### Plan readiness

Large work keeps shared constraints in a program envelope and splits only
independent execution slices. Concrete security, irreversible or external,
data, release, or cross-component acceptance risk triggers a fresh
`plan-verifier`; file count or “non-trivial” alone does not. `REVISE` returns
all known P0-P2 blockers in one pass; P3/P4 and adjacent hardening do not block.

After two automatic revisions for one unit, the main session stops resubmitting,
dispositions every blocker as `FIX`, `DEFER`, or `REJECT`, and narrows, splits,
or continues independent slices. User input is reserved for unresolved P0/P1,
product or authority choices, or an original scope that can no longer be met.

### Outcome verification

A risk-triggered fresh verifier receives the exact completed-work claim and
acceptance after the primary flow has been exercised. It returns `CONFIRMED`,
`REFUTED`, or `INCONCLUSIVE`; P3/P4 advisories do not block confirmation, while
`REFUTED` requires a reproducible P0-P2 blocker. A known blocker takes
precedence over missing evidence for another condition; otherwise any
unevaluated required condition is `INCONCLUSIVE`. The verifier reads and runs
checks but never plans, edits, fixes, delegates, or exposes raw secrets.

Role verdicts are evidence, not implementation or scope authority. The main
session records `FIX`, `DEFER`, or `REJECT` after adjudicating reproducibility,
scope, claim relevance, priority, and confidence. P0 freezes the affected
slice; P1 is fixed or paused for user direction. Regressions caused by the
reviewed implementation remain
claim-relevant even when the brief omitted the affected flow, and an introduced
P2 regression must be fixed or paused rather than hidden by a narrowed claim.
Other bounded in-acceptance P2 is fixed, while lower-priority findings may be
reported with a narrowed claim. An inconclusive gate is retried once only after
its prerequisite materially changes.

### Long autonomous runs

Before likely long work, the main session announces `AUTO` or `ASK`; absence is
not authority, and `/goal` preserves only the objective. `AUTO` covers approved,
reversible scope and P2 adjudication, not new version-control, publish, install,
credential, destructive, external, scope, or spending authority. `ASK` uses
Codex `request_user_input` only when exposed, otherwise pauses the turn.

Normal recovery is one targeted recheck of the original reproduction plus a
bounded basic regression. Five materially changed P1/P2 passes remain an
emergency ceiling for high-risk, claim-critical recovery, not a quota.
Verification identity includes the complete tested candidate, claim,
acceptance, contract, external evidence or prerequisites, and environment; a
prior verifier's own output is not a change.
The candidate fingerprint covers committed head, tracked and staged diff,
untracked input paths plus content, and dirty submodule content. Artifact
digests complement source identity unless the artifact is the sole deliverable.
A fifth failure pauses only that slice and its dependents when risk is not
cross-cutting; recovery stops earlier when another pass would only search
adjacent risk.

### Continuation liveness

User input does not necessarily replace the task already in progress. The
main-session policy therefore keeps an unfinished root objective active when a
message answers a pending decision, steers or corrects the work, asks for
status or explanation, or resumes a pause. Contextually clear replacement
intent may supersede it without a literal cancellation phrase.

Before pausing, the main session exposes the objective, current phase or slice,
pending blocker or decision, and exact resume point. A decision response binds
to that point only when it resolves the decision unambiguously; otherwise the
pause remains and the session asks one concise clarification. Status and
explanation requests resume only work not gated by the unresolved decision;
otherwise the session remains paused. An incomplete objective cannot end with a
normal final: the session must continue or return `PAUSED_NEEDS_USER` with the
blocker, question, and resume point. A user-requested pause instead records the
objective, phase, and resume point without inventing a blocker or question. It
remains active through status or explanation requests until the user explicitly
resumes or clearly replaces the objective.

This is a prompt-level liveness contract. It neither persists task state outside
the conversation nor changes Codex App, app-server, approval, security, or
scope behavior. Static assertions prevent accidental policy removal; they are
not behavioral proof that a live model or host always complies.

The verifier is post-hoc evidence classification, not a pre-execution cancel
hook. Native proof requires observed V2 selection, one `spawn_agent` with exact
typed arguments, call/activity correlation, and child `turn_context.model` and
`turn_context.effort` matching the installed role. It records only redacted,
hashed identifiers and receipt fields. A namespace is neither required nor
sufficient evidence.

## Staging boundary

The native smoke first copies the post-install active target into a distinct,
not-yet-existing staged home using canonical containment, confined reads,
TOCTOU checks, cleanup on failure, and exclusive atomic no-replace publication.
Only the canonical native-V2 config projection, hashed policy/manifest input,
and `auth.json` are materialized. Unrelated active config and existing runtime
metadata are outside the smoke projection and are not copied or hashed. Before
launch the staged home is an exact minimal allowlist; Codex creates its own
runtime state there only after preflight. The verifier compares active and
staged projected config, policy, and canonical role-manifest hashes before it
can launch Codex. It also rejects project-local configuration and instruction
discovery in the supplied smoke working directory.

`NATIVE_OK` is the only completed native gate. `SKIPPED` remains incomplete and
`FAILED` blocks migration completion. Historical adapter behavior belongs only
to explicitly labeled offline fixtures and archived evidence.
