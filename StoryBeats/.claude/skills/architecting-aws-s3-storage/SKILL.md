---
name: architecting-aws-s3-storage
description: "Architects secure, cost-optimized, and resilient object storage on Amazon S3 following AWS Well-Architected Framework (6-pillar) principles. Use when designing, reviewing, or implementing S3-based data lakes, backup/archive strategies, static content delivery, or multi-account storage governance on AWS."
---

## Function

Specialist in Amazon S3 object storage architecture — security, reliability, cost optimization, and operational excellence — aligned to the AWS Well-Architected Framework (6 pillars) and the S3 feature state as of July 2026.

## Version Context

**Technology**: Amazon S3 (Amazon Simple Storage Service)  
**Target State**: July 2026 service state (S3 User Guide — continuously updated)  
**Research Date**: 2026-07-31  
**Currency Threshold**: Review after 2027-07-31 — S3 evolves quarterly

**Critical changes in current edition** (vs. older mental models):

- **ACLs disabled by default** — new general purpose buckets ship with Object Ownership = *Bucket owner enforced*; access governed by IAM/bucket/VPC-endpoint policies and Organizations SCPs/RCPs only.
- **SSE-S3 on by default** — every new bucket is encrypted at rest automatically; no opt-in required.
- **SSE-C disabled by default since April 2026** — must be explicitly re-enabled per bucket via `PutBucketEncryption`.
- **Block Public Access (BPA) on by default** at bucket level; now enforceable org-wide via AWS Organizations.
- **Four bucket types** — general purpose (multi-AZ), directory/Express One Zone (single-AZ/low-latency), table (Apache Iceberg), vector (ML embeddings).
- **Account regional namespace** — bucket names can be scoped to your account's region, preventing name squatting after deletion.
- **Strong read-after-write consistency** for GET/LIST after PUT/DELETE in all Regions — no eventual-consistency window on object data.

