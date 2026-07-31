# AWS CloudTrail — Architecture Research Knowledge Base
**Target Edition**: AWS CloudTrail 2025
**Domain**: Audit Logging, Governance & Compliance
**Audience**: Cloud Architects and Tech Leads
**Research Date**: 2026-07-31
**Status**: Production-Ready

## Metadata

```yaml
Full_Name: "AWS CloudTrail — Audit Logging, Governance & Compliance Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "CloudTrail — Audit Logging & Governance"
Target_Edition: "AWS CloudTrail 2025"
Architecture_Context: "Enterprise governance, compliance and SecOps — centralized audit logging across multi-account AWS Organizations"
Official_Source_URL: "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-07-31"
Author: "framework-researcher subagent"
Currency_Threshold: "2027-07-31 (review after this date — re-verify pricing, Security Hub control IDs, GA states, data-event resource types)"
Source_Hierarchy: "Official AWS docs > AWS Well-Architected / Security Hub / CIS mappings > AWS Organizations integration docs > AWS blogs (<=12 mo) > reject all else"
```

> **Version Absolutism note.** This document is pinned to **AWS CloudTrail as documented in 2025**. It reflects the current baseline: **four event types** (management, data, **network activity**, Insights); **CloudTrail Lake** with One-year extendable and Seven-year retention pricing tiers; the **organization trail delegated administrator**; and the current **AWS Security Hub CSPM** control set (`CloudTrail.1`–`CloudTrail.10`). Older-edition patterns — e.g., "CloudTrail only has management + data + Insights events", global service events replicated to every Region (changed **2021-11-22**), or "SSE-S3 is fine for logs" — are treated as misinformation and corrected inline. Every claim below traces to an official AWS URL accessed **2026-07-31**.

---

## Executive Summary

**What CloudTrail is.** AWS CloudTrail is the AWS service that records **API and non-API account activity** — the identity of the caller, time, source IP, request parameters, and response elements — for actions taken through the AWS Management Console, SDKs, CLI, and by AWS services themselves. It is the foundational **audit and governance** control of any AWS environment and the primary evidence source for security investigations, change tracking, and compliance auditing. CloudTrail logs **four event types**: management events (control-plane), data events (data-plane, high-volume), **network activity events** (VPC-endpoint API calls), and Insights events (anomaly detection). By default a trail logs **management events only**. Source: [CloudTrail concepts](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html) (accessed 2026-07-31).

