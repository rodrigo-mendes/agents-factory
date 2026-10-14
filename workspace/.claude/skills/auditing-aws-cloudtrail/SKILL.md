---
name: auditing-aws-cloudtrail
description: "Configures AWS CloudTrail audit logging for security-critical, multi-account AWS environments. Use when designing or reviewing CloudTrail trails, log integrity, S3 bucket hardening, KMS encryption, monitoring integration, or multi-account log aggregation following AWS Security Reference Architecture and Security Hub CSPM controls."
---

## Function

Specialist in AWS CloudTrail security architecture — trail provisioning, log integrity validation, S3 hardening, KMS encryption, CloudWatch/EventBridge/GuardDuty integration, and multi-account organization trails aligned to AWS SRA and CIS AWS Foundations Benchmark v5.0.0.

## Version Context

**Technology**: AWS CloudTrail
**Target version**: AWS CloudTrail 2026
**Research date**: 2026-08-26
**Currency threshold**: Review after 2027-08-26
**Support status**: Active

**Critical breaking change (2026):**
- CloudTrail Lake is **no longer open to new customers as of May 31, 2026**. New architectures requiring SQL-based event querying must use Athena over S3-delivered logs or Amazon Security Lake instead.

**Important 2025/2026 changes:**
- Network Activity Events (VPC endpoint API calls) reached GA on February 14, 2025.
- AWS Control Tower landing zone 4.0 deprecated four standalone CloudTrail guardrails — their function is now inherent to the managed organization trail.
- CloudTrail Lake EDS federation to AWS Glue + Athena is available for existing customers.

**Documentation conflict (unresolved 2026-08-26):**
- The Security best-practices page says logs are "by default encrypted by using SSE-KMS." The Security Hub CloudTrail.2 control page says the default is SSE-S3. **Treat SSE-KMS as opt-in and explicitly configure it regardless of wording.**

**Deprecated / unavailable for new deployments:**
- CloudTrail Lake event data stores — closed to new customers since May 31, 2026.

