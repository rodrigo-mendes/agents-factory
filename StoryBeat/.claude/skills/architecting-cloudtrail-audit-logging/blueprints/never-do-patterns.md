# Never-Do Patterns — AWS CloudTrail Audit Logging (2026)

Full anti-patterns with detection commands and side-by-side alternatives for the 6 prohibited patterns.

---

## A1 — Relying on Event history instead of a trail

**Risk**: HIGH
**Why prohibited**: Event history is a non-permanent 90-day, management-events-only console
record — "it is not a permanent record, and it does not provide information about all possible
types of events." Violates Security pillar traceability. No forensic record beyond 90 days; no data, network, or Insights events.

```
# WRONG — no trail configured; team relies on Event history
No aws cloudtrail create-trail was ever run.
Audit evidence: "just use the CloudTrail console Events tab."

# Detection
aws cloudtrail describe-trails --query 'trailList[?IsMultiRegionTrail==`true`]'
# Returns: [] (empty)
# Security Hub: CloudTrail.1 FAILED
```

```bash
# CORRECT — multi-Region organization trail delivering to S3
aws cloudtrail create-trail \
  --name org-cloudtrail-central \
  --s3-bucket-name <log-archive-audit-bucket> \
  --is-multi-region-trail \
  --include-global-service-events \
  --is-organization-trail \
  --enable-log-file-validation
aws cloudtrail start-logging --name org-cloudtrail-central
```

**Impact if not corrected:** Compliance violation; no forensic record beyond 90 days;
no data/network/Insights events ever captured.

---

## A2 — Single-Region trail (missing global service and other-Region events)

**Risk**: HIGH
**Why prohibited**: A single-Region trail created in any Region other than us-east-1 silently
drops all global service events (IAM, STS, CloudFront) because those events land in us-east-1.
All activity in other enabled Regions is also missed.

```bash
# WRONG — single-Region trail in eu-west-1
aws cloudtrail create-trail \
  --name eu-trail \
  --s3-bucket-name <bucket> \
  --no-is-multi-region-trail   # <-- anti-pattern flag
# Result: IAM/STS/CloudFront events silently dropped; other-Region activity invisible

# Detection
aws cloudtrail describe-trails \
  --query 'trailList[?IsMultiRegionTrail==`false`].[Name,HomeRegion]'
# AWS Config: multi-region-cloudtrail-enabled NONCOMPLIANT
```

```bash
# CORRECT — multi-Region trail (console default; explicit in CLI)
aws cloudtrail create-trail \
  --name org-cloudtrail-central \
  --s3-bucket-name <log-archive-audit-bucket> \
  --is-multi-region-trail \              # <-- correct flag
  --include-global-service-events \
  --is-organization-trail
```

**Impact if not corrected**: Blind spots for IAM/STS credential abuse and cross-Region activity;
incomplete forensics during incident response.

---

## A3 — Unencrypted logs and/or no integrity validation

**Risk**: CRITICAL
**Why prohibited**: Unencrypted audit logs breach confidentiality of control-plane activity.
Without integrity validation, log tampering or deletion is undetectable — logs lose forensic
admissibility and compliance evidentiary value.

```bash
# WRONG — unencrypted, no integrity validation
aws cloudtrail create-trail \
  --name insecure-trail \
  --s3-bucket-name <bucket>
  # KmsKeyId not set — defaults to S3-managed AES256 (no CMK control)
  # EnableLogFileValidation defaults to false

# Detection
aws cloudtrail describe-trails \
  --query 'trailList[?KmsKeyId==null].[Name]'
# Security Hub: CloudTrail.2 FAILED (no CMK)
# Security Hub: CloudTrail.4 FAILED (no integrity validation)
# AWS Config: cloud-trail-encryption-enabled NONCOMPLIANT
# AWS Config: cloud-trail-log-file-validation-enabled NONCOMPLIANT
```

```bash
# CORRECT — CMK encryption + integrity validation
aws cloudtrail update-trail \
  --name org-cloudtrail-central \
  --kms-key-id <cmk-arn> \
  --enable-log-file-validation
```

**Impact if not corrected**: Data breach of audit data (confidential API calls exposed);
loss of forensic admissibility; compliance violation under CIS, SOC2, PCI-DSS, HIPAA.

---

## A4 — Log bucket in a workload account with permissive access and no deletion protection

**Risk**: CRITICAL
**Why prohibited**: Logs co-located with the audited workload can be deleted or altered by
the same principals that a breach would compromise. Violates segregation of duties — an attacker
(or insider) can erase their tracks. Broad `s3:*` grants make this trivial.

