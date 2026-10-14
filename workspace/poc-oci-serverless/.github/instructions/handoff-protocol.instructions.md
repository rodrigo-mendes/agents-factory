---
name: handoff-protocol
description: Agent-to-agent handoff protocol for the OCI serverless lifecycle — every agent reads existing handoff records on intake and writes one on exit. Applies to all agents and surfaces (IDE, cloud agent, CLI).
applyTo: "**"
---

# Handoff Protocol

All agent-to-agent handoffs in this repo pass through **structured record files** under `docs/handoff/<capability>/` — never through lossy prose. Source of truth: [docs/handoff/README.md](../../docs/handoff/README.md).

`<capability>` = the function/capability slug (e.g. `func-api-facade`). Records for one capability live in its own namespaced directory.

## Every agent MUST

1. **Intake (on start):** read any existing records in `docs/handoff/<capability>/` for the capability you are working on, and use them as context — skip re-analysis / re-discovery of anything already recorded there.
2. **Exit (on finish):** write a record to `docs/handoff/<capability>/` capturing what you did, then state the single next action.

## Two record kinds (frontmatter `kind:`)

| Kind | Written by | Consumed by | Content |
|------|-----------|-------------|---------|
| `work-order` (`stream-{a,b,c}.md`) | `@oci-serverless-architect` | `@oci-serverless-stack`, leaf agents | scope, components, constraints, dependencies, acceptance criteria |
| `report` (`report-*.md`) | `@oci-functions-java`, `@oci-terraform` | `@oci-serverless-stack` | files changed, OCIDs, validation, acceptance status, next action |
| `report` → `deploy-report.md` | `@oci-deployer` | `@oci-debugger`, user | image tag, smoke HTTP status, OCIDs, outcome |
| `report` → `diagnosis-report.md` | `@oci-debugger` | `@oci-deployer` / `@oci-terraform` | root cause, evidence, exact fix, classification |

Skeleton templates: `docs/handoff/_templates/`.

## Per-agent contract (summary)

- **architect** → writes `stream-{a,b,c}.md` work-orders.
- **stack** → reads work-orders; delegates (via the `agent` tool); requires a `report-*.md` back from each delegated agent before proceeding.
- **functions-java / terraform** → on exit write `report-java.md` / `report-terraform-*.md` (files changed, resource OCIDs, validation).
- **deployer** → on intake read `diagnosis-report.md` (apply the recorded fix, skip rediscovery); on exit write `deploy-report.md`.
- **debugger** → on intake read `deploy-report.md` (skip re-probe); on exit write `diagnosis-report.md` (root cause + exact fix).

## Invocation mechanism (this surface)

- In VS Code / JetBrains: agents may offer native `handoffs:` buttons (see each `.github/agents/*.agent.md`), or you `@`-mention the next agent / run its `/prompt`.
- On GitHub.com cloud agent and Copilot CLI (no agents/prompt files): the file records **are** the whole mechanism — read the latest record, do the work, write the next record, and state the next action in prose in that record's **Next action** section.

The records and their schema are identical across all surfaces; only the invocation UX differs.
