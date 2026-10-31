# AWS Skills — Family Rules v2026 (R07–R13)

Second half of [family-rules-v2026.md](family-rules-v2026.md) (split to keep each file under 160 lines;
same header, provenance and conventions apply).

## R07 — Multi-Account Workload Isolation via Organizations

**Policy**: Separate each workload × environment into its own AWS account under the appropriate
OU. Management account holds no workloads. Use Control Tower Account Factory or AFT for
provisioning.

**Test**: `aws organizations list-accounts` — management account contains only governance tooling;
workload accounts use dedicated OU paths.

**Source**: FF-09, SEC-AD-1, `architecting-aws-multi-account-organizations`

---

## R08 — Infrastructure as Code for All Production Changes

**Policy**: All production infrastructure defined in CloudFormation/CDK templates committed to Git
and deployed via CI/CD pipelines. No console-only production changes. Treat manual changes as
incidents.

**Test**: CloudFormation stack drift detection on all production stacks; CI/CD audit log verifies
all changes deployed via pipeline.

**Source**: FF-10, `applying-waf-operational-excellence-pillar`

---

## R09 — Multi-AZ Deployment for All Production Compute

**Policy**: Span stateless compute across ≥2 AZs behind an ELB. Enable Multi-AZ explicitly on
RDS and ElastiCache. S3 and DynamoDB are Multi-AZ by default and require no action.

**Test**: `aws autoscaling describe-auto-scaling-groups` → `AvailabilityZones` count ≥2;
`aws rds describe-db-instances` → `MultiAZ = true`.

**Source**: FF-11, `applying-aws-reliability-pillar`, `designing-aws-vpc-networks`

---

## R10 — One NAT Gateway Per Availability Zone

**Policy**: Provision one NAT Gateway per AZ in that AZ's public subnet. Route each AZ's private
subnets exclusively to their own AZ's NAT GW. Never share a single NAT Gateway across AZs.

**Test**: Count NAT Gateways per region; count must equal number of AZs in use for private
workloads. Each private route table's default route targets a NAT GW in the same AZ.

**Source**: FF-12, `designing-aws-vpc-networks`

---

## R11 — Free S3 and DynamoDB Gateway VPC Endpoints on All Private Route Tables

**Policy**: Create S3 and DynamoDB gateway endpoints (free) in every VPC with private subnets.
Update all private subnet route tables to route S3 and DynamoDB prefix lists to the gateway
endpoint, not the NAT Gateway.

**Test**: `aws ec2 describe-route-tables` → private route tables have `pl-*` prefix list routes
pointing to `vpce-*` (gateway endpoint), not `nat-*`.

**Source**: FF-13, `designing-aws-vpc-networks`, `applying-aws-well-architected`

---

## R12 — Mandatory Resource Tagging for Cost Allocation and Governance

**Policy**: Apply at minimum: `Environment`, `Owner`, `CostCenter`, `Workload`, and `ManagedBy`
tags to all billable resources. Enforce via SCPs/tag policies at the OU level. Use AWS Cost
Allocation Tags activated in the management account.

**Test**: `aws resourcegroupstaggingapi get-resources` with `TagFilters` for required tags;
flag resources missing any mandatory tag.

**Source**: `managing-aws-costs`, `optimizing-aws-costs`, `applying-waf-cost-optimization`
(no single master URL — derived from recurring always-do patterns across cost-related skills)

---

## R13 — Confidence-Tagging Notation (Cross-Skill Convention)

**Policy**: When the agent cites a fact from a skill, preserve the skill's confidence tag:
- `(unverified)` — no official URL in the skill; the fact must not be stated as certain
- `(medium confidence)` — source older than 12 months, or inferred from absence of evidence
- No tag — high confidence fact with a dated official source URL in the skill

The agent must surface all `(unverified)` and `(medium confidence)` items it relied on in the
response's **Questions / Limitations** section.

**Source**: FF-20, factory internal convention (cross-skill)
