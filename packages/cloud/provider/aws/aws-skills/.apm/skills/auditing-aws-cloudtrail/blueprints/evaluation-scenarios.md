# Evaluation Scenarios — auditing-aws-cloudtrail

Skill version: AWS CloudTrail 2026 (research date 2026-08-26)
Run via: `/evaluating-skill-scenarios auditing-aws-cloudtrail`

---

## Scenario 1 — Canonical: New multi-account CloudTrail setup

```json
{
  "skills": ["auditing-aws-cloudtrail"],
  "query": "We are setting up CloudTrail for a new AWS Organization with 50 accounts. We want centralized audit logging with tamper-proof logs and encryption. What is the recommended architecture?",
  "expected_behavior": [
    "Recommends a single organization trail (multi-Region) created from the management account",
    "Specifies logs delivered to a dedicated Log Archive account in the Security OU per AWS SRA",
    "Includes enabling log file integrity validation (SHA-256 + SHA-256/RSA digest files)",
    "Specifies SSE-KMS encryption with explicit KMS key policy statements (GenerateDataKey, Decrypt, DescribeKey) and aws:SourceArn condition",
    "Specifies S3 Block Public Access (all four settings) and bucket policy with cloudtrail.amazonaws.com service principal",
    "Recommends deny SCPs for cloudtrail:StopLogging and cloudtrail:DeleteTrail on member OUs",
    "Does NOT recommend CloudTrail Lake (closed to new customers May 31, 2026)"
  ]
}
```

---

## Scenario 2 — Canonical: Security Hub CSPM remediation

```json
{
  "skills": ["auditing-aws-cloudtrail"],
  "query": "Security Hub is reporting CloudTrail.6 as Critical and CloudTrail.2 as Medium failed findings. How do I remediate?",
  "expected_behavior": [
    "CloudTrail.6 remediation: enable all four Block Public Access settings on the CloudTrail S3 bucket",
    "CloudTrail.6 remediation: verifies no bucket policy statement allows public access",
    "CloudTrail.2 remediation: explicitly configure SSE-KMS on the trail (not relying on defaults due to conflicting AWS documentation)",
    "Provides CLI or console steps for both remediations",
    "Notes that findings can take up to 18 hours to update after remediation",
    "Mentions verifying with aws s3api get-public-access-block and aws cloudtrail get-trail"
  ]
}
```

---

## Scenario 3 — Canonical: CloudWatch monitoring alarms

```json
{
  "skills": ["auditing-aws-cloudtrail"],
  "query": "We need to set up CloudWatch alarms for CIS AWS Foundations Benchmark v5.0.0 security events. Which alarms are mandatory and what are their filter patterns?",
  "expected_behavior": [
    "Lists the 14 CIS-mapped mandatory alarm controls (CloudWatch.1 through CloudWatch.14)",
    "Provides at least three verbatim metric filter patterns (e.g., root usage, console sign-in failures, security group changes)",
    "Specifies namespace CloudTrailMetrics with Sum statistic over 5-minute periods",
    "Notes the required IAM role for CloudWatch Logs integration (CloudTrail_CloudWatchLogs_Role)",
    "References Security Hub CloudTrail.5 (trail must be integrated with CloudWatch Logs)"
  ]
}
```

---

## Scenario 4 — Edge Case: CloudTrail Lake for new deployment

```json
{
  "skills": ["auditing-aws-cloudtrail"],
  "query": "We want to use CloudTrail Lake event data stores for our new AWS deployment to get SQL-based event querying.",
  "expected_behavior": [
    "Immediately flags that CloudTrail Lake is closed to new customers as of May 31, 2026",
    "Does NOT proceed to configure CloudTrail Lake for the new deployment",
    "Recommends alternative: Athena over S3-delivered logs, or Amazon Security Lake for OCSF-normalized querying",
    "Explains Security Lake prerequisites (multi-Region org trail with read+write management events)",
    "Notes existing customers are unaffected"
  ]
}
```

---

## Scenario 5 — Edge Case: MFA Delete vs lifecycle on log archive bucket

```json
{
  "skills": ["auditing-aws-cloudtrail"],
  "query": "We need both MFA Delete on the CloudTrail S3 bucket for compliance and a lifecycle policy to transition logs to Glacier after 90 days. Can we enable both?",
  "expected_behavior": [
    "Explicitly states MFA Delete and S3 lifecycle configurations are mutually exclusive on the same bucket",
    "Asks the user to choose one based on compliance requirements",
    "Offers S3 Object Lock with WORM (write-once-read-many) as an alternative for immutability requirements",
    "Does NOT configure both simultaneously",
    "References this as an Ask First decision requiring explicit choice"
  ]
}
```

---

## Scenario 6 — Anti-Pattern Trap: Broad FullAccess IAM policy

```json
{
  "skills": ["auditing-aws-cloudtrail"],
  "query": "To simplify operations, we want to attach AWSCloudTrail_FullAccess to all DevOps team members so they can manage CloudTrail configuration.",
  "expected_behavior": [
    "Flags this as a Never Do anti-pattern",
    "Explains AWSCloudTrail_FullAccess grants ability to disable and reconfigure auditing — AWS states it is not intended to be shared or applied broadly",
    "Recommends restricting this policy to account administrators only",
    "Provides least-privilege alternatives: log readers need kms:Decrypt + S3 read; CLI validators need only s3:ListObjects, s3:GetObject, s3:GetBucketLocation",
    "Recommends using SCPs to prevent cloudtrail:StopLogging and cloudtrail:DeleteTrail as a defense-in-depth layer"
  ]
}
```
