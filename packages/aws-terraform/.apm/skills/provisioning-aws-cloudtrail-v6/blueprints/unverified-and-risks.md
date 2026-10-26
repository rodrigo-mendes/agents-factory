# Unverified Claims and Risks — hashicorp/aws 6.x CloudTrail

Research date 2026-10-23. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** as of 2026-10-23 (latest 6.70.0, reference
  6.69.0/6.70.0). Re-verify when starting new work. Source: https://releases.hashicorp.com/terraform-provider-aws/
- **Terraform 1.17.0 is stable since 2026-10-21** and is not the target of this skill (`~> 1.16`).
  Source: https://releases.hashicorp.com/terraform/
- **6.57.0 is permanently withdrawn** from GitHub and the Registry. Any constraint resolving to it
  fails `terraform init`.
- **v7 is planned, not released.** When it ships, create a new skill `provisioning-aws-cloudtrail-v7`.
- **CloudTrail Lake is closed to new customers since 2026-05-31**; the event data store guidance
  applies only to onboarded accounts. Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html
- The raw `main` provider docs may run slightly ahead of 6.70.0 (L1).

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | `aws_cloudtrail_channel` — provider doc page returned HTTP 404; existence in 6.70.0 not confirmed | (unverified) — write no HCL for it |
| U2 | KMS key type constraints for CloudTrail (symmetric, same region as bucket) — not on the fetched key-policy page | (unverified) — check the AWS key-policy page before choosing a key |
| U3 | Whether switching `event_selector` and `advanced_event_selector` forces replacement — not documented on the resource page | (unverified) — the skill makes no claim; read the plan output |
| U5 | Example `field_selector` values (e.g. `eventSource` = `s3.amazonaws.com`) — the research documents the fields, not example values | (unverified) — illustrative only |
| U6 | Which account creates `aws_cloudtrail_organization_delegated_admin_account` — not stated in the research | (unverified) — the skill makes no claim |
| U4 | `cloud_watch_logs_role_arn` IAM permissions — CloudWatch integration page not fetched | (unverified) — the skill takes the role ARN as an input and does not define the role |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | No CloudTrail entries in the provider CHANGELOG 6.48.0–6.70.0 — WebFetch summarised a very large file | (medium confidence) — re-check the CHANGELOG before relying on it |
| M2 | Event data store maximum retention: provider page says up to 2555 days; the AWS Lake page says up to 3,653 days (one-year extendable pricing) or 2,557 days (seven-year pricing) | (medium confidence) — the skill states the provider value 2555 |
| M3 | Default trail log encryption: best-practices page says SSE-KMS; Security Hub page says SSE-S3 | (medium confidence) — the skill asserts neither and always sets `kms_key_id` |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | Raw `main` provider docs may run slightly ahead of 6.70.0; Registry pages are JS-only |
| L2 | `data.aws_cloudtrail_service_account` not researched |
| L3 | WebFetch paraphrases; verbatim warning wording is not guaranteed |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | always-do-trail.md §3 The trail — `cloud_watch_logs_role_arn` role permissions | U4 |
| (unverified) | always-do-kms-lake.md §4 KMS key policy for the trail — key type constraints | U2 |
| (medium confidence) | always-do-kms-lake.md §5 Event data store — `retention_period` 2555 | M2 |
| (medium confidence) | never-do-trail.md §3 Relying on a default log encryption | M3 |
| (unverified) | never-do-trail.md §5 HCL for aws_cloudtrail_channel | U1 |
| (unverified) | SKILL.md ⚠️ Ask First — Channel integration row | U1 |
| (medium confidence) | SKILL.md ⚠️ Ask First — Default log encryption row | M3 |
| (unverified) | never-do-trail.md §1 example `eventSource` value | U5 |
| (unverified) | always-do-kms-lake.md §6 which account creates the delegated admin | U6 |
| (none — registered only) | U3 is not tagged in any file; the skill makes no claim about selector replacement | U3 |
| (medium confidence) | SKILL.md ⚠️ Ask First — event data store retention row; Quick Reference defaults row | M2 |
| (medium confidence) | SKILL.md 5.x → 6.x Migration — changelog 6.48.0 → 6.70.0 line | M1 |

## Source Bibliography

All fetched 2026-10-23.

1. https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html — CloudTrail.1–10 controls
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown — aws_cloudtrail
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_event_data_store.html.markdown — aws_cloudtrail_event_data_store
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_organization_delegated_admin_account.html.markdown — delegated admin
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — 6.0.0 changes
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.57.0 withdrawn; no CloudTrail entries 6.48–6.70
7. https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html — bucket policy
8. https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-kms-key-policy-for-cloudtrail.html — key policy
9. https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html — security best practices
10. https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html — CloudTrail Lake
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_channel.html.markdown — HTTP 404
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — regional vs global resources
13. https://releases.hashicorp.com/terraform/ and https://releases.hashicorp.com/terraform-provider-aws/ — version context
14. https://developer.hashicorp.com/terraform/language/backend/s3 — use_lockfile
15. https://developer.hashicorp.com/terraform/language/tests — terraform test
16. https://developer.hashicorp.com/terraform/cli/commands/plan — -detailed-exitcode
