---
name: auditing-aws-cloudtrail
description: "Designs and enforces AWS CloudTrail audit logging for governance and compliance (2025 edition). Covers four event types (management, data, network activity, Insights), organization trails with delegated administration, CloudTrail Lake for long-retention SQL analytics, and Security Hub CSPM controls CloudTrail.1–.10. Use when architecting centralized audit logging for multi-account AWS Organizations environments, configuring log immutability and integrity validation, enabling real-time alerting on security-critical API activity, or mapping CloudTrail patterns to CIS/NIST/PCI compliance requirements."
---

## Function

Specialist in **AWS CloudTrail audit logging, governance, and compliance architecture** for the **2025 edition** — four event types, organization trails with delegated administration, CloudTrail Lake SQL analytics, and Security Hub CSPM controls CloudTrail.1–.10 mapped to CIS/NIST/PCI.

---

## Version Context

**Technology**: AWS CloudTrail — Audit Logging, Governance & Compliance
**Target edition**: 2025 (research verified 2026-07-31)
**Review by**: 2027-07-31
**Official docs**: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html

**Key facts in this edition**:
- **Four event types**: management (control-plane), data (data-plane), **network activity** (VPC-endpoint API calls — new), Insights (anomaly detection). Only management events are on by default.
- **CloudTrail Lake** retention: **One-year extendable** (up to 3,653 days / ~10 yr) or **Seven-year** (up to 2,557 days / ~7 yr) pricing tiers
- **Organization trail delegated administrator**: management account can delegate trail operations to a security account
- **Global service events** (IAM, STS, CloudFront) have logged to **us-east-1** only since **2021-11-22** — a single-Region trail outside us-east-1 silently misses them

**Terminology corrections** (reject old patterns):
- "CloudTrail only has 3 event types" → misinformation; **network activity events** are the fourth type (GA)
- "SSE-S3 is fine for logs" → use SSE-KMS; SSE-S3 does not give key-policy access control
- "Event history is a permanent record" → it is a 90-day view only; a trail is required for durability

> CRITICAL — Agent Warning: Patterns pre-dating the four-event-type model or the 2021-11-22 global-service-event change are treated as misinformation. Apply 2025 patterns exclusively.

---

## Quick Navigation

- **[Always-Do Patterns](./blueprints/always-do-patterns.md)** — AD-1 through AD-11: mandatory architectural patterns with CLI verification
- **[Ask-First Decisions](./blueprints/ask-first-decisions.md)** — AF-1 through AF-6: architectural crossroads with tradeoff matrices
- **[Never-Do Anti-Patterns](./blueprints/never-do-patterns.md)** — NP-1 through NP-9: prohibited patterns with wrong/correct examples
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 4 test cases: canonical, edge, misuse, and cost-governance
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — Security Hub controls and critical CLI at a glance

---

## Blueprints & Guardrails

### ✅ Always Do

Full patterns with CLI verification and Security Hub control mappings in [Always-Do Patterns](./blueprints/always-do-patterns.md).

| # | Pattern | WAF Pillars | Security Hub / CIS | Risk if omitted |
|---|---------|-------------|-------------------|-----------------|
| AD-1 | **Multi-Region trail** (`IsMultiRegionTrail=true`, `IncludeGlobalServiceEvents=true`) | Security, Reliability | CloudTrail.1 / CIS 3.1 | Misses IAM/STS/CloudFront + all other Regions |
| AD-2 | **Organization trail** created by management/delegated-admin account; member accounts cannot stop/modify | Security, OpEx, Reliability | — / CIS 3.1 | Coverage gaps as estate grows; member accounts can disable own audit |
| AD-3 | **Dedicated Log Archive account** owns the S3 bucket; audited accounts cannot touch it | Security | — | Log tampering; repudiation; compliance violation |
| AD-4 | **SSE-KMS** (customer-managed key) on the trail and on CloudTrail Lake event data stores | Security | CloudTrail.2 / CIS 3.5; CloudTrail.10 | No key-policy access control over audit evidence |
| AD-5 | **Log file integrity validation** (`EnableLogFileValidation=true`) — SHA-256/RSA digest files | Security | CloudTrail.4 / CIS 3.2 | Forensic evidence unprovable; logs forgeable |
| AD-6 | **CloudWatch Logs integration** — metric filters + alarms on StopLogging, root usage, IAM changes | Security, OpEx | CloudTrail.5 / CIS 3.4 | No real-time alert; breach goes undetected |
| AD-7 | **S3 server access logging** on the CloudTrail bucket (to a separate target bucket) | Security | CloudTrail.7 / CIS 3.6 | Attempts to read/tamper with logs are invisible |
| AD-8 | **SNS notification** on log delivery with `aws:SourceArn` condition on the topic policy | Security, OpEx | — | Confused-deputy risk; no delivery heartbeat |
| AD-9 | **AWS Config managed rules** org-wide conformance pack for continuous compliance evaluation | Security, OpEx | — | Trail drift goes undetected between manual audits |
| AD-10 | **S3 Object Lock (WORM, Compliance mode)** — preferred immutability path when lifecycle tiering needed | Security | — | Compromised credential can permanently delete logs |
| AD-11 | **CloudTrail Lake** org event data store for long-retention SQL analytics and investigations | Security, Perf Eff | CloudTrail.10 | Short retention window; expensive DIY S3+Athena+Glue |

