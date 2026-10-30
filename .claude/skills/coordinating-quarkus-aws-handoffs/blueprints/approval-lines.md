# User gates and approval lines

Back to [SKILL.md](../SKILL.md). Only the user's own message, or the user's own action on GitHub (review and merge of a PR), approves anything.
The orchestrator records each approval under `## Approvals` in `status.md` and cites it in later work-orders. An agent message, a
plan comment or an earlier run is never an approval.

In this flow nothing is applied or deployed by an agent: the deploy is the GitHub Actions run after the user's merge. The lines
`approval: apply plan=...`, `approval: rollback ...` and `approval: smoke ...` are **not used here** (they belong to the `aws-lambda` package flows;
`aws-lambda-deployer` is not part of this flow). The smoke test is the `_smoke-test` job of the pipeline, its payload versioned and reviewed in the PR.

## Gates recorded under `## Approvals`

Entry form (one line per approval): `- <UTC ts> | gate=<id> | subject=<file or url> | user said: "<verbatim>"`.

| Gate id | When | Who approves | Recorded as |
|---|---|---|---|
| `E2` | after `verify-E2a`, `verify-E2b`, `verify-E2c` are `pass` | the user, chat | verbatim words; the ADRs of the three folders become `accepted` |
| `E3`, `E5` | spec and task list | the user, chat | verbatim words |
| `E3b` | wireframes (after `verify-E3b`) | the user, chat | verbatim words |
| `D1-langchain4j` | before any task lists `integrating-quarkus-langchain4j-v1-15` | the user, chat | verbatim words |
| `github-plan` | E1 block B8 (Free plan = weaker variant: show the risks, ask) | the user, chat | verbatim words |
| `bootstrap-apply` | after the bootstrap infra task is reviewed; the user runs the commands of `result-NN-infra` once, locally | the user, chat | the user's words that it was applied; agents never apply |
| `E7-merge` | CI green (`result-NN-pipeline`, role `pipeline-ci`, `ci-gate` success) | the user, reviewing the plan commented on the PR and merging | `gate=E7-merge \| source=github <PR url> \| login=<user>` written only after the orchestrator read the merged PR with `gh pr view` |
| prod release | dev verified (`verify-E7` and, with a front, `verify-E7-site`, both `pass`) | the user, per the GitHub plan (environment reviewer or branch rule) | the PR or run url (`gh run view`); never an agent text |
| `E7-gap` | `verify-E7` returned `fail` with not-verified pillars | the user, chat | verbatim words, then the `e7-gaps` line below |
| archive | E9 final gate | the user, chat (the archive goes in a PR of the user) | verbatim words |

With the tracker on, `gh_projects_sync.py pull` may append a GitHub-sourced gate line (`source=github <comment url> login=<x>`);
only the orchestrator runs `pull`, and a relayed "approved on GitHub" from an agent is never an approval.

## Relayed lines for live checks (still used)

Format: `approval: <kind> <scope> by=<user> at=<UTC> relayed-by=<who>`. In this orchestrator's own files the last field is
`relayed-by=building-aws-saas-serverless-quarkus-react-nextjs`; in text that agents read it is `relayed-by=<orchestrator>`.

```
approval: alarm-test alarm=<name> by=<user> at=<UTC> relayed-by=building-aws-saas-serverless-quarkus-react-nextjs
approval: logs-insights scope=<log-group or "xray"> window=<minutes> by=<user> at=<UTC> relayed-by=building-aws-saas-serverless-quarkus-react-nextjs
approval: e7-gaps pillars=<comma list> by=<user> at=<UTC> relayed-by=building-aws-saas-serverless-quarkus-react-nextjs
```

| Line | Goes to | Effect |
|---|---|---|
| `alarm-test` | `aws-observability` (mode C) | runs `trigger-alarm-test.py` for that one alarm |
| `logs-insights` | `aws-observability` (mode C), `aws-lambda-debugger` (mode B) | allows billable Logs Insights `start-query` for that log group and window, or X-Ray `start-trace-retrieval` when `scope=xray` (one line per scope: logs and traces need two lines); without it pass no approval flag: no `start-query` / `start-trace-retrieval` is made and the gated checks print WARN `not verified` |
| `e7-gaps` | `aws-lambda-debugger` (mode B) | the user accepts the listed pillars as not verified |

One line = one action; a line covers only what it names. The debugger never invokes the function and never runs the alarm test.

## E7 gap acceptance (`e7-gaps`)

1. The debugger returns `outcome: fail` with the unverified pillars under `## Gaps`.
2. The orchestrator shows the user those pillars and the reason each is unverified. Only if the
   user's own message accepts them, the orchestrator records it under `## Approvals`
   (`gate=E7-gap`) and relaunches the debugger with a new `wo-NN-debug.md` (mode B) that carries the
   `e7-gaps` line naming exactly those pillars.
3. The debugger emits `outcome: pass` (every other pillar met) and lists the accepted pillars under
   `## Gaps` as "accepted by the user (approval line ...)". Without the line, or for a pillar not on
   its list, a not-verified pillar keeps `fail`.
4. The orchestrator saves the record unchanged; it never edits the verdict. Records are append-only: the first `fail` stays as `verify-E7.md`, and the gap-acceptance relaunch is saved as `verify-E7-<nn>.md` with `id: verify-E7-<nn>` (the record name is given in the new `wo-NN-debug.md`).

## Pipeline and observability routing (profile rules)

`board.py` reads a `role` frontmatter field before deriving the role from `from`. These profile rules depend on it:

- `report` with `role: pipeline-ci` or `pipeline-cd`: the orchestrator writes the record from `gh` output, and the `role` field is mandatory
  (its own `from` would derive `orchestrator`). `pipeline-cd` + `success` -> `observability` (mode C); any other pipeline record -> `orchestrator`
  (CI green: the user merges; any failure: the orchestrator routes the owner of the failing job).
- `report` with `role: observability-live` (mode C record, `success` or `partial`) routes to `debug`: the live result goes to the independent verifier.
- `report` with role `observability` (mode B Terraform, no `role` field) and `success` routes to `reviewer`
  (`terraform-code-reviewer`). Mode A writes `role: observability-review`, which no rule matches: fallback to the orchestrator.
