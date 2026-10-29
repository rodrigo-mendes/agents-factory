# Approvals and trust model

Derived from `scripts/gate_command.py`, `_model.py` (`evaluate`, `recheck_user_comment`) and
`gh_projects_sync.py pull`. Back to [SKILL.md](../SKILL.md).

## Contents

- [Principle](#principle)
- [Grammar](#grammar)
- [Gate workflow checks](#gate-workflow-checks)
- [What the workflow records](#what-the-workflow-records)
- [Pull: the orchestrator re-check](#pull-the-orchestrator-re-check)
- [Trust anchors and limits](#trust-anchors-and-limits)

## Principle

A GitHub comment is **evidence**, not approval. Three independent steps stand between a comment and a
gate: the gate workflow validates it, the orchestrator's `pull` re-validates it, and only the orchestrator
writes the line into `handoff/status.md` `## Approvals`. With `approval_source: chat` (the default)
the workflow ignores commands and `pull` refuses (exit 1, "approval_source is chat").

## Grammar

Only the **first line** of the comment is read, against these exact forms; the rest is quoted back
verbatim and never interpreted.

| Command | Where | Verdict |
|---|---|---|
| `/approve E<n>` | change issue | gate approved |
| `/reject E<n> <reason>` | change issue | gate rejected |
| `/accept delta-<nn>` | change issue | delta accepted |
| `/reject delta-<nn> <reason>` | change issue | delta rejected |
| `/revise delta-<nn> <answer>` | change issue | delta revise (answers a delta) |
| `/answer escalation-<nn> <text>` | that escalation's own issue | escalation answered |

Gates: E1, E2, E3, E5, E7, E9. An injection-looking body such as `/approve E2` followed by a shell
substitution on the next line is plain text: line 1 is the command, the rest is quoted.

## Gate workflow checks

`gate_command.py evaluate` reads the payload only from env (`COMMENT_BODY`, `COMMENT_AUTHOR`,
`COMMENT_URL`, `COMMENT_ID`, `ISSUE_NUMBER`, `CREATED_AT`), never argv. A command is recorded only when:

1. the author is in `tracker.approvers` and is not `tracker.bot_login`;
2. the body does not contain the bot marker;
3. the issue carries this tool's key marker and was created by a trusted author (bot_login or an approver);
4. gate: the change issue's **Stage** field equals the gate (no out-of-order approvals), the comment is
   newer than the Stage value's `updatedAt` (register R1), and the gate has no approved/rejected label yet;
5. delta: its comment is `proposed` or `revise` and the user comment is newer than the delta comment's `updated_at`;
6. escalation: the issue is the escalation's own, still open, and the comment is newer than its creation.

Outcomes: comments by the bot login and unknown verbs are **silently ignored**; every other failure
gets a refusal comment (reason + accepted grammar), no label.

## What the workflow records

On accept (with `--apply`): label `gate:E<n>:approved|rejected` or `delta:<nn>:<verdict>`, the Gate
field text `E<n> approved|rejected` (gates only), and a confirmation comment from the App or machine
user: bot marker, a fenced YAML block and the user's text quoted.

```yaml
decision: {change: list-tenant-items, gate: E2, verdict: approved, by: alice, comment_url: "...", comment_id: 991, created_at: "..."}
```

## Pull: the orchestrator re-check

`pull` (orchestrator only) reads the change issue and its escalation issues, keeps only comments whose
author login equals `tracker.bot_login`, and for each confirmation not yet in `pulled`:

1. fetches the referenced user comment again;
2. re-checks: same author as recorded, author is an approver and not the bot, no bot marker,
   `created_at` identical to the recorded one, confirmation not older than the user comment, and the
   first line still holds the recorded command (an edited comment is refused);
3. gate approved: appends to `## Approvals` (idempotent through `pulled` and a check for the comment URL):

```
- <UTC ts> | gate=E2 | subject=<change issue url> | source=github <comment_url> login=alice | user said: "<verbatim text>"
```

4. every other decision (rejected gate, delta, escalation) is printed as `DECISION <json>` for the
   orchestrator, which writes the records itself.

A dry-run prints `PLAN append status.md ## Approvals: ...` and writes nothing.

## Trust anchors and limits

- Two trust rules. `pull` accepts confirmation records only from `tracker.bot_login` (exact login).
  Adoption of mirrored objects and the gate's issue-author check accept `bot_login` or an approver
  (`_model.trusted_author`, which fails closed: with neither set nobody is trusted).
- `user.type == "Bot"` alone is not relied on (unverified, register R6). `bot_login` must not be an approver.
- With `approval_source` `github` or `both`, every bridge subcommand (and `gate_command.py evaluate` and
  `recheck`) reads the token's login (`gh api user`, fallback GraphQL viewer) and exits 1 when it is in
  `approvers` (family rule 13), so an agent sharing the operator's `gh` cannot post an approval in an
  approver's name. Locally use a machine-user token in `GH_TOKEN` (an App installation token cannot read its login, so it is refused outside Actions) and approve in the browser; in
  Actions an unreadable login (App installation token) only warns.
- `pull` refuses unless the profile and `openspec/github-tracker.yaml` are committed unchanged at HEAD, and
  prints `TRUST approvers=... bot_login=...`. The check compares the working tree with HEAD only: a
  **committed** edit of `approvers` or `bot_login` passes, so the printed TRUST line is the mitigation and
  the orchestrator must show it to the user for review. `pull` also checks that the user comment belongs to the same
  issue as the confirmation, and takes gate and delta decisions only from the change issue.
- The gate workflow runs only on issues carrying an `openspec` label; comments by anyone outside
  `approvers` are ignored silently (no refusal comment), refusals go only to approvers.
- The archive workflow does not trust the label: `gate_command.py recheck [<root>] --profile <yaml> --gate E<n>`
  (env `ISSUE_NUMBER`, read-only, first job `authorize`) must find the bot's confirmation and re-verify the
  user comment before any npm code runs. It does not replace `pull`: the archive pull request is a proposal.
- A stolen App key or PAT could post a forged confirmation; the `pull` re-check of the **user** comment
  (author, allowlist, time, text) is what makes a forged confirmation without a real approver comment fail.
- A comment edit after the confirmation is detected only by the `created_at` and text comparison.
- `/approve` for a gate other than the current Stage is refused with the current stage named: the fix
  is to wait for the Stage to reach that gate, never to repost.