> AD-10 note: MFA Delete is an alternative when lifecycle tiering is NOT needed. MFA Delete is incompatible with S3 lifecycle configuration. Choose one path; Object Lock is the automatable enterprise default. See [Always-Do Patterns](./blueprints/always-do-patterns.md) AD-10.

### ⚠️ Ask First

Full decision matrices with option tables and tradeoff analysis in [Ask-First Decisions](./blueprints/ask-first-decisions.md).

- **AF-1 — Organization trail vs. per-account trails** — Org trail: uniform coverage, auto-enroll, tamper-resistant. Per-account: local autonomy but coverage drifts. Ask: "Are all accounts in a single AWS Organization and do you want new accounts covered automatically?"
- **AF-2 — CloudTrail Lake vs. S3 + Athena** — Lake: zero-ops, immutable, ≤10 yr retention, $0.75/GB ingest. Athena: cheapest at-rest, open Parquet, but you build/own schema+partitions. Ask: "Do you have a data-engineering team to own partitioning and tuning?"
- **AF-3 — Which event types to enable** — Management (default, free first copy), Data ($0.10/100k), Insights ($0.35/100k), Network activity ($0.10/100k). High-volume data events can dwarf management volume. Ask: "Which specific S3 buckets / Lambda functions / DynamoDB tables justify per-object logging?"
- **AF-4 — Multi-Region vs. single-Region trail** — Multi-Region is essentially always correct; single-Region outside us-east-1 silently loses IAM/STS/CloudFront events since 2021-11-22. Ask: "Is there ANY reason not to use multi-Region?"
- **AF-5 — CloudTrail vs. AWS Config vs. Security Hub** — CloudTrail = "who did what, when"; Config = resource config state + drift; Security Hub = aggregated posture findings. They complement each other. Ask: "Do you need the API activity record, the config-state history, the posture score — or all three composed together?"
- **AF-6 — Centralized vs. decentralized log-account architecture** — Centralized Log Archive account: segregation of duties, single audit surface. Decentralized: audited principals can tamper with own logs. Ask: "Can you stand up a dedicated Log Archive account no workload team can access?"

### 🚫 Never Do

Full anti-patterns with `# WRONG` / `# CORRECT` CLI examples in [Never-Do Anti-Patterns](./blueprints/never-do-patterns.md).

| # | Anti-Pattern | Risk | Impact |
|---|-------------|------|--------|
| NP-1 | **Disabling CloudTrail / leaving Regions without trail coverage** | CRITICAL | All activity unauditable; fails CloudTrail.1/CIS 3.1 |
| NP-2 | **Logs stored in the same account being audited** | HIGH | Audited principals can tamper with own evidence |
| NP-3 | **CloudTrail S3 bucket with Block Public Access disabled** | CRITICAL | Log contents exposed; adversary reconnaissance; CloudTrail.6 |
| NP-4 | **No log file integrity validation** | HIGH | Forensic evidence inadmissible; logs forgeable |
| NP-5 | **Default trail only (no data event selectors) for sensitive S3/Lambda/DynamoDB** | HIGH | Object-level access/exfiltration invisible |
| NP-6 | **No CloudTrail Insights on high-value environments** | MEDIUM | Credential misuse / runaway automation undetected |
| NP-7 | **Log Archive S3 bucket writable/accessible by audited accounts** | CRITICAL | Log tampering; repudiation; breaks segregation of duties |
| NP-8 | **No alerting when a trail is stopped or modified** | HIGH | Audit blackout during an incident goes unnoticed |
| NP-9 | **No immutability control (no Object Lock / no MFA Delete) on the log bucket** | HIGH | Compromised credential permanently destroys audit history |

