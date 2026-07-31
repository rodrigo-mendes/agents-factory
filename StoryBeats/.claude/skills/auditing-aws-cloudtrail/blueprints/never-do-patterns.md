# Never-Do Anti-Patterns — AWS CloudTrail 2025

> Source: [research_aws_cloudtrail_2025.md](../../../docs/research_aws_cloudtrail_2025.md), verified 2026-07-31.
> Each anti-pattern includes the risk level, blast radius, `# WRONG` pattern, and `# CORRECT` alternative.

---

## NP-1 — Disabling CloudTrail / Leaving Regions Without Trail Coverage

**Risk Level**: CRITICAL
**Blast Radius**: Entire account/org — every action becomes unauditable; fails Security Hub CloudTrail.1/CIS 3.1.

```bash
# WRONG — No trail, or single-Region trail outside us-east-1
aws cloudtrail describe-trails
# Returns no multi-region trail  OR  shows IsMultiRegionTrail=false
# Result: all IAM/STS/CloudFront activity silently unlogged; other Regions unaudited

# CORRECT — One multi-Region org trail covering all enabled Regions
aws cloudtrail create-trail \
  --name org-trail \
  --s3-bucket-name <log-archive-bucket> \
  --is-multi-region-trail \
  --include-global-service-events \
  --is-organization-trail \
  --enable-log-file-validation

aws cloudtrail start-logging --name org-trail

# Continuous enforcement
# AWS Config: multi-region-cloud-trail-enabled
# Security Hub: CloudTrail.1 (High), CloudTrail.3 (High)
```

**Impact**: Compliance violation; undetectable breach; fails PCI DSS Req 10, SOC 2 CC7, CIS 3.1.

Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html (accessed 2026-07-31)

---

## NP-2 — Storing Logs in the Same Account Being Audited

**Risk Level**: HIGH
**Blast Radius**: All audit evidence for that account — audited principals can read/alter/delete the evidence of their own actions.

```bash
# WRONG — Trail delivering to an S3 bucket in the same account as workloads/admins
aws cloudtrail describe-trails \
  --query 'trailList[].{Trail:Name,Bucket:S3BucketName}'
# The bucket owner account == the account running workloads
# An admin who can run workloads can also run: aws s3 rm s3://<bucket> --recursive

# CORRECT — Trail delivers to a dedicated Log Archive account
# Bucket resides in a DIFFERENT AWS account; only trusted auditors have read access
# See AD-3 in always-do-patterns.md for the bucket policy
aws s3api get-bucket-policy --bucket <log-archive-bucket>
# Confirm: bucket owner account != any audited account
```

**Impact**: Log tampering; repudiation; compliance violation; forensic evidence inadmissible.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)

---

## NP-3 — CloudTrail S3 Bucket Without Block Public Access

**Risk Level**: CRITICAL
**Blast Radius**: All historical logs in the bucket — exposes log content for adversary reconnaissance; fails Security Hub CloudTrail.6 (Critical) / CIS 3.3.

```bash
# WRONG — Block Public Access not enabled
aws s3api get-public-access-block --bucket <cloudtrail-bucket>
# Returns: BlockPublicAcls: false  OR  command returns AccessDenied (public bucket)

# CORRECT — All four Block Public Access settings enabled on bucket AND account level
aws s3api put-public-access-block \
  --bucket <log-archive-bucket> \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Verify
aws s3api get-public-access-block --bucket <log-archive-bucket>
# Expected: all four = true

# Also enforce via SCP at org level:
# Deny s3:PutBucketPublicAccessBlock where the value disables any block setting
# Security Hub: CloudTrail.6 (Critical)
```

**Impact**: Data breach / reconnaissance exposure — adversary can enumerate API call patterns, IP addresses, account structure.

Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html (accessed 2026-07-31)

---

## NP-4 — No Log File Integrity Validation

**Risk Level**: HIGH
**Blast Radius**: Evidentiary value of the entire log set — without signed digests you cannot prove logs were not modified/deleted.

