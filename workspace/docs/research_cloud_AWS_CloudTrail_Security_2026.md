# AWS CloudTrail — Security Architecture: Audit Logging (2026)

> Anti-hallucination research base. Every pattern is sourced to official AWS documentation with an
> access date. Items that could not be confirmed against an official source are tagged
> `⚠️ unverified` or `⚠️ IRRESOLVABLE`. Do not treat this file as legal or compliance advice.

## Metadata

```yaml
Full_Name: "AWS CloudTrail — Security Architecture: Audit Logging"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture - CloudTrail Audit Logging"
Target_Edition: "AWS CloudTrail 2026"
Architecture_Context: "Multi-account AWS Organizations with centralized logging and CSPM controls"
Official_Source_URL: "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/"
Output_Format: Markdown
Primary_Audience: Cloud Security Architects and Tech Leads
Research_Date: "2026-08-26"
Research_Depth: "exhaustive"
Currency_Threshold: "2027-08-26 — review after this date"
```

---

## Executive Summary

AWS CloudTrail is the control-plane and data-plane audit trail for AWS accounts. It records API
calls and related events, delivering them to S3 and/or CloudWatch Logs, and enables near-real-time
reaction via EventBridge. Every AWS account has a **free 90-day management-event history** in the
console; meaningful security audit capability requires a **configured trail** or **CloudTrail Lake
event data store** for retention, encryption, integrity validation, and downstream analysis.

**Critical 2026 architectural change.** ⚠️ **AWS CloudTrail Lake is no longer open to new customers
as of May 31, 2026.** Existing customers continue as normal. New architectures requiring SQL-based
event querying must use alternative query surfaces (Athena over S3-delivered logs, or Security
Lake). This is the highest-impact breaking change for architects in 2026.
[✓ Official | https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake-service-availability-change.html — accessed 2026-08-26]

**Three most critical guardrails.** (1) **Enable an organization trail** — a single organization
trail covers all accounts; member accounts cannot delete or reconfigure it. (2) **Enable log file
integrity validation** — without digest files, log tampering is undetectable. (3) **Never leave the
CloudTrail S3 bucket publicly accessible** — Security Hub rates this **Critical** (CloudTrail.6)
because public exposure aids adversaries in understanding the account's activity.

---

## 1. Event Types and What Is Logged by Default

**Source:** "CloudTrail concepts" — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html — accessed 2026-08-26

CloudTrail records **four event types**:

| Event Type | Also Known As | Logged by Default | Cost |
|---|---|---|---|
| **Management events** | Control plane operations | ✅ Yes (trails + EDS) | First copy free; additional copies $2.00/100K |
| **Data events** | Data plane operations | ❌ No | $0.10/100K |
| **Network activity events** | VPC endpoint API calls | ❌ No | $0.10/100K |
| **Insights events** | Anomaly detection | ❌ No | $0.35/100K (mgmt), $0.03/100K (data) per type |

### 1.1 Management Events

Records control-plane operations on AWS resources — IAM `AttachRolePolicy`, EC2 `CreateSubnet`,
CloudTrail `CreateTrail`, console `ConsoleLogin`. These include both API and non-API events.

### 1.2 Data Events

Records resource-level operations — S3 object-level ops (`GetObject`, `PutObject`, `DeleteObject`),
Lambda `Invoke`, DynamoDB item-level ops, SNS `Publish`, SQS ops, and 200+ `resources.type` values
(including Bedrock and other AI services). Must be explicitly enabled with event selectors.

- **Basic event selectors:** support S3 objects, Lambda functions, DynamoDB tables.
- **Advanced event selectors:** required for all other resource types and for CloudTrail Lake event data stores.

### 1.3 Network Activity Events (GA since February 14, 2025)

