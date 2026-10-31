---
name: provision-aws-terraform
description: "Routes a closed AWS Terraform requirement (hashicorp/aws 6.x) to the aws-terraform-engineer agent. Use when a fully specified AWS resource set (e.g. S3 + KMS, Lambda + SQS) must be written or reviewed as HCL and verified offline."
argument-hint: "<requirement summary> <terraform-dir> (e.g. 'private S3 bucket with KMS and access logging, with mocked test ./infra')"
context: fork
agent: aws-terraform-engineer
disable-model-invocation: true
---

# Provision AWS Terraform

## Function

Routes a closed AWS Terraform requirement to the `aws-terraform-engineer` agent. The agent loads
only the matching `provisioning-aws-<service>-v6` knowledge skills, writes or reviews HCL, and runs
offline checks. It states no AWS facts of its own.

## How to phrase a closed requirement

The agent is non-interactive. Supply all of the following or it returns NEEDS-INPUT questions:

1. **Services and resources** wanted (list below).
2. **Target directory** and whether it is a root module or a reusable module.
3. **Region(s) and account scope** (single region, multi-region, organization-wide).
4. **Decisions** the skills treat as Ask First for those services (e.g. NAT zonal vs regional).
5. **Naming/tagging inputs** (names or prefixes, tag keys and values).
6. **State backend**: S3 bucket, key, region and lock method, or "no backend". The agent never
   invents bucket or key names.
7. Whether a `terraform test` (fully mocked provider) is wanted.

## Services covered

Naming rule: `provisioning-aws-<service>-v6`. The 26 services: acm, api-gateway, cloudfront,
cloudtrail, cloudwatch, cognito, cost-management, dynamodb, eventbridge, iam, kms, lambda,
organizations, parameter-store, route53, s3, sam, secrets-manager, ses, shield, sns, sqs,
step-functions, vpc, waf, xray. The service-to-skill mapping is maintained in the agent
(`aws-terraform-engineer`), not here.

## What the agent will and will not do

**Will:** write or review HCL following each skill's Always Do / Never Do rows; run
`terraform fmt -check -recursive`, `init -backend=false -input=false` and `validate`; run
`terraform test` only if no `*.tftest.hcl` has `command = apply` or an unmocked provider, with AWS
credentials unset and every provider mocked; report exact outputs; surface every `(unverified)` /
`(medium confidence)` skill item instead of using it as a rule.

**Will not:** run `terraform apply`, `destroy`, `import`, `console`, `refresh`, `taint`,
`force-unlock`, `workspace`, state subcommands, `-lock=false`, or any `aws` CLI call; plan against
real credentials; write outside the target project; write secrets; assume missing requirements
(it returns questions); cover services outside the list (EKS, RDS, ECS, ALB, Transit Gateway,
other clouds) or provider 5.x / 7.x. Commands that skills show (`plan -out=tfplan`, `import`,
`apply`, CI steps) are descriptions for humans/CI: the agent reports "skill suggests X; not run".

## Usage examples

```
/provision-aws-terraform "private S3 bucket (name acme-logs-eu), tags team=platform, KMS CMK with separate key policy resource and default rotation, backend s3 bucket acme-tfstate key logs/terraform.tfstate eu-west-1 use_lockfile, mocked terraform test" ./infra/storage
/provision-aws-terraform "SQS queue with dead-letter queue and SNS subscription, reusable module, no backend" ./modules/messaging
/provision-aws-terraform "review the CloudFront + ACM + Route 53 alias stack for guardrail violations" ./infra/edge
```

## Evaluation Scenarios

See [./blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).
