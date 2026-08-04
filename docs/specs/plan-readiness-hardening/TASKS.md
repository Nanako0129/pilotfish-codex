# TASKS — Plan Readiness Hardening

Open batch. Derived from the PR #6 review; no task restates work already
merged in that PR.

## Installer transparency

- [x] T1. Print planned canonical role replacements in the dry-run path of
      `install/install.py`. Minimal fix: emit the existing `notes` (and ideally
      the same change summary) before the `dry_run` early-return, without
      creating the pending sidecar or calling `_commit`. Do not invent a second
      planning path. Satisfies AC-R1, AC-R2, AC-R4. (G1)
- [x] T2. Add a regression test asserting that a dry run against a
      release-pinned v1.3.0 home names both replaced roles on stdout and leaves
      the home byte-identical; plus a dry-run drift case that still aborts.
      Satisfies AC-R1–AC-R4. (G1)

## Upgrade allowlist maintenance

- [ ] T3. Replace the literal `CANONICAL_ROLE_UPGRADE_DIGESTS` with digests
      derived at load time from `install/previous/<version>/agents/<role>.toml`.
      Exact-bytes matching and `installed_role_drift` for every other
      difference are unchanged. Satisfies AC-U1, AC-U2. (G2)
- [ ] T4. Copy the outgoing v1.3.1 role templates into
      `install/previous/v1.3.1/agents/` and add the release-procedure step to
      `install/AGENT-INSTALL.md`. Satisfies AC-U3. (G2)
- [ ] T5. Add a test that an installed role matching any shipped previous
      release upgrades, and that a byte modified in any of those payloads still
      aborts. Satisfies AC-U4. (G2)

## Test strictness

- [ ] T6. Normalize whitespace before the `Plan epoch` and `format-recovery`
      removal assertions in `tests/test_policy.py`. Satisfies AC-T1. (G3)

## Brake durability

- [ ] T7. Either record the per-unit `REVISE` and `REFUTED` counts against the
      stable unit ID in the Plan artifact, or document the context-compaction
      reset as a known limitation under `docs/design.md#plan-readiness`.
      Satisfies AC-B1. (G4)

## Decisions pending Miyago

- [ ] T8. Confirm the release number for the PR #6 payload (`1.3.1` as
      proposed, or `1.4.0`), and decide whether to create the missing `v1.3.0`
      and later tags.