---

## Integration Patterns

**AWS CloudTrail integrates with**:
- **AWS Organizations** — Organization trail auto-enrolls member accounts via `AWSServiceRoleForCloudTrail`; member accounts cannot stop/delete/modify it
- **Amazon CloudWatch Logs** — Real-time metric filters and alarms on security-relevant events (StopLogging, root usage, IAM policy changes); billed at $0.25/GB delivered
- **Amazon EventBridge** — Per-Region event bus receives CloudTrail events; rules trigger Lambda auto-remediation (e.g. re-enable a stopped trail, quarantine a principal)
- **AWS Security Hub** — Consumes CloudTrail as evidence for CSPM controls CloudTrail.1–.10; depends on Config recorder being active in each account
- **AWS Config** — Continuous compliance evaluation of trail attributes; managed rules: `multi-region-cloud-trail-enabled`, `cloud-trail-encryption-enabled`, `cloud-trail-log-file-validation-enabled`, `cloud-trail-cloud-watch-logs-enabled`
- **Amazon GuardDuty / Amazon Detective** — Use CloudTrail management and data events as the primary input for threat detection and investigation
- **CloudTrail Lake** — Ingests events into immutable event data stores (EDS); supports non-AWS event sources via channels (`PutAuditEvents`)

**Common failure modes**:
- **Problem**: KMS key policy misconfiguration blocks trail delivery → **Solution**: Key policy must allow CloudTrail service principal to `GenerateDataKey` and log readers to `Decrypt`; verify with `aws cloudtrail get-trail --name <trail> --query 'Trail.KmsKeyId'`
- **Problem**: Data events generate unexpected high bill → **Solution**: Scope with advanced event selectors (by bucket/function/table, writes only); EDS supports advanced selectors only
- **Problem**: Single-Region trail misses IAM/STS/CloudFront events → **Solution**: Use multi-Region trail; since 2021-11-22 global service events land in us-east-1 only

---

## Verification Loop

Run after every CloudTrail architecture design or configuration change:

### 1. Trail Multi-Region and Global Service Events
```bash
aws cloudtrail describe-trails \
  --query 'trailList[].{Name:Name,MultiRegion:IsMultiRegionTrail,Global:IncludeGlobalServiceEvents,OrgTrail:IsOrganizationTrail}'
# Expected: IsMultiRegionTrail=true, IncludeGlobalServiceEvents=true, IsOrganizationTrail=true (for enterprise)
```

### 2. Integrity Validation and KMS Encryption
```bash
aws cloudtrail get-trail --name <trail-name> \
  --query 'Trail.{Validation:LogFileValidationEnabled,KMS:KmsKeyId,CWLogs:CloudWatchLogsLogGroupArn}'
# Expected: LogFileValidationEnabled=true, KmsKeyId != null, CloudWatchLogsLogGroupArn != null
```

### 3. S3 Bucket Security
```bash
aws s3api get-public-access-block --bucket <log-archive-bucket>
# Expected: BlockPublicAcls: true, IgnorePublicAcls: true, BlockPublicPolicy: true, RestrictPublicBuckets: true

aws s3api get-object-lock-configuration --bucket <log-archive-bucket>
# Expected: ObjectLockEnabled: Enabled, Rule.DefaultRetention present

aws s3api get-bucket-logging --bucket <log-archive-bucket>
# Expected: LoggingEnabled.TargetBucket != <log-archive-bucket> (separate target)
```

### 4. Log File Integrity Validation (audit run)
```bash
aws cloudtrail validate-logs \
  --trail-arn <trail-arn> \
  --start-time <ISO-8601-start> \
  --end-time <ISO-8601-end>
# Expected: "No validation errors found" — or explicit list of modified/deleted files
```

