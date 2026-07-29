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
independent execution slices. A fresh `plan-verifier` reviews the envelope,
then the next executable slice. Bare `READY` opens the approval gate;
structured `REVISE` carries blocker evidence and the smallest observable
closure check.

After two automatic revisions for one unit, the main session stops resubmitting
it and returns the unresolved choices to the user. This does not make the unit
ready or reset shared prerequisites. Security-sensitive units complete
read-only security review before their first readiness pass.

### Outcome verification

A fresh verifier receives the exact completed-work claim and acceptance. It
independently falsifies that claim and returns `CONFIRMED`, `REFUTED`, or
`INCONCLUSIVE`; P3/P4 advisories do not block confirmation, while `REFUTED`
requires a reproducible P0-P2 blocker. The verifier reads and runs checks but
never plans, edits, fixes, delegates, or exposes raw secrets.

The main session adjudicates reproducibility, scope, claim relevance, priority,
and confidence. P0/P1 must be fixed or paused for user direction; bounded
in-acceptance P2 is fixed, while other P2 and P3/P4 are reported with a narrowed
claim when necessary. Regressions caused by the reviewed implementation remain
claim-relevant even when the brief omitted the affected flow. An inconclusive
gate is retried once only after its prerequisite materially changes.

### Long autonomous runs

Before likely long work, the main session announces `AUTO` or `ASK`; absence is
not authority, and `/goal` preserves only the objective. `AUTO` covers approved,
reversible scope and P2 adjudication, not new version-control, publish, install,
credential, destructive, external, scope, or spending authority. `ASK` uses
Codex `request_user_input` only when exposed, otherwise pauses the turn.

Blocking P1/P2 recovery shares five materially changed passes: two normal and
three recovery. Candidate identity includes the committed head plus working-tree
diff or tested-artifact digest. A fifth failure pauses only that slice and its
dependents when risk is not cross-cutting, so unrelated approved safe slices can
continue.

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
