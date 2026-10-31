# AWS Skills — Family Rules v2026

> Shipped with `aws-architecture-advisor` (copied 2026-10-29 from the factory provenance file `workspace/aws/_family_rules_v2026.md`, which now
> points here). This copy is the one aws-architect and the aws-architect rules read; edit it here, not in `workspace/`.

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


Rules R07–R13 (multi-account, IaC, multi-AZ, NAT, gateway endpoints, tagging, confidence tags):
[family-rules-v2026-r07-r13.md](family-rules-v2026-r07-r13.md).
