# Always-Do Patterns — AWS CloudTrail 2025

> Source: [research_aws_cloudtrail_2025.md](../../../docs/research_aws_cloudtrail_2025.md), verified 2026-07-31.
> All AWS CLI commands target the 2025 CloudTrail API. Degree of freedom: **Low** for all patterns (security-critical, consistency required).

---

## AD-1 — Multi-Region Trail Covering All Enabled Regions

**Why**: A complete record of activity requires all enabled Regions; multi-Region trails guarantee global service event logging (IAM/STS/CloudFront in us-east-1 since 2021-11-22) and detect activity in otherwise-unused Regions. Maps to Security Hub CloudTrail.1 (High) and CIS 3.1.

**WAF Pillars**: Security, Reliability

```bash
# ✅ CORRECT — Create a multi-region trail
aws cloudtrail create-trail \
  --name org-trail \
  --s3-bucket-name <log-archive-bucket> \
  --is-multi-region-trail \
  --include-global-service-events \
  --enable-log-file-validation \
  --kms-key-id <kms-key-arn>

# ✅ CORRECT — Convert an existing single-region trail
aws cloudtrail update-trail \
  --name <existing-trail-name> \
  --is-multi-region-trail \
  --include-global-service-events

# Verify
aws cloudtrail describe-trails \
  --query 'trailList[].{Name:Name,MultiRegion:IsMultiRegionTrail,Global:IncludeGlobalServiceEvents}'
# Expected: IsMultiRegionTrail=true, IncludeGlobalServiceEvents=true

# Enforce continuously
# AWS Config rule: multi-region-cloud-trail-enabled
```

**Trade-offs**: Slightly more management-event volume (first copy is still free); no meaningful latency cost.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html (accessed 2026-07-31)

---

## AD-2 — Organization Trail via AWS Organizations (with Delegated Administrator)

**Why**: One org trail covers every current and future account; member accounts cannot stop/modify it. Closes the "disable-my-own-audit" gap. New accounts auto-enroll via `AWSServiceRoleForCloudTrail`.

**WAF Pillars**: Security, Operational Excellence, Reliability

```bash
# ✅ CORRECT — Register a delegated admin (from management account)
aws cloudtrail register-organization-delegated-admin \
  --member-account-id <security-account-id>

# ✅ CORRECT — Create organization trail (run from management account or delegated admin)
aws cloudtrail create-trail \
  --name org-trail \
  --s3-bucket-name <log-archive-bucket> \
  --is-multi-region-trail \
  --include-global-service-events \
  --is-organization-trail \
  --enable-log-file-validation \
  --kms-key-id <kms-key-arn>

aws cloudtrail start-logging --name org-trail

# Verify — management/delegated-admin account
aws cloudtrail describe-trails \
  --query 'trailList[?IsOrganizationTrail==`true`].[Name,IsMultiRegionTrail,S3BucketName]'

# Verify — member account (can see ARN, cannot modify)
aws cloudtrail list-trails
```

**Trade-offs**: Requires trusted access enabled between Organizations and CloudTrail; org trail can only be modified in its home Region by management/delegated-admin.

Do not delete `AWSServiceRoleForCloudTrail` in member accounts — it is required for org logging and is managed by CloudTrail.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html (accessed 2026-07-31)

---

## AD-3 — Dedicated, Centralized S3 Log-Archive Bucket in a Separate Account

**Why**: Integrity, completeness, and availability of logs require segregation of duties — audited principals must not control the log store.

**WAF Pillars**: Security

```json
// ✅ CORRECT — Minimal S3 bucket policy for the Log Archive bucket
// Replace <log-archive-account-id>, <management-account-id>, <org-id>, <trail-arn>
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AWSCloudTrailAclCheck",
      "Effect": "Allow",
      "Principal": {"Service": "cloudtrail.amazonaws.com"},
      "Action": "s3:GetBucketAcl",
      "Resource": "arn:aws:s3:::<log-archive-bucket>",
      "Condition": {"StringEquals": {"aws:SourceArn": "<trail-arn>"}}
    },
    {
      "Sid": "AWSCloudTrailWrite",
      "Effect": "Allow",
      "Principal": {"Service": "cloudtrail.amazonaws.com"},
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::<log-archive-bucket>/AWSLogs/*",
      "Condition": {
        "StringEquals": {
          "s3:x-amz-acl": "bucket-owner-full-control",
          "aws:SourceArn": "<trail-arn>"
        }
      }
    }
  ]
}
```

