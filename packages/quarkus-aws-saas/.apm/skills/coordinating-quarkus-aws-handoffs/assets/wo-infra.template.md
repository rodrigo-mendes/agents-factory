---
kind: work-order
id: wo-<nn>-infra
from: building-quarkus-aws-saas
to: aws-terraform-engineer
change: <change-id>
task: <task-id>
refs: []
requirements: [R1]
status: pending
createdAt: <ISO 8601 UTC>
---

## Scope

Infrastructure for task <task-id>: <resources, e.g. Lambda + alias, HTTP API route, DynamoDB table,
IAM role>. Terraform directory: `<path>`. Offline only: `terraform fmt -check`, `init -backend=false`,
`validate` and, if wanted below, a fully mocked `terraform test`. The engineer never runs `terraform plan`,
`apply`, `destroy` or `import`; the plan is the deployer's (E7).

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

- `openspec/specs/architecture/adr/<NNN>-<title>.md` - <service, tenancy model, secret pattern, runtime mode decided>.

## Constraints

- Provider/Terraform versions as the skills state; one IAM role per Lambda, least privilege; encryption
  on; tags required by the architecture spec; no secrets in `.tf` or `.tfvars`.
- Inputs from the code result: artifact path and name, handler, runtime, timeout, memory.

## Limits

- build_attempts: <effective value>   (source: profile | override | args)

## Acceptance criteria

- [ ] `terraform fmt -check`, `init -backend=false` and `terraform validate` pass (exact outputs in the result); `terraform test` passes only if wanted and fully mocked.
- [ ] Output names the Terraform directory and the variables the deployer needs (the deployer plans in E7).
- [ ] Result record valid (`result-<nn>-infra.md`, kind `report`, from `assets/result-code.template.md`, outcome `success|partial|failed|needs-input`; engineer status DONE -> success, PARTIAL -> partial, NEEDS-INPUT -> needs-input, failed validate -> failed) with `## Spec impact`.
