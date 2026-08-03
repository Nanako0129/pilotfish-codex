# PROGRESS — Model Routing Tuning

- Status: In progress
- Updated: 2026-08-03

## Phases

- [x] P0. Merge PR #9 and close superseded PR #7/#8. GitHub marked all three
      PRs merged at `8bf61c9073cfb06b346d3b545cdc2641ccc36570`.
- [x] P1. Apply root Luna-medium and Terra/Sol routing decisions.
- [x] P2. Update validators, fixtures, and targeted tests.
- [x] P3. Run verification and report remaining gaps. The 87-test suite,
      validator, Python compilation, Codex config override, changed-file
      Markdown lint, and `git diff --check` pass. Full-repository Markdown lint
      still reports pre-existing `.ai/` violations.
