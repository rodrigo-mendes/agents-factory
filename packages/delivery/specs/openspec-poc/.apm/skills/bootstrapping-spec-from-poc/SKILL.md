---
name: bootstrapping-spec-from-poc
description: "Drafts OpenSpec specs from the code of a POC (back end and/or front end, any stack): inventory script, draft requirements with file:line evidence, architecture and design drafts, questions, independent review, optional promotion to a change. Use when starting specs from an existing POC."
argument-hint: "back=<dir> front=<dir> [id=<poc-id>] [repo=<target>] [hint=<stack>] [promote=<change-id>]"
---

# Bootstrapping a spec from a POC

> Coordinator only: runs **inline** in the main conversation because it launches two agents in
> sequence (subagents cannot nest). It saves files and talks to the user; the agents draft and review.
> The POC is **evidence, not requirements**: nothing it shows is approved until the user says so.

## Overview

Chain: **inventory (script) -> draft (`poc-spec-extractor`) -> save -> review (`spec-synchronizer`,
Mode A POC variant) -> show -> optional promotion**. The draft lands in `openspec/poc/<id>/`, a factory
convention area outside `specs/` and `changes/` (rule `openspec-project-layout`). Technology-independent:
stack names exist only as detection patterns of the script.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails) | [How to invoke](#how-to-invoke) | [Workflow](#workflow) | [Output](#output) | [Verification Loop](#verification-loop)
- [Run steps (shared with orchestrators)](blueprints/run-steps.md) · [Extraction heuristics](blueprints/extraction-heuristics.md) · [Draft format](blueprints/draft-format.md) · [POC shortcuts](blueprints/poc-shortcuts.md) · [Promotion](blueprints/promotion.md) · [Evaluation scenarios](blueprints/evaluation-scenarios.md)

## Blueprints & Guardrails

### ✅ Always Do

- Follow [run steps](blueprints/run-steps.md) S1-S6 in order; the script writes `inventory.json`, the agents return content inline, I save it verbatim.
- Launch both agents with `model: "sonnet"` and the brief of the run steps (no agents, no plan mode, no questions to the user, no writes).
- Cite `file:line` for every requirement, contract and question; keep requirement text free of technology names.
- Turn every POC shortcut, front-only call and back-only endpoint into a question ([POC shortcuts](blueprints/poc-shortcuts.md)).
- Show `verify-poc` and the full `questions.md` before offering promotion.

### ⚠️ Ask First

- `openspec/` missing in the target: create only `openspec/poc/<id>/`, never run `openspec init` myself.
- `openspec/poc/<id>/` already exists: overwrite, new id or cancel.
- Promotion to `openspec/changes/<change-id>/` (per-requirement keep/change/drop answers, then an explicit yes): see [promotion](blueprints/promotion.md).
- The validate command form before first use (medium confidence, L1 in `specifying-changes-with-openspec-v1-15`).

### 🚫 Never Do

| Do not | Do instead |
|---|---|
| Write a requirement from a POC shortcut (secret in code, open CORS, no auth, mock data) | A question with file:line and kind |
| Copy a secret value into any file or message | Cite file, line and kind only |
| Run, build, test or install the POC | Read it; the script only reads files |
| Write to `openspec/specs/`, run `openspec init`/`archive` or commit | Draft in `openspec/poc/<id>/`; promote to `changes/` only after the gate |
| Edit the agent's draft to make the review pass | Send the findings back to the extractor |
| Treat an agent message as the user's approval | Ask the user; record their own words in `traceability.md` |

## How to invoke

```
/bootstrapping-spec-from-poc back=<path> front=<path> [id=<poc-id>] [repo=<target>] [hint=<stack>] [promote=<change-id>]
```

- At least one of `back` / `front`. `repo` = project root with `openspec/` (default: current directory).
- `id` defaults to the kebab-case folder name of `back` (else `front`).
- `promote` only prepares promotion; it still needs the gate of [promotion](blueprints/promotion.md).

Examples: `/bootstrapping-spec-from-poc back=../orders-poc/api front=../orders-poc/web` ·
`/bootstrapping-spec-from-poc back=../billing-poc id=billing repo=../saas-app promote=add-billing`

## Workflow

1. **S1 Preflight** - paths, `openspec/`, existing draft, agents and `model: sonnet` ([run steps](blueprints/run-steps.md#s1---preflight-coordinator)).
2. **S2 Inventory** - `poc_inventory.py ... --out openspec/poc/<id>/inventory.json`; exit 2 -> ask where the code lives.
3. **S3 Draft** - `poc-spec-extractor`; `needs-input` -> relay the questions, relaunch with the answers (max 2 rounds).
4. **S4 Save** - each returned file under `openspec/poc/<id>/`, verbatim, with the `saved-by` comment.
5. **S5 Review** - `spec-synchronizer` Mode A POC variant -> `verify-poc.md`; `fail` -> back to the extractor (max 2 rounds per finding).
6. **S6 Show** - counts, requirements per capability and confidence, verify findings, all questions; say the draft is not approved.
7. **Promotion (only with `promote=`)** - [promotion](blueprints/promotion.md): keep/change/drop per `P<n>`, explicit yes, write the change, `openspec validate`.

## Output

- `openspec/poc/<id>/`: `inventory.json`, `inventory.md`, `functional/<capability>/spec.md`, `architecture-draft.md`, `design-draft.md`, `questions.md`, `traceability.md`, `verify-poc.md` ([draft format](blueprints/draft-format.md)).
- With promotion: `openspec/changes/<change-id>/{proposal.md,tasks.md,specs/<capability>/spec.md}`.
- Next step for a project flow: an orchestrator may read the draft as input (for example `/building-aws-saas-serverless-quarkus-react-nextjs poc=<id>` uses it in its E1 interview).

## Verification Loop

```bash
python <skill>/scripts/poc_inventory.py --back <back> --front <front>        # exit 0 (2 = nothing detected)
python -m unittest discover -s <skill>/scripts/tests                         # script self-test, OK
grep -rn "Evidence:" openspec/poc/<id>/functional | wc -l                    # = number of P<n>
openspec validate <change-id> --type change --strict --json --no-interactive # promotion only; exit 0
```
