---
name: applying-aws-well-architected
description: "Applies AWS Well-Architected Framework (WAF) six-pillar patterns to production AWS workloads. Use when designing, reviewing, or auditing multi-tenant SaaS, web APIs, or data pipelines against AWS WAF standards (Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability)."
---

## Function

Specialist in AWS Well-Architected Framework (WAF) six-pillar architecture for production AWS workloads: multi-tenant SaaS, web APIs, and data pipelines.

## Version Context

**Framework**: AWS Well-Architected Framework
**Publication date**: November 6, 2024 (current stable edition as of 2026-07-31)
**Primary source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html
**Pillars**: 6 — Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability

**Source-age notice**: The whitepaper carries a Nov 6, 2024 publication date (~20 months at skill authoring time). Retained as the current stable edition — `.../latest/...` URLs resolve to this revision. Verify against [Document revisions](https://docs.aws.amazon.com/wellarchitected/latest/framework/document-revisions.html) before customer deliverables.

**Sustainability added December 2021** — any source citing only 5 pillars is outdated/misinformation.

⚠️ **CRITICAL — Agent Warning**:
Reject any 5-pillar AWS WAF guidance. Pre-Dec 2021 sources are misinformation.
Do not mix non-AWS WAF patterns (Azure CAF, GCP WAF) without explicit labeling.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 8 mandatory patterns with full detail (services, verification, trade-offs)
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 5 architectural crossroads with option matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 7 anti-patterns with ❌ wrong / ✅ correct examples
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 4 test cases (canonical, edge, misuse, multi-pillar)
- **[Verification Loop](#verification-loop)** — AWS CLI and Config checks
- **[Quick Reference](#quick-reference)** — 6-pillar summary and service map
- **[External Resources](#external-resources)** — Official documentation

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **AD-1 — Centralize identity, eliminate long-term static credentials** — Use IAM Identity Center + IAM roles (instance profiles, IRSA on EKS, task roles on ECS) + AWS STS. Never embed IAM user access keys. (Security pillar)
- **AD-2 — Encrypt data at rest and in transit by default** — AWS KMS for customer-managed keys; EBS encryption-by-default; S3 SSE-KMS; RDS/Aurora storage encryption; ACM-managed TLS ≥ 1.2 at ALB/CloudFront. (Security pillar)
- **AD-3 — Design for Multi-AZ high availability** — Deploy every tier across ≥ 2 AZs; RDS Multi-AZ or Aurora multi-AZ; EC2 Auto Scaling behind Elastic Load Balancing. (Reliability pillar)
- **AD-4 — Manage infrastructure and operations as code** — All infra in CloudFormation/CDK; changes via CodePipeline; no console ClickOps in production; Config for drift detection. (Operational Excellence + Security pillars)
- **AD-5 — Implement observability with actionable alarms** — Structured logs to CloudWatch Logs; business-KPI alarms (not just CPU); X-Ray tracing across tiers; CloudTrail in all Regions. (Operational Excellence pillar)
- **AD-6 — Store secrets in AWS Secrets Manager** — Applications fetch at runtime via IAM-scoped calls; enable automatic rotation for DB credentials; never commit secrets to Git or bake into images. (Security pillar)
- **AD-7 — Establish multi-account governance with guardrails** — AWS Organizations + SCPs; Control Tower; separate accounts per environment/workload; centralized immutable log-archive account. (Security + Operational Excellence pillars)
- **AD-8 — Set budgets, cost-allocation tags, and right-sizing reviews** — Mandatory tags via Organizations tag policies; AWS Budgets per account; Compute Optimizer reviews quarterly; Instance Scheduler for dev. (Cost Optimization + Sustainability pillars)

### ⚠️ Ask First

For complete decision matrices, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **AF-1 — Compute model** — Lambda vs. ECS Fargate vs. EKS vs. EC2 Auto Scaling. Confirm traffic pattern (spiky/sustained), ops maturity, runtime duration, and cost profile before selecting.
- **AF-2 — Primary datastore** — Aurora vs. RDS vs. DynamoDB vs. ElastiCache. Confirm access patterns (relational/key-value), scale requirements, and consistency needs before designing the data tier.
- **AF-3 — Multi-tenant SaaS isolation** — Pool vs. Silo vs. Bridge model. Confirm tenant count, compliance requirements (data residency, SOC 2), and budget before choosing isolation strategy.
- **AF-4 — Data pipeline model** — AWS Glue vs. Kinesis/MSK vs. EMR vs. Lambda+S3 events. Confirm latency SLA (batch/near-real-time/streaming) and data volume before selecting.
- **AF-5 — Purchasing model** — On-Demand vs. Compute Savings Plans/Reserved Instances vs. Spot. Confirm baseline vs. burst profile and workload fault-tolerance before committing.

### 🚫 Never Do

For anti-patterns with full code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

- **ND-1 — Long-lived IAM user access keys in application code** — Critical risk. Credential leakage = account-wide blast radius. Use IAM roles + STS temporary credentials instead.
- **ND-2 — Single-AZ production deployment** — High risk. One AZ event = full outage. Deploy Multi-AZ with ELB + RDS Multi-AZ or Aurora.
- **ND-3 — Public S3 bucket / overly permissive access** — Critical risk. Leading cause of cloud data breaches. Enable S3 Block Public Access; serve content via CloudFront with Origin Access Control.
- **ND-4 — Unencrypted data at rest or in transit** — High risk. Compliance failure (PCI DSS, HIPAA, GDPR). Enable EBS default encryption, ALB HTTPS with ACM, RDS StorageEncrypted=true.
- **ND-5 — Manual ClickOps changes in production** — Medium-High risk. Causes configuration drift and failed disaster recovery. All changes via CloudFormation/CDK + CodePipeline.
- **ND-6 — No cost guardrails (untagged, unbudgeted spend)** — Business risk. Runaway spend and no attribution. Enforce tag policies, AWS Budgets, and Compute Optimizer.
- **ND-7 — Disabling or not centralizing audit logging** — High risk. Destroys forensic capability. CloudTrail organization trail to immutable S3 archive account; SCP denies disabling it.

---

## Integration Patterns

For detailed integration examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **Security ↔ Operational Excellence** — IaC-managed SCPs + Config rules enforce security controls without manual intervention; CloudTrail feeds Security Hub and GuardDuty.
- **Reliability ↔ Cost Optimization** — Multi-AZ design pairs with Savings Plans for baseline capacity and Spot for burst/batch; Compute Optimizer right-sizes without sacrificing availability.
- **Performance Efficiency ↔ Sustainability** — Serverless (Lambda, Fargate) maximizes resource utilization and reduces idle waste; managed services (DynamoDB, S3) share infrastructure across tenants.

**Common review pitfalls**:
- **Problem**: Treating the 6 pillars as independent checklists → **Solution**: Cross-pillar design (e.g., encryption = Security + Reliability; IaC = OE + Security).
- **Problem**: Using only 5 pillars (omitting Sustainability) → **Solution**: Confirm all 6 are addressed; Sustainability = mandatory since Dec 2021.
- **Problem**: Selecting compute model before validating traffic pattern → **Solution**: Always resolve AF-1 first; compute choice cascades to datastore, cost, and IaC complexity.

---

## Verification Loop

Run after applying WAF patterns to validate architectural adherence. These are AWS CLI and Config checks — adapt ARNs and account IDs to the target environment.

### 1. Identity and Access

```bash
# Long-lived IAM user access keys (AD-1 / ND-1)
aws iam list-users --query 'Users[].UserName' --output text | xargs -I{} \
  aws iam list-access-keys --user-name {} --query 'AccessKeyMetadata[?Status==`Active`]'
# Expected: empty or near-zero active keys

# IAM Access Analyzer — unused access findings
aws accessanalyzer list-findings --analyzer-arn <analyzer-arn> \
  --query 'findings[?findingType==`UnusedAccess`]'
# Expected: 0 findings
```

### 2. Encryption (AD-2 / ND-4)

```bash
# EBS default encryption per region
aws ec2 get-ebs-encryption-by-default --query 'EbsEncryptionByDefault'
# Expected: true

# RDS encryption status
aws rds describe-db-instances \
  --query 'DBInstances[?StorageEncrypted==`false`].[DBInstanceIdentifier]'
# Expected: empty list
```

### 3. High Availability (AD-3 / ND-2)

```bash
# RDS Multi-AZ check
aws rds describe-db-instances \
  --query 'DBInstances[?MultiAZ==`false`].[DBInstanceIdentifier,Engine]'
# Expected: empty list for production instances

# Auto Scaling group AZ distribution
aws autoscaling describe-auto-scaling-groups \
  --query 'AutoScalingGroups[].{Name:AutoScalingGroupName,AZs:AvailabilityZones}'
# Expected: each group spans >= 2 AZs
```

### 4. Audit Logging (AD-5 / ND-7)

```bash
# CloudTrail status — all trails
aws cloudtrail describe-trails --query 'trailList[].{Name:Name,MultiRegion:IsMultiRegionTrail,LogValidation:LogFileValidationEnabled}'
# Expected: IsMultiRegionTrail=true, LogFileValidationEnabled=true

# CloudTrail logging enabled
aws cloudtrail get-trail-status --name <trail-name> --query 'IsLogging'
# Expected: true
```

**Troubleshooting**:
- RDS `MultiAZ=false` in prod → convert instance; plan for ~20 min failover window.
- EBS encryption not default → enable per Region: `aws ec2 enable-ebs-encryption-by-default`.
- CloudTrail missing → create org trail pointing to centralized S3 archive account with Object Lock.

---

## Quick Reference

**6 Pillars at a glance**:

| Pillar | Core mandate | Key AWS services |
|--------|-------------|-----------------|
| Operational Excellence | Automate, observe, learn | CloudFormation, CDK, CloudWatch, X-Ray, Systems Manager |
| Security | Least-privilege, defense-in-depth, traceability | IAM, KMS, Secrets Manager, GuardDuty, Security Hub, CloudTrail |
| Reliability | Multi-AZ, auto-recover, test failure | RDS Multi-AZ, Aurora, EC2 Auto Scaling, ELB |
| Performance Efficiency | Right service, right size, go global | Lambda, ECS/EKS, DynamoDB, CloudFront, Compute Optimizer |
| Cost Optimization | Consumption model, tag, right-size | Budgets, Cost Explorer, Savings Plans, Spot, Compute Optimizer |
| Sustainability | Maximize utilization, managed services | Fargate, Lambda, S3 Lifecycle, EC2 Auto Scaling, Instance Scheduler |

**Critical AWS Config rules to enable**:

| Config Rule | Pillar | Anti-pattern caught |
|-------------|--------|---------------------|
| `iam-user-no-policies-check` | Security | ND-1 |
| `access-keys-rotated` | Security | ND-1 |
| `encrypted-volumes` | Security | ND-4 |
| `rds-storage-encrypted` | Security | ND-4 |
| `s3-bucket-server-side-encryption-enabled` | Security | ND-3 / ND-4 |
| `s3-bucket-public-read-prohibited` | Security | ND-3 |
| `multi-region-cloudtrail-enabled` | Security | ND-7 |
| `rds-multi-az-support` | Reliability | ND-2 |

---

## Blueprints Directory Structure

```
.claude/skills/applying-aws-well-architected/
├── SKILL.md                              <- This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md             <- AD-1 to AD-8 with full detail
    ├── ask-first-decisions.md            <- AF-1 to AF-5 with option matrices
    ├── never-do-patterns.md              <- ND-1 to ND-7 with ❌ wrong / ✅ correct
    └── evaluation-scenarios.md           <- 4 test scenarios
```

---

## External Resources

### Official — AWS Well-Architected Framework (November 6, 2024 edition)

- [WAF Welcome / Introduction](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) — primary entry point
- [The Six Pillars](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html) — pillar definitions
- [Document Revisions](https://docs.aws.amazon.com/wellarchitected/latest/framework/document-revisions.html) — verify current edition before reuse
- [Operational Excellence Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html)
- [Security Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html)
- [Reliability Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-principles.html)
- [Performance Efficiency Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html)
- [Cost Optimization Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html)
- [Sustainability Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html)

### Supporting

- [AWS Well-Architected Program Homepage](https://aws.amazon.com/architecture/well-architected/) — WA Tool, lenses
- [AWS SaaS Lens](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html) — Pool/Silo/Bridge isolation detail (AF-3)
- [AWS Prescriptive Guidance](https://aws.amazon.com/prescriptive-guidance/) — patterns and strategies
- [Security Pillar Whitepaper](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
- [Reliability Pillar Whitepaper](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html)
- [Cost Optimization Pillar Whitepaper](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)