Records AWS API calls made through VPC endpoints from a private VPC to AWS services. Provides
visibility into resource operations within a VPC. GA'd February 14, 2025 across all commercial
Regions. Original GA: five services (S3, EC2, KMS, Secrets Manager, CloudTrail); current supported
set is broader per the live concepts page.
[✓ Official | https://aws.amazon.com/about-aws/whats-new/2025/02/aws-cloudtrail-network-activity-events-vpc-endpoints-generally-available/ — accessed 2026-08-26]

Can log all API calls or only `accessDenied` calls. Configured via advanced event selectors.

### 1.4 Insights Events

Detect unusual API call rate or error rate activity vs. the account's typical usage patterns.

- **`ApiCallRateInsight`:** write-only management API calls per minute vs. baseline.
- **`ApiErrorRateInsight`:** API calls returning error codes.
- Baseline: past 28 days, **recalculated daily** on a trailing 28-day window. No charge for baseline analysis.
- ⚠️ **Data event Insights are only supported on trails, not on CloudTrail Lake event data stores.**

### 1.5 Free 90-Day Event History

Every AWS account gets a **viewable, searchable, downloadable, immutable 90-day record of management
events** per Region — no trail required, no charge. Data events, network activity events, and
Insights events are **not** captured in the free history.

---

## 2. Trail Architecture

**Source:** "CloudTrail concepts" — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html — accessed 2026-08-26

A **trail** configures delivery of CloudTrail events to an S3 bucket, with optional delivery to
CloudWatch Logs and Amazon EventBridge.

**Limit:** five trails per Region (a multi-Region trail counts as one per Region).

### 2.1 Multi-Region vs Single-Region

| | Multi-Region Trail | Single-Region Trail |
|---|---|---|
| Created by | AWS Console (default) | AWS CLI/API only |
| Covers | All enabled Regions → one S3 bucket | One Region only |
| Recommended? | ✅ Yes (Security Hub CloudTrail.1) | Only if specifically required |
| Modifiable from | Home Region only | That Region |

Global service events (IAM, STS, CloudFront) are recorded in the Region where created **and** in
`us-east-1` (as of November 22, 2021). For multi-Region trails, `IncludeGlobalServiceEvents` must
be `true`.

### 2.2 Organization Trails

An organization trail delivers CloudTrail events for the management account **and all member
accounts** to the same S3 bucket, CloudWatch Logs group, and EventBridge bus.

Key behaviors:
- Console-created organization trails are **multi-Region by default**.
- A named copy appears in each member account — but **member accounts cannot delete, stop logging,
  or reconfigure an organization trail**. Only the management account or delegated administrator
  can change it.
- The S3 bucket folder structure: `AWSLogs/{managementAccountId}/{organizationID}/{memberAccountId}/`.
- Requires the management account to explicitly grant S3 bucket access for member-account logs (see
  Section 4).

---

## 3. CloudTrail Lake — Event Data Stores

**Source:** "Working with AWS CloudTrail Lake" — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html — accessed 2026-08-26

> ⚠️ **CRITICAL BREAKING CHANGE (2026):** CloudTrail Lake is no longer open to new customers as of
> **May 31, 2026**. Existing customers continue unaffected. New architectures must not rely on
> CloudTrail Lake for new deployments.

For existing customers:
- Events stored as immutable **event data stores (EDS)** in **Apache ORC** columnar format.
- Retention options:
  - **One-year extendable retention pricing:** up to **3,653 days (~10 years)**.
  - **Seven-year retention pricing:** up to **2,557 days (~7 years)**.
- SQL queries via full Trino `SELECT` + optional natural-language query generator (GA in 7 Regions).
- **14 managed dashboards** + custom dashboards (up to 10 widgets each).
- **Highlights dashboard** refreshes every 6 hours (last 24h window; ⚠️ GA status in 2026 unverified).
- Delivery latency: ~5 minutes average (not guaranteed).
- Federation to AWS Glue Data Catalog → query with Amazon Athena.
- Pricing: $0.75/GB ingestion (one-year pricing); $2.50–$0.50/GB tiered (seven-year); $0.005/GB scanned for queries.

---

## 4. Log File Integrity Validation

**Source:** "Validating CloudTrail log file integrity" — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-intro.html — accessed 2026-08-26

Integrity validation uses **SHA-256 for hashing** and **SHA-256 with RSA for digital signing** —
making it computationally infeasible to modify, delete, or forge log files without detection.

### How It Works

1. CloudTrail creates a **hash for every delivered log file**.
2. **Every hour**, it creates and delivers a **digest file** referencing the last hour's log files
   with a hash of each.
3. Each digest file is **signed with the private key** of a per-Region public/private key pair.
4. **Digest chaining:** each digest contains the **digital signature of the previous digest file**;
   the current digest's signature is in the S3 object metadata.
5. Digest files go to the **same S3 bucket** as logs but in a **separate folder** (enables granular
   security policies without disrupting log processing).

Enabling validation only **delivers** digest files — validation itself is performed by the CLI or
a custom tool.

### CLI Validation

**Source:** "Validating CloudTrail log file integrity with the AWS CLI" — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-cli.html — accessed 2026-08-26

```bash
aws cloudtrail validate-logs \
  --trail-arn <trailARN> \
  --start-time <start-time> \
  [--end-time <end-time>] \
  [--s3-bucket <bucket>] \
  [--s3-prefix <prefix>] \
  [--account-id <account-id>]   # required for organization trails
```

Prerequisites:
- Online connectivity to AWS.
- `s3:ListObjects`, `s3:GetObject`, `s3:GetBucketLocation` on referenced S3 buckets.
- Files must **not** have been moved from their original S3 location (locally downloaded files cannot be validated).
- Command is Region-specific — use the `--region` global option.

Failure messages: `INVALID: signature verification failed`, `INVALID: has been moved from its original location`, `INVALID: hash value doesn't match`, `INVALID: not found`.

**Recommendation:** Enhance digest security with **S3 MFA Delete**.

---

## 5. Encryption

**Source:** "Security best practices in AWS CloudTrail" — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html — accessed 2026-08-26  
**Source:** "Configure AWS KMS key policies for CloudTrail" — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-kms-key-policy-for-cloudtrail.html — accessed 2026-08-26

⚠️ **Documentation conflict (flag):** The Security best practices page states logs are "by default ... encrypted by using server-side encryption with a KMS key (SSE-KMS)." The Security Hub **CloudTrail.2** control page states the default is **SSE-S3**. These two live AWS pages conflict. **Treat SSE-KMS as opt-in and explicitly verify/configure it regardless of default wording.**

### SSE-KMS Configuration Rules

- KMS key must be in the **same AWS Region** as the S3 bucket.
- Required KMS key-policy statements (service principal `cloudtrail.amazonaws.com`):
  1. **Encrypt:** `kms:GenerateDataKey*` with `kms:EncryptionContext:aws:cloudtrail:arn` (StringLike) scoped to specific trail ARNs.
  2. **Decrypt:** `kms:Decrypt` for the CloudTrail service principal and for user/role principals that need to read logs.
  3. **Describe:** `kms:DescribeKey`.
- **Best practice:** Add `aws:SourceArn` (trail ARN) condition to the KMS key policy so CloudTrail uses the key only for specific trails.
- ⚠️ Event data stores: `aws:SourceArn`/`aws:SourceAccount` condition keys are **NOT supported** in the KMS key policy for CloudTrail Lake EDS.
- **Misconfiguration risk:** If encryption is enabled and the KMS key is disabled/deleted or key policy is misconfigured, **CloudTrail cannot deliver logs**.

### SSE-KMS + Log Validation Gotcha

If the bucket policy denies non-KMS encryption, you must also allow `AES256`, or you cannot create trails:

```json
"StringNotEquals": {
  "s3:x-amz-server-side-encryption": ["aws:kms", "AES256"]
}
```

---

## 6. S3 Bucket Security

**Source:** "Amazon S3 bucket policy for CloudTrail" — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html — accessed 2026-08-26

### Required Bucket Policy Statements

Two mandatory statements for the `cloudtrail.amazonaws.com` service principal:

1. `AWSCloudTrailAclCheck20150319`: `s3:GetBucketAcl` on the bucket ARN.
2. `AWSCloudTrailWrite20150319`: `s3:PutObject` on `.../AWSLogs/{accountId}/*` with condition
   `s3:x-amz-acl = bucket-owner-full-control`.

**Best practice:** Add `aws:SourceArn` (trail ARN) condition to both statements. Use the service
principal `cloudtrail.amazonaws.com` — older per-Region account-ID policies fail for new Regions.

Organization trails require a **third statement** (`AWSCloudTrailOrganizationWrite20150319`) on
`.../AWSLogs/{o-organizationID}/*`; `aws:SourceArn` must reference a management-account trail ARN.

### S3 Security Hardening Checklist

| Control | Requirement | Security Hub Control |
|---|---|---|
| Block Public Access | All four settings enabled | **CloudTrail.6 (Critical)** |
| Server access logging | Enabled on CloudTrail bucket | CloudTrail.7 (Low) |
| MFA Delete | Enabled for versioning protection | Best practice |
| Lifecycle rules | Configured for retention | Best practice |
| Dedicated account | Log Archive account (separate from workloads) | AWS SRA / Control Tower |
| Object Lock | Immutable storage for regulatory compliance | AWS SRA |

⚠️ **MFA Delete is incompatible with S3 lifecycle configurations.** Choose one based on compliance
requirements.

**Common misconfiguration errors:**
- Incorrect log file prefix in bucket policy → CloudTrail cannot deliver.
- Misconfigured/unreachable bucket → CloudTrail retries delivery for 30 days (charges still accrue).
- Using old per-Region CloudTrail account-ID ARNs in policy → fails for new Regions.

---

## 7. IAM Least Privilege

**Source:** "Security best practices in AWS CloudTrail" — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html — accessed 2026-08-26

- **`AWSCloudTrail_FullAccess` managed policy** grants the ability to disable/reconfigure auditing
  functions. AWS states it "is not intended to be shared or applied broadly." Apply to account
  administrators only.
- **Log readers** need `kms:Decrypt` (per-principal with `Null` encryption-context condition) +
  S3 read permissions on the bucket.
- **CLI validators** need only `s3:ListObjects`, `s3:GetObject`, `s3:GetBucketLocation`.

---

## 8. Security Hub CSPM Controls

**Source:** "Security Hub CSPM controls for AWS CloudTrail" — https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html — accessed 2026-08-26

| Control | Title | Severity | Config Rule |
|---|---|---|---|
| **CloudTrail.1** | ≥1 multi-Region trail capturing read+write management events | High | `multi-region-cloudtrail-enabled` |
| **CloudTrail.2** | Encryption at rest (SSE-KMS) enabled | Medium | `cloud-trail-encryption-enabled` |
| **CloudTrail.3** | At least one trail enabled | High | `cloudtrail-enabled` |
| **CloudTrail.4** | Log file integrity validation enabled | Low | `cloud-trail-log-file-validation-enabled` |
| **CloudTrail.5** | Trail integrated with CloudWatch Logs | Medium | `cloud-trail-cloud-watch-logs-enabled` |
| **CloudTrail.6** | S3 bucket not publicly accessible | **Critical** | Custom Security Hub rule |
| **CloudTrail.7** | S3 server access logging enabled | Low | Custom Security Hub rule |
| **CloudTrail.9** | Trails tagged | Low | `tagged-cloudtrail-trail` (custom) |
| **CloudTrail.10** | Lake EDS encrypted with customer-managed KMS key | Medium | `event-data-store-cmk-encryption-enabled` |

Note: CloudTrail.8 is absent from the current control list (sequence jumps 7 → 9). After enabling
Security Hub standards, findings can take **up to 18 hours**.

Benchmarks covered: **CIS AWS Foundations Benchmark v5.0.0, v3.0.0, v1.4.0, v1.2.0**; NIST 800-53 r5; PCI DSS; NIST 800-171.

---

## 9. Multi-Account Architecture (AWS SRA + Control Tower)

**Source:** "Security OU – Log Archive account" — https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/log-archive.html — accessed 2026-08-26  
**Source:** "Security OU – Security Tooling account" — https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/security-tooling.html — accessed 2026-08-26  
**Source:** "Logging" (AWS Control Tower Prescriptive Guidance) — https://docs.aws.amazon.com/prescriptive-guidance/latest/designing-control-tower-landing-zone/logging.html — accessed 2026-08-26

### Recommended Account Structure

```
AWS Organizations
└── Security OU
    ├── Log Archive account         ← S3 bucket for org trail logs (immutable sink)
    └── Security Tooling account    ← Delegated admin for CloudTrail, GuardDuty, etc.
```

- **Log Archive account:** dedicated repository aggregating CloudTrail + Config logs from all
  accounts. Immutable storage via S3 Object Lock. Access restricted to automated, monitored
  mechanisms only.
- **Security Tooling account:** delegated administrator for CloudTrail management. S3 bucket for
  org trail logs is in Log Archive; management authority is in Security Tooling — these are
  deliberately separated.

### AWS Control Tower Auto-Provisioning

Control Tower automatically provisions the Log Archive account and sets up an organization-level
CloudTrail trail.

- Landing zone ≥ 3.0: **organization trail** (previous releases created per-account trails; upgrading
  to 3.0 converts them and preserves existing log files in their S3 buckets).
- **Default retention (Control Tower):** 1 year for standard account logging; **10 years for access
  logging**.
- Maximum customizable retention: **15 years**.
- Opt-in/opt-out of Control Tower managing the trail is configurable.

⚠️ **Guardrail deprecation (landing zone 4.0):** Four CloudTrail guardrails ("Disallow Configuration
Changes to CloudTrail," "Integrate CloudTrail Events with Amazon CloudWatch Logs," "Enable CloudTrail
in All Available Regions," "Enable Integrity Validation for CloudTrail Log File") are no longer
deployed from landing zone 4.0 — their function is now inherent to the managed organization trail.
⚠️ *This item was partially confirmed via search snippets; verify exact wording on the mandatory-controls page before quoting.*

### Preventing Tampering with SCPs

Recommended: explicit `Deny` SCP on `cloudtrail:StopLogging` and `cloudtrail:DeleteTrail` applied
to all member OUs. Combined with the org trail's built-in member-account restrictions, this makes
disabling audit logging extremely difficult without management-account access.

⚠️ *The verbatim SCP JSON was confirmed conceptually via CloudTrail best-practices and org-trail docs but the exact example-SCP page was not fetched; confirm against the AWS Organizations SCPs examples page before using verbatim.*

---

## 10. Monitoring Integration

### 10.1 CloudTrail → CloudWatch Logs → Metric Filters + Alarms

**Source:** "Creating CloudWatch alarms for CloudTrail events: examples" — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudwatch-alarms-for-cloudtrail.html — accessed 2026-08-26  
**Source:** "Security Hub CSPM controls for Amazon CloudWatch" — https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html — accessed 2026-08-26

**Flow:** Trail → CloudWatch Logs log group → metric filter (namespace `CloudTrailMetrics`, value 1)
→ alarm (Sum, 5-min period) → SNS topic notification.

**Role required:** `CloudTrail_CloudWatchLogs_Role` (or equivalent IAM role with CloudWatch Logs
write permissions).

**CIS-mapped mandatory alarms (Security Hub CloudWatch controls):**

| Control | Event |
|---|---|
| CloudWatch.1 | Root user usage |
| CloudWatch.2 | Unauthorized API calls |
| CloudWatch.3 | Console sign-in without MFA |
| CloudWatch.4 | IAM policy changes |
| CloudWatch.5 | CloudTrail configuration changes |
| CloudWatch.6 | Management Console authentication failures |
| CloudWatch.7 | Disabling/deletion of customer-managed KMS keys |
| CloudWatch.8 | S3 bucket policy changes |
| CloudWatch.9 | AWS Config configuration changes |
| CloudWatch.10 | Security group changes |
| CloudWatch.11 | NACL changes |
| CloudWatch.12 | Network gateway changes |
| CloudWatch.13 | Route table changes |
| CloudWatch.14 | VPC changes |

**Selected verbatim filter patterns (from official docs):**

Security group changes:
```
{ ($.eventName = AuthorizeSecurityGroupIngress) || ($.eventName = AuthorizeSecurityGroupEgress) || ($.eventName = RevokeSecurityGroupIngress) || ($.eventName = RevokeSecurityGroupEgress) || ($.eventName = CreateSecurityGroup) || ($.eventName = DeleteSecurityGroup) }
```

Console sign-in failures (alarm at ≥3 in 5 min):
```
{ ($.eventName = ConsoleLogin) && ($.errorMessage = "Failed authentication") }
```

Root account usage:
```
{ $.userIdentity.type = "Root" && $.userIdentity.invokedBy NOT EXISTS && $.eventType != "AwsServiceEvent" }
```

⚠️ *The root-usage filter pattern above appeared in AWS content but its exact verbatim form on the
additional-examples page could not be confirmed (page failed to render via WebFetch).*

IAM policy changes (abbreviated — see official docs for full pattern):
```
{($.eventName=DeleteGroupPolicy)||($.eventName=DeleteRolePolicy)||($.eventName=PutGroupPolicy)||($.eventName=PutRolePolicy)||...}
```

### 10.2 CloudTrail → EventBridge (Near-Real-Time)

**Source:** "AWS service events delivered via AWS CloudTrail" — https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-service-event-cloudtrail.html — accessed 2026-08-26

- CloudTrail sends events to the **default EventBridge event bus only**. To use a custom bus, forward from a default-bus rule.
- `detail-type` values:
  - `AWS API Call via CloudTrail` — public AWS service API requests
  - `AWS Console Signin via CloudTrail`
  - `AWS Console Action via CloudTrail`
  - `AWS Service Event via CloudTrail`
  - `AWS Insight via CloudTrail` — requires CloudTrail Insights enabled
  - `AWS Network Activity Event via CloudTrail` — requires network activity event selectors

- **Critical rule state:** write/mutating management events + data events + network activity events match a default `ENABLED` rule; **read-only management events require rule state `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`**.

### 10.3 CloudTrail → Amazon GuardDuty

**Source:** "GuardDuty foundational data sources" — https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_data-sources.html — accessed 2026-08-26

- CloudTrail **management events** are a GuardDuty foundational data source.
- GuardDuty consumes them via an **independent, duplicated stream directly from CloudTrail** — no trail configuration required, no additional cost for foundational-source access.
- GuardDuty extracts fields and discards logs; your CloudTrail config is unaffected.
- Global service events (IAM, STS, S3, CloudFront, Route 53) are replicated/processed in each Region where GuardDuty is enabled.
- **S3 data events** and **Lambda** activity are separate protection plans (S3 Protection, Lambda Protection) with separate pricing.

### 10.4 CloudTrail → Amazon Security Lake

**Source:** "CloudTrail event logs in Security Lake" — https://docs.aws.amazon.com/security-lake/latest/userguide/cloudtrail-event-logs.html — accessed 2026-08-26

Security Lake ingests CloudTrail as **three separate sources**:
1. Management events
2. S3 data events
3. Lambda data events

**Prerequisite:** at least one multi-Region organization trail logging read+write management events,
with logging enabled. Security Lake normalizes events to **OCSF schema** + **Apache Parquet** format.

### 10.5 CloudTrail Insights (Anomaly Detection)

**Source:** "Working with CloudTrail Insights" — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-insights-events-with-cloudtrail.html — accessed 2026-08-26  
**Source:** "Costs for Insights events" — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/insights-events-costs.html — accessed 2026-08-26

- Two Insights types: **`ApiCallRateInsight`** (unusual write-API call volume) and **`ApiErrorRateInsight`** (unusual error rates).
- **28-day baseline** established on enable; recalculated daily on trailing 28-day window.
- **No charge for baseline analysis.**
- Both start and end Insights events are generated, bracketing the anomalous activity window.
- Pricing: management events $0.35/100K per Insights type; data events $0.03/100K.
- ⚠️ **Data event Insights: only supported on trails, not CloudTrail Lake event data stores.**

---

## 11. Pricing Reference

**Source:** AWS CloudTrail Pricing — https://aws.amazon.com/cloudtrail/pricing/ — accessed 2026-08-26  
⚠️ *Pricing figures are as displayed on 2026-08-26. Verify on the billing page before quoting to customers.*

| Feature | Price |
|---|---|
| Management events (first copy) | Free |
| Management events (additional copies) | $2.00 / 100,000 events |
| Data events | $0.10 / 100,000 events |
| Network activity events | $0.10 / 100,000 events |
| Data aggregations | $0.03 / 100,000 events analyzed |
| Insights — management | $0.35 / 100,000 events analyzed per type |
| Insights — data events | $0.03 / 100,000 events analyzed per type |
| CloudTrail Lake — ingestion (one-year pricing) | $0.75/GB (CloudTrail events); $0.50/GB (other sources) |
| CloudTrail Lake — ingestion (seven-year pricing) | Tiered: first 5 TB $2.50/GB; next 20 TB $1.00/GB; >25 TB $0.50/GB |
| CloudTrail Lake — extended storage | ~$0.023/GB-month |
| CloudTrail Lake — SQL queries | $0.005/GB scanned |
| S3 storage for delivered logs | Billed separately at standard S3 rates |

---

## 12. Well-Architected Security Pillar Alignment (SEC04)

**Source:** "SEC04-BP01 Configure service and application logging" — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_detect_investigate_events_app_service_logging.html — accessed 2026-08-26  
**Source:** "Detection" — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html — accessed 2026-08-26

SEC04 (Detect and investigate security events) best practices (2026 authoritative titles):
- **SEC04-BP01:** Configure service and application logging
- **SEC04-BP02:** Capture logs, findings, and metrics in standardized locations
- **SEC04-BP03:** Correlate and enrich security alerts
- **SEC04-BP04:** Initiate remediation for non-compliant resources

SEC04-BP01 explicitly states:
> "Establish a trail for each AWS account using AWS CloudTrail or an AWS Organizations trail, and
> configure an Amazon S3 bucket for it."

> "AWS CloudTrail Logs, VPC Flow Logs, and Route 53 resolver query logs are the basic logging
> sources to support security investigations in AWS."

Retention framing: "Customers generally have between three months to one year of logs readily
available for querying, with retention of up to seven years."

---

## 13. Known Misconfigurations and Anti-Patterns

| Anti-Pattern | Consequence | Source |
|---|---|---|
| Single-Region trail only | Blind to other Region activity; fails CloudTrail.1 | Concepts page |
| CloudTrail.6 violation (public S3 bucket) | Critical — adversary reconnaissance | Security Hub controls |
| Applying AWSCloudTrail_FullAccess broadly | Anyone can disable audit logging | Best-practices page |
| KMS key without aws:SourceArn condition | Key can be used for unintended trails | KMS key policy page |
| Disabling KMS key while encryption enabled | CloudTrail stops delivering logs | KMS key policy page |
| Old per-Region account-ID bucket policy | Log delivery fails for new Regions | S3 bucket policy page |
| Incorrect log file prefix in bucket policy | Log delivery fails | S3 bucket policy page |
| SSE-KMS-only bucket policy without AES256 | Cannot create trails with log validation | Best-practices page |
| MFA Delete + lifecycle configuration | Not supported — pick one | Best-practices page |
| Misconfigured/unreachable bucket | CloudTrail retries 30 days; charges still accrue | CloudTrail docs |
| EventBridge rule as ENABLED for read-only events | Read-only management events not matched | EventBridge docs |
| Data event Insights on event data stores | Not supported — only trails | Insights docs |

---

## 14. Unverified Items Index

Items that could not be directly confirmed from a fetched official page:

1. ⚠️ **Root-usage CloudWatch filter pattern verbatim:** confirmed conceptually but the additional-examples page did not render via WebFetch.
2. ⚠️ **SCP example JSON (cloudtrail:StopLogging / cloudtrail:DeleteTrail):** concept confirmed across multiple pages; verbatim JSON on the Organizations example-SCPs page not fetched.
3. ⚠️ **Control Tower landing zone 4.0 guardrail deprecation exact wording:** confirmed via search snippet; mandatory-controls page not fetched line-by-line.
4. ⚠️ **Highlights dashboard GA status in 2026:** last confirmed state is *preview* (Nov 2024 announcement); GA announcement not found.
5. ⚠️ **Exact current count of network activity event supported services:** GA announcement listed 5; live concepts page lists many more. No single authoritative current-total page confirmed.
6. ⚠️ **SSE-KMS vs SSE-S3 default:** two live AWS pages conflict as of 2026-08-26. See Section 5.
7. ⚠️ **"Event history is free":** stated on pricing/features pages (not fetched directly); the concepts page only states the 90-day management-event scope.

---

*Research compiled 2026-08-26. All live-fetched sources from `docs.aws.amazon.com` and `aws.amazon.com`. Review before 2027-08-26.*
