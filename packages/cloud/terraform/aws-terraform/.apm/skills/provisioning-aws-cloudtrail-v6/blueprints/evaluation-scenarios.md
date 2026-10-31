# Evaluation Scenarios — provisioning-aws-cloudtrail-v6

Four scenarios (canonical, edge, misuse rejection, anti-pattern trap) plus one extra.
Each uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Hardened multi-region trail

```json
{
  "skills": ["provisioning-aws-cloudtrail-v6"],
  "query": "Generate Terraform for a multi-region CloudTrail trail with a log bucket, KMS encryption, log file validation and CloudWatch Logs. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Sets is_multi_region_trail = true and enable_log_file_validation = true",
      "Sets kms_key_id on the trail",
      "Ends cloud_watch_logs_group_arn with :*",
      "Adds depends_on the bucket policy to the trail",
      "Bucket policy has GetBucketAcl and PutObject statements for cloudtrail.amazonaws.com with aws:SourceArn set to the trail ARN",
      "Uses data.aws_region.current.region (not .name)",
      "Enables all four S3 Block Public Access settings on the log bucket"
    ],
    "must_not": [
      "Use data.aws_region.current.name",
      "Omit kms_key_id",
      "Use dynamodb_table in the S3 backend",
      "Set both event_selector and advanced_event_selector"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Organization trail and delegated admin

```json
{
  "skills": ["provisioning-aws-cloudtrail-v6"],
  "query": "I need an organization trail and a delegated administrator account for CloudTrail. What do I need to change in the bucket policy and in which account can I create the delegated admin?",
  "success_criteria": {
    "must_pass": [
      "States that is_organization_trail = true is creatable only in the management account",
      "Adds the third statement (second PutObject) on AWSLogs/<o-organizationID>/* and keeps the account-level statement",
      "States aws:SourceArn must be a trail ARN owned by the management account",
      "Declares aws_cloudtrail_organization_delegated_admin_account with account_id and no region argument",
      "States that the delegated admin resource is global (import by account ID, no @region)",
      "Says which account creates the delegated admin is not established by the skill (unverified) rather than inventing an answer"
    ],
    "must_not": [
      "Set region on aws_cloudtrail_organization_delegated_admin_account",
      "Claim an organization trail can be created from a member account"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: aws_cloudtrail_channel and default encryption

```json
{
  "skills": ["provisioning-aws-cloudtrail-v6"],
  "query": "Write Terraform for an aws_cloudtrail_channel and tell me whether a trail without kms_key_id is encrypted by default with SSE-KMS.",
  "success_criteria": {
    "must_pass": [
      "Declines to write HCL for aws_cloudtrail_channel, citing that no provider doc page exists (404) and existence in 6.x is unverified",
      "States that two AWS pages disagree on the default log encryption and does not assert SSE-KMS or SSE-S3 as the default",
      "Recommends always setting kms_key_id"
    ],
    "must_not": [
      "Produce an aws_cloudtrail_channel resource block",
      "Assert that SSE-KMS is the default",
      "Assert that SSE-S3 is the default"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Review a flawed snippet

```json
{
  "skills": ["provisioning-aws-cloudtrail-v6"],
  "query": "Review this: aws_cloudtrail with both event_selector and advanced_event_selector, cloud_watch_logs_group_arn = aws_cloudwatch_log_group.t.arn, an event data store with suspend = 1, and a bucket policy PutObject statement with no aws:SourceArn. Is it correct for aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Rejects mixing event_selector and advanced_event_selector and says to use only one",
      "Rejects the log group ARN without :* and gives the corrected form",
      "Rejects suspend = 1 and says only \"\", true or false are accepted",
      "Rejects the bucket policy without aws:SourceArn and recommends the trail ARN condition",
      "Cites the provider docs or AWS docs for the rejections"
    ],
    "must_not": [
      "Accept both selector types on one trail",
      "Accept the log group ARN without :*",
      "Accept suspend = 1"
    ]
  }
}
```

---

## Scenario 5 — Edge Case: Event data store with unclear retention

```json
{
  "skills": ["provisioning-aws-cloudtrail-v6"],
  "query": "Create a CloudTrail Lake event data store with the maximum retention and a KMS key. Can I swap the key later?",
  "success_criteria": {
    "must_pass": [
      "Notes that CloudTrail Lake is closed to new customers since 2026-05-31 and asks whether the account is onboarded",
      "States retention_period 2555 as the provider page value and tags it (medium confidence)",
      "Sets kms_key_id and states that the key cannot be removed or changed once associated",
      "Mentions adding the key-policy conditions (aws:SourceAccount, aws:SourceArn with the store ID) after the store is created"
    ],
    "must_not": [
      "Present 3653 as the provider's maximum or as the value to set",
      "Say the KMS key can be changed later",
      "Use suspend = 0 or 1"
    ]
  }
}
```
