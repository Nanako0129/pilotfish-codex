# PROGRESS — Plan Readiness Hardening

- Slug: `plan-readiness-hardening`
- Status: Proposed — no implementation started

## Phases

- [x] P0. Review PR #6 and verify its claims locally (79 offline tests pass,
      prior canonical digests match `main` templates, drift abort holds,
      dry-run gap reproduced).
- [x] P1. Installer transparency (T1, T2) — dry-run emits `notes` including
      `upgraded canonical role …`; regression covers named roles, no writes,
      and dry-run drift abort.
- [ ] P2. Upgrade allowlist maintenance (T3, T4, T5) — follow-up for author.
- [ ] P3. Test strictness and brake durability (T6, T7) — follow-up for author.
- [ ] P4. Release numbering and tag decision (T8) — Miyago / author.

## Notes

P1 was the only phase that gated merging PR #6. Dry-run now surfaces planned
canonical role replacements; remaining P2–P4 are non-blocking follow-ups.
