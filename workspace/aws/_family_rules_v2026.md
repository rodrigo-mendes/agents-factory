# AWS Skills — Family Rules v2026

> Superseded as the runtime source on 2026-10-29: the shipped copy is `packages/aws-architect/.apm/skills/aws-architecture-advisor/references/family-rules-v2026.md`.
> Keep this file as research provenance only.

Numbered, testable policy decisions applied across the 40 aws-skills. Each rule maps to one or
more `always-do`/`never-do` patterns and the shared Version Context facts in `_family_facts_v2026.md`.

These rules are compiled into instruction files under
`packages/aws-architect/.apm/instructions/`.

---

## R01 — Least-Privilege IAM: One Role Per Compute Resource

**Policy**: Assign one dedicated IAM execution role per Lambda function, ECS task, EKS Pod, or
EC2 instance. Scope permissions to exact actions on specific ARNs. Never share a role across
multiple workload units.

**Test**: `aws iam list-roles` — verify no role name is referenced by more than one Lambda
function/ECS task definition serving different business purposes.

**Source**: FF-04, SEC-AD-3, `securing-aws-iam-serverless`, `architecting-aws-security-pillar`

---

## R02 — No Long-Term Static Access Keys for Human Identities

**Policy**: All human AWS console and API access routes through IAM Identity Center → STS
temporary credentials. Zero IAM users with `AccessKey` active for human operators. Machine
workloads use IAM roles exclusively.

**Test**: `aws iam get-credential-report` → expect no human account with `access_key_1_active=true`.

**Source**: FF-05, SEC-AD-2, `applying-aws-well-architected`, `architecting-aws-security-pillar`

---

## R03 — Phishing-Resistant MFA on All Root and Human Accounts

**Policy**: Register FIDO2 hardware security key on every account root; delete root access keys.
Enforce hardware MFA (not TOTP/SMS) for IAM Identity Center workforce users. Apply SCP to deny
sensitive APIs without MFA.

**Test**: `aws iam get-account-summary` → `AccountMFAEnabled = 1`; root credential report shows
no active access keys.

**Source**: FF-06, SEC-AD-4, `securing-aws-iam-serverless`

---

## R04 — Encryption at Rest for All Sensitive Data Stores

**Policy**: Enable KMS CMKs for regulated/confidential stores (S3, EBS, RDS, DynamoDB, SQS).
Enable S3 default encryption and EBS encryption-by-default account-wide. Run Macie to detect
unclassified sensitive data.

**Test**: `aws s3api get-bucket-encryption` on all buckets; `aws rds describe-db-instances` →
`StorageEncrypted = true`; `aws ec2 get-ebs-encryption-by-default`.

**Source**: FF-07, SEC-AD-5, `applying-aws-well-architected`, `architecting-aws-security-pillar`

---

## R05 — Encryption in Transit (TLS) for All Data Flows

**Policy**: Enforce TLS on all ALB/CloudFront listeners. Use HTTPS-only S3 bucket policies.
Deny unencrypted API Gateway traffic. Enforce TLS 1.2+ on RDS parameter groups. AWS-managed
KMS handles in-transit encryption for service-to-service calls within the AWS backbone.

**Test**: `aws elbv2 describe-listeners` → no HTTP listener on port 80 without redirect; S3
bucket policies must include `"aws:SecureTransport": "false"` Deny condition.

**Source**: `architecting-aws-security-pillar` (SEC07), `securing-vpc-network-access`

---

## R06 — Continuous Detection Stack Before Any Workload Reaches Production

**Policy**: Enable in this order before deploying workloads: (1) CloudTrail org trail → Log
Archive S3 with Object Lock, (2) GuardDuty org-wide delegated admin in Audit account, (3)
Security Hub with AWS Foundational Security Best Practices, (4) AWS Config aggregator across all
accounts.

**Test**: `aws cloudtrail get-trail-status` → `IsLogging = true`; `aws guardduty list-detectors`
→ detector with `OrganizationConfiguration` enabled.

**Source**: FF-08, SEC-AD-6, `architecting-cloudtrail-audit-logging`, `auditing-aws-cloudtrail`

---

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
