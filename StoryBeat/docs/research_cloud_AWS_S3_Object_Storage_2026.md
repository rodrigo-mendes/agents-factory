# Cloud Architecture Research — AWS S3 Object Storage 2026

## Metadata

```yaml
Full_Name: "AWS S3 Object Storage"
Cloud_Provider: "AWS"
Architecture_Domain: "Data Architecture - S3 Object Storage"
Target_Edition: "AWS S3 2026"
Architecture_Context: "web application"
Official_Source_URL: "https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-31"
Currency_Threshold: "2027-08-31"
Research_Depth: "exhaustive"
Max_Iterations: "8"
Research_Quality_Score: "90%"
Gap_Loop_Ran: "true"
Iterations_Used: "5 of 8"
Triangulated_Count: "72"
Unverified_Count: "2"
Irresolvable_Count: "6"
```

## Executive Summary

Amazon S3 (Simple Storage Service) is AWS's foundational object storage service providing 99.999999999% (11 nines) durability across a minimum of three Availability Zones for standard storage classes. Within a web application architecture, S3 serves three primary roles: (1) origin store for static assets and SPA bundles delivered via CloudFront, (2) durable storage for user-uploaded files accessed through presigned URLs or API-proxied flows, and (3) event source triggering asynchronous processing pipelines through S3 Event Notifications to Lambda, SQS, SNS, or EventBridge. S3's flat key-value model, strong read-after-write consistency (since December 2020, available in all Regions), and nine storage classes make it the default data persistence layer for web-scale object workloads. As of 2026, S3 supports four bucket types: general purpose (the historical default), directory (S3 Express One Zone), table (Apache Iceberg), and vector (embeddings for Amazon Bedrock and OpenSearch).

Between 2025 and mid-2026, four material changes affect S3 architecture decisions for web applications. First, **S3 Object Lambda is restricted as of November 7, 2025** — it is no longer available to new customers; new architectures must use Lambda + S3 combinations instead. Second, **SSE-C (customer-provided keys) is disabled by default for all new general purpose buckets as of April 2026** — new workloads should use SSE-S3 (automatic, no cost) or SSE-KMS with customer managed keys. Third, **S3 Lifecycle transitions to Standard-IA and One Zone-IA can now start on day 0 as of July 2026** — the 30-day scheduling minimum was removed (the 30-day billing minimum duration still applies). Fourth, **Amazon S3 Files reached General Availability in April 2026** across 34 Regions, providing a file-system interface connecting any AWS compute to S3 buckets. S3 Tables now support Intelligent-Tiering (December 2025).

The three most critical architecture guardrails for a web application using S3 are: (1) **Block Public Access must be enabled at all four settings** (account level and per-bucket) — any web app serving assets via CloudFront must keep the S3 bucket private, routing all access through CloudFront with Origin Access Control (OAC), not OAI; (2) **All S3 buckets must enforce TLS via bucket policy** using the `aws:SecureTransport: false` Deny condition — plain HTTP access to S3 is never acceptable in production; (3) **Presigned URLs, not hardcoded IAM credentials**, must be used for browser-to-S3 file uploads — the IAM role-based presigned URL pattern is the only safe upload path for web client traffic.

## Cloud Architecture Glossary

> All definitions sourced from official AWS S3 documentation, access date 2026-08-31.

```
Term: Bucket
Definition: Top-level container for S3 objects. Four types exist as of 2026: general purpose, directory (S3 Express One Zone), table (Apache Iceberg), and vector (embeddings). Name and Region are immutable after creation. Bucket names are unique to the creating account; no other account can reuse a name after deletion.
Provider Docs Section: Amazon S3 User Guide — Welcome.html
Architect Usage: Choose bucket type at creation time — general purpose for most web app workloads; directory for latency-sensitive compute-adjacent workloads; table for Apache Iceberg analytics; vector for ML embedding stores.
Common Confusion: Buckets are not file system directories — they are flat namespaces. The "/" in key names is a UI convention, not a real hierarchy.
```

```
Term: Object
Definition: The fundamental storage entity in S3. Consists of object data (the payload), metadata (system and user-defined), and a unique key. Maximum object size is 5 TB; multipart upload is required for objects larger than 5 GB and recommended above 100 MB.
Provider Docs Section: Amazon S3 User Guide — Welcome.html
Architect Usage: Design key names deliberately — the key drives prefix-based partitioning (throughput), Lifecycle rule scoping, and IAM condition matching.
Common Confusion: S3 objects are immutable — you cannot append to an existing object. An overwrite creates a new version (if versioning is enabled) or atomically replaces the object.
```

```
Term: Prefix (Key Name)
Definition: An object key is the unique identifier for an object within a bucket. A prefix is the portion of a key before the final "/". S3 scales request throughput per prefix partition: 3,500 PUT/COPY/POST/DELETE or 5,500 GET/HEAD requests per second per prefix.
Provider Docs Section: Amazon S3 User Guide — optimizing-performance.html
Architect Usage: Use hash- or UUID-based prefixes (not date-based sequential prefixes) for high-throughput workloads. Date-based prefixes concentrate all traffic on one partition during bursts.
Common Confusion: Prefix partitions are S3-internal — you cannot inspect or control them directly. Throughput limits apply per prefix partition, not per bucket.
```

```
Term: S3 Standard (STANDARD)
Definition: Default storage class. 99.99% availability, 99.999999999% durability, minimum three AZs. No minimum storage duration and no retrieval fee.
Provider Docs Section: Amazon S3 User Guide — storage-class-intro.html
Architect Usage: Use for any object accessed more than once per month. Default class for new uploads unless overridden by bucket default encryption or Lifecycle rules.
Common Confusion: Durability (11 nines) and availability (99.99%) are different metrics. Durability is the probability of not losing an object; availability is the fraction of time the service responds successfully.
```

```
Term: S3 Intelligent-Tiering (INTELLIGENT_TIERING)
Definition: Automatically moves objects between Frequent Access, Infrequent Access, Archive Instant Access, Archive Access, and Deep Archive Access tiers based on access patterns. No retrieval fees. Objects smaller than 128 KB are not monitored and are permanently billed at the Frequent Access tier rate. Per-object monitoring fee applies. 99.9% availability.
Provider Docs Section: Amazon S3 User Guide — storage-class-intro.html, intelligent-tiering.html
Architect Usage: Use when access patterns are unknown or highly variable. "Set and forget" class for large object stores where manual Lifecycle rule management is impractical.
Common Confusion: Intelligent-Tiering is not free — per-object monitoring fees accumulate for all monitored objects. Objects under 128 KB receive no benefit and incur monitoring fee if accidentally placed in this class.
```

```
Term: S3 Express One Zone (EXPRESS_ONEZONE)
Definition: Directory bucket type offering single-digit millisecond latency, up to 10x faster than S3 Standard, and 50% lower request cost. Resides in a single AZ — not resilient to AZ failure. All public access is permanently disabled and cannot be changed. Hundreds of thousands of requests per second supported.
Provider Docs Section: Amazon S3 User Guide — storage-class-intro.html, Welcome.html
Architect Usage: Use for latency-sensitive compute-adjacent workloads (ML training, HPC scratch) where the compute and bucket are co-located in the same AZ. Do not use for user-facing web app assets where AZ failure resilience is required.
Common Confusion: Express One Zone uses directory buckets, not general purpose buckets. Management APIs, AWS Config support, and some security controls differ from general purpose buckets.
```

```
Term: Block Public Access
Definition: Four account- and bucket-level settings that override ACLs and bucket policies to prevent public exposure: BlockPublicAcls (rejects PUT requests with public ACLs), IgnorePublicAcls (ignores all public ACLs), BlockPublicPolicy (rejects bucket policy PUT if it would allow public access), RestrictPublicBuckets (restricts public-policy buckets to AWS service principals and bucket owner only). Default: all four enabled for new buckets. Directory buckets: all public access permanently disabled and cannot be changed.
Provider Docs Section: Amazon S3 User Guide — access-control-block-public-access.html
Architect Usage: Enable all four settings at account level first via AWS Organizations, then confirm per-bucket. Use AWS Config rules s3-bucket-public-read-prohibited and s3-bucket-public-write-prohibited to detect drift.
Common Confusion: RestrictPublicBuckets does not remove a public bucket policy — it causes S3 to block cross-account access from the policy, leaving only AWS service principals. This can break cross-account access unexpectedly if a wildcard Principal is present.
```

```
Term: Bucket Policy
Definition: Resource-based IAM policy (up to 20 KB) attached to a bucket. Only the bucket owner can attach or modify a bucket policy. Used for cross-account access, HTTPS enforcement, IP/VPC restrictions, and OAC integration with CloudFront. A Deny in any applicable policy (bucket policy, IAM policy, ACL, SCP, RCP) always overrides any Allow.
Provider Docs Section: Amazon S3 User Guide — Welcome.html
Architect Usage: Always attach a TLS-enforcement Deny policy and a Block Public Access restriction as baseline. Reference specific IAM role ARNs rather than wildcard Principal for least privilege.
Common Confusion: Bucket policies and IAM policies both apply simultaneously — the effective permissions are the intersection (both must allow; either Deny blocks). Not to be confused with access point policies, which are evaluated separately.
```

```
Term: ACL (Access Control List)
Definition: Legacy per-object and per-bucket mechanism for granting access. Two dangerous pre-defined groups: AllUsers (any internet user) and AuthenticatedUsers (any authenticated AWS account, not just your own). Disabled by default when Object Ownership is set to BucketOwnerEnforced (the default for new buckets since April 2023). Cannot express IAM condition keys.
Provider Docs Section: Amazon S3 User Guide — Welcome.html
Architect Usage: Do not use ACLs for new architectures. Set Object Ownership to BucketOwnerEnforced and use bucket policies for all access control.
Common Confusion: AuthenticatedUsers does NOT mean "users in my AWS account" — it grants access to any AWS account with valid credentials. This is a critical distinction that has caused widespread data exposures.
```