```bash
# WRONG — Trail with integrity validation disabled
aws cloudtrail get-trail --name <trail-name> \
  --query 'Trail.LogFileValidationEnabled'
# Returns: false

# CORRECT — Enable on every trail; never omit
aws cloudtrail update-trail \
  --name <trail-name> \
  --enable-log-file-validation

# Validate periodically
aws cloudtrail validate-logs \
  --trail-arn <trail-arn> \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z
# No output = no tampering detected

# AWS Config rule: cloud-trail-log-file-validation-enabled
# Security Hub: CloudTrail.4 (Low) / CIS 3.2
```

**Impact**: Compliance violation; unprovable/forgeable evidence; forensic inadmissibility.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)

---

## NP-5 — Default Management-Only Trail for Sensitive S3 / Lambda / DynamoDB

**Risk Level**: HIGH
**Blast Radius**: Sensitive data stores — no record of who read or exfiltrated data.

```bash
# WRONG — Trail using default selectors only (management events)
aws cloudtrail get-event-selectors --trail-name <trail-name>
# Returns: ReadWriteType=All with no DataResources entries
# Result: S3 GetObject/PutObject/DeleteObject, Lambda Invoke, DynamoDB PutItem — ALL INVISIBLE

# CORRECT — Add advanced event selectors for each sensitive resource type
# Example: S3 writes for a sensitive bucket, Lambda invocations for a specific function
aws cloudtrail put-event-selectors \
  --trail-name <trail-name> \
  --advanced-event-selectors '[
    {
      "Name": "s3-sensitive-bucket-writes",
      "FieldSelectors": [
        {"Field": "eventCategory", "Equals": ["Data"]},
        {"Field": "resources.type", "Equals": ["AWS::S3::Object"]},
        {"Field": "resources.ARN", "StartsWith": ["arn:aws:s3:::<sensitive-bucket>/"]},
        {"Field": "readOnly", "Equals": ["false"]}
      ]
    },
    {
      "Name": "lambda-all-invocations",
      "FieldSelectors": [
        {"Field": "eventCategory", "Equals": ["Data"]},
        {"Field": "resources.type", "Equals": ["AWS::Lambda::Function"]},
        {"Field": "resources.ARN", "Equals": ["arn:aws:lambda:<region>:<account>:function:<function-name>"]}
      ]
    }
  ]'
```

**Cost warning**: Data events are billed at $0.10/100k events. Always scope to specific resources and operation types (reads vs writes) to avoid bill shock.

**Impact**: Data breach undetected; compliance gap for regulated data (HIPAA, PCI DSS, GDPR).

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html (accessed 2026-07-31)

---

## NP-6 — No CloudTrail Insights for High-Value Environments

**Risk Level**: MEDIUM
**Blast Radius**: Time-to-detect for anomalous automation or credential abuse — Insights analyzes management write API rate and error rate.

```bash
# WRONG — Insights disabled; anomalies only found in retrospective queries
aws cloudtrail get-insight-selectors --trail-name <trail-name>
# Returns: InsightSelectors=[] OR command not applicable (Insights not enabled)

# CORRECT — Enable Insights (write management API rate + error rate) on the org trail
aws cloudtrail put-insight-selectors \
  --trail-name <trail-name> \
  --insight-selectors '[
    {"InsightType": "ApiCallRateInsight"},
    {"InsightType": "ApiErrorRateInsight"}
  ]'

# Route Insights events to alerting (Insights events delivered to a sub-path in the same S3 bucket
# and to CloudWatch Logs if configured)
aws cloudtrail get-insight-selectors --trail-name <trail-name>
# Expected: ApiCallRateInsight and ApiErrorRateInsight both listed
```

**Pricing**: $0.35 per 100,000 management events analyzed (trail-based).

**Impact**: Delayed breach detection — credential misuse, mass DeleteBucket, runaway automation runs undetected until damage is done.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html (accessed 2026-07-31)

---

## NP-7 — Log Archive S3 Bucket Writable or Accessible by Audited Accounts

**Risk Level**: CRITICAL
**Blast Radius**: Integrity of the entire centralized log store — audited accounts can tamper with or destroy evidence.