```
# WRONG
CloudTrail S3 bucket: in workload account (same account being audited)
Bucket versioning: off
MFA delete: off
IAM policy on developers: s3:* on audit bucket

# Detection
aws s3api get-bucket-location --bucket <bucket-name>
# Compare account ID in bucket ARN vs CloudTrail account ID — must differ (log-archive account)

aws s3api get-bucket-versioning --bucket <bucket-name>
# Returns: {} (empty) or Status: Suspended — anti-pattern

# Security Hub: CloudTrail.6 (bucket not publicly accessible — also checks ownership)
```

```bash
# CORRECT — dedicated bucket in separate log-archive account
# 1. Bucket in log-archive account (separate AWS account, not the workload account)
# 2. Versioning + MFA delete enabled
aws s3api put-bucket-versioning \
  --bucket <log-archive-audit-bucket> \
  --versioning-configuration Status=Enabled,MFADelete=Enabled \
  --mfa "arn:aws:iam::<log-archive-account-id>:mfa/root <mfa-code>"
# 3. Least-privilege bucket policy with aws:SourceArn condition (see always-do-patterns.md M2)
```

**Impact if not corrected**: Attacker erases their tracks; audit trail unavailable during
incident response; complete loss of forensic evidence.

---

## A5 — Broadly granting AWSCloudTrail_FullAccess

**Risk**: HIGH
**Why prohibited**: Holders of `AWSCloudTrail_FullAccess` "have the ability to disable or
reconfigure the most sensitive and important auditing functions." Wide grants let an attacker
(or malicious insider) silently turn off logging — a classic cover-your-tracks technique.

```
# WRONG
IAM policy attachment: AWSCloudTrail_FullAccess on "DeveloperGroup" (100+ users)
No SCP restricting cloudtrail:StopLogging / cloudtrail:DeleteTrail

# Detection
aws iam list-entities-for-policy \
  --policy-arn arn:aws:iam::aws:policy/AWSCloudTrail_FullAccess
# If this returns more than ~2-3 admin principals: over-provisioned
```

```bash
# CORRECT
# 1. Limit AWSCloudTrail_FullAccess to the fewest account administrators possible
# 2. Add an SCP at the organization root to prevent disabling logging even for admins
# (break-glass role is the only exception via condition key)
```

**SCP to deny trail tampering:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyCloudTrailTampering",
      "Effect": "Deny",
      "Action": [
        "cloudtrail:StopLogging",
        "cloudtrail:DeleteTrail",
        "cloudtrail:UpdateTrail"
      ],
      "Resource": "*",
      "Condition": {
        "ArnNotLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:role/BreakGlassCloudTrailAdmin"
        }
      }
    }
  ]
}
```

**Impact if not corrected**: Audit logging silently disabled by a compromised credential;
complete loss of visibility; forensic timeline destroyed.

---

## A6 — Building NEW audit-analytics architecture on CloudTrail Lake in 2026

**Risk**: MEDIUM
**Why prohibited**: CloudTrail Lake is closed to new customers from **2026-05-31**. New
dependencies build on a feature that receives only critical bug/security fixes and has no
new-customer onboarding — a dead end for architecture investment.

```
# WRONG (for a non-existing-customer account)
Design: "Create CloudTrail Lake event data store for 7-year audit retention"
aws cloudtrail create-event-data-store \
  --name audit-eds \
  --retention-period 2557
# For a new account post-2026-05-31: this will be rejected / not recommended

# Detection
Design review references creating new EDS in a non-existing-customer account.
```

```
# CORRECT for new builds
Option A (recommended): Amazon CloudWatch
  - Native OpenSearch analytics, OCSF/OTel ingestion, Apache Iceberg access
  - Supports 60+ AWS sources including CloudTrail
  - Replaces Lake as the recommended analytics target per AWS (2026)

Option B (lowest cost): S3 + Athena
  - Trail delivers to S3; Glue crawler for schema; Athena for ad-hoc SQL
  - Most portable (Parquet/Iceberg); lowest at-rest cost
  - Best for infrequent forensic queries and low-budget estates

Both: CloudTrail trails (not Lake) remain the durable event-delivery primitive.
```

**Impact if not corrected**: Architecture built on a feature not accepting new customers;
future rework required; no Lake support roadmap for new builds.

**Source**: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake-service-availability-change.html (accessed 2026-08-26)
