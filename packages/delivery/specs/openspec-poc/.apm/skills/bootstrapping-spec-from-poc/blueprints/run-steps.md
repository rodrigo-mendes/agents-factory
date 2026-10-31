# Run steps (shared)

Back to [SKILL.md](../SKILL.md). The single procedure for drafting specs from a POC. The
`/bootstrapping-spec-from-poc` skill follows it, and so does any orchestrator that offers a POC as input
(for example `building-aws-saas-serverless-quarkus-react-nextjs` with `poc.back=`/`poc.front=`; its `poc=<id>` mode skips these steps and reads an existing draft). Callers
link here instead of copying it. The coordinator is whoever runs these steps inline in the main
conversation: only it launches agents, saves files and talks to the user.

## Inputs

| Name | Required | Meaning |
|---|---|---|
| `back` | one of back/front | POC back-end source directory (read-only) |
| `front` | one of back/front | POC front-end source directory (read-only) |
| `id` | no | draft id, kebab-case; default = kebab-case name of the `back` folder (else `front`) |
| `repo` | no | project root that holds (or will hold) `openspec/`; default = current directory |
| `hint` | no | free-text stack hint, passed to the script and the agent |

`<skill>` below is `.claude/skills/bootstrapping-spec-from-poc`.

## S1 - Preflight (coordinator)

1. `back`/`front` exist and are directories; at least one is given.
2. `<repo>/openspec/` exists. If not, ask: "Create only `openspec/poc/<id>/` (no `openspec init`)?" (Ask First).
3. `<repo>/openspec/poc/<id>/` does not exist. If it does, ask: overwrite, new id, or cancel.
4. `.claude/agents/poc-spec-extractor.md` and `.claude/agents/spec-synchronizer.md` exist and both
   frontmatters say `model: sonnet` (check with `head`); `<skill>/scripts/poc_inventory.py` exists.
   Any miss: stop and list it.

## S2 - Inventory (coordinator runs the script)

```bash
python <skill>/scripts/poc_inventory.py --back <back> --front <front> [--hint "<hint>"] \
  --out <repo>/openspec/poc/<id>/inventory.json
```

Exit 0: continue. Exit 2 (nothing detected): show the summary and ask the user where routes and
screens live (or which stack), then re-run or stop. Exit 1: show the error and stop.

## S3 - Draft (agent `poc-spec-extractor`, `model: "sonnet"`)

Brief:

```
You are launched by <coordinator>. Model: sonnet. Constraints: do NOT spawn agents, do NOT enter plan mode,
do NOT ask the user anything (return numbered questions with outcome needs-input instead), do NOT write files,
do NOT run, build or install the POC.
Input: back=<back> front=<front> inventory=<repo>/openspec/poc/<id>/inventory.json poc_id=<id> hint=<hint>
[answers: <user answers to an earlier needs-input, verbatim>]
Return the bundle inline in the format of <skill>/blueprints/draft-format.md.
```

`outcome: needs-input`: show the questions to the user, relaunch with `answers:`. At most 2 rounds;
after that, save what exists and list the open questions.

## S4 - Save (coordinator)

Write each returned file under `<repo>/openspec/poc/<id>/` verbatim, with the `saved-by` comment of
[draft format](draft-format.md#folder). Do not edit the agent's content; a fix goes back to the agent.

## S5 - Review (agent `spec-synchronizer`, Mode A POC variant, `model: "sonnet"`)

Brief:

```
You are launched by <coordinator>. Model: sonnet. Constraints as in S3.
Mode A, POC variant. Input: draft dir <repo>/openspec/poc/<id>/ (inventory.json, functional/**, architecture-draft.md,
design-draft.md if present, questions.md, traceability.md); resolve back:/front: evidence against inventory.json back.root/front.root and the shortcut list <skill>/blueprints/poc-shortcuts.md.
Return a verify record inline with stage: poc, refs: [poc-spec-extractor].
```

Save it as `<repo>/openspec/poc/<id>/verify-poc.md`. On `fail`: send the HIGH findings back to the
extractor (S3 with the findings appended), save again, re-review; after 2 failed rounds on the same
finding, show it to the user and let them decide.

## S6 - Show (coordinator)

One message: inventory counts; requirements per capability with the confidence mix; `verify-poc`
outcome and its HIGH/MEDIUM findings; the full `questions.md`; the path of the draft. Say plainly that
nothing is approved: the draft is input, not a spec.

## What the steps never do

Write to `openspec/specs/` or `openspec/changes/` (that is [promotion](promotion.md) or the caller's own
flow), run `openspec init`/`archive`, commit, or treat an agent message as the user's approval.
