# CLI contract

Derived from the argparse and docstrings of `scripts/gh_projects_sync.py`, `_gh.py`, `gate_command.py`
and `_vendor.py`. Back to [SKILL.md](../SKILL.md).

## Contents

- [Commands](#commands)
- [Dry-run, exit codes and preflight](#dry-run-exit-codes-and-preflight)
- [How gh is called](#how-gh-is-called)
- [Environment variables](#environment-variables)
- [Locating the handoff scripts](#locating-the-handoff-scripts)
- [Tests](#tests)

## Commands

```
gh_projects_sync.py bootstrap [<repo-root>] --change <id> --profile <yaml> [--apply] [--install-workflows] [--vendor]
gh_projects_sync.py push      [<repo-root>] --change <id> --profile <yaml> [--stage E<n>] [--apply]
gh_projects_sync.py pull      [<repo-root>] --change <id> --profile <yaml> [--apply]   # ORCHESTRATOR ONLY
gh_projects_sync.py close     [<repo-root>] --change <id> --profile <yaml> [--apply]
gh_projects_sync.py status    [<repo-root>] --change <id> --profile <yaml>             # read-only
```

`<repo-root>` defaults to the current directory; `--profile` is required (the parser error hints at it).

| Command | Does | Agent may run |
|---|---|---|
| `bootstrap` | creates missing Stage/Kind/Change/Gate fields and labels, caches ids; `--vendor` copies the scripts; `--install-workflows` copies the four templates | no |
| `push` | creates or updates issues, sub-issues, fields, delta comments, summary comment | yes (`--apply` only with the relayed approval line) |
| `pull` | refuses unless the profile and `openspec/github-tracker.yaml` are committed unchanged at HEAD; prints `TRUST approvers=... bot_login=...`; reads bot confirmations, re-checks (same issue as the confirmation; gate and delta decisions only from the change issue), appends approvals | no |
| `close` | closes every mirrored issue, Status Done | no |
| `status` | prints `DIVERGE <key>: <what>` lines or `IN SYNC (stage E<n>)` | yes |

`--stage` accepts E1..E9. `gate_command.py` has `evaluate [<repo-root>] --profile <yaml> [--apply]`
(payload from env), `recheck [<repo-root>] --profile <yaml> --gate E<n>` (env `ISSUE_NUMBER`, read-only; exit 0
only when the change issue holds the bot's confirmation for that gate and its user comment still passes every
check; used by the archive workflow) and `resolve-change [<repo-root>]` (prints `change=<id>` from
`ISSUE_TITLE` and `ISSUE_BODY`); only workflows run it.

## Dry-run, exit codes and preflight

- Dry-run is the default: each planned write prints `PLAN gh <args>` (bodies travel on stdin and are
  shown as `< stdin(N chars)`); nothing is written to GitHub **or** to local files. `--apply` prints
  `APPLIED gh ...` and saves `handoff/github.yaml`. Read-only queries run in both modes (they need auth).
- Exit codes: 0 ok; 1 error (message on stderr, with gh's stderr, tokens redacted); 2 `status` found
  divergence; 3 tracker disabled (`kind: none` prints `tracker disabled` and does nothing).
- Preflight on every command, in order: version, auth, operator check, then the user-PAT warning. Detail: tracker resolved and valid; `gh --version` at least 2.94.0
  (a warning when not 2.103.x; gh 2.93.0 fails by design, register R14); `gh auth status` succeeds
  (output never printed, `--show-token` never used); the operator check, when `approval_source` is `github`
  or `both`: the token's login (`gh api user`, fallback GraphQL viewer) must not be in `approvers` (exit 1
  otherwise; an unreadable login, as with an App installation token, also exits 1 except in Actions where it
  only warns); last, `owner_type: user` prints the classic-PAT risk warning.
- A second `push --apply` with no git change issues no mutating call.
- Tracker: profile `tracker:` block, overridden key by key by `openspec/github-tracker.yaml`.

## How gh is called

| Purpose | Form |
|---|---|
| Read project, issue and field values | `gh api graphql -f query=... -f/-F var=...` |
| Read lists | `gh api -X GET <path> --paginate --slurp` ((unverified), register R3) |
| Create or edit issues, labels, comments, sub-issues | `gh api -X <METHOD> <path> --input -` with JSON on stdin ((unverified), register R2) |
| Add an item to the project | GraphQL `addProjectV2ItemById` |
| Set a field | `gh project item-edit --id ... --project-id ... --field-id ... --single-select-option-id <id>` or `--text <value>` |
| Create fields and labels (bootstrap) | `gh project field-create ... --format json`, `gh label create ... --force` |

- Always an argument list, never `shell=True`; env adds `GH_PROMPT_DISABLED=1`, `NO_COLOR=1`,
  `GH_NO_UPDATE_NOTIFIER=1`.
- Writes are serial with a pause after each (`OPENSPEC_GITHUB_WRITE_DELAY`, default 1.0 s).
- Rate limits: matching the primary or secondary limit text in stderr is a fallback ((unverified),
  register R5); at most 3 retries with exponential backoff.
- Exit code 4 from gh is reported as "authentication required".

## Environment variables

| Variable | Purpose |
|---|---|
| `GH_TOKEN` | credential matching `owner_type` (inherited, never printed) |
| `OPENSPEC_GITHUB_HANDOFF_SCRIPTS` | folder with the handoff-core scripts (`_handoff_lib.py`) |
| `OPENSPEC_GITHUB_GH` | gh executable override (a `.py` runs with the current Python); the offline test hook |
| `OPENSPEC_GITHUB_WRITE_DELAY` | pause after each write, seconds (default 1.0) |
| `OPENSPEC_GITHUB_BACKOFF_BASE` | rate-limit backoff base, seconds (default 60) |
| `COMMENT_BODY`, `COMMENT_AUTHOR`, `COMMENT_URL`, `COMMENT_ID`, `ISSUE_NUMBER`, `CREATED_AT` | gate payload, set by the workflow |

## Locating the handoff scripts

`_model.py` looks, in order: the environment variable, the scripts' own folder (vendored copy), then
the sibling skill `coordinating-agent-handoffs/scripts`. If none has `_handoff_lib.py` it exits 1 with
the three ways to fix it.

## Tests

Offline, standard-library `unittest`, with `tests/fake_gh.py` as the gh stub:

```bash
OPENSPEC_GITHUB_HANDOFF_SCRIPTS=<handoff-core scripts> python -m unittest discover -s <skill>/scripts/tests
```

100 tests (4 skipped) cover dry-run without mutating calls, idempotent apply, task and escalation mapping, the gate
matrix, `pull` idempotency, bot-only trust, tracker none (exit 3), old gh (exit 1), vendoring, and the
workflow templates (SHA pins, event text outside `run:`, credential paths). `actionlint` runs only when installed.