```bash
# WRONG — Bucket policy grants audited member accounts s3:DeleteObject or s3:PutBucketPolicy
aws s3api get-bucket-policy --bucket <log-archive-bucket>
# Policy contains: Principal: {"AWS": "arn:aws:iam::<member-account-id>:root"}
#   Action: ["s3:DeleteObject", "s3:PutObject", "s3:PutBucketPolicy"]
# Result: member account admin can delete their own evidence

# CORRECT — Only CloudTrail service principal may write; with aws:SourceArn condition
# No audited principal has delete/overwrite rights
# Combined with S3 Object Lock (see AD-10) for defense-in-depth
aws s3api get-bucket-policy --bucket <log-archive-bucket>
# Expected policy allows:
#   Principal: cloudtrail.amazonaws.com  Action: s3:GetBucketAcl, s3:PutObject
#   Condition: aws:SourceArn = <trail-arn>
# No other principals have write or delete actions
```

**Impact**: Log tampering; repudiation; compliance violation; forensic evidence destroyed.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)

---

## NP-8 — No Alerting When a Trail Is Stopped or Modified

**Risk Level**: HIGH
**Blast Radius**: All subsequent activity becomes invisible — an attacker's first move is often `StopLogging` / `DeleteTrail`.

```bash
# WRONG — No metric filter or EventBridge rule on trail-disruption events
aws logs describe-metric-filters \
  --log-group-name <cloudtrail-log-group>
# No filter pattern matching StopLogging/DeleteTrail/UpdateTrail

# CORRECT — CloudWatch Logs metric filter + alarm + SNS
aws logs put-metric-filter \
  --log-group-name <cloudtrail-log-group> \
  --filter-name trail-stop-or-modify \
  --filter-pattern '{ ($.eventName = StopLogging) || ($.eventName = DeleteTrail) || ($.eventName = UpdateTrail) }' \
  --metric-transformations \
    metricName=TrailStopOrModify,metricNamespace=CloudTrailAlerts,metricValue=1

aws cloudwatch put-metric-alarm \
  --alarm-name trail-stop-or-modify \
  --metric-name TrailStopOrModify \
  --namespace CloudTrailAlerts \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions <sns-topic-arn>

# CORRECT — EventBridge rule for automated remediation (re-enable a stopped trail)
# Rule: source=aws.cloudtrail, detail-type=AWS API Call via CloudTrail
#       detail.eventName = StopLogging
# Target: Lambda function that calls aws cloudtrail start-logging
```

**Impact**: Undetected audit blackout during an incident; attacker operates silently after disabling logging.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudwatch-alarms-for-cloudtrail.html (accessed 2026-07-31)

---

## NP-9 — No Immutability Control (Missing Object Lock / MFA Delete) on the Log Bucket

**Risk Level**: HIGH
**Blast Radius**: Permanent, irreversible loss of audit history — a single compromised credential can permanently delete log object versions.

```bash
# WRONG — Log bucket without versioning, Object Lock, or MFA Delete
aws s3api get-bucket-versioning --bucket <log-archive-bucket>
# Returns: {} (versioning not enabled)

aws s3api get-object-lock-configuration --bucket <log-archive-bucket>
# Returns: NoSuchObjectLockConfiguration

# CORRECT — Option 1: S3 Object Lock (Compliance mode) — enterprise default
# MUST be enabled at bucket creation (cannot be added after)
# See AD-10 in always-do-patterns.md for full bucket-creation commands

# CORRECT — Option 2: MFA Delete (when lifecycle tiering is definitively NOT needed)
# Cannot coexist with S3 lifecycle configuration
aws s3api put-bucket-versioning \
  --bucket <log-archive-bucket> \
  --versioning-configuration 'Status=Enabled,MFADelete=Enabled' \
  --mfa "<serial-number> <mfa-token>"

# Verify either path
aws s3api get-object-lock-configuration --bucket <log-archive-bucket>
# OR
aws s3api get-bucket-versioning --bucket <log-archive-bucket>
# Expected: ObjectLockEnabled=Enabled (Object Lock path) OR MFADelete=Enabled (MFA Delete path)
```

**Impact**: Irrecoverable evidence loss; compliance violation; forensic investigation impossible.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
