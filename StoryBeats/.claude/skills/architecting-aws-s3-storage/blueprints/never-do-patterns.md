# Never Do Patterns — Amazon S3 Storage Architecture

**Tier**: Complex (7 anti-patterns — all require immediate correction) | **Source**: S3 User Guide — Security best practices, accessed 2026-07-31

---

## Anti-Pattern 1 — Publicly accessible bucket for private data (BPA disabled)

**Risk**: CRITICAL  
**Pillar**: Security  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

**Why**: Public read/write exposure is the top cause of S3 data breaches. Disabling BPA and granting `"Principal":"*"` exposes every object in the bucket to anyone on the internet.

**Blast radius**: Entire bucket contents exposed to exfiltration or overwritten by any internet actor.

```json
// ❌ WRONG: BPA disabled + public bucket policy
// aws s3api put-public-access-block with all settings = false
// Then:
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-bucket/*"
  }]
}
// Result: anyone on the internet can download any object

// ✅ CORRECT: Keep BPA on; serve public content via CloudFront + OAC
// Bucket policy — grants CloudFront OAC only:
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowCloudFrontOAC",
    "Effect": "Allow",
    "Principal": {"Service": "cloudfront.amazonaws.com"},
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-bucket/*",
    "Condition": {
      "StringEquals": {
        "AWS:SourceArn": "arn:aws:cloudfront::ACCOUNT_ID:distribution/DISTRIBUTION_ID"
      }
    }
  }]
}
```

**Detection**:

```bash
# Check BPA settings
aws s3api get-public-access-block --bucket "$BUCKET_NAME"
# Any setting = false is a finding

# AWS Config managed rules
aws configservice describe-compliance-by-config-rule \
  --config-rule-names s3-bucket-public-read-prohibited s3-bucket-public-write-prohibited
# Expected: COMPLIANT — any NON_COMPLIANT requires immediate remediation

# IAM Access Analyzer for S3
aws accessanalyzer list-findings --analyzer-arn "$ANALYZER_ARN" \
  --filter '{"resourceType":{"eq":["AWS::S3::Bucket"]}}'
# Any "public" finding is critical
```

---

## Anti-Pattern 2 — Wildcard bucket policy or IAM grants in production (`s3:*` / `"Principal":"*"`)

**Risk**: CRITICAL  
**Pillar**: Security  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

**Why**: Wildcard actions grant any S3 operation — including destructive ones (DeleteObject, DeleteBucket) — to the matched principal. Combined with a broad principal, this is a privilege escalation path.

**Blast radius**: Any allowed principal can read, write, delete, or modify any object and bucket configuration.

```json
// ❌ WRONG: wildcard actions + broad principal
{
  "Effect": "Allow",
  "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
  "Action": "s3:*",
  "Resource": ["arn:aws:s3:::my-bucket", "arn:aws:s3:::my-bucket/*"]
}

// ✅ CORRECT: scoped actions + specific role ARN + specific prefix
{
  "Effect": "Allow",
  "Principal": {"AWS": "arn:aws:iam::123456789012:role/AppReadRole"},
  "Action": ["s3:GetObject", "s3:HeadObject"],
  "Resource": "arn:aws:s3:::my-bucket/app-prefix/*"
}
```

**Detection**:

```bash
# Validate policy for overly permissive statements
aws accessanalyzer validate-policy \
  --policy-type RESOURCE_POLICY \
  --policy-document "$(aws s3api get-bucket-policy --bucket "$BUCKET_NAME" --query Policy --output text)"
# Look for SECURITY_WARNING findings about wildcard actions or principals

# Manual grep on retrieved policy
aws s3api get-bucket-policy --bucket "$BUCKET_NAME" \
  --query Policy --output text | python3 -m json.tool | grep -E '"s3:\*"|"Action": "\*"'
# Any match is a finding
```

---

## Anti-Pattern 3 — Long-term access keys hardcoded in app/config for S3 access

**Risk**: HIGH  
**Pillar**: Security  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

**Why**: Long-term IAM user access keys are not automatically rotated. A key embedded in source code, config files, or container images grants standing S3 access until the key is manually revoked — a window that is often days or months.

**Blast radius**: Leaked key grants full standing access to S3 (and any other AWS service the user has permissions for) until manually revoked.

```python
# ❌ WRONG: hardcoded credentials in application code
import boto3
s3 = boto3.client(
    's3',
    aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
    aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    region_name='us-east-1'
)

# ✅ CORRECT: IAM role; SDK picks up credentials automatically
# No credentials in code — attach IAM role to compute:
# EC2: instance profile | Lambda: execution role | EKS: IRSA | ECS: task role
import boto3
s3 = boto3.client('s3')  # SDK resolves credentials from instance metadata
```