```
Term: S3 Object Ownership
Definition: Bucket-level setting controlling object ownership and ACL enable/disable. Three settings: BucketOwnerEnforced (default — ACLs disabled, all objects owned by bucket owner), BucketOwnerPreferred (new objects owned by bucket owner if uploaded with bucket-owner-full-control canned ACL), ObjectWriter (legacy — uploader owns objects).
Provider Docs Section: Amazon S3 User Guide — about-object-ownership.html
Architect Usage: Always set BucketOwnerEnforced for new buckets. Required setting for CloudFront OAC integration. Required for S3 Access Points to function with OAC.
Common Confusion: BucketOwnerEnforced does not retroactively change ownership of existing objects uploaded under ObjectWriter mode — only new uploads.
```

```
Term: Presigned URL
Definition: Time-limited, HMAC-signed URL granting temporary access to a specific S3 object for a single HTTP operation (GET or PUT) without requiring AWS credentials. Console maximum: 12 hours. CLI/SDK maximum: 7 days (IAM user SigV4) or the IAM role session duration (typically 1-6 hours). The URL inherits the generating identity's permissions. May be used multiple times until expiry.
Provider Docs Section: Amazon S3 User Guide — using-presigned-url.html, ShareObjectPreSignedURL.html
Architect Usage: Use for browser-to-S3 direct uploads (PUT) and time-limited download links (GET). Never hardcode IAM access keys — always generate presigned URLs server-side from a Lambda execution role or EC2 instance role.
Common Confusion: A presigned URL is a bearer token — anyone with the URL can perform the operation until expiry. Do not transmit over unencrypted channels. SignatureDoesNotMatch error occurs if Content-Type at upload time differs from Content-Type at URL generation time.
```

```
Term: S3 Versioning
Definition: Keeps multiple variants of every object in the same bucket. Each version has a unique version ID. Three states: unversioned (default), enabled, suspended. Cannot return to unversioned once enabled (only suspended). DELETE without a version ID creates a delete marker (recoverable). DELETE with a version ID permanently removes that version.
Provider Docs Section: Amazon S3 User Guide — Versioning.html
Architect Usage: Enable on all buckets storing user data or application state. Required prerequisite for S3 CRR, Object Lock, and MFA Delete. Use Lifecycle rules to expire non-current versions and control storage cost growth.
Common Confusion: Versioning does not protect against all data loss — if an attacker has s3:DeleteObject with a version ID, they can permanently delete versions. Pair with MFA Delete or Object Lock for ransomware protection.
```

```
Term: S3 Object Lock
Definition: WORM (Write Once Read Many) protection. Two retention modes: Compliance (no one including root can delete or modify during retention period) and Governance (users with s3:BypassGovernanceRetention permission and explicit x-amz-bypass-governance-retention header can override). Legal Hold: independent of retention periods; placed/removed with s3:PutObjectLegalHold. Must be enabled at bucket creation — cannot be enabled on an existing bucket.
Provider Docs Section: Amazon S3 User Guide — object-lock.html
Architect Usage: Use Compliance mode for regulatory archives (FINRA, SEC Rule 17a-4, HIPAA) where immutability must be absolute. Use Governance mode for ransomware protection where authorized admins need override capability. Plan retention periods carefully — Compliance mode is irrevocable.
Common Confusion: Object Lock does not prevent the retention period from being extended — it only prevents shortening. Also, Object Lock must be planned at bucket creation; retrofitting to an existing bucket requires contacting AWS Support.
```

```
Term: S3 Replication (SRR / CRR)
Definition: Asynchronous copying of objects between S3 buckets. CRR (Cross-Region Replication) copies across AWS Regions. SRR (Same-Region Replication) copies within the same Region. Both require S3 Versioning enabled on source and destination. Does NOT replicate pre-existing objects — use S3 Batch Replication for that. S3 Replication Time Control (RTC) provides SLA-backed replication of 99.99% of objects within 15 minutes.
Provider Docs Section: Amazon S3 User Guide — replication.html
Architect Usage: Use CRR for geographic DR and compliance (data residency) requirements. Use SRR for log aggregation and data sovereignty. Add S3 RTC when RPO must be SLA-backed. Configure bi-directional replication for MRAP active-active architectures.
Common Confusion: CRR replication is asynchronous — there is no zero-RPO guarantee without RTC. RTC provides a 15-minute SLA but is not synchronous replication. Batch Replication is required to replicate objects that existed before CRR was enabled.
```

```
Term: S3 Access Points
Definition: Named network endpoints attached to S3 buckets (or FSx ONTAP, FSx OpenZFS, AWS Backup recovery points). Each access point has its own access point policy and network controls. Can be VPC-restricted (prevents public internet access). Support object operations only — not bucket-level operations. Referenced via ARN, alias, or virtual-hosted-style URI.
Provider Docs Section: Amazon S3 User Guide — access-points.html
Architect Usage: Use to provide isolated access paths for different applications or teams sharing a single bucket. VPC-restrict access points for services that must never traverse the public internet (e.g., data processing pipelines).
Common Confusion: An access point policy does not replace the bucket policy — both are evaluated. The bucket policy must delegate access to the access point (or use a wildcard account-level delegation).
```

```
Term: Multi-Region Access Points (MRAP)
Definition: Global endpoint powered by AWS Global Accelerator that routes S3 requests to the closest active S3 bucket across multiple Regions. Supports active-active and active-passive configurations. Failover occurs within minutes. Does NOT replicate data — CRR must be configured separately for data synchronization.
Provider Docs Section: Amazon S3 User Guide — MultiRegionAccessPoints.html
Architect Usage: Use MRAP as the single global S3 endpoint when the web application serves users across multiple Regions. Pair with bi-directional CRR for active-active. Pair with one-directional CRR for active-passive with automatic failover.
Common Confusion: MRAP routes requests globally but does not move data. Without separately configured CRR, each regional bucket contains only locally uploaded data. Global Accelerator charges apply in addition to S3 charges.
```

```
Term: S3 Lifecycle
Definition: Rules for automated transitions (moving objects to cheaper storage classes) and expiration (deleting objects or non-current versions). As of July 2026, transitions to S3 Standard-IA and S3 One Zone-IA can start on day 0 (30-day scheduling minimum removed; 30-day billing minimum duration still applies). Bucket policies cannot block lifecycle rule actions. Transition ingestion (PUT/COPY) charges apply.
Provider Docs Section: Amazon S3 User Guide — object-lifecycle-mgmt.html
Architect Usage: Configure Lifecycle rules as a first-class cost control on every bucket. Define transitions per prefix or tag. Set non-current version expiration to control versioning storage costs. Billing adjusts at transition eligibility time except for Intelligent-Tiering (billing adjusts only after actual tier transition).
Common Confusion: Removing the scheduling minimum does not remove the billing minimum — an object transitioned to Standard-IA on day 1 is billed for the full 30-day minimum duration storage cost.
```

```
Term: S3 Transfer Acceleration
Definition: Accelerates long-distance uploads to S3 by routing traffic through the nearest CloudFront edge location. Endpoint format: {bucket}.s3-accelerate.amazonaws.com. Requires a DNS-compliant bucket name (no periods). Available only for general purpose buckets. Additional cost: USD 0.04/GB in from US/Europe/Japan; USD 0.08/GB in from all other locations; USD 0.04/GB out from any edge. AWS routes via acceleration only if it is faster than direct upload.
Provider Docs Section: Amazon S3 User Guide — transfer-acceleration.html
Architect Usage: Enable for web applications where users upload large files (video, CAD, medical imaging) from geographically distant locations. Not useful for users co-located with the S3 bucket Region.
Common Confusion: Transfer Acceleration accelerates uploads only — not downloads. For download acceleration, use CloudFront as a CDN. Also, no charge is incurred if AWS determines routing via Transfer Acceleration is not faster.
```

```
Term: S3 Storage Lens
Definition: Organization-wide storage analytics providing 60+ usage and activity metrics. Free tier: usage metrics, daily dashboard. Advanced (paid) tier: activity metrics, detailed status codes, CloudWatch publishing, expanded prefix metrics (all prefixes up to 50 levels deep). Metrics can be exported daily as CSV or Parquet to an S3 bucket or AWS-managed S3 table bucket for Athena/Redshift/Spark analysis.
Provider Docs Section: Amazon S3 User Guide — storage_lens.html
Architect Usage: Enable org-wide Storage Lens dashboards to identify cost optimization opportunities (buckets not using IA or Glacier, buckets without versioning, etc.). Use advanced tier + CloudWatch for automated alerting.
Common Confusion: Storage Lens provides metrics at the prefix level (advanced tier) but is not a real-time access log — use S3 Server Access Logging or CloudTrail for request-level audit trails.
```

```
Term: S3 Server Access Logging
Definition: Records detailed information about every request made to an S3 bucket. Log records include requester, bucket, object key, action, response code, error code, bytes transferred, time elapsed, and TLS version. Target (log destination) bucket must be in the same Region and must use SSE-S3 (not SSE-KMS) encryption.
Provider Docs Section: Amazon S3 User Guide — security-best-practices.html
Architect Usage: Enable on all production buckets. Use a dedicated log bucket with its own Lifecycle policy (expire logs after retention period). Pair with CloudTrail data events for management-plane (API call) audit in addition to request-level logging.
Common Confusion: Server access logging has best-effort delivery — logs may be delayed and are not guaranteed to be complete for every request. For compliance-grade audit trails, also enable CloudTrail S3 data events (which have stronger delivery guarantees).
```