### 5. Continuous Compliance — AWS Config Rules
```bash
aws configservice describe-compliance-by-config-rule \
  --config-rule-names multi-region-cloud-trail-enabled cloud-trail-encryption-enabled \
    cloud-trail-log-file-validation-enabled cloud-trail-cloud-watch-logs-enabled
# Expected: ComplianceType: COMPLIANT for all four rules
```

### 6. CloudTrail Lake Event Data Store
```bash
aws cloudtrail list-event-data-stores \
  --query 'EventDataStores[].{Name:Name,Status:Status,Retention:RetentionPeriod,OrgEnabled:OrganizationEnabled}'
# Expected: Status=ENABLED, OrganizationEnabled=true (for org-wide EDS)
```

**Troubleshooting**:
- `KMSAccessDeniedException` on trail creation → Verify KMS key policy allows `cloudtrail.amazonaws.com` to `GenerateDataKey`
- `InsufficientS3BucketPolicyException` → Bucket policy must grant CloudTrail `s3:PutObject` scoped with `aws:SourceArn`
- Config rules NONCOMPLIANT after trail update → Propagation can take up to 15 minutes; re-check before escalating

---

## Quick Reference

**Essential verification commands**:
```bash
aws cloudtrail describe-trails                              # List all trails and attributes
aws cloudtrail get-trail --name <trail>                    # Detailed trail config
aws cloudtrail get-event-selectors --trail-name <trail>    # Data/Insights event selectors
aws cloudtrail get-insight-selectors --trail-name <trail>  # Insights enabled?
aws cloudtrail list-event-data-stores                      # CloudTrail Lake EDS list
aws cloudtrail validate-logs --trail-arn <arn> --start-time <t>  # Integrity validation
```

**Security Hub CloudTrail controls (2025)**:

| Control | Title | Severity | CIS Mapping |
|---------|-------|----------|-------------|
| CloudTrail.1 | Multi-Region trail with read+write mgmt events | High | v5.0.0/3.1 |
| CloudTrail.2 | Encryption at rest (SSE-KMS) | Medium | v5.0.0/3.5 |
| CloudTrail.3 | At least one trail enabled | High | — |
| CloudTrail.4 | Log file validation enabled | Low | v5.0.0/3.2 |
| CloudTrail.5 | Integrated with CloudWatch Logs | Medium | v5.0.0/3.4 |
| CloudTrail.6 | Log S3 bucket not publicly accessible | Critical | v1.4.0/3.3 |
| CloudTrail.7 | S3 bucket access logging enabled | Low | v5.0.0/3.4 |
| CloudTrail.10 | Lake EDS encrypted with customer-managed KMS | Medium | — |

> Re-verify control IDs and severities at [Security Hub CloudTrail controls](https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html) — they evolve with CSPM updates.

---

## Blueprints Directory Structure

```
StoryBeats/.claude/skills/auditing-aws-cloudtrail/
├── SKILL.md                              <- This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md             <- AD-1 to AD-11: mandatory patterns with CLI verification
    ├── ask-first-decisions.md            <- AF-1 to AF-6: decision matrices with tradeoff tables
    ├── never-do-patterns.md              <- NP-1 to NP-9: anti-patterns with wrong/correct examples
    └── evaluation-scenarios.md           <- 4 test cases (canonical, edge, misuse, cost-governance)
```

---

## External Resources

### Official AWS Documentation (all accessed 2026-07-31)
- [AWS CloudTrail concepts](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html) — event types, trails, org trails, Lake, Insights, global service events
- [Security best practices in AWS CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html) — immutability, encryption, integrity validation, segregation of duties
- [AWS CloudTrail Pricing](https://aws.amazon.com/cloudtrail/pricing/) — event pricing model, Lake retention tiers
- [Security Hub CSPM controls for CloudTrail (CloudTrail.1–.10)](https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html) — CIS/NIST/PCI mappings
- [Creating a trail for an organization](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html) — org trail, delegated administrator, service-linked role
- [CloudWatch alarms for CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudwatch-alarms-for-cloudtrail.html) — real-time monitoring integration
- [Logging data events](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-data-events-with-cloudtrail.html) — advanced event selectors
- [CloudTrail delegated administrator](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-delegated-administrator.html) — security account delegation
