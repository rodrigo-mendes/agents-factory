# Always Do Patterns — Amazon S3 Storage Architecture

**Tier**: Complex (security-critical, multi-pillar) | **Source**: S3 User Guide — Security best practices, accessed 2026-07-31

---

## Pattern 1 — Keep Block Public Access enabled (bucket + org level)

**Pillar**: Security  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

All four BPA settings must be enabled at bucket level. For multi-account estates, enforce at the AWS Organizations root or OU so new accounts inherit automatically — blocking any single account from accidentally opening a bucket.

```bash
# Verify all four BPA settings on a specific bucket
aws s3api get-public-access-block --bucket "$BUCKET_NAME"
# Expected output:
# {
#   "PublicAccessBlockConfiguration": {
#     "BlockPublicAcls": true,
#     "IgnorePublicAcls": true,
#     "BlockPublicPolicy": true,
#     "RestrictPublicBuckets": true
#   }
# }

# Enable all four settings if missing
aws s3api put-public-access-block --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,\
BlockPublicPolicy=true,RestrictPublicBuckets=true

# Detect public buckets with AWS Config
aws configservice describe-compliance-by-config-rule \
  --config-rule-names s3-bucket-public-read-prohibited s3-bucket-public-write-prohibited
# Expected: ComplianceType = COMPLIANT
```

**Serving public content**: Use Amazon CloudFront with Origin Access Control (OAC) pointing at a private bucket. The bucket stays private; CloudFront serves the public. Never disable BPA to host public content from the bucket directly.

**Trade-off**: BPA blocks legitimate public static-website hosting via bucket policy — CloudFront + OAC is the correct pattern (zero performance penalty; adds CDN caching).

---

## Pattern 2 — Disable ACLs (Object Ownership = Bucket owner enforced)

**Pillar**: Security, Operational Excellence  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

This is the default for new general purpose buckets. Leave it unchanged. All access is controlled through IAM policies, bucket policies, VPC endpoint policies, and Organizations SCPs/RCPs. Centralized policy-based control is auditable; ACLs are not.

```bash
# Verify Object Ownership setting
aws s3api get-bucket-ownership-controls --bucket "$BUCKET_NAME"
# Expected: ObjectOwnership = BucketOwnerEnforced

# For cross-account writes: bucket policy, not ACLs
# ✅ Correct: bucket policy grants s3:PutObject to the source account role
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowCrossAccountPut",
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::SOURCE_ACCOUNT_ID:role/UploaderRole"},
    "Action": "s3:PutObject",
    "Resource": "arn:aws:s3:::'"$BUCKET_NAME"'/*"
  }]
}'
```

**What happens when a caller sends ACL grants**: PUT requests with `x-amz-acl` header or `x-amz-grant-*` headers return HTTP 400 `AccessControlListNotSupported`. Coordinate with any legacy uploaders or third-party services to remove ACL parameters from their SDK calls.

---

## Pattern 3 — Encrypt at rest: SSE-S3 baseline; SSE-KMS for sensitive/regulated data

**Pillar**: Security  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

SSE-S3 (AES-256, AWS-managed keys) is applied automatically to every new bucket — no action required for baseline encryption. For sensitive or regulated data, set bucket default encryption to SSE-KMS with a customer-managed KMS key and enable S3 Bucket Keys to reduce KMS API call cost by approximately 99%.

```bash
# Set bucket default encryption to SSE-KMS + S3 Bucket Keys
aws s3api put-bucket-encryption --bucket "$BUCKET_NAME" \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "'"$KMS_KEY_ARN"'"
      },
      "BucketKeyEnabled": true
    }]
  }'

# Verify encryption configuration
aws s3api get-bucket-encryption --bucket "$BUCKET_NAME"
# Expected: SSEAlgorithm = aws:kms, BucketKeyEnabled = true

# KMS key policy must allow S3 service principal
# Add to the KMS key policy (under Statement):
# {
#   "Sid": "AllowS3SSE",
#   "Effect": "Allow",
#   "Principal": {"Service": "s3.amazonaws.com"},
#   "Action": ["kms:GenerateDataKey", "kms:Decrypt"],
#   "Resource": "*"
# }
```

**SSE-C warning**: Customer-provided keys (SSE-C) are now DISABLED by default for new general purpose buckets since April 2026. SSE-C forces the caller to supply the key on every request and cannot be used by AWS services (Replication, S3 Batch). Re-enable only if there is a mandatory organizational reason to own the encryption key material and you accept the operational burden.

**DSSE-KMS**: Use only when compliance explicitly requires dual-layer KMS encryption (highest cost/latency).

---

## Pattern 4 — Enforce TLS — deny non-TLS via bucket policy

**Pillar**: Security  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

Every bucket policy must contain an explicit Deny statement that rejects any request where `aws:SecureTransport` is `false`. This prevents unencrypted HTTP requests, which expose data and credentials to eavesdropping and MITM attacks.

```bash
# Apply TLS-enforcement deny to a bucket policy
# (merge into existing policy if one already exists)
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyNonTLS",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::'"$BUCKET_NAME"'",
        "arn:aws:s3:::'"$BUCKET_NAME"'/*"
      ],
      "Condition": {
        "Bool": {"aws:SecureTransport": "false"}
      }
    }
  ]
}'

# Verify compliance
aws configservice describe-compliance-by-config-rule \
  --config-rule-names s3-bucket-ssl-requests-only
# Expected: ComplianceType = COMPLIANT
```

**Do not pin TLS certificate thumbprints**: AWS rotates S3 TLS certificates automatically; pinning causes unexpected 403s.

**Legacy HTTP-only clients**: Must be updated to use HTTPS. The Deny statement rejects them immediately — this is a breaking change for any legacy client that has not migrated to HTTPS.

