# TESTS — Plan Readiness Hardening

Acceptance criteria for the open findings in
[`SPEC.md`](./SPEC.md). Criteria already satisfied by PR #6 are not restated.

## Installer transparency

- **AC-R1**: Given an existing Codex home whose `agents/plan-verifier.toml` and
  `agents/security-reviewer.toml` hold release-pinned prior canonical bytes,
  `install.py --dry-run` shall name each role it would replace (at minimum the
  note text `upgraded canonical role plan-verifier` and
  `upgraded canonical role security-reviewer`, or equivalent planned-write
  lines that identify those two paths).
- **AC-R2**: A dry run shall not create, modify, or remove any file in the
  Codex home, including the install-state sidecar and its pending file.
  Snapshot the home tree (or fingerprint every path under it) before and after
  the dry-run call; they must be identical.
- **AC-R3**: A dry run against a home already matching the packaged payloads
  shall report no planned replacement (`already up to date; nothing to change`
  and no upgrade notes).
- **AC-R4**: A dry run against a home whose `plan-verifier.toml` differs from
  both the packaged payload and every allowlisted prior digest shall still
  abort with `installed_role_drift` before any write, identical to a real
  install.

## Upgrade allowlist

- **AC-U1**: For every role directory under `install/previous/`, an installed
  role whose bytes equal a shipped prior payload shall upgrade through the
  transactional write path, recording the prior bytes for rollback.
- **AC-U2**: An installed role whose bytes match neither the packaged payload
  nor any shipped prior payload shall abort with `installed_role_drift` before
  any write. A single added byte shall be sufficient to trigger this.
- **AC-U3**: The set of digests accepted at runtime shall equal the digests of
  the files under `install/previous/*/agents/`, with no separately maintained
  literal to drift from them.
- **AC-U4**: After a successful upgrade, every installed role file shall be
  byte-identical to its packaged template, and the post-write fingerprint
  verification shall pass.

## Test strictness

- **AC-T1**: The `Plan epoch` and `format-recovery` removal assertions in
  `tests/test_policy.py` shall be evaluated against whitespace-normalized
  policy text, so a term reintroduced across a line break fails the test.

## Brake durability

- **AC-B1**: Either the Plan artifact shall carry the per-unit `REVISE` and
  `REFUTED` counts keyed by stable unit ID, or `docs/design.md` shall state
  that the counts live in main-session context and do not survive compaction.
  A design document that asserts the brake without either property does not
  satisfy this criterion.

## Regression guards

- **AC-G1**: The full offline suite shall pass, and markdownlint shall report
  zero errors across the repository's Markdown files.
- **AC-G2**: The readiness role boundary pinned by PR #6 shall remain intact:
  `plan-verifier` returns only `READY`/`REVISE`, `verifier` returns only
  `CONFIRMED`/`REFUTED`, and neither prompt mentions the other's verdicts.
