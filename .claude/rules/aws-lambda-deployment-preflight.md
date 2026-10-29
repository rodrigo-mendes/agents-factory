---
name: aws-lambda-deployment-preflight
description: "Pre-flight checks before deploying an AWS Lambda .zip function with Terraform: artifact and size limits, non-deprecated runtime, handler, environment variables without secrets, saved plan with relayed approval, waiters, version and alias. Use when editing Terraform for a Lambda or preparing a Lambda release."
paths:
  - "**/*.tf"
  - "**/*.tfvars"
---

# AWS Lambda deployment pre-flight (.zip Event Functions)

Technical facts live in the two skills named below. This rule states what to check before a deploy
and where to look; it does not duplicate skill bodies. Tags `(unverified)` and
`(medium confidence)` from a skill apply here too.

Activation: a glob cannot test file content. The binary artifact (`function.zip`) is not an editable
file, so a glob on it would never load; the pattern covers Terraform sources and variable files
only. Apply this rule **only when the Terraform declares** `aws_lambda_function` (or a module that
wraps it); otherwise ignore it.

Overlap: this is the AWS counterpart of the OCI `deployment-preflight-checks` rule (different cloud,
different project kind, not loaded together). It composes with the AWS Terraform rules of package
`aws-terraform` (`aws-terraform-code-standards`, `aws-terraform-project-config`,
`aws-terraform-skills-management`: plan with `-out`, never `-auto-approve`); the more restrictive
wins. Do not confuse them with the OCI rule `terraform-standards`. HCL itself belongs to
`provisioning-aws-lambda-v6`; building the artifact belongs to the Quarkus developing skills.

## Skills

| Need | Skill |
|---|---|
| Pre-flight, plan gate, waiters, publish, alias, smoke test, rollback | `deploying-aws-lambda` |
| Diagnosis of a failed or misbehaving deployed function (read-only) | `debugging-aws-lambda` |

Blueprints of `deploying-aws-lambda`: `preflight-and-plan`, `apply-waiters-publish-alias`,
`smoke-test-and-verification`, `rollback-and-cleanup`, `always-do-patterns`, `never-do-patterns`.

## Pre-flight checklist (all before the plan is shown)

1. Artifact exists and is the Quarkus build's `function.zip`; direct upload and unzipped size limits
   respected, otherwise S3 upload (`deploying-aws-lambda`, `preflight-and-plan`).
2. Runtime is not deprecated (`developing-quarkus-amazon-lambda-v3-40` lists the current table).
3. Handler is configured as the skill states; native builds also carry the environment variable the
   Quarkus skill names (`developing-quarkus-amazon-lambda-v3-40`).
4. Environment variables hold no secret values and the full map is declared
   (`deploying-aws-lambda`, `never-do-patterns`).
   Projects may deny agents read access to `*.tfvars` (this repository's `settings.json` does): then
   check only the `.tf` side and report the `.tfvars` values as not checked; never ask to lift the deny.
5. `terraform plan -input=false -out=tfplan` is shown to the user, then STOP until the orchestrator
   relays the user's explicit approval of that saved plan (`always-do-patterns`, gate 1).
6. The alias's current version is recorded as `PREV` before apply (`always-do-patterns`).
7. Waiters follow every apply; a version is published; callers and triggers use the alias ARN
   (`apply-waiters-publish-alias`).

## Always

- Apply only the saved, reviewed plan: `terraform apply -input=false tfplan`.
- Run the waiter after each apply, then smoke-test through the alias and assert `StatusCode`,
  absence of `FunctionError` and `ExecutedVersion` (`smoke-test-and-verification`).
- Stop on `LastUpdateStatus` or `State` of `Failed` and hand over to `debugging-aws-lambda`.

## Ask First

- Traffic shifting, upload path, rollback channel, code signing, provisioned or reserved
  concurrency, runtime update mode: take the question from the skill's Ask-First table.
- SnapStart: only published versions or aliases; confirm the skill's activation checks before shifting
  traffic.

## Never

- `terraform apply -auto-approve`, or an apply without the relayed approval.
- Publish, invoke or update again while `LastUpdateStatus` is `InProgress`.
- Target `$LATEST` or an unqualified ARN in production.
- Send a partial environment map, or put secret values in environment variables.
- `delete-function` without `--qualifier`.
- Mutate anything while debugging: `debugging-aws-lambda` is read-only.

## Verify

- Grep the `.tf` files for `auto-approve`, `$LATEST` and literal secret-looking values in
  `environment`.
- Check that the plan file is the one shown to the user before applying it.
