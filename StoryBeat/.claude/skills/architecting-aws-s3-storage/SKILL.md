---
name: architecting-aws-s3-storage
description: "Architects AWS S3 object storage for web applications including bucket security hardening, storage class selection, presigned URL upload patterns, CloudFront OAC integration, versioning, replication, and cost optimization via Lifecycle rules. Use when designing, configuring, or reviewing S3 bucket architecture in an AWS web application context (2026)."
---

## Function
Specialist in AWS S3 object storage architecture for web applications — bucket security, access control, storage class optimization, event-driven upload pipelines, and disaster recovery. Target: AWS S3 2026. Research date: 2026-08-31.

## Version Context

**Service**: Amazon S3 Object Storage
**Target edition**: AWS S3 2026
**Research date**: 2026-08-31
**Currency threshold**: 2027-08-31
**Support status**: Active (GA)

**Critical 2025-2026 changes**:
- **S3 Object Lambda RESTRICTED (Nov 7, 2025)**: Not available to new customers. Use Lambda + S3 combinations instead.
- **SSE-C disabled by default (April 2026)**: All new general purpose buckets have SSE-C disabled. Use SSE-S3 (automatic, free) or SSE-KMS.
- **Lifecycle scheduling minimum removed (July 2026)**: Standard-IA and One Zone-IA transitions can now start on day 0. The 30-day billing minimum duration still applies.
- **Amazon S3 Files GA (April 2026)**: File-system interface connecting any AWS compute to S3 buckets, available in 34 Regions.
- **Four bucket types (2026)**: General purpose, directory (Express One Zone), table (Apache Iceberg), vector (ML embeddings).
- **S3 Tables Intelligent-Tiering (December 2025)**: Table buckets now support Intelligent-Tiering.

**Deprecated / Restricted**:
- S3 Object Lambda: restricted Nov 2025 — do not use for new architectures
- CloudFront OAI (Origin Access Identity): deprecated — use OAC for all new distributions
- S3 ACLs: legacy mechanism — use bucket policies with `BucketOwnerEnforced`
- SSE-C: disabled by default on new buckets (April 2026)

