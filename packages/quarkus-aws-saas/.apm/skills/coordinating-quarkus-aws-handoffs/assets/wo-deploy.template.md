---
kind: work-order
id: wo-<nn>-deploy
from: building-quarkus-aws-saas
to: aws-lambda-deployer
change: <change-id>
task: deploy
refs: [result-<nn>-code, result-<nn>-infra]
requirements: [R1]
status: pending
createdAt: <ISO 8601 UTC>
---

## Scope

Release the already-built artifact through a saved Terraform plan, apply only an approved plan, wait,
smoke-test through the alias, roll back if the work-order allows it. Steps 0-8 of `deploying-aws-lambda`.

## Skills

- deploying-aws-lambda

## Requirements

- R1: <requirement> - smoke scenario: <happy path>.

## Constraints

- artifact: `<path/function.zip>` expected sha256: `<hash>`
- terraform_dir: `<path>`; function_name: `<name>`; alias: `<alias>`; region: `<region>`
- identity: AWS profile `<name>` (never credentials in text)
- smoke: payload `<json or file>` (approved by the user together with the plan: `approval: smoke ...` below); assert `StatusCode`, no `FunctionError`, expected body `<...>`
- traffic_strategy: all-at-once | weighted canary `<weights>`; upload_path: `<direct|s3>`
- rollback: only with a relayed `approval: rollback alias=<alias> to=<PREV> ...` line (no pre-authorisation)
- cold start target (NFR): `<ms>`

Approval lines (the orchestrator pastes the user's approval verbatim, one per apply; absent = stop at the plan):

```
approval: apply plan=<planfile> sha256=<hash> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas
approval: smoke payload=<file or sha256> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas
```

Relaunch: records are append-only. The first launch (no approval line) ends `needs-input` at the plan gate and
its `result-<nn>-deploy.md` is kept as evidence. The relaunch is a **new** work-order `wo-<mm>-deploy.md` (next
free number) with `refs: [result-<nn>-deploy]` and the relayed approval lines; it skips re-planning, the
deployer re-verifies the plan's sha256 now and stops with `needs-input` on a mismatch.

## Limits

- deploy_cycles: <effective value>   (source: profile | override | args)

## Acceptance criteria

- [ ] `terraform plan` shows no unexpected destroy; plan hash recorded.
- [ ] Applied only with a matching approval line; waiter passed; `ExecutedVersion` equals the new version.
- [ ] Smoke test of every happy-path scenario OK.
- [ ] `result-<nn>-deploy.md` valid (kind `deploy-report`) with Release, Approval, Evidence, Suggested next step.
