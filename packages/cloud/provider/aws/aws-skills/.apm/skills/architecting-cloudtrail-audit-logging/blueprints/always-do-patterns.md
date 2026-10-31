# Always-Do Patterns — AWS CloudTrail Audit Logging (2026)

Full configuration details for the 7 mandatory patterns summarised in SKILL.md.

---

## M1 — Deploy a multi-Region organization trail

**Pillar**: Security (traceability), Operational Excellence
**Degree of freedom**: Low — fragile, must be exact

```bash
# Create from management account (or delegated CloudTrail administrator account)
aws cloudtrail create-trail \
  --name org-cloudtrail-central \
  --s3-bucket-name <log-archive-account-audit-bucket> \
  --is-multi-region-trail \
  --include-global-service-events \
  --is-organization-trail \
  --cloud-watch-logs-log-group-arn <log-group-arn> \
  --cloud-watch-logs-role-arn <delivery-role-arn> \
  --kms-key-id <cmk-arn>

aws cloudtrail update-trail \
  --name org-cloudtrail-central \
  --enable-log-file-validation

aws cloudtrail start-logging --name org-cloudtrail-central
```

**Verification:**
```bash
aws cloudtrail describe-trails \
  --query 'trailList[?IsOrganizationTrail==`true` && IsMultiRegionTrail==`true`].[Name,HomeRegion,KmsKeyId]'
# Security Hub: CloudTrail.1
# AWS Config: multi-region-cloudtrail-enabled
```

**Architecture note:** `IsOrganizationTrail=true` requires the calling account to be the
management account or a delegated CloudTrail administrator. A copy is auto-created in each
member account and cannot be altered or disabled by member-account users.

---

## M2 — Deliver logs to a dedicated S3 bucket in a separate log-archive account

**Pillar**: Security (segregation of duties, log integrity/availability)
**Degree of freedom**: Medium — pattern prescribed, implementation varies per org

