# Always Do Patterns — applying-aws-well-architected

Source: AWS Well-Architected Framework, November 6, 2024 edition (research date 2026-08-27).
Edition blog: https://aws.amazon.com/blogs/architecture/announcing-updates-to-the-aws-well-architected-framework-guidance-3/ (2024-11-06)
Sources without a publish date below were accessed 2026-08-27.

---

## AD-1 — Multi-Account Workload Separation

**Pillar alignment**: Security (SEC01-BP01); also anchors Reliability and Operational Excellence
**Why**: Blast radius containment — a compromised or misconfigured account cannot affect other workloads. SCPs/RCPs at OU level enforce consistent guardrails without per-account configuration.
**AWS services**: AWS Organizations, Control Tower, SCPs, RCPs (launched 2024-11-13), IAM Identity Center
**Decision**: One AWS account per workload × environment under named OUs. Security OU holds Log Archive + Audit accounts. Management account holds no workloads.

**Verification**:
```bash
aws organizations list-accounts --query 'Accounts[*].[Name,Status]'
# Config rule: account-part-of-organizations on all member accounts
```

**Source**: SEC01-BP01 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html

---

## AD-2 — Federated Human Access via IAM Identity Center

**Pillar alignment**: Security (design principle 1 — strong identity foundation)
**Why**: Temporary STS credentials expire automatically; federation via an existing IdP removes per-user IAM users with access keys.
**AWS services**: IAM Identity Center, AWS STS, corporate IdP (SAML 2.0 / OIDC)
**Decision**: All human access via Identity Center SSO with permission sets. Zero IAM users with long-term access keys for humans.

**Verification**:
```bash
aws iam generate-credential-report
aws iam get-credential-report --output text --query Content | base64 -d \
  | awk -F',' 'NR>1 && ($9=="true" || $12=="true") {print $1,$9,$12}'
# Expected: no output for human users. Config rule: iam-user-no-policies-check
```

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

## AD-3 — IAM Roles for All Workload Identities

**Pillar alignment**: Security (design principle 1)
**Why**: Embedded access keys in code/config are a leading cause of credential leaks; roles issue temporary credentials automatically.
**AWS services**: EC2 instance profiles, Lambda execution roles, ECS task roles, EKS Pod Identity, IAM Roles Anywhere
**Decision**: Never embed access keys in application code, environment variables, or AMIs. Assign IAM roles at the compute resource level.

**Verification**: `aws iam list-access-keys` for all users; secret scanning in CI/CD (e.g., Amazon CodeGuru Security).

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html + Security Pillar

---

## AD-4 — Phishing-Resistant MFA for IAM and Root Users

**Pillar alignment**: Security (design principle 1)
**Why**: SMS and TOTP MFA are vulnerable to SIM swap and phishing; FIDO2 keys require physical possession.
**Decision**: Register a FIDO2 hardware security key on root. Delete root access keys. SCP denying sensitive API calls without MFA.

**Verification**: IAM console MFA status; Config rule `mfa-enabled-for-iam-console-access`.

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

## AD-5 — Encryption at Rest with AWS KMS

**Pillar alignment**: Security (SEC08-BP01/02)
**Why**: Unencrypted data at rest is exposed to anyone with storage-level access (snapshot copies, cross-account access, insiders). KMS usage is audited via CloudTrail.
**Decision**: KMS encryption for all EBS volumes, S3 buckets, RDS instances, DynamoDB tables, SQS queues. Audit key use via CloudTrail + CloudWatch Logs Insights.

**Verification**: Config rules `encrypted-volumes`, `s3-bucket-server-side-encryption-enabled`, `rds-storage-encrypted`.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html

---

## AD-6 — Continuous Detection Stack

**Pillar alignment**: Security (SEC04-BP01–BP04)
**Why**: Continuous automated detection reduces mean time to detect (MTTD) from weeks to minutes.
**Decision**: One CloudTrail org trail writing to S3 in the Log Archive account. GuardDuty org-wide with a delegated administrator. Findings aggregated in Security Hub. Config rules in all accounts. Enable from day 1.

**Verification**:
```bash
aws guardduty list-detectors
# Expected: detector present with OrganizationConfiguration enabled
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html

---

## AD-7 — Multi-AZ Deployment for All Production Compute

**Pillar alignment**: Reliability (REL10-BP01 — fault isolation)
**Why**: A single AZ can fail independently; multi-AZ keeps the workload available.
**Decision**: Span stateless compute across ≥2 AZs behind an ELB. Enable Multi-AZ explicitly on RDS and ElastiCache (S3 and DynamoDB are Multi-AZ by default).

**Verification**:
```bash
aws autoscaling describe-auto-scaling-groups \
  --query 'AutoScalingGroups[*].[AutoScalingGroupName,AvailabilityZones]'
aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,MultiAZ]'
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/use-fault-isolation-to-protect-your-workload.html

---

## AD-8 — Centralized Backup for All Critical Data

**Pillar alignment**: Reliability (REL09-BP01)
**Why**: Replication does not protect against logical corruption, ransomware, or accidental deletion.
**Decision**: AWS Backup plans covering all critical resources in all accounts. S3 versioning; DynamoDB and RDS PITR. Test restores at minimum quarterly.

**Verification**: AWS Backup compliance report; test-restore runbook execution record.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/failure-management.html

---

## AD-9 — Infrastructure as Code for All Resources

**Pillar alignment**: Operational Excellence (design principle 3 — safely automate where possible)
**Why**: Console changes are not reproducible, auditable, or deterministically reversible.
**Decision**: All production infrastructure in CloudFormation/CDK, in version control, deployed via CI/CD. Systems Manager Automation for operational runbooks.

**Verification**: CloudTrail — flag `CreateBucket`, `RunInstances`, etc. not triggered by CloudFormation. Config rule `cloudformation-stack-drift-detection-check`.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html

---

## AD-10 — Elastic Scaling to Match Demand

**Pillar alignment**: Reliability (REL-AD-4), Performance Efficiency (PE-AD-3), Cost Optimization (CO-AD-1), Sustainability (SUS-AD-B)
**Why**: Fixed capacity either over-provisions (cost/sustainability waste) or under-provisions (reliability failure).
**Decision**: Scaling policies on business KPI metrics, not just CPU. Minimum capacity for baseline availability; maximum capacity to cap cost.

**Verification**: CloudWatch Auto Scaling activity log; test scale-out/scale-in in lower environments.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/change-management.html + SUS02-BP01
