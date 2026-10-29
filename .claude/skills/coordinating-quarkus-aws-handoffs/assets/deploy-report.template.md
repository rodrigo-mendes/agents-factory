---
kind: deploy-report
id: result-<nn>-deploy            # file name never starts with "report"
from: aws-lambda-deployer
to: building-quarkus-aws-saas
change: <change-id>
task: deploy
refs: [wo-<nn>-deploy, result-<nn>-code, result-<nn>-infra]
requirements: [R1]
outcome: success                  # success | partial | failed | needs-input
deploy_cycles: <n>                # this run's cycles; the board counts failed deploy-reports per change
createdAt: <ISO 8601 UTC>
---

## Release

- Function, region, alias, `PREV` version, new version, previous and new alias routing.
- Artifact: path and SHA-256.
- Plan: plan file, plan SHA-256, change summary (add/change/destroy counts).

## Approval

- The verbatim relayed approval line(s) used, or "none - stopped at gate".

## Evidence

- Commands actually run with outputs: waiter results, `State`, `LastUpdateStatus`, smoke assertions
  with `ExecutedVersion`. Secrets, tokens and event bodies redacted.
- `smoke_start_epoch: <epoch seconds taken just before the smoke invoke>` (the observability Mode C window starts here).
- Rollback: performed or not, why, result.
- Unconfirmed: every `(unverified)` / `(medium confidence)` item relied on.

## Suggested next step

success -> observability (`aws-observability` mode C -> `result-<nn>-observability`, then `aws-lambda-debugger` mode B -> `verify-E7`);
failed -> diagnosis (`aws-lambda-debugger` mode A); needs-input -> the numbered questions.
The orchestrator routes. Context: this file.

## Cleanup proposal

- `none`, or the old versions (never the alias target or `PREV`) and the exact `aws lambda delete-function --function-name <fn> --qualifier <N>` per version. Proposal only: the deployer never runs `delete-function`; after E9 the user runs the listed commands themselves if they want.

## Files

- `<terraform_dir>/tfplan` (saved plan)
- `<terraform_dir>/.terraform.lock.hcl` (only if `init` changed it)
