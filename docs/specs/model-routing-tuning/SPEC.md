# Model routing tuning

- Slug: `model-routing-tuning`
- Status: Done
- Owner: Miyago
- Created: 2026-08-03

## Goal

Keep PR #9's Nanako-authored orchestration policy, then tune model routing for
lower routine cost without weakening high-judgment work.

## Decisions

- Merge PR #9 first; close PR #7 and #8 as superseded by the integrated branch.
- Main session defaults to `gpt-5.6-luna` at `medium` effort.
- Main-session planning and dispatch reasoning may escalate Luna to `xhigh`,
  with `max` reserved for genuinely difficult orchestration decisions.
- Mechanical Luna roles remain unchanged at their existing low/medium levels.
- Use Terra up to `xhigh` for general Plan and outcome reasoning; `high` is
  sufficient for routine verification.
- Keep security review and execution on Sol, capped at `high`.
- Do not rewrite Nanako's continuation, risk-triggered review, or installer
  safety policy unless a routing change requires a contract update.

## Scope

- Root model and effort defaults in the config template and installer.
- Non-security reviewer role model bindings, if needed to activate Terra.
- Security role effort cap and matching historical fixtures/tests.
- Validator, template, installer, and targeted policy tests.

## Non-goals

- Re-designing PR #9's orchestration lifecycle.
- Changing mechanical role behavior or adding unconditional Sol calls.
- Running a paid live Codex behavioral gate.

## Verification

- Validate the generated config and all role TOMLs.
- Run targeted installer/template/policy tests and the full offline unittest
  suite once after integration.
- Run Python compilation, Markdown lint, and `git diff --check`.
- Confirm the active Codex config accepts Luna/medium and the selected effort
  values before any local config write.
