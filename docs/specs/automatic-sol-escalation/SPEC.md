---
id: spec-automatic-sol-escalation
title: Automatic Sol escalation gate
status: completed
created: 2026-08-04
updated: 2026-08-04
author: Miyago
approved_by: Miyago — 「修好它」
tags: [routing, verification, sol]
priority: high
---

<!-- markdownlint-disable-next-line MD025 -->
# Automatic Sol escalation gate

## Requirements

1. A material pre-approval Plan that crosses the existing independent-review
   trigger must not receive a local readiness recommendation before the main
   session calls the typed `plan-verifier` role.
2. The auto-routing prompt must not tell Codex to call, spawn, or delegate to
   any agent. It must nevertheless produce observable `plan-verifier` child
   evidence bound to `gpt-5.6-sol` at `high`.
3. The gate must preserve the existing trigger boundaries, review ordering, and
   two-`REVISE` budget. Routine work remains Luna-first; Terra remains absent.
4. A missing, wrong-role, or wrong-binding child fails the live verifier. It
   cannot be reported as a successful policy-only check.
5. Passing evidence binds one fresh parent rollout to its exact
   `plan-verifier` child. The verifier records the submitted no-directive
   prompt, checks the parent `spawn_agent` arguments, follows the matching
   activity event to the child ID, and then checks the child model and effort.
   Stale, unlinked, ambiguous, or extra-role-only evidence fails closed.
6. The quota-spending smoke runs against a newly installed isolated Codex home.
   The active global policy is updated only after a passing result, and then
   its policy and role digests must match the tested candidate.
7. A native `UserPromptSubmit` hook compiles the existing risk trigger into a
   structured, per-session marker only when the prompt names a Plan/approval
   and a defined security, data, release, external, or irreversible boundary.
   The marker contains only schema, runtime IDs, category labels, and retry
   state; it stores no user prompt.
8. A native `Stop` hook trusts that marker, not free text, to detect a current
   risk-triggered Plan turn that ended without a linked `plan-verifier` child.
   It automatically continues the turn with the missing review gate and
   performs no external action. Codex's one-time hook trust remains required
   by the platform.
9. The Stop hook treats only structured JSONL runtime envelopes as dispatch
   evidence: one current-parent `spawn_agent` call, its matching activity, and
   the matching `plan-verifier` child ID. Text inside user, assistant, or tool
   bodies never proves a review occurred; malformed or ambiguous evidence does
   not suppress the gate.
10. The hook has one continuation attempt per runtime turn. It emits only a
   source-owned constant directive, no transcript/path/body text, logs, or
   temporary copies. It validates a regular non-symlink transcript under the
   configured session root and reads a bounded tail/current segment.
11. Candidate-to-active integrity covers the policy, role manifest, hook
    registration, and hook script bytes. Missing, stale, or changed hook files
    abort propagation before active-home writes.

## Non-goals

- Claiming a hard runtime guarantee for arbitrary task classification. Native
  Codex exposes no pre-response hook that can force `spawn_agent`.
- Adding a separate classifier, model provider, or Terra fallback.
- Bypassing Codex hook trust globally or using a managed-policy escape hatch.
- Running automatic quota-spending probes in CI.

## Architecture / Plan

### Decisions

- **Decision:** Make the pre-approval trigger a mandatory tool-use gate in the
  policy text, rather than a general delegation preference.
  - **Reason:** The 2026-08-04 read-only live smoke met the security,
    production, cross-service, and approval triggers but Luna answered
    `REVISE` locally with no child call.
  - **By:** Miyago (2026-08-04)
- **Decision:** Extend the native dispatch verifier with a manually gated
  auto-route E2E probe.
  - **Reason:** Static policy checks and explicit-spawn probes cannot establish
    that the parent actually chose Sol at runtime.
  - **By:** Miyago (2026-08-04)
- **Decision:** Treat the rollout's `multi_agent_version` as diagnostic only.
  - **Reason:** Codex 0.146 emitted `v1` for the failed smoke while the former
    verifier assumed `v2`; child role and binding are the stable acceptance
    evidence for this gate.
  - **By:** Miyago (2026-08-04)
- **Decision:** Use a narrowly scoped native `Stop` hook as the enforcement
  retry for an observed missing Plan-review child.
  - **Reason:** Two fresh no-directive candidate smokes returned local Luna
    reviews without any `spawn_agent`, despite the mandatory policy wording.
    The hook can continue the same turn only after verifying the risk signal
    and missing child in the current transcript segment.
  - **By:** Miyago (2026-08-04)
