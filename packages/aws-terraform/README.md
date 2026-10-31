# aws-terraform

26 knowledge skills for provisioning AWS infrastructure with Terraform (**hashicorp/aws 6.x**,
**Terraform ~> 1.16**), plus 3 scoped instruction files. The executor agent
`aws-terraform-engineer` and its routing command `/provision-aws-terraform` live in
`packages/terraform` (next to `terraform-instructions-compiler`); this package supplies the skills it loads.
Dependency note: `packages/terraform` depends on this package, so installing `terraform` also
installs the 26 AWS skills and the 3 instruction files.

## Target versions

| Tool | Constraint | Reference |
|---|---|---|
| Terraform CLI | `~> 1.16` (>= 1.16, < 2.0) | newest 1.16.x is 1.16.7 (2026-10-22). The constraint also admits 1.17+, which the skills have not been verified against; 1.17.0 has been stable since 2026-10-21 |
| hashicorp/aws | `~> 6.69` (root module); minimum only in reusable modules | latest 6.70.0 (2026-10-21), allowed by the constraint |

Never pin provider 6.57.0 (withdrawn). Sources: https://releases.hashicorp.com/terraform/ ,
https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md ,
https://releases.hashicorp.com/terraform-provider-aws/

## Skills (26)

| Skill | Scope |
|---|---|
| `provisioning-aws-acm-v6` | ACM certificates: DNS validation, imports, private CA, CloudFront us-east-1 |
| `provisioning-aws-api-gateway-v6` | REST (`aws_api_gateway_*`) and HTTP/WebSocket (`aws_apigatewayv2_*`) APIs |
| `provisioning-aws-cloudfront-v6` | Distributions, OAC, cache and response headers policies, functions, Route 53 alias, logging v2 |
| `provisioning-aws-cloudtrail-v6` | Trails, log bucket and KMS policies, event data stores, delegated admin |
| `provisioning-aws-cloudwatch-v6` | Log groups, metric and subscription filters, alarms, dashboards |
| `provisioning-aws-cognito-v6` | User pools, app clients, domains, identity pools |
| `provisioning-aws-cost-management-v6` | Budgets and actions, Cost Anomaly Detection, cost categories, CUR, Data Exports, Savings Plans |
| `provisioning-aws-dynamodb-v6` | Tables, indexes, PITR, encryption, autoscaling, global tables |
| `provisioning-aws-eventbridge-v6` | Buses, rules, targets, archives, connections, API destinations, Scheduler, pipes |
| `provisioning-aws-iam-v6` | Roles, policies, OIDC providers, users, groups, password policy |
| `provisioning-aws-kms-v6` | Customer managed keys (symmetric/asymmetric), aliases, key policies, grants, multi-Region, external keys |
| `provisioning-aws-lambda-v6` | Functions, aliases, permissions, URLs, event sources, layers, concurrency, code signing |
| `provisioning-aws-organizations-v6` | Organization, OUs, accounts, SCPs, attachments, delegated admins |
| `provisioning-aws-parameter-store-v6` | `aws_ssm_parameter`, SecureString write-only values, reads, hierarchies, tiers |
| `provisioning-aws-route53-v6` | Zones, records, routing policies, health checks, query logging, DNSSEC, Resolver |
| `provisioning-aws-s3-v6` | Buckets: ownership, BPA, SSE, TLS policy, versioning, lifecycle, access logging, objects |
| `provisioning-aws-sam-v6` | SAM with Terraform: SAM CLI hook, SAR and CloudFormation stacks with the SAM transform |
| `provisioning-aws-secrets-manager-v6` | Secrets, versions, write-only values, rotation, policies, replicas |
| `provisioning-aws-ses-v6` | SESv2 identities, DKIM, MAIL FROM, configuration sets, event destinations, pools |
| `provisioning-aws-shield-v6` | Shield Advanced: subscription, protections, groups, health checks, SRT access |
| `provisioning-aws-sns-v6` | Topics, FIFO, KMS, topic policies, subscriptions, DLQs |
| `provisioning-aws-sqs-v6` | Queues, FIFO, encryption, queue policies, dead-letter queues and redrive |
| `provisioning-aws-step-functions-v6` | State machines, aliases, activities, logging, KMS, IAM role |
| `provisioning-aws-vpc-v6` | VPC, subnets, IGW, NAT gateways, route tables, security groups, NACLs, endpoints, flow logs |
| `provisioning-aws-waf-v6` | WAFv2: web ACLs, rule groups, IP sets, associations, logging |
| `provisioning-aws-xray-v6` | X-Ray sampling rules, groups, encryption config |

Note: `aws-terraform-engineer` does not write CloudWatch alarms, dashboards or retention policy, nor X-Ray groups or sampling; those belong to `aws-observability` Mode B (the engineer may only create the log group a Lambda needs, with the retention given in the work-order).

## Instructions (3)

Under `.apm/instructions/`, with `applyTo` on Terraform files:
`aws-terraform-code-standards` (constraints, region semantics, global services, identity import,
tests), `aws-terraform-project-config` (versions, S3 backend locking, lock file, 5.x upgrade path)
and `aws-terraform-skills-management` (how to pick and refresh skills).

## How the agent uses them

`/provision-aws-terraform "<closed requirement>" <terraform-dir>` forks to the non-interactive
`aws-terraform-engineer` agent (`packages/terraform`). It loads only the skills matching the
requirement, writes or reviews HCL, and runs offline checks only (`terraform fmt -check -recursive`,
`init -backend=false`, `validate`, and `terraform test` only when every provider is mocked, no run
uses `command = apply`, and AWS credentials are unset). It never runs apply, destroy, import,
state mutations or `aws` CLI calls. It returns questions for incomplete requirements (including
the state backend and naming/tagging inputs), Ask First decisions and services outside the 26
skills, and surfaces `(unverified)` / `(medium confidence)` skill items.

## Recommended permission rules

The agent's Bash access is limited by its prompt only. Recommendation: add rules like these to
your own `.claude/settings.json` or `settings.local.json`. This package does not install or
enforce them.

```json
{
  "permissions": {
    "allow": [
      "Bash(terraform fmt:*)",
      "Bash(terraform init -backend=false:*)",
      "Bash(terraform validate:*)",
      "Bash(terraform test:*)",
      "Bash(TF_IN_AUTOMATION=1 terraform:*)",
      "Bash(env -u AWS_ACCESS_KEY_ID:*)"
    ],
    "deny": [
      "Bash(terraform apply:*)",
      "Bash(terraform destroy:*)",
      "Bash(terraform import:*)",
      "Bash(terraform state:*)",
      "Bash(terraform console:*)",
      "Bash(terraform refresh:*)",
      "Bash(terraform taint:*)",
      "Bash(terraform force-unlock:*)",
      "Bash(terraform workspace:*)",
      "Bash(aws:*)"
    ]
  }
}
```

Adjust the syntax to your Claude Code version (verify against the permissions documentation).

## Scope limits

- Each skill covers one AWS service or logical group; services without a skill (EKS, RDS, ECS, ALB, Transit Gateway, ...) are not covered.
- Skills lock to the **6.x** provider line; a v7 release needs new `-v7` skills.
- `provisioning-aws-sam-v6` covers the SAM CLI with Terraform and CloudFormation-deployed SAM; SAM is not a provider resource.
- Re-read the version sources before new work.