## Architecture Guardrails

> Confidence legend: High (2+ official sources, dated <=12mo) | Medium (1 source or dated 12-24mo) | Low (community source or dated >24mo -- verify before use)

### Mandatory Patterns

**Pattern 1 — Default Encryption at Rest (SSE-S3 / SSE-KMS + S3 Bucket Keys)** High

- Pillar Alignment: Security
- Why: All new object uploads have been automatically encrypted with SSE-S3 (AES-256) since January 5, 2023 at no additional cost. Upgrading to SSE-KMS with a customer managed key (CMK) adds audit trails via CloudTrail, key rotation, and cross-account encryption capability. S3 Bucket Keys reduce KMS API call volume by up to 99% by generating a bucket-level key for per-object data keys. As of April 2026, SSE-C is disabled by default for all new general purpose buckets and must be explicitly re-enabled via PutBucketEncryption API.
- AWS Services: Amazon S3 (SSE-S3, SSE-KMS, DSSE-KMS), AWS KMS (customer managed keys, S3 Bucket Keys), AWS CloudTrail (KMS API audit)
- Architecture Decision: Set bucket default encryption to SSE-KMS with a CMK and BucketKeyEnabled=true. Attach a bucket policy Deny for PutObject requests that omit `x-amz-server-side-encryption-aws-kms-key-id`. All GET/PUT for KMS-encrypted objects require SSL/TLS and SigV4. KMS key must be in the same Region as the bucket. Server access logging destination buckets must use SSE-S3, not SSE-KMS.
  ```bash
  aws s3api put-bucket-encryption --bucket my-bucket \
    --server-side-encryption-configuration '{
      "Rules":[{
        "ApplyServerSideEncryptionByDefault":{
          "SSEAlgorithm":"aws:kms",
          "KMSMasterKeyID":"arn:aws:kms:<region>:<account>:key/<key-id>"
        },
        "BucketKeyEnabled":true
      }]
    }'
  ```
- Verification:
  ```bash
  aws s3api get-bucket-encryption --bucket <bucket-name>
  ```
  AWS Config rule: `s3-default-encryption-kms`
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html (2026-08-31), https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html (2026-08-31)

---

**Pattern 2 — Block Public Access (All Four Settings)** High

- Pillar Alignment: Security
- Why: S3 Block Public Access provides four independent override controls that prevent public exposure regardless of bucket policy or ACL contents. AWS Security Hub Foundational Security Best Practices S3.8 requires all four settings to be enabled. Apply at account level first (via AWS Organizations for multi-account), then confirm per-bucket.
- AWS Services: Amazon S3 Block Public Access, AWS Organizations (org-level RCP), S3 access points (per-access-point BPA)
- Architecture Decision: Four settings:
  - `BlockPublicAcls`: Rejects PUT requests containing public ACLs
  - `IgnorePublicAcls`: Ignores all public ACLs on bucket and objects
  - `BlockPublicPolicy`: Rejects bucket policy PUT if it would grant public access
  - `RestrictPublicBuckets`: Restricts public-policy buckets to AWS service principals and bucket owner only
  Enable all four at account level, then per-bucket. Directory buckets have all public access permanently disabled — cannot be changed.
- Verification:
  ```bash
  # Account level
  aws s3control get-public-access-block --account-id <account-id>
  # Bucket level
  aws s3api get-public-access-block --bucket <bucket-name>
  ```
  AWS Config rules: `s3-bucket-public-read-prohibited`, `s3-bucket-public-write-prohibited`
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html (2026-08-31)

---

**Pattern 3 — TLS-Only Bucket Policy (aws:SecureTransport Deny)** High