```bash
# Verify bucket ownership and policy
aws s3api get-bucket-policy --bucket <log-archive-bucket>
# Confirm: aws:SourceArn condition present; no member-account principals with write/delete
```

**Trade-offs**: Cross-account setup complexity; one more account to govern. Use the AWS Organizations multi-account landing zone pattern.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)

---

## AD-4 — Server-Side Encryption with SSE-KMS (Customer-Managed Key)

**Why**: SSE-KMS adds a key-policy access-control layer over audit logs and satisfies encryption-at-rest compliance. Maps to Security Hub CloudTrail.2 (Medium) / CIS 3.5; and CloudTrail.10 for Lake EDS.

**WAF Pillars**: Security

```bash
# ✅ CORRECT — Set KMS key on trail
aws cloudtrail update-trail \
  --name <trail-name> \
  --kms-key-id <kms-key-arn>

# Verify
aws cloudtrail get-trail --name <trail-name> --query 'Trail.KmsKeyId'
# Expected: full KMS key ARN

# AWS Config rule: cloud-trail-encryption-enabled

# ✅ CORRECT — Associate KMS key on CloudTrail Lake EDS
# Note: KMS key on an EDS CANNOT be changed/removed after association — plan carefully
aws cloudtrail create-event-data-store \
  --name org-eds \
  --kms-key-id <kms-key-arn> \
  --organization-enabled \
  --multi-region-enabled \
  --retention-period 365
```

**Trade-offs**: KMS API request charges; key-policy misconfiguration can block trail delivery (`KMSAccessDeniedException`). If the S3 bucket policy forces SSE-KMS, the bucket's default encryption algorithm must also allow the CloudTrail service principal.

Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html (accessed 2026-07-31)

---

## AD-5 — Log File Integrity Validation Enabled

**Why**: Produces SHA-256 hashes and SHA-256/RSA-signed digest files, making it computationally infeasible to modify, delete, or forge logs without detection. Essential for forensics and legal admissibility. Maps to Security Hub CloudTrail.4 / CIS 3.2.

**WAF Pillars**: Security

```bash
# ✅ CORRECT — Enable on trail creation (already shown in AD-1) or update
aws cloudtrail update-trail \
  --name <trail-name> \
  --enable-log-file-validation

# Verify attribute
aws cloudtrail get-trail --name <trail-name> --query 'Trail.LogFileValidationEnabled'
# Expected: true

# AWS Config rule: cloud-trail-log-file-validation-enabled

# ✅ CORRECT — Run validation during audit close
aws cloudtrail validate-logs \
  --trail-arn <trail-arn> \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z
# Expected: "No validation errors found"
# Any output listing modified/deleted files = tamper indicator
```

**Trade-offs**: Negligible cost; digest files add tiny storage. No meaningful downside — always enable.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)

---

## AD-6 — CloudWatch Logs Integration for Real-Time Monitoring and Alarms

**Why**: S3 delivery is for durable storage; CloudWatch Logs enables real-time alerting on StopLogging, root usage, IAM policy changes. Maps to Security Hub CloudTrail.5 / CIS 3.4.

**WAF Pillars**: Operational Excellence, Security

```bash
# ✅ CORRECT — Set CloudWatch Logs on trail (IAM role required for CloudTrail to deliver)
aws cloudtrail update-trail \
  --name <trail-name> \
  --cloud-watch-logs-log-group-arn <log-group-arn> \
  --cloud-watch-logs-role-arn <cloudtrail-cw-role-arn>

# Verify
aws cloudtrail get-trail --name <trail-name> \
  --query 'Trail.CloudWatchLogsLogGroupArn'
# Expected: non-null ARN

# AWS Config rule: cloud-trail-cloud-watch-logs-enabled
```

**Mandatory metric filters to create** (create CloudWatch Alarm + SNS for each):

