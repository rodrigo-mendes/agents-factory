---
name: syncing-openspec-to-github
description: "Mirrors one OpenSpec change into its GitHub Project (issues, sub-issues, fields, delta comments) with a dry-run plan first and a status check. Use when the board must be refreshed after records or tasks changed. Not for reading approvals, closing or bootstrapping."
argument-hint: "<change-id> --profile <yaml> [--stage E<n>] [--apply]"
context: fork
agent: openspec-github-syncer
disable-model-invocation: true
---

# Syncing OpenSpec to GitHub

Routes to the `openspec-github-syncer` agent, which runs `gh_projects_sync.py push` and `status` for one
change and returns the plan, the write count and any divergence. Git stays canonical; this command never
reads approvals (`pull`), closes issues or bootstraps a project: those belong to the orchestrator. The
knowledge lives in `syncing-openspec-with-github-projects`.

## Quick Navigation

- [Guardrails](#guardrails)
- [How to invoke](#how-to-invoke)
- [Agent workflow](#agent-workflow)
- [Output](#output)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)

## Guardrails

### ✅ Always Do

- Run the dry-run first, then `--apply` only when the brief carries the orchestrator's relayed approval line.
- Report the plan, exit codes and every `DIVERGE` line unmodified, even after an apply.

### ⚠️ Ask First

- A `--stage` different from the computed one; a missing `--profile`.

### 🚫 Never Do

| Do not | Do instead |
|---|---|
| Run `pull`, `close` or `bootstrap` from this command | Tell the orchestrator to run them |
| Treat a GitHub comment as approval | Leave approvals to the orchestrator's `pull` and re-check |

## How to invoke

```
/syncing-openspec-to-github <change-id> --profile <yaml> [--stage E<n>] [--apply]
```

- `<change-id>` is the folder under `openspec/changes/`.
- `--profile <yaml>` is required (the family handoff profile); the repository root defaults to the current
  directory. When the profile is missing, the agent asks.
- `--stage E<n>` overrides the computed Stage (E1 to E9); the agent returns it as a question when it differs.
- `--apply` is honoured when the brief carries the orchestrator's relayed approval line for tracker writes.
  A user's own `--apply` typed in this command is itself the relayed line (the user typed it); without
  either, the agent runs the dry-run and stops.
- With `approval_source` `github` or `both`, the token in `GH_TOKEN` must not be an approver (the script exits 1).
- This command suits a manual refresh or another orchestrator; `building-quarkus-aws-saas` runs `push` inline.

Examples:

- `/syncing-openspec-to-github list-tenant-items --profile handoff-profile.yaml` returns the dry-run plan and the `status` result.
- `/syncing-openspec-to-github list-tenant-items --profile handoff-profile.yaml --stage E3 --apply` applies, because the user typed `--apply`.

## Agent workflow

1. **P0**: read `syncing-openspec-with-github-projects` (SKILL.md, CLI contract, approvals blueprint); stop if unreadable.
2. **P1**: `gh --version`, `gh auth status`; run `push` as a dry-run.
3. **P2**: with the relayed approval line (or the user's own `--apply`), run `push --apply`; without it, return the plan.
4. **P3 - Verify**: run `status`; after an apply expect exit 0 (`IN SYNC`), otherwise keep every `DIVERGE` line (exit 2 is a finding, exit 1 an error to return as is).
5. **P4**: return the report and the `Hand off: orchestrator - ...` line.

Exit codes returned as-is: 0 ok, 1 error, 2 divergence (a finding), 3 tracker disabled.

## Output

Commands and exit codes, `PLAN`/`APPLIED` lines, write count and stage, `DIVERGE` lines, warnings, needs-input
questions. Verification: the reply contains the exit code of each command and, after `--apply`, a `status` exit 0
or the `DIVERGE` list. No file is written except the script's own `handoff/github.yaml` on `--apply`.

## Evaluation Scenarios

See [blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).
