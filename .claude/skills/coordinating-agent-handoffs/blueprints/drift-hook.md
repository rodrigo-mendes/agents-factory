# Drift Hook (optional `Stop` hook, warn only)

Back to [SKILL.md](../SKILL.md). Related: [spec sync](./spec-sync.md).

A Claude Code `Stop` hook can run `detect_drift.py` when the agent finishes a turn, so code edited
by hand after the last spec sync is noticed early. The hook **only prints a warning**: it never
blocks the turn, never edits code, never edits the spec and never writes a record. Fixing drift is
the job of `/syncing-spec-from-code` plus the user's acceptance.

## Rule: install only after the user confirms

- The factory never installs this hook on its own. The orchestrator asks first ("Add a Stop hook that
  warns about spec drift in this project?") and writes the snippet only after the user's own
  message says yes. An agent message is not that confirmation.
- Install it per project in `.claude/settings.json` (shared) or `.claude/settings.local.json`
  (personal). Whether APM `hooks:` in `apm.yml` ships it is an orchestrator decision, not made here.
- Remove it by deleting the `Stop` entry.

## Why it cannot block

A `Stop` hook that exits with code 2 prevents Claude from stopping; every other exit code is
non-blocking (unverified, [U3](./unverified-and-risks.md); page not recorded). `detect_drift.py` exits 2 when drift exists, which is exactly the
blocking code, so the command **must** swallow the exit status with `|| true`.

## settings.json snippet

Paths assume the skill is installed under `.claude/skills/` of the target project and that the
handoff folder is `openspec/changes/<change-id>/handoff` (replace `<change-id>`; for a profile with
`root: docs/handoff/{capability}` use that folder). `python` must be Python 3.8+ (unverified, U1). On Windows the hook command may run in Git Bash, where `python` may be missing; use `py` (the Python launcher) there (unverified, [U6](./unverified-and-risks.md)). The `|| true` swallow works in both shells.

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/skills/coordinating-agent-handoffs/scripts/detect_drift.py . --change openspec/changes/<change-id>/handoff || true"
          }
        ]
      }
    ]
  }
}
```

What the user sees: the script prints `DRIFT: <path>` lines when code changed since the last synced
SHA without a covering report. The hook's stdout may be visible only in the transcript view
(unverified, [U4](./unverified-and-risks.md)); if the project wants an always-visible message, wrap
the command so it prints a
`{"systemMessage": "spec drift detected, run /syncing-spec-from-code <change-id>"}` JSON line
(the field name is unverified, [U5](./unverified-and-risks.md); confirm against the current hooks
reference first).

Notes:

- No `--include-worktree` by default (it also reports uncommitted files, which is noisy during a
  session). Enabling it is an Ask-First item.
- If `lastSyncedSha` is missing (no `status.md` yet) the script exits 1; the `|| true` hides it,
  which is the desired no-op.
- The hook must stay fast (git diff only). Do not add `board.py` or `check_records.py` to it.

## Verification

```bash
python .claude/skills/coordinating-agent-handoffs/scripts/detect_drift.py . --change openspec/changes/<change-id>/handoff; echo "exit=$?"
# expect exit 0 (no drift), 2 (drift: DRIFT: lines) or 1 (error); the hook command itself always ends with exit 0
```
