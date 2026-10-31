# openspec-poc

Drafts **OpenSpec** specs from the code of a **proof of concept** (POC): back end, front end or both,
any stack. The POC is treated as **evidence, not requirements**: every drafted item cites `file:line`
and a confidence, and every POC shortcut (hard-coded secret, open CORS, no auth, mock data, a front
call with no endpoint) becomes a question for the user. Nothing is approved until the user says so.

Depends on `factory-core`, `openspec-core` (format and CLI) and `handoff-core` (the `spec-synchronizer`
reviewer). No technology is assumed: stack names appear only as detection patterns of the script.

## Contents

| Artifact | Path under `.apm/` | Role |
|---|---|---|
| Skill `bootstrapping-spec-from-poc` (inline coordinator, `/bootstrapping-spec-from-poc`) | `skills/bootstrapping-spec-from-poc/` | runs the inventory, launches the extractor and the reviewer, saves the draft, optional promotion |
| Script `poc_inventory.py` | `skills/bootstrapping-spec-from-poc/scripts/` | stdlib, read-only: endpoints, OpenAPI, models, validations, errors, auth, shortcuts, tests, screens, calls, back-front cross-check; tests in `scripts/tests/` |
| Agent `poc-spec-extractor` | `agents/poc-spec-extractor.agent.md` | read-only, `model: sonnet`; returns the draft bundle inline |
| Reviewer | `spec-synchronizer` (package `handoff-core`) | Mode A, POC variant; returns `verify-poc` |

## Flow

```
/bootstrapping-spec-from-poc back=<dir> front=<dir>
  S1 preflight -> S2 poc_inventory.py --out openspec/poc/<id>/inventory.json
  -> S3 poc-spec-extractor (draft, inline) -> S4 save openspec/poc/<id>/
  -> S5 spec-synchronizer Mode A POC variant -> verify-poc.md
  -> S6 show counts, findings, questions
  -> [promote=<change-id>] keep/change/drop per P<n> + user's yes -> openspec/changes/<change-id>/ + openspec validate
```

Draft area `openspec/poc/<id>/` (factory convention, rule `openspec-project-layout`): `inventory.json`,
`inventory.md`, `functional/<capability>/spec.md`, `architecture-draft.md`, `design-draft.md`,
`questions.md`, `traceability.md`, `verify-poc.md`.

## Use with a project orchestrator

The steps live in one blueprint (`run-steps.md`) that orchestrators follow instead of copying.
`/building-aws-saas-serverless-quarkus-react-nextjs` accepts `poc=<id>` (an existing draft) or
`poc.back=`/`poc.front=` (draft first) and uses the draft **only as input to its E1 interview**: what
the POC shows becomes confirmation questions with evidence; every block still needs the user's
confirmation. It does not promote; its own E3 writes the change.

## Run the script tests

```bash
cd .apm/skills/bootstrapping-spec-from-poc
python -m unittest discover -s scripts/tests
```
