---
name: architecting-cloudtrail-audit-logging
description: "Architects tamper-evident AWS CloudTrail audit-logging for AWS Organizations production workloads (2026 edition). Use when designing or reviewing CloudTrail configuration for multi-account estates, compliance evidence collection, threat-detection pipelines, or forensic-grade audit trails."
---

## Function

Specialist in AWS CloudTrail security architecture for multi-account AWS Organizations estates.
Covers trail topology, log integrity/encryption, analytics target selection, real-time alerting,
and threat-detection integration aligned to AWS Well-Architected Framework 2026.

## Version Context

**Service**: AWS CloudTrail
**Target edition**: 2026
**Research date**: 2026-08-26
**Currency threshold**: 2027-08-26

**Critical 2026 change — CloudTrail Lake closed to new customers (2026-05-31):**
CloudTrail Lake (event data stores / EDS) is closed to new customers from 2026-05-31.
Existing Lake customers keep the service (critical fixes only). New audit-analytics
architectures must target Amazon CloudWatch or S3 + Athena instead.
Trails, Insights, and Aggregated Events are unaffected.

**New since late 2025 / 2026:**
- Data-event aggregation (5-min summaries for security monitoring, 2025-11-24)
- CloudTrail Insights for data events (anomaly detection on data-plane, 2025-11-20)
- AWS Organizations membership events in CloudTrail (`AccountJoinedOrganization` / `AccountDepartedOrganization`, 2026-05-28)
- EventBridge `PutEvents` data-plane logging to CloudTrail (2026-05-04)

**Deprecated/End-of-life for new customers:** CloudTrail Lake (EDS) — do not design new systems on it.

> CRITICAL — Agent Warning: Reject any design that creates new CloudTrail Lake event data stores
> for non-existing-customer accounts. Do not mix Lake patterns with new-architecture guidance.

## Quick Navigation