⚠️ **CRITICAL — Agent Warning**: This skill targets AWS S3 2026. Reject patterns referencing OAI for new deployments, S3 Object Lambda for new customers, or SSE-C as a default encryption mechanism.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 three-tier operational patterns
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 5 test scenarios for skill-evaluator
- **[Integration Patterns](#integration-patterns)** — CloudFront OAC, presigned URL, event-driven pipeline
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands with expected outputs
- **[Quick Reference](#quick-reference)** — Critical limits, storage class hierarchy, essential commands

---

## Blueprints & Guardrails

### ✅ Always Do

**1. Default Encryption — SSE-KMS + S3 Bucket Keys** [High confidence]
Set bucket default encryption to SSE-KMS with a customer managed key (CMK) and `BucketKeyEnabled=true`. Bucket Keys reduce KMS API calls by up to 99%. Enforce at upload via bucket policy Deny on PutObject missing the KMS key header. Server access log destination buckets must use SSE-S3 (not SSE-KMS — unsupported for log delivery).
```bash
aws s3api put-bucket-encryption --bucket <bucket> \
  --server-side-encryption-configuration '{
    "Rules":[{"ApplyServerSideEncryptionByDefault":{
      "SSEAlgorithm":"aws:kms",
      "KMSMasterKeyID":"<key-arn>"},"BucketKeyEnabled":true}]}'
```

**2. Block Public Access — All Four Settings** [High confidence]
Enable at account level first (via AWS Organizations), then per-bucket: `BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets`. All production assets must be served via CloudFront + OAC from a private bucket — never from a public S3 endpoint.
```bash
aws s3api put-public-access-block --bucket <bucket> \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

**3. Enforce TLS via Bucket Policy (aws:SecureTransport Deny)** [High confidence]
Attach a `Deny` on all S3 actions when `aws:SecureTransport` is `"false"`. Apply to both the bucket ARN and the `/*` wildcard resource. Add `aws:PrincipalIsAWSService` condition to exclude AWS service principals if needed (some AWS services redact the SecureTransport context key).

**4. Enable Versioning + Non-Current Version Lifecycle Expiration** [High confidence]
Enable versioning on all buckets storing user data or application state. Versioning is required for CRR, Object Lock, and MFA Delete. Pair with a Lifecycle rule to expire non-current versions after the desired retention window — without it, storage cost grows unboundedly. Note: a bucket cannot return to the unversioned state once versioning is enabled.

**5. Disable ACLs — Object Ownership = BucketOwnerEnforced** [High confidence]
Set `ObjectOwnership` to `BucketOwnerEnforced` for all new buckets. Required for CloudFront OAC integration and S3 Access Points with OAC. Eliminates risk from `AllUsers` and `AuthenticatedUsers` ACL grants.
```bash
aws s3api put-bucket-ownership-controls --bucket <bucket> \
  --ownership-controls '{"Rules":[{"ObjectOwnership":"BucketOwnerEnforced"}]}'
```

**6. Enable Server Access Logging + CloudTrail Data Events** [High confidence]
Enable server access logging on all production buckets. Destination: dedicated log bucket in the same Region using SSE-S3 (not SSE-KMS). Enable CloudTrail S3 data events for management-plane audit. Enable GuardDuty S3 Protection. Server access logging has best-effort delivery — CloudTrail has stronger guarantees for compliance-grade audit trails.

### ⚠️ Ask First

**1. Storage Class Selection** — Ask: "What is the access frequency distribution of stored objects?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| S3 Standard | ms latency, 99.99% availability, no retrieval fee | Highest storage cost | Accessed > 1x/month |
| S3 Intelligent-Tiering | Auto cost optimization, no retrieval fees | Per-object monitoring fee; <128 KB objects not monitored (billed at Frequent tier) | Unknown/variable access patterns |
| S3 Standard-IA | Lower storage cost vs Standard | Retrieval fee; 30-day billing minimum | Backups accessed < 1x/month |
| S3 Glacier Instant | Lowest cost with ms latency | Retrieval fee; 90-day billing minimum | Archive accessed quarterly |
| S3 Glacier Deep Archive | Lowest storage cost | Hours retrieval; 180-day billing minimum | Compliance archives < 1x/year |
| S3 Express One Zone | Single-digit ms; 50% lower request cost | Single AZ — not resilient to AZ failure | ML/HPC compute co-located in same AZ |

**2. Static Website / SPA Hosting** — Ask: "Does the application require HTTPS, a custom domain, or SSE-KMS?"
Always use **S3 REST endpoint + CloudFront + OAC** for production (HTTPS, private bucket, SSE-KMS support, all Regions). S3 website endpoint is HTTP-only, does not support OAC, and requires a public bucket — acceptable only for non-production HTTP-only prototypes.

**3. User Upload Path** — Ask: "Do uploaded files need server-side validation or virus scanning before storage?"
- **Presigned PUT URL** (default): direct browser-to-S3; no server bandwidth consumed; CORS required; max 7 days (IAM user) or role session duration
- **Backend proxy** (API Gateway + Lambda): full server-side control; but Lambda 6 MB sync / 10 MB async payload limit applies
- **Post-upload scanning**: use S3 Event Notification + Lambda for antivirus/validation after objects land in S3

**4. Replication Strategy** — Ask: "What is the required RPO and do users access data from multiple Regions?"

| Option | RPO | Cost Driver | When |
|--------|-----|-------------|------|
| Single-region | No SLA (3 AZs internally) | Baseline | RPO > 24h acceptable |
| CRR (standard) | Hours (no SLA) | 2x storage + inter-region transfer | Geographic DR |
| CRR + RTC | 15-min SLA (99.99% of objects) | CRR + per-object RTC charge | SLA-backed near-real-time DR |
| MRAP + CRR | Minutes failover routing; RPO = CRR/RTC | + Global Accelerator charges | Active-active or single global endpoint |

**5. Transfer Acceleration vs CloudFront** — Ask: "Are users uploading large files from locations geographically distant from the S3 Region?"
Enable Transfer Acceleration for distant large-file uploads (USD 0.04-0.08/GB in; no charge if AWS determines routing is not faster). Use CloudFront for read/download acceleration. ACM certificate for CloudFront must be provisioned in us-east-1 regardless of bucket Region.

### 🚫 Never Do

**1. Public Bucket / Block Public Access Disabled** — CRITICAL
❌ Disabling BPA + `"Principal": "*"` in bucket policy = all objects readable by any internet user. Violates Security Hub S3.8, GDPR/PCI DSS/HIPAA.
✅ Enable all four BPA settings. Serve assets via CloudFront + OAC. Detect: `aws s3api get-bucket-policy-status --bucket <name>` — `IsPublic` must be `false`.

**2. Unencrypted Objects / Disabling Default Encryption** — HIGH
❌ Uploading without encryption or attempting SSE-C on a new bucket (disabled by default April 2026) — fails silently or with access errors.
✅ Set `SSEAlgorithm: aws:kms` with CMK + `BucketKeyEnabled: true`. Verify: `aws s3api get-bucket-encryption`.

**3. Wildcard Bucket Policy Principal `*` Without Restrictive Condition** — CRITICAL
❌ `{"Principal": "*", "Action": "s3:PutObject", "Effect": "Allow"}` with no Condition — effectively public when BPA is misconfigured; `RestrictPublicBuckets` silently breaks all cross-account access.
✅ Scope to specific IAM role ARN: `{"Principal": {"AWS": "arn:aws:iam::<account>:role/<role>"}}`.

**4. Using ACLs Instead of Bucket Policies** — HIGH
❌ `aws s3api put-object-acl --acl public-read` or relying on `AuthenticatedUsers` — grants access to all 300M+ AWS accounts globally, not just your own.
✅ Set `ObjectOwnership: BucketOwnerEnforced`. Use bucket policies and IAM policies exclusively.

**5. No Versioning on Stateful / Critical Data** — HIGH
❌ Unversioned bucket — any `DeleteObject` permanently destroys the object. Blocks CRR, Object Lock, and MFA Delete.
✅ Enable versioning. DELETE without version ID inserts a recoverable delete marker. Pair with non-current version expiration Lifecycle rule.

**6. Hardcoded IAM Access Keys in Application Code** — CRITICAL
❌ `boto3.client('s3', aws_access_key_id='AKIA...')` — long-term credentials in source code are the primary S3 breach vector.
✅ Use IAM execution role (Lambda, EC2 instance profile, ECS task role). Use presigned URLs for browser-to-S3 uploads.

**7. S3 Object Lambda for New Architectures** — CRITICAL
❌ S3 Object Lambda restricted Nov 7, 2025 — not available to new customers.
✅ Use Lambda + S3 PutObject for write-time transformations, or CloudFront Functions / Lambda@Edge for delivery-time transformations.

---

## Integration Patterns

**S3 + CloudFront + OAC (Static Website / SPA)**
Private S3 REST endpoint as CloudFront origin. OAC with `SigningBehavior: always` (SigV4 on every request). Bucket policy grants `s3:GetObject` to `cloudfront.amazonaws.com` with `Condition: AWS:SourceArn` scoped to the specific distribution ARN. `BucketOwnerEnforced` required. ACM certificate must be in us-east-1. Use CloudFront Functions for SPA path rewriting (`/about` → `/index.html`).

**S3 + Lambda (Presigned URL Direct Upload)**
API Gateway → Lambda generates presigned PUT URL using execution role credentials → Browser uploads directly to S3 over HTTPS. CORS required on S3 bucket. Use `s3:signatureAge` condition in bucket policy for tighter URL reuse control. S3 Event Notification triggers Lambda for post-upload processing (thumbnails, virus scan, metadata extraction).

**S3 + EventBridge + SQS/Lambda (Event-Driven Pipeline)**
S3 Event Notifications → SNS / SQS standard / Lambda / EventBridge. Route to EventBridge for fan-out to multiple consumers or FIFO SQS (standard SQS only for direct S3 → SQS). Use separate source and destination buckets to prevent infinite trigger loops. Processing must be idempotent (at-least-once delivery).

**Common Problems**:
- `SignatureDoesNotMatch` on presigned PUT → Content-Type at upload must match Content-Type specified at URL generation time
- CloudFront 403 after S3 content update → Run `aws cloudfront create-invalidation --distribution-id <id> --paths "/*"`
- AWS Backup PITR stops silently → EventBridge must not be disabled in bucket notification configuration
- CRR rule ignores pre-existing objects → Run S3 Batch Replication for objects that existed before CRR was enabled
- OAC returning 403 → Verify `BucketOwnerEnforced` is set and bucket policy uses `AWS:SourceArn` for the distribution

---

## Verification Loop

Run after every bucket creation or security configuration change:

### 1. Security Baseline
```bash
# Block Public Access — all four must be true
aws s3api get-public-access-block --bucket <bucket>

# Encryption
aws s3api get-bucket-encryption --bucket <bucket>
# Expected: SSEAlgorithm: aws:kms, BucketKeyEnabled: true

# TLS policy — look for Deny with aws:SecureTransport: "false"
aws s3api get-bucket-policy --bucket <bucket>

# Object Ownership — must be BucketOwnerEnforced
aws s3api get-bucket-ownership-controls --bucket <bucket>

# Versioning — must be Enabled
aws s3api get-bucket-versioning --bucket <bucket>

# Logging enabled
aws s3api get-bucket-logging --bucket <bucket>

# Public policy status — IsPublic must be false
aws s3api get-bucket-policy-status --bucket <bucket>
```

### 2. AWS Config Rule Compliance
```bash
aws configservice describe-compliance-by-config-rule \
  --config-rule-names \
    s3-bucket-public-read-prohibited \
    s3-bucket-public-write-prohibited \
    s3-default-encryption-kms \
    s3-bucket-ssl-requests-only \
    s3-bucket-versioning-enabled \
    s3-bucket-logging-enabled \
  --compliance-types NON_COMPLIANT
# Expected: empty results (no NON_COMPLIANT rules)
```

### 3. External Access Findings
```bash
aws accessanalyzer list-findings \
  --analyzer-arn <analyzer-arn> \
  --filter '{"resourceType":{"eq":["AWS::S3::Bucket"]},"status":{"eq":["ACTIVE"]}}'
# Expected: no active findings for production buckets
```

**Troubleshooting**:
- `AccessDenied on GetObject via CloudFront` → Verify OAC bucket policy includes `AWS:SourceArn` for the distribution ARN; verify `BucketOwnerEnforced` is set
- `SSE-C fails on new bucket` → SSE-C disabled by default (April 2026); switch to SSE-S3 or SSE-KMS
- `CRR rule not replicating` → Both source and destination buckets must have versioning enabled

---

## Quick Reference

**Essential security baseline commands** (run after every bucket creation):
```bash
aws s3api get-public-access-block --bucket <bucket>
aws s3api get-bucket-encryption --bucket <bucket>
aws s3api get-bucket-versioning --bucket <bucket>
aws s3api get-bucket-ownership-controls --bucket <bucket>
aws s3api get-bucket-policy-status --bucket <bucket>   # IsPublic must be false
```

**Critical limits**:

| Resource | Limit | Notes |
|----------|-------|-------|
| Object size maximum | 5 TB | Multipart required > 5 GB; recommended > 100 MB |
| Presigned URL max (SDK/CLI, IAM user) | 7 days | Limited to role session duration for assumed roles |
| Presigned URL max (Console) | 12 hours | |
| S3 throughput per prefix partition | 3,500 PUT/COPY/POST/DELETE or 5,500 GET/HEAD req/s | Use hash/UUID prefixes for high-throughput workloads |
| Bucket policy size | 20 KB | |
| Standard-IA / One Zone-IA billing min | 30 days | Scheduling min removed July 2026; billing min still applies |
| Glacier Instant / Flexible billing min | 90 days | |
| Glacier Deep Archive billing min | 180 days | |
| Object Lock enablement | Bucket creation only | Cannot retrofit — contact AWS Support for existing buckets |
| Intelligent-Tiering monitoring | Objects ≥ 128 KB | < 128 KB: not monitored; billed at Frequent Access rate |

**Storage class cost order** (highest → lowest storage cost):
Standard → Standard-IA → Glacier Instant Retrieval → One Zone-IA → Glacier Flexible Retrieval → Deep Archive

**Typical web app Lifecycle rule**:
Standard (0-30d) → Standard-IA (30-90d) → Glacier Instant Retrieval (90-365d) → Glacier Deep Archive (365d+)

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/architecting-aws-s3-storage/
├── SKILL.md                              <- This file (guardrails + verification)
└── blueprints/
    └── evaluation-scenarios.md           <- 5 test scenarios for skill-evaluator
```

**When to add blueprints** (not currently needed — SKILL.md fits within 500 lines):
- `blueprints/always-do-patterns.md` — if full code examples for all 6 patterns exceed inline budget
- `blueprints/integration-patterns.md` — if CloudFront OAC + presigned URL examples need full IaC context
- `blueprints/replication-dr-patterns.md` — if CRR + MRAP + RTC architecture detail is needed

---

## External Resources

### Official Documentation (research date: 2026-08-31)
- [Amazon S3 User Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)
- [S3 Security Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [Block Public Access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
- [SSE-KMS Encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html)
- [Bucket Encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html)
- [Presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)
- [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
- [S3 Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- [S3 Replication](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html)
- [S3 Storage Classes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html)
- [S3 Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [S3 Transfer Acceleration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/transfer-acceleration.html)
- [S3 Multi-Region Access Points](https://docs.aws.amazon.com/AmazonS3/latest/userguide/MultiRegionAccessPoints.html)
- [S3 Object Lambda — RESTRICTED Nov 2025](https://docs.aws.amazon.com/AmazonS3/latest/userguide/transforming-objects.html)
- [CloudFront OAC](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- [CloudFront Secure Static Site](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/getting-started-secure-static-website-cloudformation-template.html)
- [IAM Access Analyzer for S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-analyzer.html)
- [Amazon Macie](https://docs.aws.amazon.com/macie/latest/user/what-is-macie.html)
- [AWS Backup PITR for S3](https://docs.aws.amazon.com/aws-backup/latest/devguide/point-in-time-recovery.html)
- [S3 Object Ownership](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html)