**Detection**:

```bash
# Generate IAM credential report — check for active long-term keys
aws iam generate-credential-report
aws iam get-credential-report --query Content --output text | base64 -d | \
  awk -F',' 'NR>1 && $9=="true" {print "Active key for user:", $1}'

# Secret scanning in code (use pre-commit hook or CI pipeline)
# Tools: git-secrets, truffleHog, AWS CodeGuru Security

# Check EC2 instances without instance profiles
aws ec2 describe-instances \
  --query 'Reservations[].Instances[?!IamInstanceProfile].InstanceId' \
  --output text
# Any instance ID here may be using long-term keys
```

---

## Anti-Pattern 4 — Single-AZ storage class as the ONLY copy of unrecreatable data

**Risk**: HIGH  
**Pillar**: Reliability  
**Source**: [S3 storage class introduction](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html)

**Why**: S3 One Zone-IA and S3 Express One Zone store data in a single Availability Zone. AWS documentation states: "Data is not resilient to the physical loss of the Availability Zone." AZ failures — while rare — do happen. The 11-nines durability guarantee applies only to multi-AZ storage classes.

**Blast radius**: Permanent, irrecoverable loss of all objects stored in One Zone-IA or Express One Zone if that AZ experiences a failure.

```bash
# ❌ WRONG: sole copy of production database backups in One Zone-IA
aws s3api put-object \
  --bucket my-critical-backups \
  --key db-backup-2026-07-31.sql.gz \
  --storage-class ONEZONE_IA \
  --body db-backup-2026-07-31.sql.gz
# If the AZ is lost, this backup is permanently gone

# ✅ CORRECT: authoritative copy in multi-AZ class
# Use ONEZONE_IA only for re-creatable data or as a CRR replica destination

aws s3api put-object \
  --bucket my-critical-backups \
  --key db-backup-2026-07-31.sql.gz \
  --storage-class STANDARD_IA \
  --body db-backup-2026-07-31.sql.gz
# Multi-AZ: resilient to AZ failure; retrieval fee applies (acceptable for backups)
```

**Acceptable uses for single-AZ classes**:
- One Zone-IA: re-creatable data (thumbnails, transcoded video) or CRR replica copies where the source is the authoritative copy
- Express One Zone: latency tier for compute-colocated access, when a durable multi-AZ copy exists elsewhere

**Detection**:

```bash
# Inventory storage class distribution in a bucket
aws s3api list-objects-v2 --bucket "$BUCKET_NAME" \
  --query 'Contents[?StorageClass==`ONEZONE_IA`].[Key,StorageClass]' \
  --output table
# Review whether any critical/unrecreatable objects appear

# Storage Lens shows class distribution across all buckets
# Navigate to S3 console > Storage Lens > Dashboard
```

---

## Anti-Pattern 5 — Allowing plaintext HTTP (no `aws:SecureTransport` deny in bucket policy)

**Risk**: HIGH  
**Pillar**: Security  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

**Why**: Without a TLS-enforcement deny, S3 will accept unencrypted HTTP requests. This exposes object data and AWS request signatures to network eavesdropping and man-in-the-middle attacks.

**Blast radius**: Any data transmitted over HTTP is interceptable; AWS credentials embedded in HTTP signatures can be replayed.

```json
// ❌ WRONG: no SecureTransport condition — bucket accepts http:// requests
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::123456789012:role/AppRole"},
    "Action": ["s3:GetObject", "s3:PutObject"],
    "Resource": "arn:aws:s3:::my-bucket/*"
  }]
  // No Deny on SecureTransport = http:// requests accepted
}

// ✅ CORRECT: explicit Deny rejects all non-TLS requests
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyNonTLS",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ],
      "Condition": {
        "Bool": {"aws:SecureTransport": "false"}
      }
    },
    {
      "Sid": "AllowAppRole",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::123456789012:role/AppRole"},
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::my-bucket/*"
    }
  ]
}
```

**Detection**:

```bash
# Test http:// access — should return 403
curl -I "http://my-bucket.s3.amazonaws.com/test-object" 2>/dev/null | head -1
# Expected: HTTP/1.1 403 Forbidden

# AWS Config managed rule
aws configservice describe-compliance-by-config-rule \
  --config-rule-names s3-bucket-ssl-requests-only
# Expected: ComplianceType = COMPLIANT
```

---

## Anti-Pattern 6 — No Versioning / no Object Lock for critical or regulated data