- **[Always-Do Patterns](./blueprints/always-do-patterns.md)** — 7 mandatory patterns with config details
- **[Never-Do Patterns](./blueprints/never-do-patterns.md)** — 6 anti-patterns with detection and alternatives
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases for skill validation
- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier summary (this file)
- **[Verification Loop](#verification-loop)** — AWS CLI + Security Hub validation commands
- **[Quick Reference](#quick-reference)** — Trail config parameters at a glance
- **[External Resources](#external-resources)** — Official AWS documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For full configuration details and architecture decisions, see [Always-Do Patterns](./blueprints/always-do-patterns.md).

**M1 — Deploy a multi-Region organization trail**
Create ONE multi-Region org trail from the management (or delegated-admin) account.
Set `IsMultiRegionTrail=true`, `IsOrganizationTrail=true`, `IncludeGlobalServiceEvents=true`.
Member accounts receive an unmodifiable copy; new accounts and Regions are captured automatically.

**M2 — Deliver logs to a dedicated S3 bucket in a separate log-archive account**
One dedicated bucket in a locked-down log-archive account. Apply the CloudTrail-generated bucket
policy plus an `aws:SourceArn` condition key. This enforces segregation of duties — the audited
workload cannot destroy its own audit record.

**M3 — Enable log file integrity validation**
Set `EnableLogFileValidation=true` on every trail. Digest files (SHA-256 + SHA-256/RSA) are
delivered alongside logs. Run `aws cloudtrail validate-logs` to assert tamper-evidence.

**M4 — Encrypt log files with SSE-KMS using a customer managed key**
Create a dedicated KMS CMK with a key policy allowing CloudTrail to encrypt and authorized
principals to decrypt. Enable automatic key rotation. Set the trail's `KmsKeyId`.

**M5 — Protect the audit bucket: least-privilege + MFA delete/versioning + lifecycle**
Enable versioning + MFA delete on the bucket. Add lifecycle rules for retention tiering.
Note: MFA-delete-enabled buckets do NOT support lifecycle configuration — choose per bucket.

**M6 — Stream trail events to CloudWatch Logs for real-time alerting**
Configure the trail's CloudWatch Logs integration. Create metric filters and alarms for
high-risk patterns: root login, IAM policy changes, CloudTrail config changes, unauthorized
API calls, and new in 2026: `AccountJoinedOrganization`/`AccountDepartedOrganization` membership events.

**M7 — Layer GuardDuty (threat detection) and Security Hub CSPM (posture)**
Enable GuardDuty org-wide (CloudTrail is a core data source). Enable Security Hub with
AWS Foundational Security Best Practices + CIS AWS Foundations to auto-evaluate CloudTrail.1–CloudTrail.7 controls.

### ⚠️ Ask First

**D1 — Audit analytics store: where to run long-retention SQL queries**

| Option | Service | Best When |
|--------|---------|-----------|
| S3 + Athena | S3, Athena, Glue | Lowest cost, ad-hoc SQL, decoupled |
| CloudWatch (2026 recommended) | CloudWatch (OpenSearch, Iceberg, OCSF/OTel) | New builds needing unified analytics + alerting |
| CloudTrail Lake (legacy) | CloudTrail Lake EDS | **Existing Lake customers only** — closed to new customers 2026-05-31 |

Ask: "Is this org already a CloudTrail Lake customer?" If NOT → default to CloudWatch or S3+Athena.

**D2 — Data-event coverage scope (cost vs forensic depth)**

| Option | Optimizes | Sacrifices |
|--------|-----------|------------|
| Management events only | Lowest cost | No data-access forensics |
| Scoped via advanced selectors | Targeted forensic depth | Config complexity |
| Full data events + aggregation | Broad coverage at controlled cost | Storage cost for raw events |
| + Insights for data events (2025-11) | Automatic anomaly detection | Additional charges |

Ask: "Which resources hold sensitive data and what is the security-monitoring budget?"
Enable scoped data events on sensitive resources first, add aggregation to control volume,
then Insights for anomaly detection.

**D3 — Trail topology: single org trail vs additional purpose-specific trails**
CloudTrail supports up to 5 trails per Region (a multi-Region trail counts as one per Region).
Ask: "Do separate teams (security, audit, dev) require isolated log copies?"
Each additional trail duplicates delivery cost; the first copy of management events per account is free.

### 🚫 Never Do

For full anti-patterns with detection commands and side-by-side examples, see [Never-Do Patterns](./blueprints/never-do-patterns.md).

| Anti-pattern | Risk | Alternative |
|---|---|---|
| **A1** — Rely on Event history instead of a trail | HIGH — 90-day limit, no data events, no permanence | Multi-Region org trail (M1) |
| **A2** — Single-Region trail (`IsMultiRegionTrail=false`) | HIGH — misses IAM/STS/CloudFront events and all other-Region activity | Multi-Region trail with `IncludeGlobalServiceEvents=true` |
| **A3** — Unencrypted logs, no integrity validation | CRITICAL — tampering undetectable, confidentiality breach | SSE-KMS CMK (M4) + `EnableLogFileValidation=true` (M3) |
| **A4** — Log bucket in the workload account, broad access, no deletion protection | CRITICAL — attacker erases their tracks; segregation failure | Dedicated bucket in log-archive account (M2, M5) |
| **A5** — Broadly granting `AWSCloudTrail_FullAccess` | HIGH — holders can disable/reconfigure logging | Limit to fewest admins; add SCP denying `cloudtrail:StopLogging`/`DeleteTrail`/`UpdateTrail` |
| **A6** — New audit-analytics architecture on CloudTrail Lake in 2026 | MEDIUM — Lake closed to new customers 2026-05-31 | Amazon CloudWatch (recommended) or S3 + Athena |

---

## Integration Patterns

**CloudTrail → CloudWatch Logs → Alarms → SNS/EventBridge**
Real-time alerting on high-risk patterns. CIS AWS Foundations monitoring recommendations
define the metric filter set (root login, IAM changes, CloudTrail config changes, unauthorized calls).

**CloudTrail → S3 → Athena (query-in-place)**
Low-cost long-retention analytics. Use Glue crawler for schema discovery; query CloudTrail
JSON logs with standard SQL. Most cost-effective for infrequent ad-hoc forensic queries.

**CloudTrail → CloudWatch (2026 recommended)**
Unified security + operational analytics. Supports Apache Iceberg access, OCSF/OTel ingestion,
OpenSearch/Logs QL/PPL queries, and 60+ AWS sources. Default for new analytics builds post-2026.

**CloudTrail ↔ GuardDuty**
CloudTrail management events and (optionally) data events are a core GuardDuty data source.
GuardDuty provides ML-based behavioral threat detection on top of the raw CloudTrail record.

**Common problems:**
- **Bucket policy rejects trail delivery** → The bucket `deny-unless-SSE-KMS` policy must also permit `AES256` or trail creation fails. Allow both: `s3:x-amz-server-side-encryption` in `["aws:kms","AES256"]`.
- **Single-Region trail silently drops IAM/STS events** → Global service events land in us-east-1; always use multi-Region trail with `IncludeGlobalServiceEvents=true`.
- **MFA delete conflicts with lifecycle rules** → These are mutually exclusive on the same bucket. Use separate buckets or disable MFA delete before applying lifecycle.

---

## Verification Loop

Run after every CloudTrail configuration change:

### 1. Trail configuration health
```bash
# Confirm org multi-Region trail exists
aws cloudtrail describe-trails \
  --query 'trailList[?IsOrganizationTrail==`true` && IsMultiRegionTrail==`true`].[Name,HomeRegion,KmsKeyId,HasCustomEventSelectors]'

# Expected: at least one trail returned; KmsKeyId populated

# Confirm CloudWatch Logs integration
aws cloudtrail get-trail-status --name <trail-name-or-arn> \
  --query '{CloudWatchLogsLogGroupArn:CloudWatchLogsLogGroupArn,IsLogging:IsLogging}'
# Expected: CloudWatchLogsLogGroupArn non-null, IsLogging: true
```

### 2. Log file integrity validation
```bash
aws cloudtrail validate-logs \
  --trail-arn <trail-arn> \
  --start-time <ISO8601-start> \
  --end-time <ISO8601-end>
# Expected: "Results requested for <date range>", no "INVALID" or "MISSING" log files
```

### 3. Security Hub CloudTrail controls
```bash
aws securityhub get-findings \
  --filters '{"ComplianceStatus":[{"Value":"FAILED","Comparison":"EQUALS"}],"GeneratorId":[{"Value":"cloudtrail","Comparison":"PREFIX"}]}' \
  --query 'Findings[].{Title:Title,Severity:Severity.Label}' \
  --output table
# Expected: no CRITICAL or HIGH failures on CloudTrail.1–CloudTrail.7
```

### 4. AWS Config managed rules
```bash
# Key rules to verify:
# multi-region-cloudtrail-enabled
# cloud-trail-encryption-enabled
# cloud-trail-log-file-validation-enabled
# cloud-trail-cloud-watch-logs-enabled
aws configservice describe-compliance-by-config-rule \
  --config-rule-names multi-region-cloudtrail-enabled cloud-trail-encryption-enabled \
    cloud-trail-log-file-validation-enabled cloud-trail-cloud-watch-logs-enabled
# Expected: ComplianceType: COMPLIANT for all four rules
```

**Troubleshooting:**
- `CloudTrail.1 FAILED` → No multi-Region trail — run M1 setup
- `CloudTrail.2 FAILED` → Trail missing KmsKeyId — configure SSE-KMS CMK (M4)
- `CloudTrail.4 FAILED` → `EnableLogFileValidation=false` — update trail (M3)
- `CloudTrail.5 FAILED` → No CloudWatch Logs integration — configure CWL delivery (M6)

---

## Quick Reference

**Critical trail configuration parameters:**
```
IsMultiRegionTrail=true
IsOrganizationTrail=true
IncludeGlobalServiceEvents=true
EnableLogFileValidation=true
KmsKeyId=<customer-managed-key-arn>
CloudWatchLogsLogGroupArn=<log-group-arn>
CloudWatchLogsRoleArn=<delivery-role-arn>
```

**Security Hub CloudTrail control set:**

| Control | What it checks |
|---------|----------------|
| CloudTrail.1 | Multi-Region trail enabled |
| CloudTrail.2 | Trail encrypted with KMS CMK |
| CloudTrail.4 | Log file integrity validation enabled |
| CloudTrail.5 | CloudWatch Logs integration active |
| CloudTrail.6 | S3 bucket not publicly accessible |
| CloudTrail.7 | S3 access logging enabled on the audit bucket |

**Event type cost profile:**

| Event type | Default | Billed separately |
|---|---|---|
| Management events | Yes (first copy free) | No (first copy per account) |
| Data events | No — opt-in | Yes |
| Network activity events | No — opt-in | Yes |
| Insights events | No — opt-in | Yes |
| Data-event aggregation | No — opt-in | Yes (reduced volume) |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/architecting-cloudtrail-audit-logging/
├── SKILL.md                              <- This file (guardrails + summary)
└── blueprints/
    ├── always-do-patterns.md             <- M1-M7 with full config/CLI details
    ├── never-do-patterns.md              <- A1-A6 with detection commands and alternatives
    └── evaluation-scenarios.md           <- 6 test scenarios for skill-evaluator
```

---

## External Resources

### Official Documentation (all accessed 2026-08-26)
- [Security best practices in AWS CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html) — Primary reference for M1–M7 and A1–A6
- [CloudTrail concepts](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html) — Event types, trails, org trails, global service events
- [CloudTrail Lake availability change (2026-05-31)](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake-service-availability-change.html) — Lake closed to new customers
- [Creating a trail for an organization](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html) — Org trail setup
- [CloudWatch Logs integration and alarms](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudwatch-alarms-for-cloudtrail.html) — Real-time alerting
- [AWS Security Hub — CloudTrail controls](https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html) — CloudTrail.1–CloudTrail.7
- [Encryption best practices for CloudTrail](https://docs.aws.amazon.com/prescriptive-guidance/latest/encryption-best-practices/cloudtrail.html) — CMK key policy guidance

### 2025–2026 What's New
- [Data-event aggregation for security monitoring (2025-11-24)](https://aws.amazon.com/about-aws/whats-new/2025/11/cloudtrail-data-event-aggregation-security-monitoring/)
- [CloudTrail Insights for data events (2025-11-20)](https://aws.amazon.com/about-aws/whats-new/2025/11/cloudtrail-insights-data-events-detect-anomalies-access/)
- [AWS Organizations membership events in CloudTrail (2026-05-28)](https://aws.amazon.com/about-aws/whats-new/2026/05/aws-organizations-cloudtrail/)
- [EventBridge PutEvents data-plane logging to CloudTrail (2026-05-04)](https://aws.amazon.com/about-aws/whats-new/2026/05/amazon-eventbridge-data-aws-cloudtrail/)

### Framework References
- [AWS Well-Architected Framework — Security pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/)
- [AWS Well-Architected Framework — Operational Excellence pillar](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/)
