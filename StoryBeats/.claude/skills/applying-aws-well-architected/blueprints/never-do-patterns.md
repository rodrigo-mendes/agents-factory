# Never-Do Patterns — AWS Well-Architected Framework

> Source: AWS WAF research file `research_aws_waf_2025.md`, accessed 2026-07-31.
> Framework edition: November 6, 2024 (current stable).

Each anti-pattern includes risk level, blast radius, detection method, impact, and
side-by-side ❌ Wrong / ✅ Correct examples using exact AWS service names.

---

## ND-1 — Long-lived IAM user access keys in application code

- **Risk level**: Critical
- **Blast radius**: Account-wide (leaked key = full API access within its policy)
- **Pillar**: Security — violates "Implement a strong identity foundation"
- **Detection**: IAM Access Analyzer, AWS Config `access-keys-rotated`, secret scanners (CodeBuild/GitHub), Amazon GuardDuty `UnauthorizedAccess` findings
- **Impact**: Credential leakage → data exfiltration, resource hijacking (e.g., crypto-mining), no automatic rotation mechanism

```text
❌ Wrong
  App config: AWS_ACCESS_KEY_ID=AKIA...  AWS_SECRET_ACCESS_KEY=...
  (IAM user access key committed to Git / baked into AMI or container image)

✅ Correct
  Attach an IAM role to the compute resource:
    - EC2: instance profile
    - ECS: task role
    - EKS: IRSA (IAM Roles for Service Accounts)
    - Lambda: execution role
  The AWS SDK obtains temporary credentials via AWS STS automatically.
  Database credentials retrieved at runtime from AWS Secrets Manager.
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html — accessed 2026-07-31

---

## ND-2 — Single-AZ production deployment / single point of failure

- **Risk level**: High
- **Blast radius**: Entire workload (one AZ event = full outage)
- **Pillar**: Reliability — violates "Scale horizontally to increase aggregate workload availability"
- **Detection**: AWS Trusted Advisor fault-tolerance checks; architecture review; `aws rds describe-db-instances --query 'DBInstances[?MultiAZ==false]'`
- **Impact**: AZ impairment causes total downtime; unplanned outage during an AZ event

```text
❌ Wrong
  Amazon RDS single-AZ + one Amazon EC2 instance in one subnet/AZ.
  No load balancer. One failure point per tier.

✅ Correct
  Amazon RDS Multi-AZ (or Amazon Aurora across 3 AZs)
  + Amazon EC2 Auto Scaling group spanning >= 2 AZs
  + Elastic Load Balancing (ALB) distributing traffic.
  Run a game-day failover test to confirm RTO before go-live.
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-principles.html — accessed 2026-07-31

---

## ND-3 — Public S3 bucket / overly permissive access

- **Risk level**: Critical
- **Blast radius**: All objects in the bucket (potential mass data breach)
- **Pillar**: Security — violates "Protect data in transit and at rest" + "Keep people away from data"
- **Detection**: Amazon S3 Block Public Access status console; AWS Config `s3-bucket-public-read-prohibited`; IAM Access Analyzer external-access findings; Amazon Macie for sensitive data discovery
- **Impact**: Public exposure of PII/customer data; a leading cause of cloud data breaches; regulatory penalties (GDPR, PCI DSS)

```text
❌ Wrong
  S3 bucket with Block Public Access disabled and a bucket policy
  granting Principal "*" s3:GetObject.

✅ Correct
  Enable S3 Block Public Access at both account level and bucket level.
  Serve public static content via Amazon CloudFront with an
  Origin Access Control (OAC) policy — CloudFront fetches from S3 privately.
  Scope bucket policies to specific IAM principals; encrypt with SSE-KMS.
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html — accessed 2026-07-31

---

## ND-4 — Unencrypted data at rest or in transit

- **Risk level**: High
- **Blast radius**: All data in the affected store or in-flight
- **Pillar**: Security — violates "Protect data in transit and at rest"
- **Detection**: AWS Config `encrypted-volumes`, `rds-storage-encrypted`, `s3-bucket-server-side-encryption-enabled`; ELB listener TLS policy audit; `aws ec2 get-ebs-encryption-by-default`
- **Impact**: Data readable if storage/media is compromised; compliance failures (PCI DSS, HIPAA, GDPR); audit finding that blocks certification

```text
❌ Wrong
  Amazon EBS volume unencrypted.
  ALB listener on HTTP :80 only (no HTTPS, no redirect).
  Amazon RDS instance with StorageEncrypted=false.