**What matters in the 2025 edition.** The event model is now **four types**, not three — **network activity events** let VPC-endpoint owners record AWS API calls made through their endpoints for ~60 services. **CloudTrail Lake** is the managed SQL analytics layer: immutable **event data stores (EDS)** with two pricing models — **One-year extendable retention** (up to **3,653 days / ~10 years**) and **Seven-year retention** (up to **2,557 days / ~7 years**) — that can aggregate an entire organization across Regions and ingest events from **outside AWS** via channels. Organization trails now support a **delegated administrator** so the management account does not have to own trail operations. **Global service events** (IAM, STS, CloudFront) have been recorded in the originating Region — **us-east-1** — since **2021-11-22**, which is exactly why single-Region trails are dangerous. Sources: [CloudTrail concepts](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html), [CloudTrail pricing](https://aws.amazon.com/cloudtrail/pricing/) (accessed 2026-07-31).

**The three most critical guardrails for enterprise governance.** (1) **One multi-Region organization trail** owned by the management/delegated-admin account, delivering to a **dedicated Log Archive account** that audited accounts cannot touch — member accounts can see but not alter it. (2) **Immutability + integrity** — enable **log file integrity validation** (SHA-256 + SHA-256/RSA digest files), **SSE-KMS** encryption, **S3 Block Public Access**, and **S3 Object Lock (WORM)** or **MFA Delete** so logs cannot be silently tampered with. (3) **Real-time detection** — stream to **CloudWatch Logs** (metric filters → alarms → SNS) and **EventBridge** (→ Lambda remediation), and enable **CloudTrail Insights** so a stopped trail or an anomalous API burst pages someone. These map directly to Security Hub controls `CloudTrail.1`–`CloudTrail.7`. Sources: [Security best practices](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html), [Security Hub CloudTrail controls](https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html) (accessed 2026-07-31).

---

## Cloud Architecture Glossary

```
Term: Trail
Definition: A configuration that enables delivery of CloudTrail events to an S3 bucket, with optional delivery to CloudWatch Logs and Amazon EventBridge; can encrypt with a KMS key and send SNS notifications on log delivery.
Provider Docs Section: CloudTrail concepts → Trails
Architect Usage: The durable, ongoing record. Event history (90 days) is NOT a trail and is not a permanent record.
Common Confusion: Confused with "Event history" — event history is a free 90-day view of management events; a trail is the durable pipeline.
```
```
Term: Management events (control-plane)
Definition: Records of management operations on resources — e.g. IAM AttachRolePolicy, EC2 CreateSubnet, CloudTrail CreateTrail — plus non-API events like the ConsoleLogin event.
Provider Docs Section: CloudTrail concepts → Management events
Architect Usage: Logged by default. The baseline for CIS/FSBP compliance and for detecting privilege changes and console sign-ins.
Common Confusion: Assuming management events include object reads/writes — those are DATA events, off by default.
```
```
Term: Data events (data-plane)
Definition: Records of resource operations performed on/in a resource — e.g. S3 GetObject/PutObject/DeleteObject, Lambda Invoke, DynamoDB PutItem. Often very high volume.
Provider Docs Section: CloudTrail concepts → Data events
Architect Usage: NOT logged by default; each resource type must be added explicitly via basic or advanced event selectors. Bill driver.
Common Confusion: Expecting S3 object access in a default trail — you must opt in per resource type.
```
```
Term: Network activity events
Definition: Records of AWS API calls made through a VPC endpoint from a private VPC to an AWS service, giving VPC-endpoint owners visibility into operations performed within a VPC. Supported for ~60 services (KMS, S3, EC2, Secrets Manager, etc.).
Provider Docs Section: CloudTrail concepts → Network activity events
Architect Usage: NOT logged by default; set the event source explicitly. Useful for data-perimeter / exfiltration monitoring.
Common Confusion: Confused with VPC Flow Logs — Flow Logs capture IP traffic metadata; network activity events capture the AWS API calls traversing the endpoint.
```
```
Term: Insights events
Definition: Records of unusual rates of write management API activity or unusual error rates, produced by continuously analyzing management events. An event is logged at the start and end of the anomaly.
Provider Docs Section: CloudTrail concepts → Insights events
Architect Usage: NOT logged by default; enable per trail/EDS. Detects credential misuse, runaway automation, mass deletes.
Common Confusion: Expecting Insights to cover data events by default — Insights analyzes management (write) activity; separate charges apply.
```
```
Term: Event history
Definition: A viewable, searchable, downloadable, immutable record of the past 90 days of management events in a Region — available with no trail and no charge.
Provider Docs Section: CloudTrail concepts → Event history
Architect Usage: Fast triage. NOT a permanent record and does not include data/Insights/network events.
Common Confusion: Treating it as compliance-grade retention — it is 90 days only.
```
```
Term: Organization trail
Definition: A trail created by the management account (or CloudTrail delegated administrator) that logs events for the management account and ALL member accounts in an AWS Organizations organization into the same S3 bucket / CloudWatch Logs / EventBridge.
Provider Docs Section: CloudTrail concepts → Organization trails
Architect Usage: The enterprise default. Member accounts see it (ARN) but cannot stop, delete, or modify it.
Common Confusion: Thinking each account needs its own trail — one org trail covers new accounts automatically via the service-linked role.
```
```
Term: CloudTrail Lake / event data store (EDS)
Definition: A managed lake that runs fine-grained SQL queries over immutable collections of events (EDS). Selected via advanced event selectors; can aggregate an org across Regions and ingest non-AWS events via channels. No trail required.
Provider Docs Section: CloudTrail concepts → CloudTrail Lake and event data stores
Architect Usage: Long-retention audit + investigation without standing up S3+Athena+Glue yourself. Retention up to 3,653 days.
Common Confusion: Confused with a trail — Lake is query/retention; a trail is delivery to S3/CloudWatch. They are billed separately and can coexist.
```
```
Term: Log file integrity validation
Definition: A feature that produces digitally signed digest files containing a hash of each delivered log, using SHA-256 for hashing and SHA-256 with RSA for signing, so you can prove a log was not modified, deleted, or forged.
Provider Docs Section: Security best practices → Enable CloudTrail log file integrity
Architect Usage: Mandatory for forensic admissibility. Validate with `aws cloudtrail validate-logs`.
Common Confusion: Assuming SSE-KMS encryption also gives integrity — encryption protects confidentiality; integrity validation proves tamper-evidence.
```
```
Term: Global service events
Definition: Events from AWS global services (IAM, STS, CloudFront). Since 2021-11-22 they are recorded in the Region where created — us-east-1 — and delivered to trails that include global service events.
Provider Docs Section: CloudTrail concepts → Global service events
Architect Usage: A single-Region trail NOT in us-east-1 will MISS IAM/STS/CloudFront activity. Use multi-Region trails.
Common Confusion: Believing global events land in every Region's trail — they do not; multi-Region trails solve this.
```
```
Term: Advanced event selectors
Definition: Fine-grained selectors (by field such as resources.type, eventName, readOnly) used to include/exclude data, network activity, and Insights inputs on trails and (exclusively) on event data stores.
Provider Docs Section: Logging data events → Advanced event selectors
Architect Usage: Use to scope high-volume data events (e.g. only writes, only a sensitive bucket) to control cost.
Common Confusion: Confused with basic selectors — EDS supports ONLY advanced selectors; basic selectors are trail-only.
```
```
Term: AWSServiceRoleForCloudTrail
Definition: The service-linked role CloudTrail creates when you make an organization trail; it performs logging tasks in member accounts and is added/removed automatically as accounts join/leave the org.
Provider Docs Section: Creating a trail for an organization → service-linked role
Architect Usage: Do not delete it in member accounts; it is required for org logging.
Common Confusion: Treating it as a customer-managed role — it is service-linked and managed by CloudTrail.
```

---

## 1. Framework Pillars (AWS Well-Architected)

CloudTrail is primarily a **Security** and **Operational Excellence** control but touches every pillar.

```
Pillar: Security
How CloudTrail contributes: CloudTrail is the authoritative audit log ("who did what, when, from where") underpinning detective controls, incident response, and forensic investigations. It feeds GuardDuty, Security Hub CSPM, and Detective. Integrity validation + SSE-KMS + Object Lock protect the evidence itself.
Assessment questions: SEC04 "How do you detect and investigate security events?" — CloudTrail is the canonical answer.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```
```
Pillar: Operational Excellence
How CloudTrail contributes: Provides operational visibility and change tracking; CloudTrail → CloudWatch Logs metric filters/alarms and CloudTrail → EventBridge enable automated response and operational dashboards. Supports post-incident analysis and root-cause via a queryable activity record.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudwatch-alarms-for-cloudtrail.html (accessed 2026-07-31)
```
```
Pillar: Reliability
How CloudTrail contributes: Multi-Region trails ensure continuous capture even in otherwise unused Regions; the organization trail auto-enrolls new accounts via the service-linked role so coverage does not silently degrade as the estate grows. Log file validation lets you assert positively that no gaps exist.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html (accessed 2026-07-31)
```
```
Pillar: Cost Optimization
How CloudTrail contributes: The first copy of management events is free; data/Insights/network events and Lake ingestion/query are billable. Advanced event selectors, S3 lifecycle tiering (Standard → Glacier → Deep Archive), and choosing the right Lake retention tier let you meet audit needs at controlled cost.
Source: https://aws.amazon.com/cloudtrail/pricing/ (accessed 2026-07-31)
```
```
Pillar: Performance Efficiency
How CloudTrail contributes: CloudTrail Lake offloads query performance to a managed, serverless SQL engine ($0.005/GB scanned), avoiding the need to size and tune your own Athena/Glue stack. Delivery is asynchronous and does not affect the performance of the audited services.
Source: https://aws.amazon.com/cloudtrail/pricing/ (accessed 2026-07-31)
```
```
Pillar: Sustainability
How CloudTrail contributes: Consolidating to a single organization trail (vs N per-account trails) and tiering aged logs to Glacier Deep Archive reduces duplicated storage and compute. Scoping data events with advanced selectors avoids ingesting/storing events with no audit value.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```

---

## 2. Mandatory Patterns (✅ Always Do)

### Pattern: Multi-Region trail covering all enabled Regions
```
Why: A complete record of activity requires capturing all enabled Regions; multi-Region trails also guarantee global service event logging (IAM/STS/CloudFront in us-east-1) and detect activity in otherwise-unused Regions. Pillar: Security, Reliability. Maps to Security Hub CloudTrail.1 (High) and CIS 3.1.
Provider Service: AWS CloudTrail (multi-Region trail), Amazon S3
Architecture Decision:
  All console-created trails are multi-Region. Set IsMultiRegionTrail=true, IncludeGlobalServiceEvents=true, and management events = Read AND Write. Convert legacy single-Region trails via the CLI.
Verification:
  aws cloudtrail describe-trails --query 'trailList[].{Name:Name,MultiRegion:IsMultiRegionTrail,Global:IncludeGlobalServiceEvents}'
  # Enforce continuously with AWS Config rule: multi-region-cloud-trail-enabled
Trade-offs: Slightly more management-event volume (still free for the first copy); no meaningful latency cost.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html (accessed 2026-07-31)
```

### Pattern: Organization trail via AWS Organizations (with delegated administrator)
```
Why: One org trail defines a uniform logging strategy for every current and future account; member accounts cannot stop/modify it, closing the "disable-my-own-audit" gap. Pillar: Security, Operational Excellence, Reliability.
Provider Service: AWS CloudTrail organization trail, AWS Organizations, service-linked role AWSServiceRoleForCloudTrail
Architecture Decision:
  Create the org trail from the management account (or register a delegated administrator in a security account). New accounts auto-enroll; removed accounts stop logging but retain historical logs in S3. Use a delegated admin so day-to-day trail ops live outside the management account.
Verification:
  aws cloudtrail describe-trails --query 'trailList[?IsOrganizationTrail==`true`]'
  aws cloudtrail list-trails   # member accounts can see, not modify
Trade-offs: Requires trusted access between Organizations and CloudTrail; the org trail can only be modified in its home Region by management/delegated-admin.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html (accessed 2026-07-31)
```

### Pattern: Dedicated, centralized S3 log-archive bucket in a separate account
```
Why: Integrity, completeness, and availability of logs require segregation of duties — audited principals must not control the log store. Pillar: Security. AWS explicitly recommends a separate log-archive account.
Provider Service: Amazon S3, dedicated AWS account (Log Archive), AWS Organizations
Architecture Decision:
  Create a dedicated Log Archive account, enroll it in the org, and target the org trail at a dedicated S3 bucket there. Bucket policy grants CloudTrail write with an aws:SourceArn condition; only trusted auditors get read.
Verification:
  aws s3api get-bucket-policy --bucket <log-archive-bucket>   # confirm aws:SourceArn condition present
Trade-offs: Cross-account setup complexity; one more account to govern.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```

### Pattern: Server-side encryption with SSE-KMS (customer-managed key)
```
Why: SSE-KMS adds an access-control layer (KMS key policy) over the audit logs and satisfies encryption-at-rest compliance. Pillar: Security. Maps to Security Hub CloudTrail.2 (Medium) / CIS 3.5; and CloudTrail.10 for Lake EDS.
Provider Service: AWS CloudTrail, AWS KMS (customer managed key), Amazon S3
Architecture Decision:
  Create a KMS key with a policy allowing CloudTrail to encrypt and log readers to decrypt; set the trail's KmsKeyId. For Lake, associate a customer-managed KMS key on the EDS (note: cannot be changed/removed after association).
Verification:
  aws cloudtrail get-trail --name <trail> --query 'Trail.KmsKeyId'
  # AWS Config rule: cloud-trail-encryption-enabled
Trade-offs: KMS request charges; key-policy misconfig can block delivery. If the S3 bucket policy forces SSE-KMS only, you must also allow AES256 or trail creation fails.
Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html (accessed 2026-07-31)
```

### Pattern: Log file integrity validation enabled
```
Why: Produces SHA-256 hashes and SHA-256/RSA-signed digest files, making it computationally infeasible to modify, delete, or forge logs without detection — essential for forensics and legal admissibility. Pillar: Security. Maps to Security Hub CloudTrail.4 / CIS 3.2.
Provider Service: AWS CloudTrail (LogFileValidationEnabled)
Architecture Decision:
  Set EnableLogFileValidation=true on every trail; digest files land in the same bucket. Periodically run validation as part of audit close.
Verification:
  aws cloudtrail get-trail --name <trail> --query 'Trail.LogFileValidationEnabled'
  aws cloudtrail validate-logs --trail-arn <arn> --start-time <t0> --end-time <t1>
  # AWS Config rule: cloud-trail-log-file-validation-enabled
Trade-offs: Negligible cost; digest files add tiny storage. No downside — always enable.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```

### Pattern: CloudWatch Logs integration for real-time monitoring & alarms
```
Why: S3 delivery is for durable storage/analysis; CloudWatch Logs enables real-time alerting on security-relevant events (e.g. failed ConsoleLogin, trail changes). Pillar: Operational Excellence, Security. Maps to Security Hub CloudTrail.5 / CIS 3.4.
Provider Service: AWS CloudTrail, Amazon CloudWatch Logs, CloudWatch metric filters + Alarms, Amazon SNS
Architecture Decision:
  Set CloudWatchLogsLogGroupArn on the trail. Create metric filters (e.g. root usage, IAM policy changes, StopLogging) → CloudWatch Alarms → SNS → PagerDuty/Slack.
Verification:
  aws cloudtrail get-trail --name <trail> --query 'Trail.CloudWatchLogsLogGroupArn'
  # AWS Config rule: cloud-trail-cloud-watch-logs-enabled
Trade-offs: CloudWatch Logs delivery is billed at $0.25/GB of events delivered, plus ingestion/storage; scope with selectors to control cost.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudwatch-alarms-for-cloudtrail.html (accessed 2026-07-31)
```

### Pattern: S3 server access logging on the CloudTrail bucket
```
Why: Captures every request against the log bucket itself — critical for detecting attempts to read/tamper with audit data. Pillar: Security. Maps to Security Hub CloudTrail.7 / CIS 3.6.
Provider Service: Amazon S3 server access logging (to a SEPARATE target bucket)
Architecture Decision:
  Enable server access logging on the CloudTrail bucket, delivering access records to a different bucket (never the same bucket — avoids a logging loop).
Verification:
  aws s3api get-bucket-logging --bucket <cloudtrail-bucket>
Trade-offs: Small storage cost for access logs; access logs are best-effort, not guaranteed real-time.
Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html (accessed 2026-07-31)
```

### Pattern: SNS notification on log file delivery (with SourceArn condition)
```
Why: Signals downstream consumers that a new log file is available and provides a heartbeat; the SNS topic policy must be hardened. Pillar: Operational Excellence, Security.
Provider Service: AWS CloudTrail SnsTopicName, Amazon SNS
Architecture Decision:
  Set the trail's SnsTopicName; add an aws:SourceArn (optionally aws:SourceAccount) condition to the SNS topic policy to prevent confused-deputy access.
Verification:
  aws cloudtrail get-trail --name <trail> --query 'Trail.SnsTopicName'
  aws sns get-topic-attributes --topic-arn <arn>   # confirm SourceArn condition
Trade-offs: One SNS notification per delivered log file — can be high volume; usually consumed by SQS/Lambda, not humans.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```

### Pattern: AWS Config integration for continuous compliance evaluation
```
Why: CloudTrail records what happened; AWS Config continuously evaluates whether trails stay compliant (multi-Region, encrypted, validated, shipping to CloudWatch). Pillar: Security, Operational Excellence.
Provider Service: AWS Config managed rules — multi-region-cloud-trail-enabled, cloud-trail-encryption-enabled, cloud-trail-log-file-validation-enabled, cloud-trail-cloud-watch-logs-enabled, cloudtrail-enabled
Architecture Decision:
  Deploy these Config rules org-wide (conformance pack) with a delegated Config administrator aggregating into the security account.
Verification:
  aws configservice describe-compliance-by-config-rule --config-rule-names multi-region-cloud-trail-enabled
Trade-offs: AWS Config per-evaluation charges; requires Config recorder enabled in each account.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```

### Pattern: S3 Object Lock (WORM) for immutable retention
```
Why: Object Lock enforces write-once-read-many so audit logs cannot be deleted/overwritten for a retention period, even by admins — the strongest anti-tamper control for compliance regimes (SEC/FINRA-style). Pillar: Security, Compliance.
Provider Service: Amazon S3 Object Lock (Compliance or Governance mode), S3 Versioning
Architecture Decision:
  Create the log bucket with Object Lock enabled at creation (requires versioning). Apply a default retention (Compliance mode for hard immutability). Object Lock is the recommended immutability path when you also need lifecycle tiering (MFA Delete conflicts with lifecycle — see trade-off).
Verification:
  aws s3api get-object-lock-configuration --bucket <log-archive-bucket>
Trade-offs: Compliance mode retention CANNOT be shortened by anyone, including root — plan retention carefully. Object Lock must be enabled at bucket creation.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```

### Pattern: MFA Delete on the CloudTrail S3 bucket
```
Why: Requires a second factor to change bucket versioning state or permanently delete an object version, so a compromised IAM credential alone cannot destroy logs. Pillar: Security.
Provider Service: Amazon S3 MFA Delete (requires versioning; configured by the bucket-owner root user)
Architecture Decision:
  Enable versioning + MFA Delete on the log bucket. Choose EITHER MFA Delete OR lifecycle tiering + Object Lock — MFA Delete is incompatible with lifecycle configuration.
Verification:
  aws s3api get-bucket-versioning --bucket <cloudtrail-bucket>   # MFADelete: Enabled
Trade-offs: MFA Delete can only be toggled by the root user with an MFA device (operationally heavy); and CANNOT be used with S3 lifecycle configurations. For most enterprises, S3 Object Lock is the more automatable immutability choice.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```

### Pattern: CloudTrail Lake for advanced SQL querying & long retention
```
Why: Provides serverless SQL over immutable event data stores (up to ~10 years), org-wide/multi-Region aggregation, and ingestion of non-AWS events — without operating your own S3+Athena+Glue pipeline. Pillar: Security, Performance Efficiency.
Provider Service: AWS CloudTrail Lake (event data store), advanced event selectors, optional customer-managed KMS key
Architecture Decision:
  Create an organization EDS in the security account. Choose One-year extendable retention (≤25 TB/mo workloads) or Seven-year retention (>25 TB/mo). Encrypt with a customer-managed KMS key (CloudTrail.10). Save/export query results to S3.
Verification:
  aws cloudtrail list-event-data-stores
  aws cloudtrail start-query --query-statement "SELECT eventName, count(*) FROM <eds-id> GROUP BY eventName"
Trade-offs: Ingestion $0.75/GB (CloudTrail events, one-year extendable) + $0.023/GB/mo extended storage + $0.005/GB scanned per query — billed SEPARATELY from a trail. KMS key on an EDS is immutable once set.
Source: https://aws.amazon.com/cloudtrail/pricing/ (accessed 2026-07-31)
```

---

## 3. Architectural Crossroads (⚠️ Ask First)

### Decision: Organization trail vs individual account trails
```
Options:
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Organization trail | CloudTrail org trail + Organizations | Uniform coverage, auto-enroll, tamper-resistance | Central dependency on mgmt/delegated-admin | You use AWS Organizations (nearly always) |
| Per-account trails | CloudTrail trail per account | Account autonomy, per-team ownership | Coverage drift, accounts can disable own audit | No Organizations, or strict account isolation |

Cost Profile: Comparable event volume; org trail avoids duplicated management effort. First management-event copy is free either way.
Scaling Characteristics: Org trail scales automatically to new accounts via AWSServiceRoleForCloudTrail; per-account trails require manual creation each time — coverage gaps grow with the estate.
Operational Burden: Org trail = centralized SecOps skill; per-account = every team must maintain logging correctly.
Lock-in Assessment: Both produce standard CloudTrail JSON in S3 — equal portability.
Ask The Architect: "Are all accounts in a single AWS Organization, and do you want new accounts covered automatically the moment they join?"
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html (accessed 2026-07-31)
```

### Decision: CloudTrail Lake vs S3 + Athena for querying
```
Options:
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| CloudTrail Lake | CloudTrail Lake EDS (SQL) | Zero-ops, immutable, org/multi-Region + non-AWS ingest, ≤10yr retention | Per-GB ingestion cost; Lake-specific SQL | Investigations, long retention, no data-eng team |
| S3 + Athena | S3, Amazon Athena, AWS Glue Data Catalog | Cheapest at-rest storage, open Parquet/partitioning, reuse existing lake | You build/maintain schema, partitions, tuning | You already run a data lake and want lowest storage cost |

Cost Profile: Lake ingestion $0.75/GB + $0.005/GB scanned; Athena ~$5/TB scanned over S3 you already pay for. Lake trades higher ingest cost for zero operations.
Scaling Characteristics: Lake is serverless and org-aware; Athena scales with partition hygiene you own.
Operational Burden: Lake = minimal; Athena = Glue crawlers, partition projection, query tuning.
Lock-in Assessment: Athena/S3 keeps raw JSON portable; Lake keeps data inside CloudTrail (export query results to S3 to mitigate).
Ask The Architect: "Do you have a data-engineering team to own partitioning/tuning, or do you want managed SQL and long retention out of the box?"
Source: https://aws.amazon.com/cloudtrail/pricing/ (accessed 2026-07-31)
```

### Decision: Management vs Data vs Insights (and Network activity) events
```
Options:
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Management only (default) | CloudTrail management events | Cost (first copy free), compliance baseline | No object-level visibility | Baseline governance everywhere |
| + Data events | Data events (S3/Lambda/DynamoDB via selectors) | Object-level forensics, data-exfil detection | $0.10/100k events — high volume cost | Sensitive data stores, regulated workloads |
| + Insights | CloudTrail Insights | Anomaly detection on write/error rates | $0.35/100k mgmt events analyzed | Detecting credential misuse / runaway automation |
| + Network activity | Network activity events | VPC-endpoint API visibility (data perimeter) | $0.10/100k events | Strict egress/exfiltration monitoring |

Cost Profile: Management (1st copy) free; additional copies $2.00/100k; data & network $0.10/100k; Insights $0.35/100k (mgmt) or $0.03/100k (data).
Scaling Characteristics: Data events can dwarf management-event volume by orders of magnitude on busy S3/Lambda — always scope with advanced selectors (e.g. writes only, one bucket).
Operational Burden: Selectors require careful curation to avoid bill shock and noise.
Lock-in Assessment: Same JSON format regardless of type — no incremental lock-in.
Ask The Architect: "Which specific S3 buckets / Lambda functions / DynamoDB tables hold sensitive data and justify per-object logging, and do you need anomaly detection (Insights)?"
Source: https://aws.amazon.com/cloudtrail/pricing/ (accessed 2026-07-31)
```

### Decision: Multi-Region vs single-Region trail
```
Options:
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Multi-Region (recommended) | CloudTrail multi-Region trail | Full coverage + global service events (IAM/STS/CloudFront) | Marginally more volume | Essentially always |
| Single-Region | CloudTrail single-Region trail (CLI only) | Narrow scope | MISSES global service events unless home = us-east-1; blind to other Regions | Rare, tightly scoped edge cases |

Cost Profile: Difference is negligible (management first copy free); risk of a single-Region miss dwarfs any saving.
Scaling Characteristics: Multi-Region auto-covers newly enabled/opt-in Regions.
Operational Burden: Multi-Region = one config; single-Region = per-Region sprawl and audit gaps.
Lock-in Assessment: None.
Ask The Architect: "Is there ANY reason not to use multi-Region? (Since 2021-11-22 IAM/STS/CloudFront log to us-east-1, a single-Region trail elsewhere silently loses them.)"
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html (accessed 2026-07-31)
```

### Decision: CloudTrail vs AWS Config vs Security Hub (overlapping concerns)
```
Options:
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| CloudTrail | CloudTrail | "Who did what, when" — API activity record | Not a config-state or posture tool | Audit trail, forensics, IR |
| AWS Config | AWS Config | Resource configuration state + drift over time; compliance rules | Not an API-call audit log | Config compliance & change history |
| Security Hub CSPM | AWS Security Hub | Aggregated posture findings vs FSBP/CIS/NIST/PCI | Depends on CloudTrail+Config as inputs | Central posture management & scoring |

Cost Profile: Three separate services — Config per-evaluation, Security Hub per-check + finding ingestion, CloudTrail per event model above. They complement, not replace, each other.
Scaling Characteristics: All are org-aware with delegated administrators; deploy via conformance packs / central configuration.
Operational Burden: Security Hub sits on top and consolidates; CloudTrail + Config are the evidence sources beneath it.
Lock-in Assessment: All AWS-native; findings exportable via EventBridge/Security Lake (OCSF).
Ask The Architect: "Do you need the API activity record (CloudTrail), the configuration-state history (Config), the posture score (Security Hub) — or, correctly, all three composed together?"
Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html (accessed 2026-07-31)
```

### Decision: Centralized vs decentralized log-account architecture
```
Options:
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Centralized Log Archive account | Dedicated account + org trail + central S3/Lake | Segregation of duties, tamper resistance, single audit surface | Cross-account setup; central bucket policy rigor | Enterprise / regulated (AWS-recommended) |
| Decentralized (logs in each account) | Per-account S3 buckets | Local autonomy | Audited principals can tamper with own logs; fragmented audit | Almost never for governance |

Cost Profile: Centralized enables one lifecycle/immutability policy and dedupe; decentralized multiplies buckets and drift.
Scaling Characteristics: Centralized + org trail auto-scales to new accounts; decentralized requires per-account effort.
Operational Burden: Centralized needs a strong Log Archive bucket policy (aws:SourceArn) and least-privilege reader access.
Lock-in Assessment: None — standard S3/JSON either way.
Ask The Architect: "Can we stand up a dedicated Log Archive account that no workload team can access, per AWS's separated-log-account guidance?"
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```

---

## 4. Never-Do Anti-Patterns (🚫)

### Anti-Pattern: Disabling CloudTrail / leaving Regions without trail coverage
```
Why: No audit trail = no forensics, no compliance evidence, blind to attacker activity. WAF Security pillar (detective controls). Violates Security Hub CloudTrail.1/.3 and CIS 3.1.
Risk Level: CRITICAL
Blast Radius: Entire account/org — every action becomes unauditable.
❌ Wrong:
  No CloudTrail trail, OR a single-Region trail in eu-west-1 only (misses all other Regions AND global IAM/STS/CloudFront events in us-east-1).
✅ Correct:
  One multi-Region AWS CloudTrail organization trail (IsMultiRegionTrail=true, IncludeGlobalServiceEvents=true) covering all enabled Regions in every account.
Detection:
  aws cloudtrail describe-trails --query 'trailList[?IsMultiRegionTrail==`true`]'
  # AWS Config: multi-region-cloud-trail-enabled ; Security Hub: CloudTrail.1
Impact: Compliance violation + undetectable breach.
Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html (accessed 2026-07-31)
```

### Anti-Pattern: Storing logs in the same account being audited (no cross-account bucket)
```
Why: Audited principals can then read/alter/delete the evidence of their own actions — breaks segregation of duties. WAF Security pillar.
Risk Level: HIGH
Blast Radius: All audit evidence for that account.
❌ Wrong:
  Org/member accounts writing CloudTrail logs to an S3 bucket in the SAME account where workloads and admins operate.
✅ Correct:
  A dedicated Log Archive AWS account owning the S3 bucket; the org trail delivers there; only trusted auditors have read.
Detection:
  Compare the trail's S3 bucket owner account vs the audited account IDs.
Impact: Log tampering, repudiation, compliance violation.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```

### Anti-Pattern: CloudTrail S3 bucket without Block Public Access
```
Why: Public log content lets adversaries mine your environment for weaknesses. WAF Security. Security Hub CloudTrail.6 (Critical) / CIS 3.3.
Risk Level: CRITICAL
Blast Radius: All historical logs in the bucket → intelligence for further attack.
❌ Wrong:
  CloudTrail S3 bucket with Block Public Access disabled or a public bucket policy/ACL.
✅ Correct:
  Amazon S3 Block Public Access enabled (all four settings) on the bucket AND at the account level via SCP; least-privilege bucket policy with aws:SourceArn.
Detection:
  aws s3api get-public-access-block --bucket <cloudtrail-bucket>
  # Security Hub: CloudTrail.6
Impact: Data breach / reconnaissance exposure.
Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html (accessed 2026-07-31)
```

### Anti-Pattern: No log file integrity validation
```
Why: Without signed digests you cannot prove logs were not modified/deleted — forensic evidence becomes inadmissible. WAF Security. Security Hub CloudTrail.4 / CIS 3.2.
Risk Level: HIGH
Blast Radius: Evidentiary value of the entire log set.
❌ Wrong:
  Trail created with EnableLogFileValidation=false (no digest files).
✅ Correct:
  EnableLogFileValidation=true on every trail; validate with aws cloudtrail validate-logs during audits.
Detection:
  aws cloudtrail get-trail --name <trail> --query 'Trail.LogFileValidationEnabled'
  # AWS Config: cloud-trail-log-file-validation-enabled
Impact: Compliance violation; unprovable/forgeable evidence.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```

### Anti-Pattern: Logging only management events for sensitive S3/Lambda/DynamoDB
```
Why: Management events do NOT capture object-level GetObject/PutObject/DeleteObject, Lambda Invoke, or DynamoDB item ops — you are blind to data access/exfiltration on sensitive stores. WAF Security.
Risk Level: HIGH
Blast Radius: Sensitive data stores — no record of who read/exfiltrated data.
❌ Wrong:
  Trail with default settings only (management events); no data event selectors for the sensitive S3 bucket.
✅ Correct:
  Add advanced event selectors for AWS::S3::Object (scoped to the sensitive bucket), AWS::Lambda::Function, AWS::DynamoDB::Table — scoped to writes/reads as required.
Detection:
  aws cloudtrail get-event-selectors --trail-name <trail>
Impact: Data breach undetected; compliance gap for regulated data.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html (accessed 2026-07-31)
```

### Anti-Pattern: No CloudTrail Insights for unusual API activity
```
Why: Without Insights, sudden bursts of write activity or error spikes (e.g. mass DeleteBucket, credential misuse) go unnoticed until damage is done. WAF Security/Operational Excellence.
Risk Level: MEDIUM
Blast Radius: Time-to-detect for anomalous automation/credential abuse.
❌ Wrong:
  Insights disabled everywhere; anomalies only found in retrospective queries.
✅ Correct:
  Enable CloudTrail Insights (write management API rate + error rate) on the org trail or an EDS; route Insights events to alerting.
Detection:
  aws cloudtrail get-insight-selectors --trail-name <trail>
Impact: Delayed breach detection / larger blast radius.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html (accessed 2026-07-31)
```

### Anti-Pattern: CloudTrail S3 bucket writable/accessible by audited accounts
```
Why: If audited accounts can write/delete in the log bucket, they can tamper with or destroy evidence — defeats the audit. WAF Security.
Risk Level: CRITICAL
Blast Radius: Integrity of the entire centralized log store.
❌ Wrong:
  Log Archive bucket policy granting audited member accounts s3:DeleteObject / s3:PutBucketPolicy, or broad cross-account write.
✅ Correct:
  Bucket policy allows only the CloudTrail service principal to write (with aws:SourceArn condition); no audited principal has delete/overwrite; combine with S3 Object Lock.
Detection:
  aws s3api get-bucket-policy --bucket <log-archive-bucket>   # review principals/actions
Impact: Log tampering, repudiation, compliance violation.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```

### Anti-Pattern: No alerting when a trail is stopped or modified
```
Why: An attacker's first move is often StopLogging / DeleteTrail / UpdateTrail; without an alarm the audit goes dark silently. WAF Security/Operational Excellence.
Risk Level: HIGH
Blast Radius: All subsequent activity becomes invisible.
❌ Wrong:
  No CloudWatch metric filter/EventBridge rule on StopLogging/UpdateTrail/DeleteTrail.
✅ Correct:
  CloudTrail → CloudWatch Logs metric filter on eventName in {StopLogging,UpdateTrail,DeleteTrail} → CloudWatch Alarm → SNS; OR EventBridge rule → Lambda auto-remediation (restart logging).
Detection:
  Confirm metric filters/alarms exist; test by stopping a non-prod trail and verifying the page fires.
Impact: Undetected audit blackout during an incident.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudwatch-alarms-for-cloudtrail.html (accessed 2026-07-31)
```

### Anti-Pattern: No immutability control (missing MFA Delete / Object Lock) on the log bucket
```
Why: Without WORM/MFA Delete a compromised credential can permanently delete log object versions. WAF Security/Compliance.
Risk Level: HIGH
Blast Radius: Permanent, irreversible loss of audit history.
❌ Wrong:
  Log bucket with versioning off and no Object Lock and no MFA Delete — a single DeleteObject destroys evidence.
✅ Correct:
  S3 Object Lock (Compliance mode) with a retention period, OR versioning + MFA Delete (note: MFA Delete is incompatible with lifecycle configs — prefer Object Lock when you also tier to Glacier).
Detection:
  aws s3api get-object-lock-configuration --bucket <bucket>
  aws s3api get-bucket-versioning --bucket <bucket>   # MFADelete status
Impact: Irrecoverable evidence loss; compliance violation.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
```

---

## Additional Research Areas (detail)

**Data events — when to enable & cost.** Data events are off by default and must be added per resource type via basic or advanced event selectors (EDS supports advanced selectors only). Common high-value targets: `AWS::S3::Object` (object-level Get/Put/Delete), `AWS::Lambda::Function` (Invoke), `AWS::DynamoDB::Table` (item ops; note streams are logged too unless filtered by eventName). Volume can be orders of magnitude above management events, so scope by bucket/function and by read vs write. Price: **$0.10 per 100,000 data events** delivered ($0.03 per 100,000 for data-event aggregations analyzed). Sources: [concepts](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html), [pricing](https://aws.amazon.com/cloudtrail/pricing/) (accessed 2026-07-31).

**Insights.** Analyzes management (write) API rate and error rate; logs a start and an end event per anomaly. Enabled per trail/EDS (`PutInsightSelectors`). Billed separately for trails vs EDS: **$0.35 per 100,000 management events analyzed**, **$0.03 per 100,000 data events analyzed**. Source: [pricing](https://aws.amazon.com/cloudtrail/pricing/) (accessed 2026-07-31).

**CloudTrail Lake.** SQL over immutable event data stores; org/multi-Region aggregation; non-AWS ingestion via channels (`PutAuditEvents`, resource type `AWS::CloudTrail::Channel`). Retention: **One-year extendable** up to **3,653 days (~10 yr)**; **Seven-year** up to **2,557 days (~7 yr)**. Query results viewable 7 days; exportable to S3. Pricing (one-year extendable): ingestion **$0.75/GB** (CloudTrail events) / **$0.50/GB** (other sources), extended storage **$0.023/GB/month**, query **$0.005/GB scanned**. Seven-year tier is volume-tiered ($2.5/$1/$0.50 per GB) plus $0.005/GB scanned. New-customer trial: 30 days / 5 GB. Sources: [concepts](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html), [pricing](https://aws.amazon.com/cloudtrail/pricing/) (accessed 2026-07-31).

**Alerting integration pattern.** CloudTrail → CloudWatch Logs → metric filter (e.g. `StopLogging`, root usage, IAM policy change) → CloudWatch Alarm → SNS → PagerDuty/Slack. CloudWatch Logs delivery from CloudTrail is **$0.25/GB delivered** plus standard CloudWatch ingest/storage. Source: [CloudWatch alarms for CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudwatch-alarms-for-cloudtrail.html) (accessed 2026-07-31).

**Automated remediation pattern.** CloudTrail delivers to Amazon EventBridge (per-Region event bus) → rule matches sensitive API → Lambda remediation (e.g. re-enable a stopped trail, quarantine an IAM principal). Source: [concepts → Trails/EventBridge](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html) (accessed 2026-07-31).

**Organizations delegation.** The management account can register a **CloudTrail delegated administrator** (a member account, typically the security account) to create/manage organization trails and event data stores. Org trails auto-enroll new accounts via `AWSServiceRoleForCloudTrail`; member accounts can view but not stop/delete/modify the org trail. If the management account is later removed as management account, its org trail becomes a non-organization trail. Source: [Creating a trail for an organization](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html) (accessed 2026-07-31).

**S3 lifecycle tiering.** CloudTrail stores logs indefinitely by default. Use S3 lifecycle rules to tier Standard → Glacier / Glacier Deep Archive or expire after N days per retention policy. Caveat: **lifecycle configuration is NOT supported on MFA-Delete-enabled buckets** — for tiered, immutable retention use **S3 Object Lock** instead of MFA Delete. Source: [Security best practices → object lifecycle management](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html) (accessed 2026-07-31).

**Security Hub FSBP / CIS CloudTrail controls (2025).**

| Control | Title (abbrev.) | Severity | CIS AWS Foundations mapping |
|---|---|---|---|
| CloudTrail.1 | ≥1 multi-Region trail with read+write management events | High | v1.2.0/2.1, v1.4.0/3.1, v3.0.0/3.1, v5.0.0/3.1 |
| CloudTrail.2 | Encryption at rest enabled (SSE-KMS) | Medium | v1.2.0/2.7, v1.4.0/3.7, v3.0.0/3.5, v5.0.0/3.5 |
| CloudTrail.3 | At least one trail enabled | High | (NIST/PCI) |
| CloudTrail.4 | Log file validation enabled | Low | v1.2.0/2.2, v1.4.0/3.2, v3.0.0/3.2, v5.0.0/3.2 |
| CloudTrail.5 | Integrated with CloudWatch Logs | Medium | v1.2.0/2.4, v1.4.0/3.4, v5.0.0/3.4 |
| CloudTrail.6 | Log S3 bucket not publicly accessible | Critical | v1.2.0/2.3, v1.4.0/3.3 |
| CloudTrail.7 | S3 bucket access logging enabled | Low | v1.2.0/2.6, v1.4.0/3.6, v3.0.0/3.4 |
| CloudTrail.9 | Trails should be tagged | Low | — |
| CloudTrail.10 | Lake EDS encrypted with customer-managed KMS key | Medium | — |

Source: [Security Hub CloudTrail controls](https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html) (accessed 2026-07-31).

---

## 5. Service Equivalence Map

> Cross-provider mapping to aid architects choosing/porting an audit-logging design. AWS names verified from CloudTrail docs (2026-07-31); GCP/Azure/OCI names reflect each provider's canonical audit service and should be re-verified against that provider's current docs.

| Service class | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|---|---|---|---|---|
| API/audit logging service | **AWS CloudTrail** | Cloud Audit Logs (Admin Activity / Data Access) | Azure Monitor **Activity Log** + Microsoft Entra audit logs | **OCI Audit** service |
| Log storage | Amazon **S3** (+ CloudTrail Lake EDS) | Cloud Logging log buckets / Cloud Storage | Log Analytics workspace / Storage Account | OCI **Logging** / Object Storage |
| Log analysis / querying | **CloudTrail Lake** (SQL) / Amazon **Athena** over S3 | Log Analytics (Logs Explorer) / BigQuery export | Log Analytics **KQL** | OCI **Logging Analytics** |
| Real-time alerting on API activity | CloudWatch Logs metric filters + **Alarms** / **EventBridge** → SNS | Cloud Monitoring alerting + log-based metrics / Eventarc | Azure Monitor **Alerts** / Event Grid | OCI **Monitoring** Alarms / Events service |
| Compliance / governance integration | **AWS Security Hub** (CSPM) + **AWS Config** | Security Command Center | Microsoft Defender for Cloud + Azure Policy | OCI **Cloud Guard** |
| Immutable log storage (WORM) | S3 **Object Lock** / immutable CloudTrail Lake EDS | Cloud Storage **Bucket Lock** (retention policy) | Azure Blob **immutable storage** (WORM) | OCI Object Storage **retention rules** |

---

## 6. Source Bibliography

```
[1] CloudTrail concepts (events, trails, org trails, Lake, Insights, global service events) — AWS, https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html, Accessed: 2026-07-31
[2] Security best practices in AWS CloudTrail — AWS, https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html, Accessed: 2026-07-31
[3] AWS CloudTrail Pricing — AWS, https://aws.amazon.com/cloudtrail/pricing/, Accessed: 2026-07-31
[4] Security Hub CSPM controls for AWS CloudTrail (CloudTrail.1–.10 + CIS/NIST/PCI mappings) — AWS, https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html, Accessed: 2026-07-31
[5] Creating a trail for an organization (org trails, delegated administrator, service-linked role) — AWS, https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html, Accessed: 2026-07-31
[6] CloudWatch alarms / CloudWatch Logs integration for CloudTrail — AWS, https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudwatch-alarms-for-cloudtrail.html, Accessed: 2026-07-31
[7] Logging data events with CloudTrail (selectors) — AWS, https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-data-events-with-cloudtrail.html, Accessed: 2026-07-31
[8] AWS CloudTrail User Guide (landing) — AWS, https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html, Accessed: 2026-07-31
[9] CloudTrail delegated administrator — AWS, https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-delegated-administrator.html, Accessed: 2026-07-31
```

> All sources are AWS "latest" living documentation or the current pricing page, verified current as of the research date. None are >12 months stale. Re-verify against the Currency_Threshold (2027-07-31): pricing figures, Security Hub control IDs/severities, CIS benchmark versions, and the data-event resource-type list evolve frequently.

---

## Scenario Coverage

**Standard case — enterprise multi-account governance.** One **multi-Region organization trail** created via a **CloudTrail delegated administrator** in the security account, delivering to a **dedicated Log Archive account** S3 bucket with **SSE-KMS**, **log file validation**, **Block Public Access**, **Object Lock (Compliance mode)**, and **S3 access logging**. Stream to **CloudWatch Logs** (metric filters/alarms on `StopLogging`, root usage, IAM changes) and **EventBridge** (Lambda remediation). Enable **Insights**. Add **data event selectors** only for sensitive S3/Lambda/DynamoDB. Long retention/investigation via a **CloudTrail Lake** org event data store. Enforce with **AWS Config** rules + **Security Hub** CloudTrail.1–.10. Key decisions: which resources justify data events; Lake retention tier; MFA Delete vs Object Lock.

**Edge case — opt-in Regions & partitions.** A multi-Region org trail whose home Region is an **opt-in Region** only receives activity from member accounts that opted into that Region; and a trail in one partition does not cover another partition. Approach: keep the org trail's home Region a default-enabled Region (commonly us-east-1 to co-locate global service events), and create a separate multi-Region org trail per partition.

**Anti-pattern case — "just turn on the default trail in one Region to save cost."** Refuse/flag: a single-Region trail outside us-east-1 silently loses IAM/STS/CloudFront global service events (behavior since 2021-11-22) and all other Regions, failing CloudTrail.1/CIS 3.1. Clarify: confirm the requirement is truly single-Region and that global-service and cross-Region blindness is acceptable — it almost never is.