⚠️ **Version Lock**: This skill targets July 2026 S3 feature state. Reject patterns predating this edition (e.g., ACL-based cross-account access, manual BPA opt-in).

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 7 mandatory patterns: BPA, ACLs-off, encryption at rest, TLS enforcement, versioning + lifecycle, audit trail, IAM roles
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 5 architectural decisions: storage class, encryption keys, DR posture, bucket type, access at scale
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 7 critical anti-patterns with ❌ wrong / ✅ correct CLI/policy pairs
- **[Integration Patterns](./blueprints/integration-patterns.md)** — S3 ↔ CloudFront/OAC, Lambda, Athena/S3 Tables, KMS, VPC Endpoint
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 scenarios: secure data lake, regulated archive, anti-pattern trap
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — S3 limits and essential commands
- **[External Resources](#external-resources)** — Official documentation

---

## Blueprints & Guardrails

### ✅ Always Do

For full patterns with CLI verification, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (Complex tier — all 7 required; security-critical, multi-pillar):

- **Keep Block Public Access enabled (bucket + org level)** — All four BPA settings on at bucket level; enforce at AWS Organizations root/OU so new accounts inherit. Serve public content via CloudFront + OAC, never via public bucket policy.
- **Disable ACLs — leave Object Ownership = Bucket owner enforced (default)** — Manage all access through IAM/bucket/VPC-endpoint policies. PUTs with custom-grant ACLs fail with HTTP 400 `AccessControlListNotSupported`; coordinate with any legacy uploaders.
- **Encrypt at rest: accept SSE-S3 baseline; upgrade to SSE-KMS for sensitive/regulated data** — Default SSE-S3 is automatic. Set bucket default encryption to SSE-KMS + S3 Bucket Keys for customer-managed key control and KMS audit trail. DSSE-KMS only where dual-layer is mandated.
- **Enforce TLS — deny non-TLS via bucket policy** — Add explicit `Deny` on `aws:SecureTransport=false` to every bucket policy. Do not pin S3 TLS certs (AWS rotates them). Monitor with AWS Config `s3-bucket-ssl-requests-only`.
- **Enable Versioning + lifecycle on every stateful bucket** — Versioning enables recovery from accidental deletion/overwrite. Always pair with lifecycle rules to: (a) transition data to IA/Glacier, (b) expire noncurrent versions, (c) abort incomplete multipart uploads after 7 days.
- **Audit object-level access: CloudTrail data events + Storage Lens + server access logging** — Enable CloudTrail data events on sensitive buckets (scoped to control per-event cost); Storage Lens org dashboard for 60+ metrics; server access logging to a dedicated log bucket.
- **Use IAM roles (temporary credentials) — never long-term access keys** — Grant least-privilege S3 actions via IAM role (EC2 instance profile, Lambda execution role, IRSA for EKS); scope `Resource` to specific bucket/prefix ARNs; no `s3:*` or `*` wildcards in production.

### ⚠️ Ask First

For decision matrices with trade-off tables, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Architectural decisions** (confirm before committing to an approach):

- **Storage class strategy** — S3 Standard vs Intelligent-Tiering vs Standard-IA vs One Zone-IA vs Glacier tiers. Confirm access frequency, retrieval-latency tolerance, and single-AZ risk tolerance. Default to Intelligent-Tiering for unknown/changing patterns.
- **Encryption key management** — SSE-S3 (zero key management) vs SSE-KMS + Bucket Keys (customer-managed key, KMS audit) vs DSSE-KMS (dual-layer, mandated workloads) vs SSE-C (disabled by default April 2026 — re-enable only if you must own keys and accept operational burden).
- **Data-protection / DR posture** — Versioning only vs SRR vs CRR vs CRR + RTC (15-min 99.99% SLA) vs Object Lock/WORM. Confirm RTO/RPO and immutability requirements. Object Lock must be enabled at bucket creation — cannot be retrofitted without AWS involvement.
- **Bucket type** — General purpose (default, multi-AZ) vs directory/Express One Zone (single-digit-ms latency, single-AZ) vs table bucket (Apache Iceberg, Athena/Redshift) vs vector bucket (ML embeddings/Bedrock). Confirm whether latency-critical enough to accept single-AZ, or if data is tabular/vector rather than generic objects.
- **Access at scale** — Bucket policy (simple, 20 KB limit) vs S3 Access Points (per-application named endpoints with own policies + per-AP BPA/VPC scoping) vs VPC endpoint + policy (private-network-only, data-exfiltration prevention). Confirm how many teams share the data and whether private-network access is required.

### 🚫 Never Do

For ❌ wrong / ✅ correct pairs and detection commands, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Critical prohibitions** (Complex tier — all 7 must be flagged before proceeding):

- **Publicly accessible bucket for private data (BPA disabled)** — CRITICAL: top cause of S3 data breaches; entire bucket contents exposed to the internet. Use CloudFront + OAC to a private bucket instead.
- **Wildcard bucket policy or IAM grants in production (`s3:*` / `"Principal":"*"`)** — CRITICAL: privilege escalation; any principal can perform any S3 action on any object. Scope to exact actions and ARNs.
- **Long-term access keys hardcoded in app/config for S3 access** — HIGH: keys grant standing S3 access until manually revoked. Use IAM roles with STS temporary credentials instead.
- **Single-AZ storage class (One Zone-IA / Express One Zone) as the ONLY copy of unrecreatable data** — HIGH: permanent data loss on AZ failure. Store authoritative copy in a multi-AZ class (Standard, Standard-IA, or Intelligent-Tiering).
- **Allowing plaintext HTTP (no `aws:SecureTransport` deny in bucket policy)** — HIGH: data and credentials interceptable in transit. Add TLS-enforcement deny to every bucket policy.
- **No Versioning / no Object Lock for critical or regulated data** — HIGH: a single `DeleteObject` or ransomware overwrite becomes unrecoverable. 11-nines durability protects against hardware loss only, not logical deletion.
- **Versioning enabled with no lifecycle rule to abort incomplete multipart uploads and expire noncurrent versions** — MEDIUM: silent, unbounded storage-cost growth. Storage Lens explicitly flags buckets missing this rule.

---

## Integration Patterns

For full integration code and configuration, see [Integration Patterns](./blueprints/integration-patterns.md).

**Key integrations**:

- **S3 ↔ CloudFront + OAC** — Serve static content privately via OAC (replaces legacy OAI); bucket stays private with BPA on; bucket policy grants `s3:GetObject` to the CloudFront service principal with distribution ARN condition.
- **S3 ↔ Lambda** — Event notifications (ObjectCreated/Removed) trigger Lambda; Lambda execution role with scoped `s3:GetObject`; objects > 6 MB should use presigned URLs rather than passing content through Lambda.
- **S3 ↔ Athena / S3 Table Buckets** — Query generic objects via Athena; use S3 Table Buckets (Apache Iceberg namespace `s3tables`) for query-optimized tabular data with Athena, Redshift Spectrum, and Spark.
- **S3 ↔ AWS KMS** — SSE-KMS bucket default encryption + S3 Bucket Keys (reduces KMS API calls ~99%); key policy must grant `s3.amazonaws.com` `kms:GenerateDataKey` and `kms:Decrypt`.
- **S3 ↔ VPC Gateway/Interface Endpoint** — Gateway endpoint (free, policy-scoped) for EC2/Lambda private access; Interface endpoint (PrivateLink, billed) for on-premises or cross-account private connectivity.

**Common issues**:

- **AccessDenied on cross-account PutObject** → Add bucket policy granting source account role `s3:PutObject`; Object Ownership = Bucket owner enforced means ACL grants are not needed.
- **SSE-KMS 403 on GetObject** → Verify caller IAM role has `kms:Decrypt` on the bucket's KMS key; check KMS key policy allows the role.
- **CloudFront 403 from S3 origin** → Confirm OAC policy attached to distribution and bucket policy grants `s3:GetObject` to the CloudFront service principal with the correct distribution ARN.
- **Replication not copying pre-existing objects** → Replication applies only to new objects; use S3 Batch Replication to backfill existing objects.

---

## Verification Loop

Run after any S3 bucket creation, policy change, or architecture modification.

### 1. Verify Block Public Access (all four settings)

```bash
aws s3api get-public-access-block --bucket "$BUCKET_NAME"
# Expected: BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy,
#           RestrictPublicBuckets all = true
```

### 2. Verify Object Ownership (ACLs disabled)

```bash
aws s3api get-bucket-ownership-controls --bucket "$BUCKET_NAME"
# Expected: ObjectOwnership = BucketOwnerEnforced
```

### 3. Verify encryption at rest

```bash
aws s3api get-bucket-encryption --bucket "$BUCKET_NAME"
# Expected: ServerSideEncryptionConfiguration with aws:kms (+ BucketKeyEnabled: true)
#           or AES256 (SSE-S3 baseline)
```

### 4. Verify TLS enforcement in bucket policy

```bash
aws s3api get-bucket-policy --bucket "$BUCKET_NAME" \
  --query Policy --output text | python3 -m json.tool | grep -A5 SecureTransport
# Expected: Deny Effect with aws:SecureTransport = "false" condition
```

### 5. Verify Versioning and lifecycle

```bash
aws s3api get-bucket-versioning --bucket "$BUCKET_NAME"
# Expected: Status = Enabled

aws s3api get-bucket-lifecycle-configuration --bucket "$BUCKET_NAME"
# Expected: Rules include AbortIncompleteMultipartUpload and NoncurrentVersionExpiration
```

### 6. Verify AWS Config compliance

```bash
aws configservice describe-compliance-by-config-rule \
  --config-rule-names \
    s3-bucket-public-read-prohibited \
    s3-bucket-ssl-requests-only \
    s3-bucket-versioning-enabled
# Expected: ComplianceType = COMPLIANT for all three rules
```

**Troubleshooting**:

- `AccessControlListNotSupported` on PUT → Caller is sending ACL grants; remove `x-amz-acl` header or ACL parameter.
- `KMS.NotFoundException` on SSE-KMS bucket access → Verify key ARN in bucket encryption config; check key policy and IAM role permissions.
- `NoSuchLifecycleConfiguration` → Add lifecycle rules; Storage Lens will flag cost impact within 24 hours.
- Replication lag exceeding expectation → Enable RTC (Replication Time Control) for the 15-minute 99.99% SLA.

---

## Quick Reference

**Essential CLI commands**:

```bash
# Create bucket with versioning, SSE-KMS, and BPA (us-east-1 requires no LocationConstraint)
aws s3api create-bucket --bucket "$BUCKET_NAME" --region us-east-1

aws s3api put-bucket-versioning --bucket "$BUCKET_NAME" \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption --bucket "$BUCKET_NAME" \
  --server-side-encryption-configuration '{
    "Rules":[{"ApplyServerSideEncryptionByDefault":{
      "SSEAlgorithm":"aws:kms","KMSMasterKeyID":"'"$KEY_ARN"'"},
      "BucketKeyEnabled":true}]}'

# List objects with storage class distribution
aws s3api list-objects-v2 --bucket "$BUCKET_NAME" \
  --query 'Contents[].StorageClass' --output text | sort | uniq -c

# Sync local directory to S3 with SSE-KMS
aws s3 sync ./local-dir "s3://$BUCKET_NAME/prefix/" \
  --sse aws:kms --sse-kms-key-id "$KEY_ARN"
```

**S3 service limits** (source: [S3 User Guide quotas](https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html), accessed 2026-07-31):

| Resource | Limit | Notes |
|---|---|---|
| Buckets per account | 10,000 (default) | Increasable via Support |
| Max object size | 5 TB | Single PUT limited to 5 GB |
| Multipart upload threshold | ~100 MB recommended | Required above 5 GB |
| Bucket policy size | 20 KB | Use Access Points for larger policy surfaces |
| Lifecycle rules per bucket | 1,000 | |
| Object Lock | Must be enabled at bucket creation | Adding to existing bucket requires AWS Support |

---

## External Resources

### Official Documentation (continuously updated)

- [Amazon S3 User Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/) — primary reference (accessed 2026-07-31)
- [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html) — accessed 2026-07-31
- [S3 storage classes comparison](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html) — accessed 2026-07-31
- [Amazon S3 storage classes](https://aws.amazon.com/s3/storage-classes/) — accessed 2026-07-31
- [Replicating objects within and across Regions](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html) — accessed 2026-07-31
- [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html) — accessed 2026-07-31
- [S3 service quotas](https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html) — accessed 2026-07-31

### Framework Guidance

- [AWS Well-Architected Framework — Pillars](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html) — 6 pillars confirmed (accessed 2026-07-31)

### Research Source

- [Research file](../../../StoryBeat/docs/research_cloud_AWS_S3_2026-07.md) — source-dated 2026-07-31