| Filter purpose | Filter pattern | Security Hub mapping |
|---|---|---|
| Trail stopped or deleted | `{ ($.eventName = StopLogging) || ($.eventName = DeleteTrail) || ($.eventName = UpdateTrail) }` | CIS 3.5 |
| Root account usage | `{ $.userIdentity.type = "Root" && $.userIdentity.invokedBy NOT EXISTS && $.eventType != "AwsServiceEvent" }` | CIS 1.1 |
| Unauthorized API calls | `{ ($.errorCode = "*UnauthorizedAccess*") || ($.errorCode = "AccessDenied*") }` | CIS 3.1 |
| IAM policy changes | `{ ($.eventName = DeleteGroupPolicy) || ($.eventName = DeleteRolePolicy) || ($.eventName = PutGroupPolicy) || ($.eventName = PutRolePolicy) || ($.eventName = PutUserPolicy) }` | CIS 3.4 |
| Console sign-in without MFA | `{ ($.eventName = "ConsoleLogin") && ($.additionalEventData.MFAUsed != "Yes") }` | CIS 1.2 |

**Trade-offs**: CloudWatch Logs delivery from CloudTrail billed at $0.25/GB delivered + standard ingest/storage. Scope selectors carefully to control cost.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudwatch-alarms-for-cloudtrail.html (accessed 2026-07-31)

---

## AD-7 — S3 Server Access Logging on the CloudTrail Bucket

**Why**: Captures every request against the log bucket itself — critical for detecting attempts to read/tamper with audit data. Maps to Security Hub CloudTrail.7 / CIS 3.6.

**WAF Pillars**: Security

```bash
# ✅ CORRECT — Enable server access logging to a SEPARATE target bucket
aws s3api put-bucket-logging \
  --bucket <log-archive-bucket> \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "<separate-access-log-bucket>",
      "TargetPrefix": "cloudtrail-access-logs/"
    }
  }'

# Verify
aws s3api get-bucket-logging --bucket <log-archive-bucket>
# Expected: TargetBucket != <log-archive-bucket>  (never same bucket — avoids logging loop)
```

**Trade-offs**: Small storage cost for access logs; access logs are best-effort (delivered on a best-effort basis, not guaranteed real-time or guaranteed delivery of all records).

Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html (accessed 2026-07-31)

---

## AD-8 — SNS Notification on Log File Delivery (with SourceArn Condition)

**Why**: Signals downstream consumers that a new log file is available and provides a delivery heartbeat. The SNS topic policy must be hardened against confused-deputy attacks.

**WAF Pillars**: Operational Excellence, Security

```bash
# ✅ CORRECT — Set SNS topic on trail
aws cloudtrail update-trail \
  --name <trail-name> \
  --sns-topic-name <sns-topic-name>

# Verify delivery config
aws cloudtrail get-trail --name <trail-name> --query 'Trail.SnsTopicARN'

# ✅ CORRECT — Harden the SNS topic policy
# Add aws:SourceArn condition to prevent confused-deputy access
# sns:Publish only for cloudtrail.amazonaws.com with matching SourceArn
aws sns get-topic-attributes --topic-arn <sns-topic-arn> \
  --query 'Attributes.Policy'
# Expected: Condition block with aws:SourceArn = <trail-arn>
```

**Trade-offs**: One SNS notification per delivered log file — can be high volume; route to SQS/Lambda for async processing rather than human inbox.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)

---

## AD-9 — AWS Config Integration for Continuous Compliance Evaluation

**Why**: CloudTrail records what happened; AWS Config continuously evaluates whether trails remain compliant. Deploy org-wide via conformance pack.

**WAF Pillars**: Security, Operational Excellence

```bash
# ✅ CORRECT — Verify compliance of the four core CloudTrail Config rules
aws configservice describe-compliance-by-config-rule \
  --config-rule-names \
    multi-region-cloud-trail-enabled \
    cloud-trail-encryption-enabled \
    cloud-trail-log-file-validation-enabled \
    cloud-trail-cloud-watch-logs-enabled \
    cloudtrail-enabled \
  --query 'ComplianceByConfigRules[].{Rule:ConfigRuleName,Status:Compliance.ComplianceType}'
# Expected: ComplianceType = COMPLIANT for all rules

# ✅ CORRECT — Deploy as a conformance pack org-wide (run from Config delegated admin)
# Conformance pack: AWS-OperationalBestPracticesForCloudTrail
aws configservice put-organization-conformance-pack \
  --organization-conformance-pack-name cloudtrail-best-practices \
  --template-s3-uri s3://<config-bucket>/conformance-packs/cloudtrail-pack.yaml
```