> CRITICAL — Agent Warning:
> Do not recommend CloudTrail Lake for any new customer or new architecture.
> All patterns in this skill assume the organization trail + S3 delivery model.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 operational rules
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases
- **[Integration Patterns](#integration-patterns)** — CloudWatch, EventBridge, GuardDuty, Security Lake
- **[Verification Loop](#verification-loop)** — CLI validation commands
- **[Quick Reference](#quick-reference)** — Security Hub controls at a glance
- **[External Resources](#external-resources)** — dated official links

---

## Blueprints & Guardrails

### ✅ Always Do

**1. Enable an organization trail (multi-Region)** — A single organization trail covers the management account and all member accounts. Member accounts cannot delete, stop, or reconfigure it. Console-created organization trails are multi-Region by default. This satisfies Security Hub CloudTrail.1 and CloudTrail.3.

**2. Enable log file integrity validation on every trail** — Without digest files (SHA-256 + SHA-256/RSA), log tampering is undetectable. Enable at trail creation; validate periodically with `aws cloudtrail validate-logs`. Satisfies CloudTrail.4.

```bash
aws cloudtrail create-trail \
  --name org-trail \
  --s3-bucket-name <log-archive-bucket> \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --include-global-service-events
```

**3. Store organization trail logs in a dedicated Log Archive account** — Per AWS SRA, the Log Archive account is a separate account within the Security OU. It acts as an immutable sink, not accessible from workload accounts. Combine with S3 Object Lock for regulatory immutability.

**4. Enable SSE-KMS encryption on the trail** — Explicitly configure KMS encryption; do not rely on defaults due to the conflicting AWS documentation noted in Version Context. The KMS key must reside in the same Region as the S3 bucket.

Required KMS key policy statements (`cloudtrail.amazonaws.com` principal):
- `kms:GenerateDataKey*` with `kms:EncryptionContext:aws:cloudtrail:arn` (StringLike, scoped to trail ARN)
- `kms:Decrypt` for CloudTrail service principal and log-reader principals
- `kms:DescribeKey`
- Add `aws:SourceArn` condition scoped to the specific trail ARN

**5. Block all public access on the CloudTrail S3 bucket** — Security Hub CloudTrail.6 is rated **Critical**. Public exposure reveals account activity to adversaries. All four Block Public Access settings must be enabled. Bucket policy must use the `cloudtrail.amazonaws.com` service principal (not per-Region account-ID ARNs, which fail for new Regions).

Required bucket policy statements:
- `AWSCloudTrailAclCheck20150319`: `s3:GetBucketAcl` — add `aws:SourceArn` condition
- `AWSCloudTrailWrite20150319`: `s3:PutObject` with `s3:x-amz-acl = bucket-owner-full-control` — add `aws:SourceArn` condition
- For organization trails: third statement `AWSCloudTrailOrganizationWrite20150319` on `.../AWSLogs/{o-organizationID}/*`

**6. Integrate trail with CloudWatch Logs** — Required for metric filters and alarms. Satisfies Security Hub CloudTrail.5. A dedicated IAM role (`CloudTrail_CloudWatchLogs_Role`) must have CloudWatch Logs write permissions. Required alarm coverage (CIS-mapped): root usage, unauthorized API calls, console login without MFA, IAM policy changes, CloudTrail configuration changes, console auth failures, KMS key changes, S3 bucket policy changes, Config changes, security group changes, NACL changes, gateway changes, route table changes, VPC changes.

**7. Apply deny SCPs for `cloudtrail:StopLogging` and `cloudtrail:DeleteTrail`** — Applied to all member OUs. Combined with the organization trail's built-in protection, this prevents accidental or malicious disabling of audit logging without management-account access.

**8. Tag every trail** — Required for Security Hub CloudTrail.9. Include at minimum: environment, owner, data-classification.

### ⚠️ Ask First

**1. Data events scope (S3, Lambda, DynamoDB, Bedrock, others)** — Data events are disabled by default and cost $0.10/100K. Ask: Which resource types and operations need visibility? Use basic event selectors for S3/Lambda/DynamoDB; use advanced event selectors for all other resource types (200+). Logging all S3 `GetObject` on high-traffic buckets can generate significant cost.

| Selector type | Supports | When to use |
|---|---|---|
| Basic | S3, Lambda, DynamoDB | Simple per-service enablement |
| Advanced | All 200+ resource types | Fine-grained filtering, new services |

**2. Network Activity Events (VPC endpoint visibility)** — GA since February 2025. Cost: $0.10/100K. Ask: Is VPC endpoint traffic in-scope for security monitoring? Can configure to log all calls or `accessDenied` only. Requires advanced event selectors.

**3. CloudTrail Insights for anomaly detection** — `ApiCallRateInsight` and `ApiErrorRateInsight`. Cost: $0.35/100K (management) and $0.03/100K (data) per type. Requires a 28-day baseline period before triggering. Ask: Is behavioral anomaly detection required, or is static CloudWatch alarm coverage sufficient?

**4. MFA Delete vs S3 lifecycle on the log archive bucket** — MFA Delete and S3 lifecycle configurations are **mutually exclusive** on the same bucket. Ask: Is MFA Delete required for regulatory compliance, or is S3 lifecycle sufficient for retention management? Choose one.

**5. Security Lake integration** — Security Lake ingests CloudTrail as three separate OCSF-normalized sources (management events, S3 data events, Lambda data events). Ask: Is a centralized OCSF/Parquet query layer required for SIEM integration? Prerequisite: at least one multi-Region organization trail logging read+write management events.

**6. EventBridge rule state for read-only management events** — Write/mutating management events and data events match rules with state `ENABLED`. Read-only management events require rule state `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`. Ask: Does the automation pipeline need to react to read-only API calls (e.g., `Describe*`, `List*`)?

### 🚫 Never Do

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| **Recommend CloudTrail Lake for new architectures** | Lake closed to new customers since May 31, 2026 | Use Athena over S3-delivered logs or Amazon Security Lake |
| **Public S3 bucket for CloudTrail logs** | Critical (CloudTrail.6) — adversary reconnaissance of account activity | Enable all four Block Public Access settings; enforce via SCP |
| **Apply `AWSCloudTrail_FullAccess` broadly** | Any principal can disable/reconfigure audit logging | Grant only to account administrators; log readers need only `kms:Decrypt` + S3 read |
| **Single-Region trail only** | Blind to other Region activity; fails CloudTrail.1 | Always create multi-Region organization trails |
| **KMS key without `aws:SourceArn` condition** | Key usable for unintended trails | Scope the key policy to specific trail ARNs via `aws:SourceArn` |
| **Disable or delete the KMS key while encryption enabled** | CloudTrail stops delivering logs with no clear error | Rotate keys via KMS key rotation; never delete active trail encryption keys |
| **Use old per-Region CloudTrail account-ID ARNs in bucket policy** | Log delivery fails for Regions added after the policy was created | Always use `cloudtrail.amazonaws.com` service principal |
| **SSE-KMS-only bucket policy without allowing AES256** | Cannot create trails with log file validation enabled | Allow both: `s3:x-amz-server-side-encryption` StringNotEquals `["aws:kms", "AES256"]` |

---

## Integration Patterns

**CloudTrail → CloudWatch Logs → Metric Filters → Alarms → SNS**
Flow: Trail delivers to a CloudWatch Logs log group. Metric filters in namespace `CloudTrailMetrics` emit value 1 per matching event. Alarms use `Sum` statistic over a 5-minute period. SNS topic delivers notifications. CIS AWS Foundations Benchmark v5.0.0 maps 14 mandatory alarm patterns (see Section 10.1 of research file for verbatim filter patterns).

**CloudTrail → EventBridge (near-real-time reactions)**
CloudTrail sends only to the **default EventBridge event bus**. Forward to a custom bus via a default-bus rule. `detail-type` values: `AWS API Call via CloudTrail`, `AWS Console Signin via CloudTrail`, `AWS Insight via CloudTrail`, `AWS Network Activity Event via CloudTrail`. Read-only management events require rule state `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`.

**CloudTrail → GuardDuty (foundational data source)**
GuardDuty consumes management events via an independent, duplicated stream — no trail configuration needed, no additional cost for foundational-source access. S3 and Lambda data events are separate protection plans with separate pricing.

**CloudTrail → Amazon Security Lake (OCSF/Parquet)**
Three ingested sources: management events, S3 data events, Lambda data events. Normalized to OCSF schema. Prerequisite: multi-Region organization trail with read+write management events enabled and logging active.

**Common problems:**

- **Problem**: CloudTrail stops delivering logs with no notification → **Solution**: Check KMS key status (not disabled/deleted) and bucket policy prefix match; verify bucket is reachable. CloudTrail retries for 30 days; charges accrue during retries.
- **Problem**: EventBridge rule never matches `Describe*` / `List*` API calls → **Solution**: Set rule state to `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`.
- **Problem**: Organization trail visible but undelivered for some member accounts → **Solution**: Verify the third bucket policy statement for `.../AWSLogs/{o-organizationID}/*` with `aws:SourceArn` referencing the management-account trail ARN.

---

## Verification Loop

Run after configuring or modifying any trail:

### 1. Validate log file integrity (CLI)

```bash
aws cloudtrail validate-logs \
  --trail-arn arn:aws:cloudtrail:<region>:<account-id>:trail/<trail-name> \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --region <region>
# Expected: "Results requested for..."  "No failures"
# For org trails add: --account-id <member-account-id>
```

### 2. Check Security Hub CSPM findings

```bash
aws securityhub get-findings \
  --filters '{"ProductFields": [{"Key": "ControlId", "Value": "CloudTrail.*", "Comparison": "PREFIX"}], "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}]}' \
  --query 'Findings[].{Control:ProductFields,Severity:Severity.Label}' \
  --region <region>
# Expected: no Critical or High findings for CloudTrail controls
# Note: findings can take up to 18 hours to appear after enabling standards
```

### 3. Confirm trail is logging

```bash
aws cloudtrail get-trail-status --name <trail-name> --region <region>
# Expected: "IsLogging": true, "LatestDeliveryError": null
```

### 4. Confirm S3 bucket not public

```bash
aws s3api get-public-access-block --bucket <log-archive-bucket>
# Expected: all four "BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets" = true
```

**Troubleshooting:**

- `INVALID: signature verification failed` → log files were modified after delivery; escalate as a security incident.
- `INVALID: has been moved from its original location` → do not move log files from their S3 path; validate in place.
- `IsLogging: false` → check SCP blocks, KMS key health, and bucket policy.
- `LatestDeliveryError` not null → check bucket policy, prefix, KMS key, and bucket reachability.

---

## Quick Reference

**Security Hub CSPM controls checklist:**

| Control | Requirement | Severity |
|---|---|---|
| CloudTrail.1 | ≥1 multi-Region trail, read+write management events | High |
| CloudTrail.2 | SSE-KMS encryption at rest | Medium |
| CloudTrail.3 | At least one trail enabled | High |
| CloudTrail.4 | Log file integrity validation enabled | Low |
| CloudTrail.5 | Trail integrated with CloudWatch Logs | Medium |
| CloudTrail.6 | S3 bucket not publicly accessible | **Critical** |
| CloudTrail.7 | S3 server access logging enabled | Low |
| CloudTrail.9 | Trails tagged | Low |

**Pricing reference (2026-08-26 — verify before quoting):**

| Feature | Price |
|---|---|
| Management events (first copy) | Free |
| Management events (additional copies) | $2.00 / 100K |
| Data events | $0.10 / 100K |
| Network activity events | $0.10 / 100K |
| Insights — management | $0.35 / 100K per type |
| Insights — data events | $0.03 / 100K per type |

**Event type defaults:**

| Type | Logged by default |
|---|---|
| Management events | Yes (free first copy) |
| Data events | No — must enable |
| Network activity events | No — must enable |
| Insights events | No — must enable |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/auditing-aws-cloudtrail/
├── SKILL.md                              <- This file (summary + guardrails)
└── blueprints/
    └── evaluation-scenarios.md          <- 6 test cases for skill-evaluator
```

---

## External Resources

### Official Documentation (all accessed 2026-08-26)

- [CloudTrail User Guide](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/) — primary reference
- [CloudTrail Concepts](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html) — event types, trails
- [Security Best Practices in AWS CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html)
- [CloudTrail Lake Service Availability Change (2026)](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake-service-availability-change.html) — **Lake closed to new customers May 31, 2026**
- [Log File Integrity Validation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-intro.html)
- [S3 Bucket Policy for CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html)
- [KMS Key Policies for CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-kms-key-policy-for-cloudtrail.html)
- [Security Hub CSPM Controls — CloudTrail](https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html)
- [CloudWatch Alarms for CloudTrail Events](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudwatch-alarms-for-cloudtrail.html)
- [AWS SRA — Log Archive Account](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/log-archive.html)
- [Control Tower — Logging](https://docs.aws.amazon.com/prescriptive-guidance/latest/designing-control-tower-landing-zone/logging.html)
- [Network Activity Events GA (Feb 2025)](https://aws.amazon.com/about-aws/whats-new/2025/02/aws-cloudtrail-network-activity-events-vpc-endpoints-generally-available/)
- [CloudTrail Pricing](https://aws.amazon.com/cloudtrail/pricing/)
- [Well-Architected Security Pillar SEC04-BP01](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_detect_investigate_events_app_service_logging.html)