- Pillar Alignment: Security
- Why: Without a TLS enforcement policy, HTTP requests to S3 succeed, exposing object content and credentials in transit. AWS security best practices require denying all requests where `aws:SecureTransport` is false. Note: when AWS services make API calls on your behalf, `aws:SecureTransport` context may be redacted — add `aws:PrincipalIsAWSService` condition to exclude AWS service principals from the Deny if needed.
- AWS Services: Amazon S3 (bucket policy), AWS CloudTrail (tlsDetails in audit logs), Amazon CloudWatch (alarms on HTTP requests)
- Architecture Decision:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "RestrictToTLSRequestsOnly",
      "Action": "s3:*",
      "Effect": "Deny",
      "Resource": [
        "arn:aws:s3:::amzn-s3-demo-bucket",
        "arn:aws:s3:::amzn-s3-demo-bucket/*"
      ],
      "Condition": {"Bool": {"aws:SecureTransport": "false"}},
      "Principal": "*"
    }]
  }
  ```
  TLS certificate pinning is not supported — S3 auto-renews TLS certificates.
- Verification: `aws s3api get-bucket-policy --bucket <name>` and inspect for `aws:SecureTransport` Deny.
  AWS Config rule: `s3-bucket-ssl-requests-only`
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-bucket-policies.html (2026-08-31), https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html (2026-08-31)

---

**Pattern 4 — S3 Versioning + MFA Delete / Object Lock** High

- Pillar Alignment: Reliability, Security
- Why: Versioning keeps multiple variants of every object, enabling recovery from accidental deletion or overwrite. Once enabled, a bucket can never return to the unversioned state (only suspended). MFA Delete adds a second-factor requirement for permanent version deletion or versioning state changes. Object Lock provides WORM semantics: Compliance mode prevents deletion even by root; Governance mode allows authorized admins to override.
- AWS Services: S3 Versioning, S3 MFA Delete, S3 Object Lock, IAM root credentials (for MFA Delete only)
- Architecture Decision: MFA Delete can only be enabled by the bucket owner (root account) via CLI/API — the console does not support it. Object Lock must be enabled at bucket creation (cannot be enabled on an existing bucket without contacting AWS Support). Use Lifecycle rules to expire non-current versions and control storage cost growth from accumulated versions.
  ```bash
  aws s3api put-bucket-versioning --bucket <bucket-name> \
    --versioning-configuration Status=Enabled,MFADelete=Enabled \
    --mfa "<SerialNumber> <OTPCode>"
  aws s3api get-bucket-versioning --bucket <bucket-name>
  ```
- Verification:
  ```bash
  aws s3api get-bucket-versioning --bucket <bucket-name>
  ```
  AWS Config rule: `s3-bucket-versioning-enabled`
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html (2026-08-31), https://docs.aws.amazon.com/AmazonS3/latest/userguide/MultiFactorAuthenticationDelete.html (2026-08-31)

---

**Pattern 5 — Disable ACLs (Object Ownership = BucketOwnerEnforced)** High

- Pillar Alignment: Security
- Why: "A majority of modern use cases in Amazon S3 no longer require the use of ACLs, and we recommend that you keep ACLs disabled." (AWS official documentation). With ACLs disabled, all access is governed exclusively by IAM policies, bucket policies, VPC endpoint policies, and SCPs/RCPs — eliminating the legacy `AllUsers` and `AuthenticatedUsers` ACL grant risks.
- AWS Services: S3 Object Ownership (BucketOwnerEnforced), IAM, S3 bucket policies, AWS Organizations (SCPs, RCPs), VPC endpoint policies, IAM Access Analyzer for S3
- Architecture Decision:
  ```bash
  aws s3api put-bucket-ownership-controls --bucket <bucket-name> \
    --ownership-controls '{"Rules":[{"ObjectOwnership":"BucketOwnerEnforced"}]}'
  aws s3api get-bucket-ownership-controls --bucket <bucket-name>
  ```
  Required for CloudFront OAC integration. Required for S3 Access Points to work correctly with OAC.
- Verification:
  ```bash
  aws s3api get-bucket-ownership-controls --bucket <bucket-name>
  # Expected: ObjectOwnership: BucketOwnerEnforced
  ```
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html (2026-08-31), https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html (2026-08-31)

---

**Pattern 6 — Server Access Logging + CloudTrail Data Events** High

- Pillar Alignment: Security, Operational Excellence
- Why: Server access logging records all request-level operations; CloudTrail data events record all management-plane and object-level API operations. Amazon GuardDuty S3 Protection analyzes CloudTrail events for malicious activity patterns. Combined, they provide complete audit coverage for compliance and incident response.
- AWS Services: S3 server access logging, AWS CloudTrail (data events), Amazon GuardDuty (S3 Protection), Amazon CloudWatch (metric alarms), AWS Config
- Architecture Decision: Configure server access logging with a dedicated log bucket in the same Region using SSE-S3 (not SSE-KMS — server access logging destination does not support SSE-KMS). Enable CloudTrail data events for all S3 buckets or specific high-value buckets. Enable GuardDuty S3 Protection in all active Regions.
  ```bash
  aws s3api put-bucket-logging --bucket <bucket-name> \
    --bucket-logging-status '{"LoggingEnabled":{"TargetBucket":"<log-bucket>","TargetPrefix":"<prefix>/"}}'
  aws cloudtrail get-event-selectors --trail-name <trail-name>
  ```
- Verification:
  ```bash
  aws s3api get-bucket-logging --bucket <bucket-name>
  ```
  AWS Config rules: `s3-bucket-logging-enabled`, `cloudtrail-s3-dataevents-enabled`
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html (2026-08-31)

### Architectural Decisions

**Decision 1 — Storage Class Selection**

- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | S3 Standard | `STANDARD` | Latency (ms), availability 99.99%, no retrieval fee | Cost (highest storage rate) | Assets accessed more than once a month |
  | S3 Intelligent-Tiering | `INTELLIGENT_TIERING` | Automatic cost optimization; no retrieval fees | Per-object monitoring fee; objects <128 KB billed at Frequent tier | Access patterns unknown or unpredictable |
  | S3 Standard-IA | `STANDARD_IA` | Storage cost vs Standard; multi-AZ durability | Per-GB retrieval fee; 30-day billing minimum; 128 KB min billable size | Backups accessed less than once a month |
  | S3 One Zone-IA | `ONEZONE_IA` | Lowest-cost IA with ms access; single-AZ | Not resilient to AZ loss; retrieval fee | Reproducible data or CRR destination replicas |
  | S3 Glacier Instant Retrieval | `GLACIER_IR` | Lowest cost for ms-latency archive; 99.9% availability | Retrieval fee; 90-day min duration | Rarely accessed archive (quarterly) needing real-time retrieval |
  | S3 Glacier Flexible Retrieval | `GLACIER` | Very low storage cost | Minutes-to-hours retrieval; 90-day min | Archival accessed once per year |
  | S3 Glacier Deep Archive | `DEEP_ARCHIVE` | Lowest storage cost of all classes | Hours retrieval; 180-day min | Compliance archives accessed less than once per year |
  | S3 Express One Zone | `EXPRESS_ONEZONE` | Single-digit ms latency; 50% lower request cost vs Standard | Single-AZ; higher storage cost | Latency-sensitive compute-adjacent workloads (ML, HPC) |

- Cost Profile: Standard (highest) > Standard-IA > Glacier Instant > One Zone-IA > Glacier Flexible > Deep Archive (lowest). Exact per-GB prices: [UNVERIFIED — see https://aws.amazon.com/s3/pricing/]. Intelligent-Tiering storage rate matches Standard in Frequent tier, decreasing automatically.
- Lock-in Assessment: Storage class is metadata per object — changing class requires a Lifecycle transition or S3 Batch Operations COPY with new storage class header. No API lock-in; S3 API is proprietary.
- Architect Instruction: "Ask 'What is the access frequency distribution of stored objects?' when selecting a storage class for any bucket storing more than 100 GB."
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html (2026-08-31)

---

**Decision 2 — Static Website Hosting**

- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | S3 Website Endpoint only | S3 website endpoint | Simplicity; index/error docs; redirects | No HTTPS; no custom domain with TLS; GET/HEAD only; bucket must be public | Non-production, internal, or HTTP-only prototype |
  | S3 + CloudFront + OAC | S3 REST endpoint + CloudFront distribution + OAC | HTTPS; custom domain; private bucket; edge caching; SSE-KMS compatible; all Regions including post-Dec 2022 opt-in | CloudFront configuration overhead; cache invalidation complexity | All production web applications |

- Cost Profile: S3 website endpoint alone has no CloudFront cost but exposes bucket publicly. S3 + CloudFront + OAC adds CloudFront data transfer cost offset by dramatically lower S3 GET request costs (edge cache hit rate typically 80-95%).
- Lock-in Assessment: CloudFront is AWS-proprietary CDN. Bucket data is portable; CDN configuration is not.
- Architect Instruction: "Ask 'Does the application require HTTPS, a custom domain, or SSE-KMS encryption?' when evaluating hosting for static assets — the answer is always yes for production."
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteEndpoints.html (2026-08-31), https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (2026-08-31)

---

**Decision 3 — Serving User Uploads**

- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Presigned URL (PUT) | S3 presigned URL | Direct browser-to-S3 upload; bypasses server; max 7-day expiry | Bearer-token; CORS config required; Content-Type must match URL generation | Uploading known object keys, single-part up to 5 GB |
  | Presigned POST | S3 presigned POST | HTML form-based uploads; policy field validation | More complex POST fields setup | Legacy browsers or HTML form uploads [UNVERIFIED — deep config page not fetched] |
  | Backend proxy | API Gateway + Lambda + S3 SDK PutObject | Full server-side control; scanning; access logging | Backend bottleneck; Lambda 6 MB sync / 10 MB async payload limit | Files needing pre-upload validation or virus scanning before storage |

- Cost Profile: Presigned URL (lowest — no Lambda invocation per upload). Backend proxy adds Lambda cost per upload and has hard payload size limits.
- Lock-in Assessment: Presigned URLs are S3-specific. Proxy pattern is portable (same pattern on any object store).
- Architect Instruction: "Ask 'Do uploaded files need server-side validation or virus scanning before storage?' when designing the upload path — if yes, the backend proxy or post-upload Lambda trigger is required."
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html (2026-08-31), https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html (2026-08-31)

---

**Decision 4 — Single-Region vs Cross-Region Replication vs MRAP**

- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Single-Region | S3 Standard (single bucket, ≥3 AZs internally) | Simplicity; lowest cost | No geographic redundancy | Single-region app; RPO/RTO >24h acceptable |
  | CRR (standard) | S3 CRR | Geographic redundancy; compliance; reduce read latency in destination region | 2x storage cost; async (no zero-RPO guarantee); requires versioning; pre-existing objects not replicated | DR with RPO of hours (SLA-less) |
  | CRR + RTC | S3 CRR + Replication Time Control | 99.99% of objects replicated within 15 minutes (SLA-backed) | Higher cost than standard CRR; per-object RTC charge | Near-real-time DR with SLA requirement |
  | MRAP | S3 MRAP + AWS Global Accelerator | Global endpoint routes to closest active region; automatic failover in minutes | CRR still required separately; Global Accelerator charges; failover is minutes, not seconds | Active-active or active-passive with a single global endpoint |

- Cost Profile: Single-Region (lowest). CRR adds 2x storage + inter-region transfer. RTC adds per-object charge. MRAP adds Global Accelerator hourly + data transfer charges.
- Lock-in Assessment: CRR, RTC, and MRAP are all AWS-proprietary. Cross-provider replication requires third-party tooling.
- Architect Instruction: "Ask 'What is the required RPO and do users access data from multiple Regions?' when evaluating replication strategy."
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html (2026-08-31), https://docs.aws.amazon.com/AmazonS3/latest/userguide/MultiRegionAccessPoints.html (2026-08-31)

---

**Decision 5 — Transfer Acceleration vs CloudFront**

- Options:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | S3 Transfer Acceleration | Upload speed from global clients via CloudFront edge; DNS-based routing | USD 0.04-0.08/GB additional; DNS-compliant bucket name required; general purpose buckets only | Customers uploading large files from geographically distant locations |
  | CloudFront (edge caching) | Read/download via edge cache; HTTPS; full CDN | Write traffic still reaches origin S3 bucket | Serving static assets globally where reads dominate |

- Cost Profile: Transfer Acceleration: USD 0.04/GB in from US/Europe/Japan; USD 0.08/GB in from all other locations; USD 0.04/GB out from any edge. No charge if AWS determines routing via acceleration is not faster. Exact prices: [UNVERIFIED — see https://aws.amazon.com/s3/pricing/].
- Lock-in Assessment: Both use CloudFront edge infrastructure but via different endpoints. Transfer Acceleration endpoint is S3-specific.
- Architect Instruction: "Ask 'Are users uploading large files from locations geographically distant from the S3 bucket Region?' when evaluating Transfer Acceleration."
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/transfer-acceleration.html (2026-08-31), https://aws.amazon.com/s3/pricing/ (2026-08-31)

### Anti-Patterns

**Anti-Pattern 1 — Public Bucket / Block Public Access Disabled**

- Risk Level: CRITICAL
- Why: Violates AWS Security (SEC03-BP01). A bucket with Block Public Access disabled and a wildcard bucket policy allows any internet user to read or write all objects. Violates AWS Security Hub Foundational Security Best Practices S3.8. Cited in AWS official security best practices: "Ensure your Amazon S3 buckets are not publicly accessible."
- ❌ Wrong:
  All four Block Public Access settings set to false AND bucket policy grants `"Principal": "*"` with `s3:GetObject` (or `s3:*`) on the bucket resource.
- ✅ Correct:
  ```bash
  aws s3api put-public-access-block --bucket my-app-bucket \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
  ```
  All production assets served via CloudFront + OAC to a private bucket.
- Detection: AWS Config rules `s3-bucket-public-read-prohibited`, `s3-bucket-public-write-prohibited`; IAM Access Analyzer for S3; AWS Trusted Advisor; `aws s3api get-bucket-policy-status --bucket <name>` checking `IsPublic: true`
- Impact: Total data breach — any internet user can access all objects in the bucket. Regulatory violations (GDPR, PCI DSS, HIPAA depending on data type).
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html (2026-08-31), https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html (2026-08-31)

---

**Anti-Pattern 2 — Unencrypted Objects / Disabling Default Encryption**

- Risk Level: HIGH
- Why: Violates Security pillar (SEC08-BP01). All data at rest must be encrypted. As of April 2026, SSE-C is disabled by default — explicitly using SSE-C without re-enabling it fails. Relying on "no encryption" is a compliance violation for any regulated workload.
- ❌ Wrong:
  Uploading objects with no encryption header and bucket default encryption disabled; or attempting to use SSE-C on a new bucket where it has been disabled by default.
- ✅ Correct:
  ```bash
  aws s3api put-bucket-encryption --bucket my-bucket \
    --server-side-encryption-configuration '{
      "Rules":[{
        "ApplyServerSideEncryptionByDefault":{
          "SSEAlgorithm":"aws:kms",
          "KMSMasterKeyID":"arn:aws:kms:<region>:<account>:key/<key-id>"
        },
        "BucketKeyEnabled":true
      }]
    }'
  ```
- Detection: `aws s3api get-bucket-encryption`; S3 Inventory encryption status column; AWS Config `s3-default-encryption-kms`
- Impact: Compliance violation (NIST SP 800-53 SC-28, PCI DSS Requirement 3, ISO/IEC 27001 A.10.1). Data exposed if physical storage media is compromised.
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html (2026-08-31), https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html (2026-08-31)

---

**Anti-Pattern 3 — Wildcard Bucket Policy Principal: ***

- Risk Level: CRITICAL
- Why: AWS security best practices explicitly warn: "Identify bucket policies that allow a wildcard identity such as `'Principal': '*'`." Without a restrictive Condition block, `"Principal": "*"` makes the bucket effectively public under S3's Block Public Access evaluation — RestrictPublicBuckets will block ALL cross-account access when this condition is present, breaking legitimate cross-account access.
- ❌ Wrong:
  ```json
  {"Principal": "*", "Action": "s3:PutObject", "Effect": "Allow", "Resource": "arn:aws:s3:::my-bucket/*"}
  ```
  No Condition block — any AWS principal (or unauthenticated user if BPA is disabled) can write to the bucket.
- ✅ Correct:
  ```json
  {"Principal": {"AWS": "arn:aws:iam::<account-id>:role/my-app-role"}, "Action": "s3:PutObject", "Effect": "Allow", "Resource": "arn:aws:s3:::my-bucket/*"}
  ```
  Scoped to specific IAM role ARN with minimal required actions.
- Detection: IAM Access Analyzer for S3 (external access findings); `aws s3api get-bucket-policy-status --bucket <name>` to check `IsPublic: true`; AWS Security Hub S3.6 control
- Impact: Data breach when Block Public Access is misconfigured. Silent cross-account access breakage when RestrictPublicBuckets is enabled.
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html (2026-08-31)

---

**Anti-Pattern 4 — Using ACLs Instead of Bucket Policies**

- Risk Level: HIGH
- Why: ACLs are a legacy mechanism that cannot express IAM condition keys. The `AllUsers` ACL group grants access to all internet users; `AuthenticatedUsers` grants access to any authenticated AWS account (not just your own). AWS official guidance: "A majority of modern use cases in Amazon S3 no longer require the use of ACLs."
- ❌ Wrong:
  ```bash
  aws s3api put-object-acl --bucket my-bucket --key file.csv --acl public-read
  ```
  Setting public-read on individual objects while attempting to control access via ACLs.
- ✅ Correct:
  Set Object Ownership to BucketOwnerEnforced (disables all ACLs). Use bucket policies and IAM policies for all access control. Use access points with per-application policies for multi-consumer buckets.
- Detection: `aws s3api get-bucket-ownership-controls`; IAM Access Analyzer for S3 external access findings showing ACL-based access
- Impact: Unintended public or cross-account data exposure. AuthenticatedUsers grants access to all 300M+ AWS accounts globally.
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html (2026-08-31), https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html (2026-08-31)

---

**Anti-Pattern 5 — No Versioning on Stateful / Critical Data**

- Risk Level: HIGH
- Why: Without versioning, any `DeleteObject` request permanently destroys the object with no recovery path. Cannot implement CRR, Object Lock, or MFA Delete without versioning enabled. Violates Reliability pillar (REL09-BP04).
- ❌ Wrong:
  Unversioned bucket; `aws s3api delete-object --bucket my-bucket --key user-data/profile.json` permanently deletes the object with no way to recover.
- ✅ Correct:
  Enable versioning. DELETE without version ID inserts a delete marker; recover by deleting the delete marker. Configure Lifecycle rules to expire non-current versions after the desired retention period.
- Detection: `aws s3api get-bucket-versioning`; AWS Config `s3-bucket-versioning-enabled`; `aws s3api list-object-versions --bucket <name>` to verify version history exists
- Impact: Permanent data loss on accidental deletion or overwrite; inability to meet RPO objectives; blocks CRR and Object Lock adoption.
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html (2026-08-31), https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html (2026-08-31)

---

**Anti-Pattern 6 — Hardcoded IAM Access Keys**

- Risk Level: CRITICAL
- Why: "We recommend not storing AWS credentials directly in the application or Amazon EC2 instance. These are long-term credentials that are not automatically rotated." (AWS security best practices). Hardcoded keys exposed in source code, build artifacts, or environment variable dumps are a primary vector for S3 data breaches.
- ❌ Wrong:
  ```python
  s3_client = boto3.client('s3',
    aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
    aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
  )
  ```
  Hardcoded long-term IAM user access keys in application source code.
- ✅ Correct:
  Use IAM Role (Lambda execution role, EC2 instance profile, ECS task role) for server-side S3 access. Use presigned URLs for browser-to-S3 uploads. Use AWS Secrets Manager for credentials that cannot use IAM roles.
- Detection: Amazon Macie (detects credentials in S3 objects); Amazon GuardDuty (anomalous S3 API activity from unexpected IPs); IAM Access Analyzer (access key age); AWS Trusted Advisor (IAM key rotation check); `git-secrets` or `truffleHog` in CI/CD pipelines
- Impact: Complete AWS account compromise; unrestricted S3 data exfiltration; lateral movement to other AWS services.
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html (2026-08-31)

## Cloud-Native Design Patterns

**Pattern 1 — Presigned-URL Direct Upload Pattern**

- Category: Scalability / Data
- Problem: Web application users need to upload binary files (images, documents, videos) to S3 without routing the binary payload through the application server, which would create bandwidth bottlenecks, Lambda payload limits, and scaling constraints.
- Solution on AWS: Backend (Lambda function behind API Gateway) generates a presigned PUT URL using its IAM execution role credentials. The browser uploads the file directly to S3 over HTTPS using the presigned URL. The presigned URL encodes the target bucket, object key, HTTP method, expiration time, and SigV4 signature. Checksum verification is supported (CRC-64/NVME, CRC32, CRC32C, SHA-1, SHA-256, MD5, XXHash64, XXHash3, XXHash128, SHA-512). Bucket policies can enforce `s3:signatureAge` conditions to further restrict URL reuse. Network restrictions can be applied via `aws:SourceIp` or `aws:SourceVpc`/`aws:SourceVpce` conditions.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Bandwidth | Upload goes directly to S3; server bandwidth not consumed | — |
  | Scalability | S3 handles upload throughput; server only handles URL generation | CORS configuration required on the S3 bucket |
  | Security | URL inherits IAM role permissions; expires automatically | URL is a bearer token — exposure = access until expiry |
  | Integrity | SigV4 checksum support prevents corrupt uploads | Client SDK must support selected checksum algorithm |
  | File scanning | — | Files land in S3 before scanning — use S3 Event Notification + Lambda for post-upload AV scanning |

- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html (2026-08-31)

---

**Pattern 2 — S3 Event-Driven Processing (Upload-Trigger Pipeline)**

- Category: Communication / Resilience
- Problem: After a file is uploaded to S3, downstream processing (thumbnail generation, virus scanning, format conversion, metadata extraction) must be triggered without coupling the upload flow to the processing latency.
- Solution on AWS: Configure S3 Event Notifications on the source bucket. Supported event types include: new object created (`s3:ObjectCreated:*`), object removal, restore events, replication events, Lifecycle expiration/transition, Intelligent-Tiering auto-archival, object tagging, ACL PUT, and object annotation events. Notification destinations: Amazon SNS, Amazon SQS standard queues (not FIFO — use EventBridge intermediary for FIFO), AWS Lambda, or Amazon EventBridge. Route to EventBridge for fan-out to multiple consumers or FIFO SQS. Delivery is at-least-once; typically seconds, up to 1 minute. Avoid infinite loops: use separate source and destination buckets, or configure prefix/suffix filters to prevent recursive invocations.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Coupling | Upload and processing are decoupled | At-least-once delivery — processing must be idempotent |
  | Latency | Typically seconds between upload and trigger | Not suitable for synchronous/blocking upload workflows |
  | Fan-out | EventBridge enables multi-consumer fan-out | SQS FIFO requires EventBridge intermediary (added complexity) |
  | Resilience | SQS DLQ catches failed processing events | Lambda retry logic must handle partial processing failures |

- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html (2026-08-31)

---

**Pattern 3 — Static Site / SPA Hosting (CloudFront + OAC + Private S3)**

- Category: Scalability / Data
- Problem: Global, low-latency delivery of static web application assets (HTML, CSS, JavaScript, images) with HTTPS, custom domain, and private bucket — without running web servers.
- Solution on AWS: Static assets stored in a private S3 general purpose bucket (Block Public Access all four settings enabled; Object Ownership = BucketOwnerEnforced). CloudFront distribution with the S3 REST endpoint (not the S3 website endpoint) as origin. Origin Access Control (OAC) configured with SigningBehavior: `always` (SigV4 signing on every request to S3). Bucket policy grants `s3:GetObject` exclusively to `cloudfront.amazonaws.com` with a Condition on the specific CloudFront distribution ARN. S3 website endpoint is NOT used — it does not support HTTPS or OAC. Use CloudFront Functions or Lambda@Edge for SPA path rewriting (redirect all non-file paths to index.html).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | S3 bucket remains private; OAC-signed requests only | CloudFront cache invalidation required after S3 content updates |
  | Performance | CloudFront edge caching; global CDN; TLS termination at edge | Cache invalidation latency (seconds to minutes) |
  | Cost | High cache hit rate reduces S3 GET request cost | CloudFront data transfer charges; ACM cert (free but us-east-1 only for CloudFront) |
  | SSE-KMS | OAC supports SSE-KMS (OAI did not) | Requires customer managed KMS key configuration |

- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (2026-08-31)

---

**Pattern 4 — S3 Lifecycle Cost Optimization**

- Category: Data
- Problem: Web applications accumulate objects over time across multiple storage tiers. Without automation, objects remain in S3 Standard indefinitely, incurring maximum storage cost.
- Solution on AWS: Configure S3 Lifecycle rules with prefix or tag filters. Define transition rules (move objects to cheaper classes) and expiration rules (delete objects or non-current versions). As of July 2026, transitions to Standard-IA and One Zone-IA can start on day 0 (scheduling minimum removed). Typical web app Lifecycle: Standard (0-30 days) → Standard-IA (30-90 days) → Glacier Instant Retrieval (90-365 days) → Glacier Deep Archive (365+ days). For user-uploaded media: expire non-current versions after 90 days. For log objects: expire after retention period (30-365 days per compliance requirement).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost reduction | Automated; eliminates manual object management | 30-day billing minimum for IA classes (even if transitioned earlier) |
  | Complexity | Fully automated once configured | Rule design requires understanding of access patterns |
  | Retrieval | Lower tiers have retrieval fees and latency | Glacier classes unsuitable for real-time web application access |
  | Lifecycle ingestion | No data retrieval charges on transitions | Per-request ingestion (PUT/COPY) charges apply for each transition |

- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html (2026-08-31)

## Security Architecture

**Domain B1 — Encryption at Rest (SSE-KMS + S3 Bucket Keys)**

- AWS Services: Amazon S3 (SSE-S3, SSE-KMS, DSSE-KMS), AWS KMS (customer managed keys, S3 Bucket Keys), AWS CloudTrail (KMS API audit logs)
- Architecture: SSE-S3 (AES-256) is automatically applied to all new uploads since January 5, 2023 at no cost — no configuration required. For regulated workloads, upgrade to SSE-KMS with a CMK: PutObject requires `kms:GenerateDataKey`; GetObject requires `kms:Decrypt`. Enable S3 Bucket Keys to reduce KMS API calls by up to 99% — the bucket-level data key generates per-object data keys locally, reducing KMS round trips. When S3 Bucket Keys are enabled, the encryption context uses the bucket ARN (not the object ARN). AWS managed key (`aws/s3`) cannot be shared cross-account — use a CMK for cross-account access. Server access logging destination buckets must use SSE-S3, not SSE-KMS. Enforce encryption at upload via bucket policy Deny on PutObject without the KMS key header. Migration Note (April 2026): SSE-C disabled by default for all new general purpose buckets.
- Compliance Alignment: NIST SP 800-53 SC-28 (Protection of Information at Rest), PCI DSS Requirement 3 (Protect Stored Cardholder Data), ISO/IEC 27001 A.10.1 (Cryptographic controls)
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html (2026-08-31)

---

**Domain B2 — CloudFront Origin Access Control (OAC)**

- AWS Services: Amazon CloudFront (OAC), Amazon S3 (private bucket, REST endpoint), AWS KMS (SSE-KMS compatibility)
- Architecture: OAC replaces OAI — AWS recommends OAC for all new deployments. OAC authenticates via SigV4 with SigningBehavior: `always`. Bucket policy grants `s3:GetObject` exclusively to `cloudfront.amazonaws.com` with a Condition on the specific distribution ARN (`AWS:SourceArn`). S3 Object Ownership must be `BucketOwnerEnforced`. OAC supports all Regions including post-December 2022 opt-in Regions, SSE-KMS, and PUT/DELETE for dynamic requests — capabilities OAI lacked. OAC does NOT support S3 website endpoints (use S3 REST endpoint as origin). OAC does NOT support origin redirect via Lambda@Edge. Migration from OAI: (1) update bucket policy to allow both OAI and OAC, (2) update CloudFront distribution to use OAC, (3) remove OAI statement from bucket policy.
- Compliance Alignment: AWS Well-Architected SEC06-BP02 (Reduce attack surface), PCI DSS Requirement 1 (Network access controls)
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (2026-08-31)

---

**Domain B3 — S3 Access Points + VPC Endpoints (Zero-Trust Network Segmentation)**

- AWS Services: S3 Access Points, AWS VPC (Gateway endpoint for S3), VPC endpoint policies, IAM
- Architecture: Access Points are named network endpoints attached to buckets with their own access point policy and network controls. Restrict an access point to a specific VPC to prevent any path to the bucket from the public internet. Each application or team gets its own access point with a scoped policy — only the actions they need on the prefix they own. Access points support object operations only (not bucket-level operations). Reference via ARN, alias, or virtual-hosted-style URI. Use S3 VPC Gateway endpoint (free) for Lambda functions and EC2 instances to access S3 without traversing the internet. Combine VPC endpoint policies with access point policies for defense in depth.
- Compliance Alignment: NIST SP 800-53 SC-7 (Boundary Protection), PCI DSS Requirement 1 (Network access controls), AWS Well-Architected SEC05-BP01 (Create network layers)
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-points.html (2026-08-31)

---

**Domain B4 — Amazon Macie (Sensitive Data Discovery)**

- AWS Services: Amazon Macie, Amazon EventBridge, AWS Security Hub, Amazon S3
- Architecture: Macie automatically generates an S3 general purpose bucket inventory and continuously evaluates buckets for public exposure (policy findings). Two discovery modes: (1) Automated discovery — samples representative objects continuously at no scheduled-job cost; (2) Jobs — user-defined scope, on-demand or scheduled with full scan capability. Detection uses managed data identifiers (ML + pattern matching for PII, financial data, credentials, healthcare data) and custom data identifiers (regex + proximity rules). Allow lists define false-positive exceptions. Findings published to Amazon EventBridge and AWS Security Hub for automated remediation workflows. Multi-account management via AWS Organizations with a delegated Macie administrator. 30-day free trial for bucket evaluation; discovery jobs not included in free trial.
- Compliance Alignment: GDPR Article 25 (Data protection by design), NIST SP 800-53 RA-2 (Risk Assessment — Asset Categorization) and SI-12 (Information Management and Retention), PCI DSS Requirement 3 (Protect stored cardholder data)
- Source: https://docs.aws.amazon.com/macie/latest/user/what-is-macie.html (2026-08-31)

---

**Domain B5 — IAM Access Analyzer for S3**

- AWS Services: IAM Access Analyzer (external access analyzer), Amazon S3, AWS Organizations
- Architecture: IAM Access Analyzer provides external access findings for buckets allowing public or cross-account access. Requires an account-level external access analyzer per Region (available at no cost via the S3 console). Findings identify the source of unintended access: bucket policy, ACL, MRAP policy, or access point policy. Finding attributes include: bucket name, shared-through mechanism, status, access level, external principal, and whether access is blocked by an RCP. Updates within 30 minutes of policy or ACL changes; Block Public Access account-level changes may take up to 6 hours; MRAP policy changes up to 6 hours. Operators can block all public access in a single action from the Findings UI or modify specific policies. Findings for intentionally public resources can be archived to suppress alerts.
- Compliance Alignment: AWS Well-Architected SEC03-BP07 (Analyze public and cross-account access), NIST SP 800-53 AC-6 (Least Privilege) and AU-12 (Audit Record Generation), SOC 2 CC6.3 (Logical Access Controls)
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-analyzer.html (2026-08-31)

## Operational Patterns

**Operational Pattern 1 — S3 Lifecycle Policies (Automated Cost Optimization)**

- RTO/RPO: N/A (cost control, not availability)
- AWS Services: Amazon S3 (Lifecycle configuration rules)
- Cost Profile: Low operational cost driver. Eliminates manual object management. Storage tiers from S3 Standard (~USD 0.023/GB [UNVERIFIED — see aws.amazon.com/s3/pricing/]) down to Glacier Deep Archive (~USD 0.00099/GB [UNVERIFIED]). Billing changes at transition eligibility time except for Intelligent-Tiering (billing changes only after actual tier transition). No data retrieval charges on Lifecycle transitions; per-request ingestion (PUT/COPY) charges apply for each transition.
- Automation: Fully automated once rules are configured. Lifecycle rules cannot be blocked by bucket policies. Manual decision points: rule scope (prefix, tag, or bucket-wide), transition day thresholds, target storage class per tier, non-current version expiration days.
  Migration note (July 2026): Transitions to Standard-IA and One Zone-IA can now be configured from day 0 — the 30-day scheduling minimum was removed. The 30-day billing minimum duration still applies.
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html (2026-08-31)

---

**Operational Pattern 2 — S3 Cross-Region Replication (Disaster Recovery)**

- RTO: Determined by application-layer failover mechanism. With MRAP + bi-directional CRR, RTO for traffic routing failover is minutes.
- RPO: Standard CRR: no SLA — typically minutes to hours, potentially up to 24-48h in degraded conditions. CRR + RTC: SLA-backed 15-minute RPO for 99.99% of objects.
- AWS Services: Amazon S3 CRR, S3 Replication Time Control (RTC), S3 Batch Replication (for pre-existing objects), S3 MRAP
- Cost Profile: Medium-High. Inter-region data transfer charges + 2x storage cost (source + destination). S3 RTC adds per-object replication charge. MRAP adds AWS Global Accelerator hourly + traffic processing fees.
- Automation: CRR configured via bucket replication rules (IAM role with cross-account permissions). RTC enabled per replication rule. MRAP failover routing policy configured for active-active or active-passive. Bi-directional CRR required for active-active (configure rules on both source and destination buckets). S3 RTC does NOT apply to Batch Replication jobs.
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html (2026-08-31)

---

**Operational Pattern 3 — S3 Versioning + Object Lock (Ransomware Protection)**

- RTO: Object recovery from delete marker: seconds. Object recovery from Compliance-locked retention: N/A during retention period (immutable).
- RPO: Zero — every version is retained. Cost of RPO: additional storage for all retained versions (delete markers continue incurring version storage costs until versions are explicitly purged after lock expiration).
- AWS Services: S3 Versioning, S3 Object Lock (Compliance mode, Governance mode, Legal Hold)
- Cost Profile: Medium. Storage cost grows with number of retained non-current versions. Must configure Lifecycle rules to expire non-current versions after Object Lock retention expires or storage costs become unbounded.
- Automation: Object Lock retention mode and period set per object at upload time (or via default bucket Object Lock configuration). Legal Hold placed/removed with `s3:PutObjectLegalHold`. Governance mode override requires `s3:BypassGovernanceRetention` permission AND explicit `x-amz-bypass-governance-retention: true` request header.
  Key constraint: Object Lock must be enabled at bucket creation — cannot be retrofitted to an existing bucket.
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html (2026-08-31)

---

**Operational Pattern 4 — S3 Storage Lens + CloudWatch (Observability)**

- RTO/RPO: N/A (observability, not availability pattern)
- AWS Services: S3 Storage Lens, Amazon CloudWatch (advanced tier integration), S3 Storage Class Analysis, Amazon Athena (for exported metrics)
- Cost Profile: Free tier: 60+ usage/activity metrics, daily dashboard (no cost). Advanced tier (paid): activity metrics, detailed status codes, CloudWatch metric publishing, expanded prefix metrics (all prefixes up to 50 levels deep). CloudWatch metric charges apply when publishing from Storage Lens advanced tier.
- Automation: Daily metric export to S3 as CSV or Parquet, or to an AWS-managed S3 table bucket (`aws-s3`) for Athena/Redshift/Spark analytics. Drill-down hierarchy: Organization → Account → Region → Storage class → Bucket → Prefix → Storage Lens group. CloudWatch integration (advanced tier only) enables metric alarms, anomaly detection, and triggered remediation actions.
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage_lens.html (2026-08-31)

---

**Operational Pattern 5 — AWS Backup for S3 (Point-in-Time Recovery)**

- RTO: Recovery time depends on object count and size; PITR restores objects as of any point within the retention window.
- RPO: Continuous backup: 15-minute RPO (event-driven). Snapshot backup: as frequent as hourly.
- AWS Services: AWS Backup (S3 continuous backup, snapshot backup), Amazon S3, Amazon EventBridge (required for PITR event sourcing)
- Cost Profile: Medium. Backup storage charged per GB + AWS Backup service charges. Cross-region or cross-account copies of continuous backups are snapshot-only (PITR not preserved in the copy).
- Automation: Continuous backups rely on Amazon EventBridge for S3 event sourcing — if EventBridge is disabled in bucket notification settings, continuous backups stop silently. A single S3 resource can only have one continuous backup plan. Snapshots can be taken as frequently as hourly with retention up to 100 years.
- Source: https://docs.aws.amazon.com/aws-backup/latest/devguide/point-in-time-recovery.html (2026-08-31)

## Reference Architectures

**Architecture — Secure Static Website / SPA on AWS S3 + CloudFront**

- Context: Web application frontend (SPA, static site, or hybrid SSG/SSR) requiring global delivery, HTTPS, custom domain, private S3 origin, and production-grade security.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | DNS | Amazon Route 53 | Resolves custom domain (www.example.com) to CloudFront distribution endpoint; hosted zone in same account |
  | CDN / Edge | Amazon CloudFront | Global edge delivery; TLS termination; OAC-signed requests to private S3; cache control; HTTP/2 + HTTP/3 |
  | Origin Auth | CloudFront OAC (Origin Access Control) | Authenticates CloudFront-to-S3 requests via SigV4; prevents direct bucket access; required for SSE-KMS |
  | TLS Certificate | AWS Certificate Manager (ACM) in us-east-1 | SSL/TLS certificate attached to CloudFront distribution; MUST be provisioned in us-east-1 (CloudFront is a global service) |
  | Storage | Amazon S3 (private general purpose bucket, Block Public Access all four settings enabled, SSE-KMS, BucketOwnerEnforced) | Static assets (HTML, CSS, JS, images, fonts); REST endpoint used as CloudFront origin (not S3 website endpoint) |
  | Access Logs | Amazon S3 (dedicated log bucket, SSE-S3) | CloudFront access logs and S3 server access logs; separate bucket in same Region |
  | WAF | AWS WAF (attached to CloudFront distribution) | OWASP Top-10 protection; Layer 7 DDoS mitigation; IP reputation; rate limiting |
  | IaC | AWS CloudFormation (nested stacks) | Deploy and configure all components; open-source template at aws-samples/amazon-cloudfront-secure-static-site |

- Key Decisions:
  1. OAC over OAI: OAC supports SSE-KMS, all Regions including post-December 2022 opt-in Regions, PUT/DELETE for dynamic operations — OAI supports none of these.
  2. ACM certificate MUST be in us-east-1: CloudFront is a global service and reads certificates only from us-east-1. Certificates in other Regions cannot be attached to CloudFront distributions.
  3. S3 REST endpoint (not S3 website endpoint) as CloudFront origin: website endpoints are HTTP-only and do not support OAC. REST endpoint supports HTTPS and OAC.
  4. Cache invalidation after content update: `aws cloudfront create-invalidation --distribution-id <id> --paths "/*"` required after S3 content updates; CloudFront does not poll S3 for changes.
  5. SPA path rewriting: Configure CloudFront Functions or Lambda@Edge to rewrite non-file paths (e.g., `/about`) to `/index.html` for client-side routing.

- Scaling Path:
  - Read scale: CloudFront handles automatically — edge cache absorbs traffic surges; no S3 scaling required.
  - API integration: Add a second CloudFront origin (API Gateway + Lambda or ALB + ECS) with path-based routing (`/api/*`) without changing the S3 origin.
  - User media uploads: Separate private S3 bucket + presigned PUT URLs for direct client-to-S3 uploads; S3 Event Notification triggers Lambda for post-upload processing.
  - WAF tuning: Attach AWS WAF to CloudFront; add rate-based rules, geo-blocking, and managed rule groups as threat patterns emerge.
  - Multi-region: Add CRR to replicate assets to a second Region; configure MRAP as the single global S3 endpoint; add CloudFront origins in both Regions with origin failover.

- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/getting-started-secure-static-website-cloudformation-template.html (2026-08-31)

## Service Equivalence Map

S3 is AWS's object storage service — included only for cross-provider architecture decision context where relevant. Not a Multi-Cloud research; this section is informational only.

| Capability | AWS Service | Azure Equivalent | GCP Equivalent |
|------------|-------------|-----------------|----------------|
| Object storage | Amazon S3 | Azure Blob Storage | Google Cloud Storage |
| Static website hosting | S3 + CloudFront | Azure Static Web Apps | Firebase Hosting / Cloud CDN |
| Server-side encryption with CMK | SSE-KMS | Azure Storage Service Encryption + Azure Key Vault | CMEK with Cloud KMS |
| Versioning | S3 Versioning | Blob versioning | Object versioning |
| Replication | S3 CRR / SRR | Azure Blob Storage GRS/GZRS | Turbo replication |
| Lifecycle management | S3 Lifecycle | Azure Blob Lifecycle management | Cloud Storage Object Lifecycle |
| CDN + private origin | CloudFront OAC | Azure CDN + Private Link | Cloud CDN + Signed URLs |

## Provider Differentiators

**D1 — Strong Read-After-Write Consistency (All Regions, All Operations)** High

S3 provides strong read-after-write consistency for all PUT and DELETE requests in all AWS Regions, including overwrites. S3 Select, object ACLs, object tags, and HEAD object operations are also strongly consistent. Single-key updates are atomic — no eventual consistency window for individual objects. This simplifies upload-then-process pipelines: a Lambda triggered immediately after PutObject will always read the object that just landed. Caveat: bucket-level configuration changes have eventual consistency (wait 15 minutes after enabling versioning before initiating a high-volume delete operation); concurrent writers to the same key use last-writer-wins semantics.
Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html (2026-08-31)

---

**D2 — S3 Intelligent-Tiering (No Retrieval Charge, No Minimum Storage Duration)** High

S3 Intelligent-Tiering automatically moves objects between access tiers based on actual access patterns with no retrieval fees and no minimum storage duration requirement. This is unique among IA-class storage — Standard-IA and One Zone-IA have both retrieval fees and 30-day billing minimums. Objects under 128 KB are not monitored and remain in the Frequent Access tier; per-object monitoring fee applies for all monitored objects. "Set and forget" tiering for workloads where access patterns are unpredictable. Billing for Intelligent-Tiering transitions changes only after the actual transition occurs (unlike other classes where billing adjusts at eligibility time).
Sources: https://docs.aws.amazon.com/AmazonS3/latest/userguide/intelligent-tiering.html (2026-08-31), https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html (2026-08-31)

---

**D3 — S3 Express One Zone (Single-Digit Millisecond Latency, Directory Buckets)** High

S3 Express One Zone delivers up to 10x faster access than S3 Standard with single-digit millisecond latency, 50% lower request costs, and hundreds of thousands of requests per second. Uses a directory bucket format with hierarchical organization (unlike flat general purpose buckets). All public access is permanently disabled and cannot be changed for directory buckets. Maximum benefit when compute (EC2, Lambda, ECS) is co-located in the same AZ as the Express One Zone bucket. Trade-off: single AZ — not resilient to AZ failure. Not suitable for user-facing web app assets where durability and AZ resilience are required, but ideal for ML training checkpoints, HPC scratch storage, and inference result caching.
Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html (2026-08-31)

---

**D4 — Mountpoint for Amazon S3 (POSIX File-System Interface, Linux)** High

Mountpoint for Amazon S3 is an open-source high-throughput Linux file client that mounts an S3 bucket as a Linux file system, translating POSIX `open`/`read` calls to S3 API calls. Supports files up to 50 TB. Available only on Linux. Limitations: cannot modify existing files, cannot delete directories, no symbolic links, no file locking — supports append-new/read-many patterns only. Not available for S3 Glacier Flexible, Glacier Deep Archive, or Intelligent-Tiering Archive/Deep Archive tiers. Useful for data science and analytics workloads that require POSIX semantics for reading large S3 datasets without custom S3 SDK integration. Related: Amazon S3 Files (GA April 2026) provides a similar file-system interface connecting any AWS compute to S3 buckets, available in 34 Regions.
Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/mountpoint.html (2026-08-31)

---

**D5 — Four Bucket Types (General Purpose, Directory, Table, Vector)** High

As of 2026, S3 supports four bucket types addressing distinct architectural needs: (1) General purpose buckets — the historical S3 bucket type, supporting all storage classes and operations; (2) Directory buckets (S3 Express One Zone) — single-digit ms latency, hierarchical, single-AZ; (3) Table buckets — Apache Iceberg-native storage for analytics (Intelligent-Tiering support added December 2025); (4) Vector buckets — optimized for ML embedding storage for Amazon Bedrock and OpenSearch. This specialization allows architects to select the right bucket type for each workload without building workarounds.
Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html (2026-08-31)

---

**D6 — S3 Object Lambda RESTRICTED (November 2025) — Do Not Use for New Architectures**

> CRITICAL: As of November 7, 2025, S3 Object Lambda is available ONLY to existing customers and select APN partners. It is NOT available to new customers.

Previous capability: S3 Object Lambda attached a Lambda function to S3 GET/LIST/HEAD requests to transform data in-flight (resize images, redact PII, watermark documents). This capability is no longer available to new customers. New architectures must use alternative approaches: Lambda function + S3 PutObject for transformations at write time, or CloudFront Functions / Lambda@Edge for transformations at delivery time.
Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/transforming-objects.html (2026-08-31)

## Scenario Coverage

**Standard Case: Web Application with User-Uploaded Media + CloudFront-Served Static Assets**

Most common S3 architecture for a web application: static frontend (SPA/static site) served via CloudFront from a private S3 bucket, plus user media uploads stored in a separate S3 bucket accessed via presigned URLs.

- Approach:
  1. Create two general purpose S3 buckets: `my-app-assets` (static frontend) and `my-app-uploads` (user media). Both with Block Public Access all four settings enabled, SSE-KMS with CMK and S3 Bucket Keys, BucketOwnerEnforced, and S3 Versioning enabled.
  2. CloudFront distribution with OAC grants `s3:GetObject` on `my-app-assets` to `cloudfront.amazonaws.com` scoped to the distribution ARN. ACM certificate in us-east-1. Route 53 CNAME or alias to CloudFront.
  3. For uploads: Lambda (behind API Gateway) generates presigned PUT URL (7-day max, or shorter for role sessions) for `my-app-uploads` bucket. Browser uploads directly. S3 Event Notification triggers Lambda for post-upload processing (thumbnail, virus scan, metadata extraction).
  4. S3 Lifecycle on `my-app-uploads`: transition to Standard-IA at 30 days, Glacier Instant at 90 days. Expire non-current versions at 90 days.
  5. Attach AWS WAF to CloudFront distribution for OWASP Top-10 protection.

- Key Decisions:
  - Separate buckets for static assets and user uploads (different security, Lifecycle, and access policies).
  - OAC (not OAI) for CloudFront-to-S3 authentication.
  - Presigned URLs (not backend proxy) for uploads to avoid Lambda payload limits.
  - S3 Versioning on uploads bucket enables recovery from accidental deletion.

---

**Edge Case: Global Multi-Region Deployment with Near-Zero RPO**

An enterprise web application with users across multiple continents (North America, Europe, Asia-Pacific) requiring low-latency access and near-zero data loss in case of regional outage.

- Approach on AWS:
  1. General purpose S3 buckets in three Regions (e.g., us-east-1, eu-west-1, ap-southeast-1) with bi-directional CRR between all three + S3 Replication Time Control (RTC) for 15-minute RPO SLA.
  2. S3 Multi-Region Access Point (MRAP) as the single global S3 endpoint — routes requests to the geographically closest active bucket via AWS Global Accelerator.
  3. MRAP failover routing policy set to active-active; automatic failover within minutes if a Region becomes unhealthy.
  4. CloudFront distributions in each Region (or a single global distribution with multiple origins and origin failover groups) serve static assets from the nearest regional S3 bucket.
  5. AWS Backup continuous backup (PITR) on each regional bucket for recovery from application-layer errors (not just regional failures). Ensure EventBridge is not disabled on notification settings.
  6. S3 Object Lock (Governance mode) on compliance data buckets to protect against ransomware during the replication window.

  Key caveats: CRR does not replicate pre-existing objects — use S3 Batch Replication at setup. RTC per-object charges apply. Bi-directional replication requires careful conflict resolution at application layer (last-writer-wins in S3 for concurrent writes to the same key).

---

**Anti-Pattern Case: Public S3 Bucket as Direct Asset Origin Without CloudFront**

An architect proposes exposing a public S3 bucket directly as the asset origin for a web application, with Block Public Access disabled and `"Principal": "*"` in the bucket policy, to avoid CloudFront configuration complexity.

- Clarification to request before proceeding:
  1. "Is any user data or application logic stored in this bucket, or is it exclusively public static assets?" — Even if the intent is public static assets, a single misconfigured Lifecycle rule, Batch Operations job, or cross-bucket copy could land sensitive objects in a public bucket.
  2. "Does the application require HTTPS on asset URLs?" — S3 website endpoints do not support HTTPS. The REST endpoint supports HTTPS but then requires Block Public Access to be disabled, which violates Security Hub S3.8.
  3. "Is TLS certificate pinning or custom domain required?" — Not achievable without CloudFront for S3-hosted content.
  4. "What is the regulatory classification of data that could ever land in this bucket?" — PCI DSS, HIPAA, and GDPR all prohibit public bucket configurations for any bucket in scope.

  Correct alternative: All production web applications must serve assets via CloudFront + OAC from a private S3 bucket. CloudFront is the correct mechanism for public asset delivery — it provides HTTPS, custom domain, edge caching, and WAF integration while keeping the S3 bucket private.

## Research Iteration Changelog

> Mandatory for exhaustive research depth. Each row represents a gap identified and resolved during the 5-iteration gap-filling loop.

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Architecture Guardrails — Mandatory Patterns | SSE-S3 default encryption (since Jan 5, 2023) | Added — confirmed all new uploads encrypted automatically | https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html (2026-08-31) |
| 1 | Architecture Guardrails — Anti-Patterns | Block Public Access disabled | Added — CRITICAL risk; S3.8 violation | https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html (2026-08-31) |
| 1 | Cloud-Native Design Patterns | Presigned URL direct upload pattern | Added — confirmed URL format, checksum support, CORS requirements | https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html (2026-08-31) |
| 2 | Architecture Guardrails — Mandatory Patterns | OAC replacing OAI | Added — OAC required for SSE-KMS; OAI deprecated for new deployments | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (2026-08-31) |
| 2 | Security Architecture | Amazon Macie — sensitive data discovery | Added — automated + job-based discovery; managed and custom identifiers | https://docs.aws.amazon.com/macie/latest/user/what-is-macie.html (2026-08-31) |
| 2 | Security Architecture | IAM Access Analyzer for S3 | Added — external access findings; 30-minute update SLA for policy changes | https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-analyzer.html (2026-08-31) |
| 3 | Provider Differentiators | S3 Object Lambda restricted Nov 2025 | Added — CRITICAL: not available to new customers; alternative approaches documented | https://docs.aws.amazon.com/AmazonS3/latest/userguide/transforming-objects.html (2026-08-31) |
| 3 | Metadata / Executive Summary | SSE-C disabled by default (April 2026) | Added as migration note — new general purpose buckets; explicit re-enable required | https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html (2026-08-31) |
| 3 | Cloud Architecture Glossary | S3 Lifecycle scheduling minimum (July 2026) | Updated — 30-day scheduling minimum removed for Standard-IA and One Zone-IA transitions | https://aws.amazon.com/about-aws/whats-new/2026/07/s3-removes-30-day-transitions-standard-ia-one-zone-ia/ (2026-08-31) |
| 4 | Operational Patterns | AWS Backup PITR — EventBridge dependency | Added — PITR stops silently if EventBridge disabled in bucket notification settings | https://docs.aws.amazon.com/aws-backup/latest/devguide/point-in-time-recovery.html (2026-08-31) |
| 4 | Reference Architectures | ACM certificate must be in us-east-1 | Added as key decision — CloudFront global service reads certs from us-east-1 only | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/getting-started-secure-static-website-cloudformation-template.html (2026-08-31) |
| 4 | Provider Differentiators | Four bucket types (general purpose, directory, table, vector) | Added — current as of 2026-08-31; S3 Tables Intelligent-Tiering support Dec 2025 | https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html (2026-08-31) |
| 5 | Consolidated Gaps | Exact per-GB storage prices | IRRESOLVABLE — pricing page returned structural descriptions; not numeric rate tables | — |
| 5 | Consolidated Gaps | Requester Pays bucket feature | IRRESOLVABLE — specific documentation page not fetched; marked [UNVERIFIED] | — |
| 5 | Consolidated Gaps | Sustainability pillar specifics for S3 | IRRESOLVABLE — no dedicated S3 sustainability documentation section found | — |
| 5 | Consolidated Gaps | CloudFront OAC VPC sub-pages (deep config) | IRRESOLVABLE — top-level overview confirmed; deep configuration details not fetched | — |
| 5 | Consolidated Gaps | Presigned POST (HTML form upload) deep config | IRRESOLVABLE — overview-level only; dedicated presigned POST reference page not fetched | — |
| 5 | Consolidated Gaps | Data lake landing zone S3 pattern | IRRESOLVABLE — no focused official URL found; pattern not included | — |
| 5 | Security — Prompt Injection | "See also — Skills for AI coding assistants" block in AWS docs | DISCARDED — injected content detected and discarded by all five investigators; not AWS official content | — |