**Trade-offs**: AWS Config per-evaluation charges; requires Config recorder enabled in each account first.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)

---

## AD-10 — S3 Object Lock (WORM) for Immutable Log Retention

**Why**: Object Lock enforces write-once-read-many so logs cannot be deleted/overwritten for the retention period — the strongest anti-tamper control. Compliance mode retention cannot be shortened by anyone, including root.

**WAF Pillars**: Security, Compliance

> Choose EITHER Object Lock OR MFA Delete — they serve the same immutability purpose. **Object Lock is the automatable enterprise default** because MFA Delete is incompatible with S3 lifecycle configuration. Use MFA Delete only when lifecycle tiering is definitively not required.

```bash
# ✅ CORRECT — Object Lock must be enabled at BUCKET CREATION (cannot be added after)
aws s3api create-bucket \
  --bucket <log-archive-bucket> \
  --region us-east-1 \
  --object-lock-enabled-for-bucket

# Apply default Compliance-mode retention (e.g. 2557 days = ~7 years)
aws s3api put-object-lock-configuration \
  --bucket <log-archive-bucket> \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "COMPLIANCE",
        "Days": 2557
      }
    }
  }'

# Verify
aws s3api get-object-lock-configuration --bucket <log-archive-bucket>
# Expected: ObjectLockEnabled=Enabled, Mode=COMPLIANCE

# ✅ ALTERNATIVE — MFA Delete (when lifecycle NOT needed)
# Can only be enabled/disabled by the bucket-owner root user with an MFA device
aws s3api put-bucket-versioning \
  --bucket <log-archive-bucket> \
  --versioning-configuration 'Status=Enabled,MFADelete=Enabled' \
  --mfa "<serial-number> <mfa-token>"

aws s3api get-bucket-versioning --bucket <log-archive-bucket>
# Expected: Status=Enabled, MFADelete=Enabled
```

**Trade-offs (Object Lock)**: Compliance mode retention CANNOT be shortened — plan the retention period with legal/compliance before applying. Must be enabled at bucket creation.
**Trade-offs (MFA Delete)**: Operationally heavy (root user + MFA device required for any toggle); incompatible with lifecycle configuration.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)

---

## AD-11 — CloudTrail Lake for Advanced SQL Querying and Long Retention

**Why**: Provides serverless SQL over immutable event data stores (up to ~10 years), org-wide/multi-Region aggregation, and ingestion of non-AWS events — without operating a DIY S3+Athena+Glue pipeline.

**WAF Pillars**: Security, Performance Efficiency

```bash
# ✅ CORRECT — Create an organization EDS (run from management account or delegated admin)
aws cloudtrail create-event-data-store \
  --name org-eds \
  --organization-enabled \
  --multi-region-enabled \
  --kms-key-id <kms-key-arn> \
  --retention-period 365   # One-year extendable tier; set up to 3653 days

# Verify
aws cloudtrail list-event-data-stores \
  --query 'EventDataStores[].{Name:Name,Status:Status,Retention:RetentionPeriod,OrgEnabled:OrganizationEnabled}'
# Expected: Status=ENABLED, OrganizationEnabled=true

# ✅ CORRECT — Run a SQL query (replace <eds-id> with event data store ARN or ID)
aws cloudtrail start-query \
  --query-statement "SELECT eventName, userIdentity.arn, COUNT(*) AS cnt
                     FROM <eds-id>
                     WHERE eventTime > '2025-01-01 00:00:00'
                       AND eventCategory = 'Management'
                     GROUP BY eventName, userIdentity.arn
                     ORDER BY cnt DESC
                     LIMIT 20"
# Returns a queryId — retrieve results with:
aws cloudtrail get-query-results --event-data-store <eds-id> --query-id <query-id>
```

**Pricing (One-year extendable tier)**:
- Ingestion: $0.75/GB (CloudTrail events), $0.50/GB (other sources)
- Extended storage: $0.023/GB/month beyond the included 90 days
- Query: $0.005/GB scanned

**Trade-offs**: Lake billed separately from a trail — both can coexist and serve different consumers. KMS key on an EDS is immutable once set. For very large environments consider Seven-year retention tier pricing (tiered at $2.5/$1/$0.50 per GB).

Source: https://aws.amazon.com/cloudtrail/pricing/ and https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html (accessed 2026-07-31)