---

## Pattern 5 — Enable Versioning + lifecycle on every stateful bucket

**Pillar**: Reliability, Cost Optimization  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

Versioning enables recovery from accidental deletion, overwrite, or application failure. Without a companion lifecycle rule, versioning silently accumulates every object version and every orphaned multipart upload, multiplying storage cost.

```bash
# Enable versioning
aws s3api put-bucket-versioning --bucket "$BUCKET_NAME" \
  --versioning-configuration Status=Enabled

# Verify versioning
aws s3api get-bucket-versioning --bucket "$BUCKET_NAME"
# Expected: Status = Enabled

# Apply lifecycle rules: abort MPU, expire noncurrent versions, transition cold data
aws s3api put-bucket-lifecycle-configuration --bucket "$BUCKET_NAME" \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "AbortIncompleteMultipartUpload",
        "Status": "Enabled",
        "Filter": {"Prefix": ""},
        "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}
      },
      {
        "ID": "ExpireNoncurrentVersions",
        "Status": "Enabled",
        "Filter": {"Prefix": ""},
        "NoncurrentVersionExpiration": {"NoncurrentDays": 90}
      },
      {
        "ID": "TransitionToIA",
        "Status": "Enabled",
        "Filter": {"Prefix": ""},
        "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}]
      }
    ]
  }'

# Verify lifecycle configuration
aws s3api get-bucket-lifecycle-configuration --bucket "$BUCKET_NAME"
```

**Prerequisite for**: S3 Replication (CRR/SRR) and S3 Object Lock — both require versioning enabled on the source bucket.

**Cost safeguard**: S3 Storage Lens explicitly flags buckets with versioning enabled but no `AbortIncompleteMultipartUpload` lifecycle rule. Check Storage Lens recommendations in the S3 console within 24 hours of bucket creation.

---

## Pattern 6 — Audit object-level access: CloudTrail data events + Storage Lens + server access logging

**Pillar**: Operational Excellence, Security  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

CloudTrail management events log bucket-level API calls by default. Object-level API calls (GetObject, PutObject, DeleteObject) require **data events** — which carry a per-event cost and must be configured explicitly.

```bash
# Enable S3 data events on a CloudTrail trail for a specific bucket
aws cloudtrail put-event-selectors --trail-name "$TRAIL_NAME" \
  --event-selectors '[{
    "ReadWriteType": "All",
    "IncludeManagementEvents": true,
    "DataResources": [{
      "Type": "AWS::S3::Object",
      "Values": ["arn:aws:s3:::'"$BUCKET_NAME"'/"]
    }]
  }]'

# Enable server access logging (dedicated log bucket required)
aws s3api put-bucket-logging --bucket "$BUCKET_NAME" \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "'"$LOG_BUCKET_NAME"'",
      "TargetPrefix": "'"$BUCKET_NAME"'/"
    }
  }'

# Verify CloudTrail data events enabled (AWS Config)
aws configservice describe-compliance-by-config-rule \
  --config-rule-names cloudtrail-s3-dataevents-enabled
# Expected: ComplianceType = COMPLIANT
```

**S3 Storage Lens**: Enable an org-level dashboard in the S3 console — it aggregates 60+ metrics across all accounts and buckets and surfaces recommendations (e.g., missing lifecycle rules, incomplete multipart uploads). Free tier covers basic metrics; advanced metrics are billed per object.

**Cost control**: Scope CloudTrail data events only to buckets that require object-level audit (e.g., sensitive data, compliance buckets). Enabling on all objects account-wide can be costly for high-throughput buckets.

---

## Pattern 7 — Use IAM roles (temporary credentials) — never long-term access keys

**Pillar**: Security  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

Long-term access keys are not automatically rotated; a leaked key grants standing S3 access until manually revoked. IAM roles use STS to issue short-lived temporary credentials automatically.

```bash
# ✅ Grant S3 access via a least-privilege IAM role policy
# Example: Lambda execution role with scoped S3 read/write on a specific prefix
aws iam put-role-policy --role-name "$LAMBDA_ROLE_NAME" \
  --policy-name "S3ScopedAccess" \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "ReadBucketPrefix",
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:HeadObject"],
        "Resource": "arn:aws:s3:::'"$BUCKET_NAME"'/app-prefix/*"
      },
      {
        "Sid": "WriteOutputPrefix",
        "Effect": "Allow",
        "Action": ["s3:PutObject"],
        "Resource": "arn:aws:s3:::'"$BUCKET_NAME"'/output-prefix/*"
      },
      {
        "Sid": "ListBucket",
        "Effect": "Allow",
        "Action": "s3:ListBucket",
        "Resource": "arn:aws:s3:::'"$BUCKET_NAME"'",
        "Condition": {
          "StringLike": {"s3:prefix": ["app-prefix/*", "output-prefix/*"]}
        }
      }
    ]
  }'

# Validate with IAM Access Analyzer
aws accessanalyzer validate-policy \
  --policy-type IDENTITY_POLICY \
  --policy-document file://policy.json
# Expected: no SECURITY_WARNING or ERROR findings for wildcards
```

**Compute identity patterns**:
- EC2 → attach IAM instance profile (never configure AWS CLI credentials on the instance)
- Lambda → specify execution role ARN on the function
- EKS → use IRSA (IAM Roles for Service Accounts) with OIDC
- ECS → use task IAM role on the task definition

**Detect long-term keys**: Run `aws iam generate-credential-report` and inspect `access_key_1_last_used_date` — keys unused for 90+ days should be deactivated. Use AWS Config `iam-user-no-policies-check` to flag users with inline policies instead of role-based access.
