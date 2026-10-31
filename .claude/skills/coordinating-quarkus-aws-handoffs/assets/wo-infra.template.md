---
kind: work-order
id: wo-<nn>-infra
from: building-aws-saas-serverless-quarkus-react-nextjs
to: aws-terraform-engineer
change: <change-id>
task: <task-id>
refs: []
requirements: [R1]
status: pending
createdAt: <ISO 8601 UTC>
---

## Functionality

Plain sentences: what exists in AWS after this task and why the requirements need it.

## Diagram

The resource diagram of `changes/<id>/infra-design.md` for these resources.

## Scope

Infrastructure for task <task-id>: <resources, e.g. Lambda + alias, HTTP API route, DynamoDB table,
IAM role>. Terraform directory: `<path>`. Offline only: `terraform fmt -check`, `init -backend=false`,
`validate` and, if wanted below, a fully mocked `terraform test`. The engineer never runs `terraform plan`,
`apply`, `destroy` or `import`; the plan and apply run in the GitHub Actions pipeline (E7), except the one-time bootstrap below.

## Closed requirement (the engineer cannot ask; every line must be filled or the answer is `needs-input`)

- Services and resources: <list>
- Root module or reusable module: <root | module>
- Region(s) and account scope: <regions; account/environment>
- Naming and tagging inputs: <names/prefixes; tag keys and values>
- State backend: <S3 bucket, key, region and lock method | no backend>
- Mocked `terraform test` wanted: <yes | no>

## Skills

- provisioning-aws-<service>-v6 (one per service, e.g. lambda, api-gateway, dynamodb, iam, cognito, sqs, cloudwatch, xray)
- Observability resources (log groups, alarms, dashboards, X-Ray) belong to `aws-observability`, not here.

## Requirements

- R1: <requirement text> - infra consequence: <what must exist for the scenarios to hold>.

## Applicable ADRs

- `architecture/adr/<NNN>-<title>.md`, `infrastructure/adr/<NNN>-<title>.md` - <service, tenancy model, secret pattern, runtime mode, state backend decided>.

## Constraints

- Provider/Terraform versions as the skills state; one IAM role per Lambda, least privilege; encryption
  on; tags required by the architecture spec; no secrets in `.tf` or `.tfvars`.
- Inputs from the code result: artifact path and name, handler, runtime, timeout, memory.

## Limits

- build_attempts: <effective value>   (source: profile | override | args)

## Acceptance criteria

- [ ] Review by `terraform-code-reviewer` (review record with `role: infra`).
- [ ] `terraform fmt -check`, `init -backend=false` and `terraform validate` pass (exact outputs in the result); `terraform test` passes only if wanted and fully mocked.
- [ ] Output names the Terraform directory and the variables the pipeline needs (the pipeline plans and applies in E7).
- [ ] Bootstrap task only (GitHub OIDC provider, `<env>-deploy` and `<env>-pr` roles, state bucket with lock): the result lists the exact commands the USER runs once, locally (`gate=bootstrap-apply`); the agents never apply.
- [ ] Result record valid (`result-<nn>-infra.md`, kind `report`, `role` optional (derived `infra`), from `assets/result-code.template.md`, outcome `success|partial|failed|needs-input`; engineer status DONE -> success, PARTIAL -> partial, NEEDS-INPUT -> needs-input, failed validate -> failed) with `## Spec impact`.