**Bucket policy — minimum required by CloudTrail (apply in log-archive account):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AWSCloudTrailAclCheck",
      "Effect": "Allow",
      "Principal": {"Service": "cloudtrail.amazonaws.com"},
      "Action": "s3:GetBucketAcl",
      "Resource": "arn:aws:s3:::<audit-bucket-name>",
      "Condition": {
        "StringEquals": {"aws:SourceArn": "arn:aws:cloudtrail:<region>:<mgmt-account-id>:trail/org-cloudtrail-central"}
      }
    },
    {
      "Sid": "AWSCloudTrailWrite",
      "Effect": "Allow",
      "Principal": {"Service": "cloudtrail.amazonaws.com"},
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::<audit-bucket-name>/AWSLogs/<org-id>/*",
      "Condition": {
        "StringEquals": {
          "s3:x-amz-acl": "bucket-owner-full-control",
          "aws:SourceArn": "arn:aws:cloudtrail:<region>:<mgmt-account-id>:trail/org-cloudtrail-central"
        }
      }
    }
  ]
}
```

> If the bucket policy enforces `deny-unless-SSE-KMS`, also allow `AES256` in the
> `s3:x-amz-server-side-encryption` condition or trail creation fails.

---

## M3 — Enable log file integrity validation

**Pillar**: Security (tamper-evidence, forensics)
**Degree of freedom**: Low — binary flag, must be set

```bash
# Enable on existing trail
aws cloudtrail update-trail \
  --name org-cloudtrail-central \
  --enable-log-file-validation

# Validate logs (run after incidents or as part of scheduled audit)
aws cloudtrail validate-logs \
  --trail-arn arn:aws:cloudtrail:<region>:<mgmt-account-id>:trail/org-cloudtrail-central \
  --start-time 2026-08-01T00:00:00Z \
  --end-time 2026-08-26T23:59:59Z
# Expected: no INVALID or MISSING log files in the range
```

**Verification:**
```bash
aws configservice describe-compliance-by-config-rule \
  --config-rule-names cloud-trail-log-file-validation-enabled
# Security Hub: CloudTrail.4
```

---

## M4 — Encrypt log files with SSE-KMS using a customer managed key

**Pillar**: Security (confidentiality of audit data)
**Degree of freedom**: Low — CMK key policy is exact; do not use AWS-managed keys

**KMS key policy excerpt (add to CMK):**
```json
{
  "Sid": "Allow CloudTrail to encrypt logs",
  "Effect": "Allow",
  "Principal": {"Service": "cloudtrail.amazonaws.com"},
  "Action": "kms:GenerateDataKey*",
  "Resource": "*",
  "Condition": {
    "StringLike": {"kms:EncryptionContext:aws:cloudtrail:arn": "arn:aws:cloudtrail:*:<mgmt-account-id>:trail/*"},
    "StringEquals": {"aws:SourceArn": "arn:aws:cloudtrail:<region>:<mgmt-account-id>:trail/org-cloudtrail-central"}
  }
},
{
  "Sid": "Allow CloudTrail to describe key",
  "Effect": "Allow",
  "Principal": {"Service": "cloudtrail.amazonaws.com"},
  "Action": "kms:DescribeKey",
  "Resource": "*"
}
```

```bash
aws cloudtrail update-trail \
  --name org-cloudtrail-central \
  --kms-key-id <cmk-arn>

# Verify
aws cloudtrail describe-trails \
  --query 'trailList[?KmsKeyId==null]'
# Expected: empty array
# Security Hub: CloudTrail.2
# AWS Config: cloud-trail-encryption-enabled
```

---

## M5 — Protect the audit bucket: least-privilege + MFA delete/versioning + lifecycle

**Pillar**: Security (integrity/availability of logs)
**Degree of freedom**: Medium — controls required, implementation varies

```bash
# Enable versioning (prerequisite for MFA delete)
aws s3api put-bucket-versioning \
  --bucket <audit-bucket-name> \
  --versioning-configuration Status=Enabled

# Enable MFA delete (requires root credentials of bucket-owner account)
aws s3api put-bucket-versioning \
  --bucket <audit-bucket-name> \
  --versioning-configuration Status=Enabled,MFADelete=Enabled \
  --mfa "arn:aws:iam::<account-id>:mfa/root-account-mfa-device <mfa-code>"
```

> MFA-delete-enabled buckets do NOT support lifecycle configuration on the same bucket.
> If you need both deletion protection AND automated tiering, use separate buckets:
> one MFA-delete-protected for short-term active logs, one lifecycle-enabled archive bucket.

**Security Hub controls to verify:**
- CloudTrail.6 — S3 bucket not publicly accessible
- CloudTrail.7 — S3 access logging enabled on the audit bucket

---

## M6 — Stream trail events to CloudWatch Logs for real-time alerting

**Pillar**: Security (detection), Operational Excellence (monitoring)
**Degree of freedom**: Medium — integration required; metric filter set is high-freedom

**CIS AWS Foundations Benchmark monitoring recommendations (metric filters to create):**

| Filter name | Pattern | Why |
|---|---|---|
| RootUsage | `{ $.userIdentity.type = "Root" }` | Root account usage is always suspicious |
| IAMPolicyChanges | `{ ($.eventName=DeleteGroupPolicy) || ($.eventName=DeleteRolePolicy) || ($.eventName=DeleteUserPolicy) || ($.eventName=PutGroupPolicy) || ($.eventName=PutRolePolicy) || ($.eventName=PutUserPolicy) || ($.eventName=CreatePolicy) || ($.eventName=DeletePolicy) || ($.eventName=CreatePolicyVersion) || ($.eventName=DeletePolicyVersion) || ($.eventName=SetDefaultPolicyVersion) }` | IAM policy modifications |
| CloudTrailChanges | `{ ($.eventName=CreateTrail) || ($.eventName=UpdateTrail) || ($.eventName=DeleteTrail) || ($.eventName=StartLogging) || ($.eventName=StopLogging) }` | Trail tampering |
| UnauthorizedAPICalls | `{ ($.errorCode=AccessDenied) || ($.errorCode=UnauthorizedOperation) }` | Lateral movement / privilege escalation attempts |
| AccountMembershipChanges (2026) | `{ ($.eventName=AccountJoinedOrganization) || ($.eventName=AccountDepartedOrganization) }` | Unauthorized org-membership changes |

```bash
# Verify CloudWatch Logs integration is active
aws cloudtrail get-trail-status --name org-cloudtrail-central \
  --query '{CloudWatchLogsLogGroupArn:CloudWatchLogsLogGroupArn,LatestCloudWatchLogsDeliveryTime:LatestCloudWatchLogsDeliveryTime}'
# Expected: CloudWatchLogsLogGroupArn non-null; LatestCloudWatchLogsDeliveryTime recent
# Security Hub: CloudTrail.5
# AWS Config: cloud-trail-cloud-watch-logs-enabled
```

---

## M7 — Layer GuardDuty (threat detection) and Security Hub CSPM (posture)

**Pillar**: Security (detection, continuous compliance)
**Degree of freedom**: High — enable org-wide; configuration of findings/standards is flexible

```bash
# Enable GuardDuty for the organization (from management account)
aws guardduty create-detector --enable --finding-publishing-frequency FIFTEEN_MINUTES
aws guardduty create-members --detector-id <detector-id> --account-details ...

# Enable Security Hub with AWS Foundational Security Best Practices
aws securityhub enable-security-hub --enable-default-standards
# This auto-enrolls: AWS Foundational Security Best Practices (CloudTrail.1-7 included)
# Add CIS AWS Foundations Benchmark v1.4 separately if required

# Check CloudTrail control set status
aws securityhub get-findings \
  --filters '{"GeneratorId":[{"Value":"cloudtrail","Comparison":"PREFIX"}],"ComplianceStatus":[{"Value":"FAILED","Comparison":"EQUALS"}]}' \
  --query 'Findings[].{Control:Title,Severity:Severity.Label,Status:Compliance.Status}'
```

**GuardDuty threat types sourced from CloudTrail:**
- `UnauthorizedAccess:IAMUser/ConsoleLoginSuccess.B` — anomalous console login
- `Recon:IAMUser/UserPermissions` — permission enumeration
- `PrivilegeEscalation:IAMUser/AdministrativePermissions` — privilege escalation attempts
- `Stealth:IAMUser/CloudTrailLoggingDisabled` — trail disabled (directly relevant)
