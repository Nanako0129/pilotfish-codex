# Copy/paste install prompt

Please install Pilotfish-Codex by fetching and reading the published
`INSTALL.md` at
`https://raw.githubusercontent.com/miyago9267/pilotfish-codex/<release-tag-or-commit-sha>/INSTALL.md`
completely. Replace the placeholder with an exact published tag or full commit
SHA; do not invent or silently use another ref. Inspect `install/install.sh`
and the detailed
`install/AGENT-INSTALL.md` runbook before executing it. Follow the playbook's
confirmation boundary: run the pinned-ref dry-run first, show me the
selected source/ref, target home, planned writes, and backups, then stop and
ask for explicit approval before writing the selected Codex home (default
`~/.codex`).
After approval, install and validate the native config and roles, complete the
one-time `/hooks` trust flow, and report exact commands, results, changed
paths, backups, and any unresolved state. Do not use `sudo`, credentials,
unsupported installer options, or a bypass flag.
