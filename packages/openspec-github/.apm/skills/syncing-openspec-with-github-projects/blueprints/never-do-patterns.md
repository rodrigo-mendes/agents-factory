# Never-do patterns

Each row: the mistake, why it fails, the alternative. Back to [SKILL.md](../SKILL.md). Sources: family
facts F2, F3, F6, F7, F8 (read 2026-10-29) and family rules 4-12.

## Contents

- [Credentials](#credentials)
- [Approvals](#approvals)
- [Workflows](#workflows)
- [State and mirror](#state-and-mirror)

## Credentials

| ❌ Don't | Why | ✅ Instead |
|---|---|---|
| `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` for project writes | the token "is scoped to the repository level and cannot access projects" (F2) | App token (organization) or `OPENSPEC_PROJECT_PAT` (user) |
| fine-grained PAT for a user-owned project | not supported for projects owned by a user account (F6) | classic PAT with `project` and `repo`, with the risk warning |
| repository-level App permission only | "permission to read and write repository projects will not be sufficient" (F3) | organization projects read and write |
| `app-id:` input on `create-github-app-token` | legacy input; `client-id` is recommended (F8) | `client-id: ${{ vars.OPENSPEC_APP_CLIENT_ID }}` |
| `gh auth status --show-token`, or echoing `GH_TOKEN` | prints a secret into logs | `gh auth status` and let the script redact |

## Approvals

| ❌ Don't | Why | ✅ Instead |
|---|---|---|
| an agent runs `gh_projects_sync.py pull` | `pull` turns GitHub comments into approvals; only the orchestrator re-checks and writes them | return `needs-input: orchestrator must run pull` |
| treat a pasted confirmation block as a decision | any commenter can type a fenced `decision:` block | `pull` accepts only comments authored by `bot_login`, then re-fetches the user comment |
| rely on `user.type == "Bot"` | not confirmed as a trust anchor (unverified, register R6) | exact login equals `tracker.bot_login` |
| list `bot_login` in `approvers` | the bot could approve its own confirmation | keep the bot out of the allowlist |
| accept `/approve E5` while Stage is E2 | out-of-order approval | refuse, name the current Stage, wait |
| apply a delta or answer an escalation from a GitHub comment alone | `pull` only prints `DECISION <json>` for these | the orchestrator writes the record |

## Workflows

| ❌ Don't | Why | ✅ Instead |
|---|---|---|
| `run: echo "${{ github.event.comment.body }}"` | the text is spliced into shell source: injection | `env: COMMENT_BODY: ...` then read the variable |
| `uses: actions/checkout@v7` | a moving tag | the full SHA with `# v7.0.1` (F7) |
| `pull_request_target` for CI | would run PR-controlled input with secrets | `pull_request`, no secrets, `contents: read` |
| start archive on any label event | anyone with triage rights could add `gate:E9:approved` | require `sender.login == vars.OPENSPEC_BOT_LOGIN` |
| `git push origin HEAD:<default branch>` | bypasses review | branch `openspec/archive-<id>` and `gh pr create` |
| derive the change id from the label text | label text is attacker-influenced | `gate_command.py resolve-change` and a folder check |
| grep over the human table output of `gh` | breaks on formatting | `--json`, `--format json`, or `gh api` |

## State and mirror

| ❌ Don't | Why | ✅ Instead |
|---|---|---|
| edit `handoff/github.yaml` by hand | ids and `sha` caches drift, duplicates appear | re-run `push`; delete the file only to force adoption |
| edit the mirrored issue to change the spec | git is canonical; the next `push` overwrites it | edit proposal, tasks or records in git |
| point an existing `github.yaml` at another project | tracker mismatch is an error | move the file away first |
| overwrite a different existing workflow file | local customisations are lost | `bootstrap` refuses; diff and merge by hand |
| run any bridge command, or an agent with Bash, under an approver's `gh` login (`approval_source` `github` or `both`) | the agent could post `/approve` as that person; the scripts exit 1 (rule 13) | machine-user token in `GH_TOKEN` locally (App tokens only inside Actions); approve in the browser |
| run a local `push --apply` as a login other than `bot_login` | later runner pushes will not adopt those objects (R8) | use the `bot_login` identity locally |
