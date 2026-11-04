# Research — AWS S3 with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-14**. Status: **COMPLETE** (unit `s3`, P4 fan-out, flat — no sub-agents).
> Registry pages render JS-only (F12); upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`) is the
> authoritative source for resource docs. Shared facts cited by ID from `_family_facts_v6.md` (F1–F13).
> Coverage reference only (not a source): `workspace/terraform/research_AWS_S3_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL).
> Resource-doc source pattern: `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/<name>.html.markdown` (2026-10-14).

## 1. Version Context

| Item | Value | Source (2026-10-14) |
|---|---|---|
| Terraform CLI | 1.16.6; target `required_version = "~> 1.16"`; 1.17.0-rc2 is pre-release, do not target | F1, F2 |
| hashicorp/aws | 6.69.0; target `version = "~> 6.69"`; no 7.x released | F3 |
| Withdrawn | 6.57.0 — never pin | F4 |
| Per-resource `region` | every S3 resource accepts optional `region`; changing it forces replacement; import `id@region` | F5 |
| Identity import | `identity` block needs Terraform ≥ 1.12.0 (satisfied by 1.16) | F11 |
| State backend | S3 backend `use_lockfile = true`; `dynamodb_table` deprecated | F7 |
| S3-specific | `bucket_namespace` added in **6.37.0** (#46917) — before the 6.48 window, available in 6.69 | [8] |
| S3-specific | `expected_bucket_owner` deprecated on multiple `aws_s3_bucket_*` resources and dropped from Resource Identity in **6.31.0** (#46262, #46272) | [8] |
| S3-specific | `blocked_encryption_types` made Optional+Computed in **6.40.0** (#47359) to stop diffs once SSE-C is disabled | [8] |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

## 2. Provider 6.x changes for S3

6.0.0 upgrade guide (F13, [2]):
- `aws_s3_bucket` (resource **and** data source): `bucket_region` added "and should be used instead of `region`"; `region` now means Enhanced Region Support (F5). Any config reading the bucket's region via `region` must switch to `bucket_region`.
- Provider-level: global S3 endpoint support deprecated (affects `us-east-1` S3 resources, excluding directory buckets, only when `s3_us_east_1_regional_endpoint = "legacy"`); `s3_us_east_1_regional_endpoint` "will be removed in v7.0.0" — remove it or set `regional`.
- The guide has **no** entries for `aws_s3_object`, `aws_s3_directory_bucket`, lifecycle `filter`, or the deprecated inline `aws_s3_bucket` arguments — inline arguments were **not removed** in 6.0 (still listed as Deprecated on the resource page, §3).
- Upgrade path: latest 5.x with clean plan → `~> 6.0` → `terraform init -upgrade` → fix S3 items → plan again.

CHANGELOG 6.48.0 → 6.69.0, `aws_s3_*` scope ([8]; no breaking changes in window):
- 6.48.0 BUG FIX `aws_s3_bucket_versioning`: perpetual drift on `versioning_configuration.mfa_delete` when `status = "Disabled"` (#48161).
- 6.52.0 New Data Source `aws_s3_bucket_notification` (#31512).
- 6.56.0 New Data Source `aws_s3_buckets` (#48965); New List Resource `aws_s3_bucket_notification` (#48974).
- 6.57.0 withdrawn (F4); 6.57.1 no S3 entries.
- 6.62.0 BUG FIX `aws_s3_account_public_access_block`: eventual-consistency issue on create (#49687).
- 6.63.0 BUG FIX `aws_s3_bucket`: setting `object_lock_enabled = true` (and deprecated `object_lock_configuration.object_lock_enabled = "Enabled"`) **no longer forces replacement** (#36530).
- 6.49–6.51, 6.53–6.55, 6.58–6.61, 6.64–6.69: no `aws_s3_` entries (strict prefix filter; `aws_s3files_*`, `aws_s3tables_*`, `aws_s3control_*` excluded).
- Earlier (context, outside window): list resources for `aws_s3_bucket`, `aws_s3_object` (6.29.0), `aws_s3_bucket_policy`/`_acl`/`_public_access_block` (6.31.0), `aws_s3_directory_bucket` (6.32.0), `aws_s3_bucket_lifecycle_configuration` (6.34.0), `aws_s3_bucket_versioning` (6.36.0).

## 3. aws_s3_bucket ([3])

- Scope: general purpose buckets only. Directory buckets → `aws_s3_directory_bucket`; Outposts → `aws_s3control_bucket`.
- No required args. `bucket` (forces new; random if omitted; ≤ 63 chars, lowercase; must not use `--<azid>--x-s3` format) | `bucket_prefix` (forces new; ≤ 37 chars; conflicts with `bucket`).
- `bucket_namespace` (forces new): `global` (default) | `account-regional`.
- `force_destroy` default `false`; deletes **all objects including locked ones**, unrecoverable; only takes effect after a successful apply stores it in state (also after import).
- `object_lock_enabled` (bool; not in all regions/partitions). Enabling Object Lock turns versioning on; neither can be turned off afterwards. Since 6.63.0 setting it no longer forces replacement (§2).
- `tags` (overrides matching `default_tags` keys), `region` (F5).
- **ABAC tagging NOTE**: tags are sent on create and read/updated via S3 Control `TagResource`/`UntagResource`/`ListTagsForResource`; the caller needs `s3:TagResource`, `s3:UntagResource`, `s3:ListTagsForResource`, otherwise the provider falls back to `PutBucketTagging`/`GetBucketTagging`/`DeleteBucketTagging`, and tag changes may fail when ABAC is enabled.
- **Deprecated inline arguments** ("will be removed in a future major version") → replacement resource:
  `acceleration_status` → `aws_s3_bucket_accelerate_configuration`; `acl`, `grant` → `aws_s3_bucket_acl`; `cors_rule` → `aws_s3_bucket_cors_configuration`; `lifecycle_rule` → `aws_s3_bucket_lifecycle_configuration`; `logging` → `aws_s3_bucket_logging`; `object_lock_configuration` → `object_lock_enabled` + `aws_s3_bucket_object_lock_configuration`; `policy` → `aws_s3_bucket_policy`; `replication_configuration` → `aws_s3_bucket_replication_configuration`; `request_payer` → `aws_s3_bucket_request_payment_configuration`; `server_side_encryption_configuration` → `aws_s3_bucket_server_side_encryption_configuration`; `versioning` → `aws_s3_bucket_versioning`; `website` → `aws_s3_bucket_website_configuration`.
- **Do not mix** a deprecated inline block with its standalone resource on the same bucket — Terraform treats the standalone settings as drift. Inline drift is detected only when a value is configured.
- Inline `server_side_encryption_configuration` does **not** support `blocked_encryption_types` — use the standalone resource.
- Attributes: `arn`, `bucket_domain_name`, **`bucket_region`**, `bucket_regional_domain_name` (use for CloudFront origins), `hosted_zone_id`, `id` (= name), `tags_all`; `website_domain`/`website_endpoint` deprecated.
- Timeouts: create 20m, read 20m, update 20m, delete 60m.
- Import: `bucket-name`; identity `{ bucket }` (+ optional `account_id`, `region`).

AWS account-regional namespace ([15]):
- Name **must** be `<prefix>-<12-digit-account-id>-<region-code>-an` (e.g. `amzn-s3-demo-bucket-111122223333-us-west-2-an`); the suffix counts toward the 63-char limit (≈ 37 chars left for the prefix in `us-east-1`). Via API you must supply the full suffix (only the console adds it).
- Only your account can ever create names in it; other accounts' CreateBucket with your suffix is rejected. Not available in me-south-1 (Bahrain) and me-central-1 (UAE).
- Enforce with condition key `s3:x-amz-bucket-namespace = account-regional` on `s3:CreateBucket` (IAM, SCP or RCP Deny).
- Terraform pattern: `bucket = "${var.prefix}-${data.aws_caller_identity.current.account_id}-${data.aws_region.current.region}-an"` with `bucket_namespace = "account-regional"` (data-source attribute names: medium confidence — M3).

## 4. Split (satellite) resources

All accept `region` (F5); identity import `{ bucket }` + optional `account_id`, `region` unless noted. Where present, `expected_bucket_owner` is **deprecated** and forces new; import then `bucket-name,123456789012`.

### aws_s3_bucket_versioning ([4])
- Required `bucket` (forces new), `versioning_configuration { status }` = `Enabled` | `Suspended` | `Disabled`. `Disabled` only for creating/importing unversioned buckets; moving Enabled/Suspended → Disabled errors.
- `mfa_delete` (`Enabled`|`Disabled`) needs top-level `mfa` = "serial code".
- Destroy **suspends** versioning (unversioned bucket: state-only removal).
- AWS recommends ~15 min after first enabling before PUT/DELETE; do not create bucket + enable versioning + write critical objects in one config. Objects needing `version_id` must reference/`depends_on` the versioning resource.
- Not for directory buckets. Import `bucket-name`.

### aws_s3_bucket_server_side_encryption_configuration ([5])
- Required `bucket` (forces new), `rule` (only one rule supported).
- `rule.apply_server_side_encryption_by_default { sse_algorithm, kms_master_key_id }`: `sse_algorithm` = `AES256` | `aws:kms` | `aws:kms:dsse`; `aws:kms` without key ID uses `aws/s3`.
- `rule.bucket_key_enabled` (S3 Bucket Keys for SSE-KMS); `rule.blocked_encryption_types` = `SSE-C` | `NONE` (rule level, not inside the default block; Optional+Computed since 6.40.0).
- Destroy resets the bucket to S3 default encryption.
- NOTE: date discrepancy inside the page — argument text says March 2026, top NOTE April 2026; AWS docs say **April 2026** (§5).
- No timeouts section. Import `bucket-name`.

### aws_s3_bucket_public_access_block ([6])
- Required `bucket`. `block_public_acls`, `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets` all **default `false`** — set all four explicitly.
- `skip_destroy`: WARNING — leaves the block in AWS as unmanaged after destroy.
- Not for directory buckets. Import `bucket-name`.

### aws_s3_account_public_access_block ([7])
- No required args; `account_id` defaults to caller account. Same four booleans, all default `false`.
- "Each AWS account may only have one S3 Public Access Block configuration" — multiple resources = perpetual diff. Custom endpoint uses provider `s3control` endpoint, not `s3`.
- AWS: account-level settings apply to **all Regions globally** (eventual propagation) ([17]) — manage once, not per region. 6.62.0 fixed a create eventual-consistency bug.
- Import `<account_id>`; identity `{ account_id }`.

### aws_s3_bucket_ownership_controls ([9])
- Required `bucket`, `rule { object_ownership }` = `BucketOwnerEnforced` (ACLs disabled; "ACLs no longer affect permissions") | `BucketOwnerPreferred` | `ObjectWriter`.
- AWS: `BucketOwnerEnforced` is the **default for new buckets**; PUTs with ACLs other than `bucket-owner-full-control` fail `400 AccessControlListNotSupported`; cross-account replication with BucketOwnerEnforced makes replicas owned by destination owner ([18]).
- Not for directory buckets. Import `bucket-name`.

### aws_s3_bucket_policy ([10])
- Required `bucket`, `policy` (≤ 20 KB; `aws_iam_policy_document` OK if a principal is set). Works for general purpose **and** directory buckets.
- **One `aws_s3_bucket_policy` per bucket** — `PutBucketPolicy` replaces the whole policy; last apply wins silently.
- Import `bucket-name`.

### aws_s3_bucket_lifecycle_configuration ([11])
- Required `bucket`, `rule` (1+). Rule: `id` (required, ≤ 255), `status` (required `Enabled`|`Disabled`).
- **Filter**: `filter {}` or exactly one of `prefix`, `tag`, `and`, `object_size_greater_than`, `object_size_less_than`. Omitting `filter` and `prefix` = all objects (same as empty filter). Rule-level `prefix` deprecated by S3 → use `filter`. Cannot change a rule from filter/no-filter to prefix-only. `and` needed to combine conditions.
- `transition_default_minimum_object_size` = `all_storage_classes_128K` (**default**) | `varies_by_storage_class`; explicit object-size filters take precedence. By default objects < 128 KB do not transition.
- Actions: `abort_incomplete_multipart_upload { days_after_initiation }`; `expiration { date | days | expired_object_delete_marker }` (marker conflicts with date/days); `noncurrent_version_expiration { noncurrent_days (req), newer_noncurrent_versions }`; `transition { date | days (default 0), storage_class }`; `noncurrent_version_transition { noncurrent_days, storage_class, newer_noncurrent_versions }`. Storage classes: `GLACIER`, `STANDARD_IA`, `ONEZONE_IA`, `INTELLIGENT_TIERING`, `DEEP_ARCHIVE`, `GLACIER_IR`.
- **Single lifecycle configuration per bucket** — multiple resources = perpetual diff. Propagation can take time (idempotence risk right after create). Versioning example uses `depends_on = [aws_s3_bucket_versioning.x]`.
- Timeouts create 3m, update 3m. Import `bucket-name` or `bucket-name,account-id`; `id` attribute deprecated.

### aws_s3_bucket_logging ([12])
- Required `bucket` (forces new), `target_bucket`, `target_prefix`. Optional `target_grant { grantee { type, … }, permission }`, `target_object_key_format { partitioned_prefix { partition_date_source = EventTime|DeliveryTime } | simple_prefix {} }`.
- Permissions: recommended — target **bucket policy** allowing `logging.s3.amazonaws.com` `s3:PutObject` with `aws:SourceAccount`; ACL `log-delivery-write` not recommended (and incompatible with BucketOwnerEnforced, see [18]).
- AWS (S3.9): target bucket must be in the same Region and must not have a default retention period (Object Lock) ([14]).
- Not for directory buckets. Import `bucket-name`.

### aws_s3_bucket_replication_configuration ([13])
- Required `bucket`, `role` (IAM role ARN), `rule`. Optional `token` (Object Lock-enabled source; from AWS Support).
- Rule: `id`, `status`, `priority` (with `filter`; unique; required for multiple destinations), `filter` (V2; `filter {}` for all; conflicts with deprecated V1 `prefix`), `delete_marker_replication` (V2 only), `source_selection_criteria { replica_modifications, sse_kms_encrypted_objects }` (KMS needs destination `encryption_configuration.replica_kms_key_id`), `existing_object_replication` (requires AWS Support activation; page warns of `MalformedXML` — M2).
- Destination: `bucket` (ARN, required), `storage_class`, `account` + `access_control_translation { owner = "Destination" }` (cross-account), `encryption_configuration`, `metrics` (`event_threshold.minutes` only 15), `replication_time` (only 15; requires `metrics`).
- **Versioning must be enabled on source and destination first** — `depends_on`. One replication config per bucket (else perpetual diff). Not for directory buckets. 6.x: use per-resource `region` for the destination bucket instead of provider aliases.
- Import `bucket-name`.

### aws_s3_bucket_object_lock_configuration ([19])
- Required `bucket` (forces new). `object_lock_enabled` optional, only value `Enabled` (forces new). `rule.default_retention { mode = COMPLIANCE|GOVERNANCE, days | years }` (exactly one of days/years).
- Can enable Object Lock on new and existing buckets; for existing: enable versioning first. `token` optional.
- Not for directory buckets. Import `bucket-name` or `bucket-name,account-id` (identity not shown on page — U3).

### aws_s3_bucket_notification ([20])
- Required `bucket`. `eventbridge` (default false), repeatable `topic`/`queue`/`lambda_function` blocks with `events` (required), `*_arn`, `filter_prefix`, `filter_suffix`, `id`.
- `PutBucketNotificationConfiguration` **replaces the whole config** — one resource per bucket (else perpetual diff); for independent consumers use EventBridge + one `aws_cloudwatch_event_rule` each.
- Destination policies (examples only): SNS `SNS:Publish` / SQS `sqs:SendMessage` for `s3.amazonaws.com` with `aws:SourceArn`; Lambda via `aws_lambda_permission` and `depends_on` it.
- Not for directory buckets. Import `bucket-name`.

### aws_s3_bucket_cors_configuration ([21])
- Required `bucket` (forces new), `cors_rule` (≤ 100): `allowed_methods` (GET|PUT|HEAD|POST|DELETE), `allowed_origins` required; `allowed_headers`, `expose_headers`, `id`, `max_age_seconds`.
- Single CORS configuration per bucket (else perpetual diff). Not for directory buckets. Import `bucket-name`.

### aws_s3_object ([22])
- Required `bucket` (name or access point ARN), `key` (leading `/` ignored, `//` collapsed).
- One of `source` | `content` | `content_base64` (conflicting; none = empty object; `content_base64` only for small data).
- Change detection: `etag = filemd5(...)` is **not compatible with KMS** (`kms_key_id` / `aws:kms`) and not MD5 for multipart > 16 MB → prefer `source_hash` (state-only).
- `server_side_encryption` = `AES256`|`aws:kms`|`aws:kms:dsse`|`aws:fsx`; `kms_key_id`; `bucket_key_enabled`; `checksum_algorithm` (CRC32, CRC32C, CRC64NVME, SHA1, SHA256); `storage_class` default `STANDARD`; `object_lock_*`; `force_destroy` default false (only for removing legal holds).
- Max 10 tags; if `tags` + `default_tags` exceed it (or directory bucket, no tags) use `override_provider { default_tags { tags = {} } }`.
- Import `bucket/key` or `s3://bucket/key`; identity `{ bucket, key }`.

### aws_s3_directory_bucket (brief) ([23])
- `bucket` must be `<name>--<azid>--x-s3`; `location { name = AZ/Local Zone ID, type = AvailabilityZone (default) | LocalZone }`; `data_redundancy`; `type = "Directory"`; `force_destroy` (same apply-first caveat).
- Versioning, PAB, ownership controls, lifecycle-config resource docs, logging, replication, object lock, notification, CORS resources state they **cannot** be used with directory buckets; bucket policy can. AWS Config does not record directory buckets ([16]).

## 5. AWS guidance

Security best practices ([16]):
- Disable ACLs (BucketOwnerEnforced; default for new buckets); access via IAM, bucket, VPC endpoint policies, SCPs, RCPs.
- Block Public Access at account and bucket level (all four settings — [17] recommends both, bucket level for S3.8); org-level BPA via AWS Organizations S3 policy (all-or-none, overrides account level). S3 applies the most restrictive combination; removing a BPA setting re-exposes existing public policies/ACLs.
- **SSE-C**: since April 2026 disabled for all new general purpose buckets, and for existing buckets in accounts with no SSE-C objects (except Bahrain/UAE); blocked requests get 403 `AccessDenied`. Keep it blocked unless required ([24]).
- Create buckets in the account-regional namespace; avoid deleting global-namespace buckets (name can be re-registered); default quota 10,000 buckets.
- Least privilege; IAM roles (no long-term keys); default SSE-S3 on all buckets, SSE-KMS/DSSE-KMS for control; enforce TLS via `aws:SecureTransport` Deny; do not pin S3 certificates.
- Consider Object Lock, Versioning, CRR (needs versioning on both), VPC endpoints.
- Detect: inventory/tags, CloudWatch metrics, server access logging, CloudTrail data events, AWS Config, Storage Lens, Trusted Advisor, GuardDuty S3 Protection, Detective, IAM Access Analyzer for S3, Macie, Security Hub CSPM.

Security Hub CSPM S3 controls ([14]):

| ID | Title (short) | Severity | Config rule |
|---|---|---|---|
| S3.1 | Account-level BPA enabled | Medium | s3-account-level-public-access-blocks-periodic |
| S3.2 | Block public read | Critical | s3-bucket-public-read-prohibited |
| S3.3 | Block public write | Critical | s3-bucket-public-write-prohibited |
| S3.5 | Require TLS | Medium | s3-bucket-ssl-requests-only |
| S3.6 | Policy restricts other accounts (blacklisted actions) | High | s3-bucket-blacklisted-actions-prohibited |
| S3.7 | Cross-Region replication | Low | s3-bucket-cross-region-replication-enabled |
| S3.8 | Bucket-level BPA | High | s3-bucket-level-public-access-prohibited |
| S3.9 | Server access logging | Medium | s3-bucket-logging-enabled |
| S3.10 | Versioned buckets have lifecycle | Medium | s3-version-lifecycle-policy-check |
| S3.11 | Event notifications | Medium | s3-event-notifications-enabled |
| S3.12 | No ACLs for user access | Medium | s3-bucket-acl-prohibited |
| S3.13 | Lifecycle configuration | Low | s3-lifecycle-policy-check |
| S3.14 | Versioning enabled | Low | s3-bucket-versioning-enabled |
| S3.15 | Object Lock enabled | Medium | s3-bucket-default-lock-enabled |
| S3.17 | Encrypted with KMS keys (SSE-KMS/DSSE-KMS; SSE-S3 fails) | Medium | s3-default-encryption-kms |
| S3.19 | Access point BPA | Critical | s3-access-point-public-access-blocks |
| S3.20 | MFA delete | Low | s3-bucket-mfa-delete-enabled |
| S3.22 / S3.23 | CloudTrail object-level write / read events | Medium | cloudtrail-all-write/read-s3-data-event-check |
| S3.24 | Multi-Region Access Point BPA | High | s3-mrap-public-access-blocked |
| S3.25 | Directory buckets have lifecycle | Low | s3express-dir-bucket-lifecycle-rules-check |

- S3.20 note: MFA delete cannot be used with a bucket that has a lifecycle configuration; only the root user can enable it — conflicts with S3.10/S3.13; Terraform `mfa` needs a live MFA code.
- S3.10/S3.14 tip: versioning without lifecycle = unbounded storage growth.
- S3.2/S3.3 do not evaluate policy conditions with wildcards/variables.

## 6. Legacy-file claims found wrong or unsupported

Checked against `workspace/terraform/research_AWS_S3_aws-v6.x.md`:
1. **Wrong**: `bucket_namespace = "account-regional"` with names like `"${var.project}-${var.environment}-${var.aws_region}"` / `"acme-corp-production-customer-data"` — account-regional names must end `-<account-id>-<region>-an` ([15]).
2. **Outdated**: `required_version = ">= 1.7"`, `version = "~> 6.0"`, backend `dynamodb_table` (F1, F3, F7).
3. **Imprecise**: inline arguments "deprecated in v6.x … removed in v7.x" — docs say only "future major version"; 6.0 removed none of them ([2], [3]).
4. **Wrong/unsupported**: "AWS's default BPA settings apply at account creation" — not stated; AWS states new buckets/objects don't allow public access by default, and Terraform PAB booleans default `false` ([6], [17]) (U1).
5. **Conflict**: `mfa_delete` suggested together with lifecycle rules — AWS says MFA delete can't be used with a lifecycle configuration ([14]).
6. **Incomplete**: SSE-C change also disabled SSE-C on existing buckets in accounts without SSE-C objects ([24]).
7. **Unsupported**: "ownership controls required before using bucket policy as sole access mechanism" (no source); "bucket key reduces KMS cost ~99%" (not verified here, U2); `newer_noncurrent_versions` labelled "v6.x" new (no changelog evidence, U4).
8. **Syntax** (M4): `principals { type = "*"; identifiers = ["*"] }` uses `;` separators — not valid HCL.

## 7. Unverified / medium-confidence items and coverage limits

- U1 Whether account-level BPA is on by default for new accounts — not stated on fetched pages.
- U2 S3 Bucket Key KMS cost reduction figure — not fetched.
- U3 `aws_s3_bucket_object_lock_configuration` / `_replication_configuration` identity import — not shown on fetched pages.
- U4 Version in which `newer_noncurrent_versions` was added — not checked.
- U5 `aws_s3_bucket_abac` resource (seen in 6.31.0 notes) — resource page not fetched.
- M1 Verbatim warning wording — WebFetch paraphrases; substance confirmed on raw markdown.
- M2 `existing_object_replication` "MalformedXML" warning — paraphrased, not verbatim.
- M3 `data.aws_region.current.region` attribute name in 6.x — not fetched for this unit.
- M4 HCL `;` invalidity — from language knowledge, not re-fetched.
- L1 CHANGELOG checked with strict `aws_s3_` prefix; `aws_s3control_*`, `aws_s3tables_*`, `aws_s3files_*`, `aws_s3vectors_*` out of scope.
- L2 Raw `main` markdown may run slightly ahead of 6.69.0 (F12).
- L3 Security Hub page lists no S3.4, S3.16, S3.18, S3.21 (presumably retired) — not investigated.
- L4 Not covered: access points, website, accelerate, request payment, inventory, analytics, intelligent-tiering config, S3 Tables/Vectors.

## 8. Security note

- None. No instruction-like or prompt-injection text was observed in fetched pages.

## Source Bibliography

All fetched 2026-10-14.

1. c:\agents\agents-factory\workspace\aws-terraform\_family_facts_v6.md (F1–F13, verified by orchestrator)
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