✅ Correct
  Enable EBS encryption-by-default at the AWS account level with AWS KMS.
  ALB: HTTPS listener with an AWS Certificate Manager (ACM) certificate;
    HTTP :80 listener redirects to HTTPS :443.
  RDS: StorageEncrypted=true with a KMS customer-managed key.
  Enforce TLS >= 1.2 via ELBSecurityPolicy-TLS13-* security policy.
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html — accessed 2026-07-31

---

## ND-5 — Manual "ClickOps" changes in production

- **Risk level**: Medium-High
- **Blast radius**: Any resource changed out-of-band
- **Pillar**: Operational Excellence — violates "Safely automate where possible"; Security — violates "Automate security best practices"
- **Detection**: AWS CloudFormation drift detection; AWS Config change timeline; AWS CloudTrail events with `userAgent` containing `console.aws.amazon.com`
- **Impact**: Configuration drift, non-reproducible environments, failed disaster recovery, undocumented changes that break compliance audits

```text
❌ Wrong
  Operator edits a security group rule in the AWS Console.
  DBA manually scales RDS instance class in production.
  Changes not recorded in any IaC repository.

✅ Correct
  Change the AWS CloudFormation template or AWS CDK construct.
  Open a PR → peer review → merge → AWS CodePipeline deploys.
  Break-glass emergency role is tightly scoped, requires MFA,
  and all actions are logged in AWS CloudTrail and reconciled
  back into IaC within the next sprint.
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html — accessed 2026-07-31

---

## ND-6 — No cost guardrails (untagged, unbudgeted spend)

- **Risk level**: Medium (business)
- **Blast radius**: Account/organization billing; no cost attribution
- **Pillar**: Cost Optimization — violates "Analyze and attribute expenditure"; Sustainability — violates "Maximize utilization"
- **Detection**: AWS Cost Explorer anomaly detection alerts absent; AWS Budgets alerts absent; tag-coverage report showing < 95% tagged spend
- **Impact**: Runaway spend, no cost attribution by team/workload, undetected idle or over-provisioned resources; organizational chargebacks impossible

```text
❌ Wrong
  No AWS Budgets configured for any account.
  Resources without cost-allocation tags (owner, environment, workload).
  Oversized Amazon EC2 instances in dev running 24/7 with no scheduler.

✅ Correct
  Mandatory cost-allocation tags enforced via AWS Organizations tag policies.
  AWS Budgets alert per account (e.g., 80% and 100% of monthly forecast).
  AWS Instance Scheduler stops dev/test instances outside working hours.
  Quarterly AWS Compute Optimizer review → right-size over-provisioned resources.
  AWS Cost Explorer anomaly detection enabled and routed to SNS → Slack/Teams.
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html — accessed 2026-07-31

---

## ND-7 — Disabling or not centralizing audit logging

- **Risk level**: High
- **Blast radius**: Whole account/organization (loss of forensic capability)
- **Pillar**: Security — violates "Maintain traceability"
- **Detection**: AWS CloudTrail status check; AWS Security Hub foundational security best practices checks; absence of SCP preventing `cloudtrail:StopLogging`
- **Impact**: No traceability of API actions; breach investigations are impossible; violates security compliance requirements (SOC 2, PCI DSS, HIPAA); audit finding = critical

```text
❌ Wrong
  AWS CloudTrail disabled or configured per-account only.
  Logs stored in the same account they audit (can be deleted by a compromised principal).
  No log-file validation enabled.
  No SCP preventing a member account from disabling CloudTrail.

✅ Correct
  AWS Organizations organization trail → centralized, immutable Amazon S3
  log-archive account with S3 Object Lock (WORM retention).
  Log-file validation enabled on all trails.
  Monitored by Amazon GuardDuty (detects anomalous API behavior) and
  AWS Security Hub (aggregates findings).
  SCP at the Organization root denies cloudtrail:StopLogging and
  cloudtrail:DeleteTrail for all member accounts.
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html — accessed 2026-07-31
