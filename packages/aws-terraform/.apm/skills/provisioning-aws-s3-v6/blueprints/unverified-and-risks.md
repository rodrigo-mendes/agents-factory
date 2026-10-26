# Unverified Claims and Risks — hashicorp/aws 6.x S3

Research date 2026-10-14. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** as of 2026-10-14 (reference 6.69.0). Re-verify when
  starting new work or after 30 days. Source: https://github.com/hashicorp/terraform-provider-aws/releases
- **Terraform 1.16.6** is the current stable CLI. **1.17.0-rc2** exists — do not target it.
  Source: https://releases.hashicorp.com/terraform/
- **6.57.0 was withdrawn** from GitHub and the Registry. Never pin it; the effect of a pin on
  `terraform init` is not stated in the research.
- **v7 is planned** — upgrade guide already documents items "removed in v7.0.0". When v7 ships,
  create a new skill `provisioning-aws-s3-v7`.
- **Deprecated inline `aws_s3_bucket` arguments** (`versioning`, `acl`, `server_side_encryption_configuration`,
  etc.) are scheduled for "a future major version" — not 6.0. Do not use them; they will be removed eventually.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Whether account-level BPA is on by default for new AWS accounts — not stated on fetched pages | (unverified) — always set all four booleans explicitly |
| U2 | Effect of `bucket_key_enabled` (S3 Bucket Keys) on KMS calls or cost, including any percentage — not fetched | (unverified) — the argument exists (research section 4); do not state a benefit |
| U3 | `aws_s3_bucket_object_lock_configuration` and `aws_s3_bucket_replication_configuration` identity import format — not shown on fetched pages | (unverified) — test import behavior before relying on identity import |
| U4 | Version in which `newer_noncurrent_versions` was added — not checked in CHANGELOG | (unverified) — argument is on the current lifecycle doc page; introduction version unknown |
| U5 | `aws_s3_bucket_abac` resource (seen in 6.31.0 CHANGELOG notes) — resource page not fetched | (unverified) — do not use until confirmed |
| U6 | Behavioral difference between Object Lock modes `COMPLIANCE` and `GOVERNANCE` (who can shorten or bypass retention) — not in the fetched pages | (unverified) — ask the user which mode; do not describe semantics |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | Verbatim warning wording in resource docs — WebFetch paraphrases; substance confirmed on raw markdown | (medium confidence) — use raw markdown source URLs to verify exact wording |
| M2 | `existing_object_replication` "MalformedXML" warning — paraphrased, not verbatim | (medium confidence) — requires AWS Support activation before use |
| M4 | HCL `;` separator invalidity in legacy research file — from language knowledge, not re-fetched | (medium confidence) — always use newline or comma separators in HCL |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG checked with strict `aws_s3_` prefix; `aws_s3control_*`, `aws_s3tables_*`, `aws_s3files_*`, `aws_s3vectors_*` out of scope |
| L2 | Raw `main` markdown may run slightly ahead of 6.69.0 |
| L3 | Security Hub page lists no S3.4, S3.16, S3.18, S3.21 (presumably retired) — not investigated |
| L4 | Not covered: access points, website configuration, accelerate, request payment, inventory, analytics, intelligent-tiering config, S3 Tables, S3 Vectors |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Ask First, SSE algorithm row — Bucket Keys cost effect | U2 |
| (unverified) | SKILL.md Quick Reference, Bucket Key row | U2 |
| (unverified) | always-do-security-encryption.md section 5 intro and HCL comment — Bucket Keys cost effect | U2 |
| (unverified) | SKILL.md Ask First, Object Lock row — difference between modes | U6 |
| (unverified) | always-do-lifecycle-versioning.md section 8 — `newer_noncurrent_versions` comment | U4 |
| (medium confidence) | SKILL.md Ask First, Replication row — `existing_object_replication` | M2 |

Register-only items (no tag appears in the skill text): U1, U3, U5, M1, M4, L1–L4. M3 was closed:
the `data.aws_region` attribute is `.region` per the 6.0 upgrade guide, so no tag is carried.
No irresolvable items (I) exist.

## Source Bibliography

All fetched 2026-10-14. Numbers match the research bibliography.

1. Shared version and region facts: the Terraform and provider pages cited inline, read 2026-10-23.
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_versioning.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_server_side_encryption_configuration.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_public_access_block.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_account_public_access_block.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_ownership_controls.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_policy.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_lifecycle_configuration.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_logging.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_replication_configuration.html.markdown
14. https://docs.aws.amazon.com/securityhub/latest/userguide/s3-controls.html
15. https://docs.aws.amazon.com/AmazonS3/latest/userguide/gpbucketnamespaces.html
16. https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html
17. https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
18. https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html
19. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_object_lock_configuration.html.markdown
20. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_notification.html.markdown
21. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_cors_configuration.html.markdown
22. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_object.html.markdown
23. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_directory_bucket.html.markdown
24. https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-s3-c-encryption-setting-faq.html
25. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
26. https://developer.hashicorp.com/terraform/language/backend/s3
27. https://developer.hashicorp.com/terraform/language/tests
28. https://developer.hashicorp.com/terraform/language/tests/mocking
29. https://developer.hashicorp.com/terraform/cli/commands/plan
30. https://developer.hashicorp.com/terraform/cli/commands/test