- **Decision:** Bound the hook to one runtime continuation and fail closed on
  untrusted transcript evidence.
  - **Reason:** A missing reentrancy bound can recursively spend quota, while a
    text parser can be spoofed by repository or user content. A single
    source-owned continuation preserves the normal native role boundary and
    leaves a failed smoke observable.
  - **By:** Miyago (2026-08-04)
- **Decision:** Split deterministic trigger compilation from Stop enforcement.
  - **Reason:** Missing child evidence alone cannot distinguish a missed review
    from an ordinary turn. The producer writes a schema-validated marker from
    a bounded policy matcher; Stop consumes the marker plus runtime envelopes
    and never infers a trigger from transcript text.
  - **By:** Miyago (2026-08-04)

### Sequence

1. Add a red offline test for a no-directive auto-route probe and its evidence
   parser.
2. Strengthen the template policy at the existing independent-review boundary
   and add source-owned `UserPromptSubmit` and `Stop` hook handlers. The
   producer writes only a bounded schema marker; Stop accepts only that marker
   and structured current-turn event envelopes. Its output is a constant
   directive or no output.
3. Implement the live-only probe in `install/verify_dispatch.py`; it writes a
   synthetic Plan in an isolated temporary directory, uses read-only Codex,
   checks that its source prompt contains no dispatch directive, and correlates
   the exact persisted parent and child rollout traces.
4. Materialize and install an isolated candidate Codex home, then run one
   manually authorized live smoke there with the hook explicitly trusted for
   the isolated run. A successful result requires the actual `plan-verifier`
   child to report Sol/high; failure leaves the active home untouched.
5. Only after `NATIVE_OK`, update the active global policy through the existing
   installer and compare its policy, role, hook-registration, and hook-script
   digests with the tested candidate.
6. If the isolated smoke omits the child, report the native limitation
   rather than claiming enforcement; a separate external wrapper would require
   a new product decision.

## Tasks

- [x] Add failing tests for the automatic Plan-review route.
- [x] Implement the policy gate, native Stop hook, and live trace verifier.
- [x] Test parent-child correlation, no-directive prompt evidence, and isolated
      candidate-home propagation.
- [x] Test hook JSONL correlation, spoofed-content rejection, one-shot retry,
      output redaction, path/size boundaries, and structured marker lifecycle.
- [x] Run the live smoke in an isolated Codex home.
- [x] Propagate the exact tested policy to the active home after separate
      home-write approval and one-time Codex hook trust.
- [x] Record the observed result and update affected documentation.
- [x] Preserve installer state when Codex records native hook trust, while
      rejecting drift in Pilotfish-owned routing fields.

## Files

- `templates/agents-md.orchestration.md` - Source policy gate.
- `templates/hooks.json` - Source-owned prompt and Stop hook registration.
- `hooks/pilotfish_autoroute_gate.py` - Marker producer and current-turn gate.
- `install/verify_dispatch.py` - Live auto-route evidence verifier.
- `tests/test_verify_dispatch.py` - Offline parser and command coverage.
- `install/install.py` - Candidate and active hook/policy propagation.
- `install/stage_smoke_home.py` - Candidate hook artifact projection.
- `tests/test_install.py` - Hook artifact transaction coverage.
- `tests/test_autoroute_hook.py` - Hook parser and continuation boundaries.
- `tests/test_install.py` - Existing temporary-home propagation coverage.
- `docs/specs/automatic-sol-escalation/SPEC.md` - This decision and progress.

## Notes

The native manual documents AGENTS-driven delegation, but the behavior remains
model-selected. The live E2E is therefore a release gate and evidence source,
not a claim of absolute platform enforcement.

On 2026-08-04, the isolated `--autoroute` candidate smoke returned `NATIVE_OK`:
the root used Luna/medium and produced one metadata-linked plan-verifier child
bound to Sol/high. The synthetic Plan fixture was removed on completion. The
candidate was then deleted before active-home propagation.

After explicit home-write approval, the same policy and hook bytes were
installed at `~/.codex` and matched their source digests. A non-bypass active
smoke completed with Luna/medium at the root and one completed metadata-linked
plan-verifier child at Sol/high. Codex showed no hook-review warning after the
user trusted the hook; the per-session marker directory was empty on completion.

Codex then recorded its native hook trust in `[hooks.state]`. The installer now
accepts that non-routing state without rewriting `config.toml`, while a changed
model, effort, Plan mode, role table, or legacy routing value still aborts before
any write. The active-home dry run completed with `already up to date`.