**Risk**: HIGH  
**Pillar**: Reliability, Security  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

**Why**: S3's 11-nines durability protects against hardware and media failure — it does not protect against accidental deletion, overwrites, ransomware, or malicious actors with write access. Without Versioning, a single `DeleteObject` call permanently destroys the object. Without Object Lock on regulated data, an attacker with delete permissions can destroy audit logs or financial records.

**Blast radius**: Irreversible loss or tampering of business-critical or compliance-mandatory data.

```bash
# ❌ WRONG: versioning disabled on a bucket holding audit logs
# A single delete call permanently destroys the log object:
aws s3api delete-object --bucket audit-logs --key 2026-07-31/cloudtrail.json.gz
# With no versioning: object is gone permanently

# ✅ CORRECT: versioning + Object Lock for regulated immutable records

# Step 1: Create bucket with Object Lock (must be at creation)
aws s3api create-bucket --bucket audit-logs-immutable \
  --region us-east-1 \
  --object-lock-enabled-for-bucket

# Step 2: Enable versioning (required for Object Lock)
aws s3api put-bucket-versioning --bucket audit-logs-immutable \
  --versioning-configuration Status=Enabled

# Step 3: Set default retention (Compliance mode — cannot be bypassed, even by root)
aws s3api put-object-lock-configuration --bucket audit-logs-immutable \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {"Mode": "COMPLIANCE", "Years": 7}
    }
  }'

# Now a delete attempt returns an error — the object is protected:
# aws s3api delete-object --bucket audit-logs-immutable --key 2026-07-31/cloudtrail.json.gz
# → "Object is WORM protected and cannot be overwritten or deleted"
```

**Detection**:

```bash
aws configservice describe-compliance-by-config-rule \
  --config-rule-names s3-bucket-versioning-enabled
# Expected: COMPLIANT for all critical buckets

aws s3api get-object-lock-configuration --bucket "$BUCKET_NAME"
# Expected on regulated buckets: ObjectLockEnabled = Enabled with retention configured
```

---

## Anti-Pattern 7 — Versioning enabled with no lifecycle rule to abort incomplete multipart uploads and expire noncurrent versions

**Risk**: MEDIUM  
**Pillar**: Cost Optimization  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html) — Storage Lens recommendation

**Why**: Enabling Versioning without cost-control lifecycle rules causes silent, unbounded storage cost growth. Every version of every object is billed. Every orphaned multipart upload part (from failed or interrupted uploads) is billed indefinitely. S3 Storage Lens explicitly flags buckets missing the `AbortIncompleteMultipartUpload` rule as a best-practice finding.

**Blast radius**: Storage costs grow silently without bound — no error, no alarm, just an ever-increasing bill.

```bash
# ❌ WRONG: versioning enabled, no lifecycle configuration
aws s3api get-bucket-lifecycle-configuration --bucket "$BUCKET_NAME"
# Returns: NoSuchLifecycleConfiguration
# Every old version and every orphaned MPU part accumulates

# ✅ CORRECT: lifecycle rules paired with versioning
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
        "NoncurrentVersionExpiration": {
          "NoncurrentDays": 90,
          "NewerNoncurrentVersions": 3
        }
      },
      {
        "ID": "TransitionCurrentToIA",
        "Status": "Enabled",
        "Filter": {"Prefix": ""},
        "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}],
        "NoncurrentVersionTransitions": [{"NoncurrentDays": 30, "StorageClass": "GLACIER"}]
      }
    ]
  }'
```

**Detection**:

```bash
# Check for missing lifecycle on versioning-enabled buckets
VERSIONED_BUCKETS=$(aws s3api list-buckets --query 'Buckets[].Name' --output text)
for bucket in $VERSIONED_BUCKETS; do
  STATUS=$(aws s3api get-bucket-versioning --bucket "$bucket" \
    --query 'Status' --output text 2>/dev/null)
  if [ "$STATUS" = "Enabled" ]; then
    LC=$(aws s3api get-bucket-lifecycle-configuration --bucket "$bucket" 2>&1)
    if echo "$LC" | grep -q "NoSuchLifecycleConfiguration"; then
      echo "MISSING LIFECYCLE: $bucket (versioning enabled, no lifecycle rules)"
    fi
  fi
done

# Storage Lens recommendations tab in the S3 console
# Will surface "Buckets without AbortIncompleteMultipartUpload lifecycle rule" finding
```

**Cost visibility**: Enable S3 Storage Lens with advanced metrics to see per-bucket incomplete multipart upload size and noncurrent version storage cost. Acts as a billing alarm without requiring custom CloudWatch metrics.
