# Object mapping (git -> GitHub)

Derived from `scripts/_model.py` (`desired_state`) and its tests. Git is canonical: the mirror is
rebuilt from files, never the other way round. Back to [SKILL.md](../SKILL.md).

## Contents

- [Objects](#objects)
- [Stage and Status](#stage-and-status)
- [Project fields and labels](#project-fields-and-labels)
- [Markers and adoption](#markers-and-adoption)
- [State file github.yaml](#state-file-githubyaml)

## Objects

| Source in git | GitHub object | Key | Fields | Notes |
|---|---|---|---|---|
| change `<id>` (`proposal.md`) | issue `change: <id>` + project item | `change` | Kind=change, Change, Stage, Status, Gate | body = `## Why` + `## What Changes` + link to the file |
| task: a `tasks.md` `## N.` group (`T<n>`) or any work-order `task:` id | sub-issue of the change | `task:<id>` | Kind=task, Change, Status | title `task: <id> <title>` |
| ADR `NNN-*.md` mentioned by the change | sub-issue of the change | `adr:<NNN>` | Kind=adr, Change, Status | only ADRs referenced by the change are mirrored |
| `escalation` record, or a report with `outcome: needs-input` | sub-issue | `escalation:<record-id>` | Kind=escalation, Change, Status | open: label `blocked`, Status Blocked; title `escalation: <id> ...` or `needs-input: <id>` |
| `spec-delta-NN` record | comment on the change issue | `delta:<record-id>` | none | edited in place when the delta status changes |
| `handoff/status.md` | one summary comment on the change issue | `summary` | none | Stage, gate prompt, Next action / Counters / State sections |

- ADR mention forms: `ADR-003`, `ADR 3`, `adr_003` in proposal, design, tasks or any record. An ADR
  shared by two changes gets **two** issues (the key marker carries the change id).
- ADR Status: Done when the ADR status is `accepted`, otherwise Todo.
- Bodies longer than 60,000 characters are truncated with a link to the file (the GitHub body limit is
  (unverified), register R15).
- `close` closes every mirrored issue and sets Status Done: done items close as `completed`; a task that is
  already cancelled stays closed `not_planned`.

## Stage and Status

| Rule | Behaviour |
|---|---|
| Stage | `--stage E<n>` wins; else the highest `verify` record with `outcome: pass` and stage `E<n>`, plus 1 (E1 when none), capped at E9 |
| Finished | a passing E9 verify marks the run finished: change Status Done |
| Change Status | Done (closing or finished) > Blocked (open escalation or unanswered needs-input) > In progress (any record) > Todo |
| Task Status (work-orders) | blocked > all done > in-progress > pending; cancelled work-orders are ignored; all cancelled gives closed `not_planned` |
| Task Status (no work-order) | `tasks.md` checkboxes: all done = Done, some = In progress, none = Todo |
| Done tasks | issue closed with reason `completed` (REST `state_reason`, (unverified), register R4) |
| Escalation | closed `completed` when answered (escalation status not open) or when a later record refers to the needs-input report |

## Project fields and labels

| Field | Type | Values |
|---|---|---|
| Stage | single select | E1..E9 |
| Kind | single select | change, task, adr, escalation |
| Change | text | change id |
| Gate | text | `E<n> pending`, then `E<n> approved` or `E<n> rejected`; `-` outside gate stages |
| Status | built-in | Todo, In progress, Blocked, Done (option names compared case-insensitively) |

- `push` never overwrites an answered Gate of the current stage with `pending`.
- Labels created by bootstrap: `openspec`, `openspec:change`, `openspec:task`, `openspec:adr`,
  `blocked`, and `gate:<E>:approved|rejected` for E1, E2, E3, E5, E7, E9. `delta:<nn>:<verdict>`
  labels are created lazily by the gate workflow.
- `push` removes only the `blocked` label; labels it does not own are untouched.
- Missing field or option: a warning is printed and the value is skipped (the gh CLI cannot add
  options to an existing field; the Status field usually lacks Blocked, register R7).

## Markers and adoption

Every body or comment written by the scripts starts with `<!-- openspec-github:bot v1 -->` and a key
marker `<!-- openspec-github:key <change>/<object> -->`. Delta comments also carry
`<!-- openspec-github:delta status=<status> -->`.

When `github.yaml` has no id for an object (a fresh Actions runner, a lost file), the script **adopts**
the existing issue or comment that carries the marker, so `board-sync` does not duplicate. Only objects
authored by `tracker.bot_login` or an approver are adopted; the check fails closed (with neither
configured nobody is trusted), and `bot_login` is required whenever `kind: github-projects`. A local `push --apply` under another login (never an approver when approvals are on GitHub) creates objects the runner will not adopt (register R8).

## State file github.yaml

`openspec/changes/<id>/handoff/github.yaml` is written by the script only (atomic replace on
`--apply`; a dry-run writes nothing locally). Readable by `_mini_yaml`.

| Key | Content |
|---|---|
| `schema` | 1 (another value is refused) |
| `tracker` | owner, owner_type, project_number, repo; a mismatch with the configured tracker is an error |
| `project_id`, `fields` | project node id and field/option ids |
| `change`, `tasks`, `adrs`, `escalations` | per object: issue, id, node_id, url, sha, state, labels, item_id, fields, parent_linked |
| `deltas` | per delta: comment_id, sha |
| `summary_comment_id`, `summary_sha` | the summary comment |
| `pulled` | confirmation comment ids already handled by `pull` (idempotency) |
| `vendor` | `{version, sha256}` recorded by `bootstrap --vendor` |

`sha` is a 16-hex digest of title and body: an unchanged object issues no write, so a second
`push --apply` with no git change makes zero mutating calls.
