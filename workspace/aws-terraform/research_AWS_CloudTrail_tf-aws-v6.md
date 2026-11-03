# Research — AWS CloudTrail with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `cloudtrail`, flat fan-out, no sub-agents).
> Registry pages render JS-only (F12); upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`) is the source for resource docs.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_CloudTrail_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL).

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (F1); 1.17.0 stable but not the target (F2) | `_family_facts_v6.md` F1, F2 |
| hashicorp/aws | latest 6.70.0, constraint `version = "~> 6.69"`; no 7.x (F3); never pin 6.57.0 (F4) | F3, F4 |
| Region model | `aws_cloudtrail`, `aws_cloudtrail_event_data_store` accept optional `region` (F5; confirmed on both resource pages [2][3], 2026-10-23) | F5, [2], [3] |
| Global exception | `aws_cloudtrail_organization_delegated_admin_account` is **global** per F14 — no `region` argument, no `@region` import. Its resource page documents no `region` argument [4] (2026-10-23), consistent with F14 | F14, [4] |
| Identity import | `aws_cloudtrail` and `aws_cloudtrail_event_data_store` document `identity { arn }` import (Terraform ≥ 1.12.0, F11) [2][3] | F11 |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

Service-specific version fact: **CloudTrail Lake is no longer open to new customers starting May 31, 2026**; existing customers continue as normal [10] (2026-10-23). Since today is 2026-10-23, `aws_cloudtrail_event_data_store` is usable only by accounts already onboarded.

## 2. Provider 6.x changes for CloudTrail

6.0.0 upgrade guide (F13, [5], 2026-10-23):
- `aws_cloudtrail_event_data_store` appears only in the **Nullable Boolean Validation Update** table for `suspend`: configs must use only `""`, `true` or `false` (not `0`/`1`) — consequence of the `TypeNullableBool` change.
- No entry for `aws_cloudtrail`, `aws_cloudtrail_organization_delegated_admin_account`, or `data.aws_cloudtrail_service_account`.
- `data.aws_region.name` deprecated → use `.region` (F15). Relevant: legacy file builds trail ARNs with `data.aws_region.current.name` — must become `.region`.
- Per-resource `region` (F5) applies to trail and event data store.

CHANGELOG 6.48.0 → 6.70.0 ([6], 2026-10-23): **no entries mentioning CloudTrail** were found in 6.71.0 (Unreleased) down to 6.40.0 (read in two windows: 6.71.0→6.55.0 and 6.54.0→6.40.0). (medium confidence — WebFetch summarizes long pages; see M1.)

## 3. aws_cloudtrail

Source [2] (2026-10-23).

- **Required:** `name`, `s3_bucket_name`.
- **Optional + defaults:**
  - `is_multi_region_trail` (default `false`) — for a multi-region trail the resource must live in the trail's home region.
  - `include_global_service_events` (default `true`) — must be enabled to capture IAM and other global service events.
  - `enable_log_file_validation` (default `false`).
  - `enable_logging` (default `true`) — drives StartLogging/StopLogging.
  - `is_organization_trail` (default `false`) — creatable only in the organization's management ("master") account.
  - `kms_key_id` — KMS key **ARN**.
  - `s3_key_prefix` — prefix after the bucket name.
  - `cloud_watch_logs_group_arn` — **must include the log stream wildcard `:*`**, e.g. `"${aws_cloudwatch_log_group.example.arn}:*"`.
  - `cloud_watch_logs_role_arn` — role assumed by the CloudWatch Logs endpoint to write to the group.
  - `sns_topic_name` — use the ARN if the topic is in a different region.
  - `insight_selector { insight_type }` — `ApiCallRateInsight` | `ApiErrorRateInsight`.
  - `region`, `tags` (overrides matching `default_tags`).
- **Do not mix:** `event_selector` and `advanced_event_selector` conflict — use only one.
  - `event_selector`: `read_write_type` (`ReadOnly`|`WriteOnly`|`All`, default `All`), `include_management_events` (default `true`), `exclude_management_event_sources` (`kms.amazonaws.com`, `rdsdata.amazonaws.com`; needs `include_management_events = true`), `data_resource { type, values }` with `type` ∈ `AWS::S3::Object`, `AWS::Lambda::Function`, `AWS::DynamoDB::Table`.
  - `advanced_event_selector`: optional `name`, required `field_selector { field, equals | not_equals | starts_with | not_starts_with | ends_with | not_ends_with }`; `field` ∈ `readOnly`, `eventSource`, `eventName`, `eventCategory`, `resources.type`, `resources.ARN`; `equals` is the only valid operator for `readOnly`, `eventCategory`, `resources.type`.
- **Ordering:** the documented basic example sets `depends_on = [aws_s3_bucket_policy.example]` on the trail — the bucket policy must exist before the trail.
- **Attributes:** `arn`, `id` (= ARN), `home_region`, `sns_topic_arn`, `tags_all`.
- **Import:** by trail ARN `arn:aws:cloudtrail:<region>:<account>:trail/<name>` (`import` block ≥ 1.5, `identity { arn }` ≥ 1.12, or CLI).
- **Timeouts:** none documented.

## 4. S3 bucket policy for CloudTrail

Sources [7] (AWS), [2] (provider example), 2026-10-23.

- Principal `Service = cloudtrail.amazonaws.com`; two statements:
  1. `s3:GetBucketAcl` on `arn:aws:s3:::<bucket>` with `StringEquals aws:SourceArn = arn:aws:cloudtrail:<region>:<account>:trail/<name>`.
  2. `s3:PutObject` on `arn:aws:s3:::<bucket>/[prefix/]AWSLogs/<account>/*` with `StringEquals s3:x-amz-acl = bucket-owner-full-control` **and** the same `aws:SourceArn`.
- AWS: "As a security best practice, add an `aws:SourceArn` condition key"; value is always the trail ARN (or array of ARNs). `aws:SourceAccount` is the documented alternative in the troubleshooting section.
- **Organization trail:** add a third `s3:PutObject` statement on `.../AWSLogs/<o-organizationID>/*`; `aws:SourceArn` must be a trail ARN owned by the **management account** and use its account ID. Keep the account-level write statement (covers conversion back to an account trail).
- Bucket cannot be Requester Pays. Prefix in bucket policy must match `s3_key_prefix` ("There is a problem with the bucket policy" otherwise).
- Misconfigured trail: CloudTrail retries delivery for 30 days and charges apply — delete the trail to stop charges.
- Use a dedicated bucket for CloudTrail logs [7][9].
- If the bucket policy only allows SSE-KMS uploads and log file validation is on, allow `AES256` too (`"StringNotEquals": {"s3:x-amz-server-side-encryption": ["aws:kms","AES256"]}`) or trail creation fails [9].

## 5. KMS key policy for CloudTrail

Source [8] (2026-10-23).

- Trails need three sections: **encrypt**, **decrypt**, **describe**.
  - Encrypt: `cloudtrail.amazonaws.com` → `kms:GenerateDataKey*`, `Resource "*"`, `StringEquals aws:SourceArn = <trail ARN>` + `StringLike kms:EncryptionContext:aws:cloudtrail:arn = arn:aws:cloudtrail:*:<account>:trail/*` (add more account IDs to the encryption context for cross-account encryption).
  - Decrypt (readers): `kms:Decrypt` with `Null kms:EncryptionContext:aws:cloudtrail:arn = false`. The service principal also gets `kms:Decrypt` (documented statement). With an existing bucket using an S3 Bucket Key, `kms:Decrypt` is required to create/update a trail with SSE-KMS.
  - Describe: `kms:DescribeKey` for `cloudtrail.amazonaws.com`, with `aws:SourceArn` recommended.
- `aws:SourceArn` recommended; `aws:SourceAccount` "supported, but not recommended" for trails.
- Event data stores: service principal gets `kms:GenerateDataKey` + `kms:Decrypt` with `aws:SourceAccount` and `aws:SourceArn = arn:aws:cloudtrail:<region>:<account>:eventdatastore/<id>` — **add these conditions after the store is created**. Users running queries need `kms:Decrypt` + `kms:GenerateDataKey`.
- Do not change existing key-policy sections when adding these; a disabled key or wrong policy stops delivery.
- Key type requirements (symmetric, same-region, multi-region keys) were not on this page — see U2.

## 6. aws_cloudtrail_event_data_store

Source [3] (2026-10-23); AWS [10].

- **Required:** `name`.
- **Defaults:** `retention_period` `2555` days; `termination_protection_enabled` `true`; `billing_mode` `EXTENDABLE_RETENTION_PRICING` (or `FIXED_RETENTION_PRICING`); `multi_region_enabled` `true`; `organization_enabled` `false`.
- `kms_key_id`: alias (`alias/…`), alias/key ARN or key ID; no default stated (default AWS encryption is SSE-S3 per Security Hub CloudTrail.10 [1]). AWS: once associated, the KMS key **cannot be removed or changed** [10].
- `suspend`: `true` stops ingestion, existing events remain queryable (bool only — §2).
- `advanced_event_selector` optional; with only `name` set the store captures all management events.
- Tip: an organization event data store must be created in the management account.
- **Retention discrepancy:** provider doc says up to 2555 days; AWS says up to 3,653 days (one-year extendable pricing) or 2,557 days (seven-year pricing) [10] — see M2.
- Import: ARN `arn:aws:cloudtrail:<region>:<account>:eventdatastore/<id>` (identity ≥ 1.12). Timeouts: create/update/delete 5m.
- Availability: closed to new customers from 2026-05-31 [10].

## 7. aws_cloudtrail_channel (brief)

- `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_channel.html.markdown` returned **HTTP 404** (2026-10-23). No provider resource of that name was found — treat as not available in hashicorp/aws 6.x (see U1). Channels are a CloudTrail Lake integration concept (`PutAuditEvents`) [10].

## 8. aws_cloudtrail_organization_delegated_admin_account

Source [4] (2026-10-23).

- Required `account_id` (member account to delegate). Attributes: `arn`, `email`, `name`, `service_principal`.
- Global (F14): no `region` argument documented; import by account ID only (`12345678901`), no `@region`.
- Example reads the delegate account ID via an aliased provider (`cloudtrail_delegate_account`).

## 9. AWS guidance

Best practices [9] (2026-10-23):
- Detective: create a trail (90-day Event history is not a permanent record); one multi-Region trail for management events + additional trails for data events; enable log file integrity validation (SHA-256 + SHA-256 with RSA); integrate with CloudWatch Logs; use GuardDuty and Security Hub.
- Preventive: dedicated, centralized bucket in a separate log archive account (organization trail where Organizations is used); SSE-KMS; add `aws:SourceArn` to the SNS topic policy; least-privilege bucket access with `aws:SourceArn`; MFA delete on the bucket (incompatible with lifecycle rules); lifecycle rules (default retention is indefinite); restrict `AWSCloudTrail_FullAccess`.

Security Hub CloudTrail controls [1] (2026-10-23):

| ID | Title | Severity | Config rule |
|---|---|---|---|
| CloudTrail.1 | ≥1 multi-Region trail with read+write management events | High | `multi-region-cloudtrail-enabled` (readWriteType ALL, includeManagementEvents true) |
| CloudTrail.2 | Encryption at rest (fails if `KmsKeyId` undefined) | Medium | `cloud-trail-encryption-enabled` |
| CloudTrail.3 | At least one trail enabled | High | `cloudtrail-enabled` |
| CloudTrail.4 | Log file validation enabled | Low | `cloud-trail-log-file-validation-enabled` |
| CloudTrail.5 | Integrated with CloudWatch Logs (`CloudWatchLogsLogGroupArn` set) | Medium | `cloud-trail-cloud-watch-logs-enabled` |
| CloudTrail.6 | Log bucket not publicly accessible | Critical | custom (all four S3 BPA settings) |
| CloudTrail.7 | S3 server access logging on the log bucket | Low | custom |
| CloudTrail.9 | Trails tagged (`requiredTagKeys`) | Low | `tagged-cloudtrail-trail` |
| CloudTrail.10 | Event data store encrypted with CMK | Medium | `event-data-store-cmk-encryption-enabled` |

CloudTrail.8 does not appear on the page.

Terraform mapping: `is_multi_region_trail = true` + default selectors (CT.1), `kms_key_id` (CT.2), `enable_logging = true` (CT.3), `enable_log_file_validation = true` (CT.4), `cloud_watch_logs_group_arn` + role (CT.5), `aws_s3_bucket_public_access_block` all true (CT.6), `aws_s3_bucket_logging` (CT.7), `tags` (CT.9), event data store `kms_key_id` (CT.10).

## 10. Legacy-file claims checked

- **Wrong/outdated:** `required_version = ">= 1.7"`, `version = "~> 6.0"` and `dynamodb_table` backend locking → use F1/F3 and `use_lockfile = true` (F7).
- **Wrong:** ARNs built with `data.aws_region.current.name` → `.region` in 6.x (F15).
- **Conflict between AWS sources (not a legacy-file error):** the AWS best-practices page [9] says trail log files are encrypted with SSE-KMS by default, while the Security Hub page [1] says the default is SSE-S3. The skill must not assert either default; always set `kms_key_id` (M3).
- **Wrong:** "Migrating from basic to advanced is a destructive trail update (trail is stopped and recreated)" — not stated on [2]; no forces-new documented (unverified claim, U3).
- **Wrong:** event data store "max 3653 for EXTENDABLE" contradicts the provider page (2555) though it matches AWS [10] (M2).
- **Unsupported:** KMS key policy in legacy omits `aws:SourceArn` on `kms:DescribeKey` and the service-principal `kms:Decrypt`; [8] documents both.
- Confirmed: `:*` suffix, `enable_log_file_validation`/`is_multi_region_trail` default `false`, `depends_on` bucket policy, `aws:SourceArn` in bucket policy, Lake closing 2026-05-31.

## 11. Unverified / medium-confidence items and limits

- U1 `aws_cloudtrail_channel` — no provider doc (404); existence in 6.70.0 unverified.
- U2 KMS key type constraints for CloudTrail (symmetric, same region as bucket) — not on fetched page.
- U3 Whether switching `event_selector` ↔ `advanced_event_selector` forces replacement — not documented.
- U4 `cloud_watch_logs_role_arn` IAM permissions (`logs:CreateLogStream`, `logs:PutLogEvents`) — CloudWatch integration page not fetched.
- M1 "No CloudTrail CHANGELOG entries 6.48.0–6.70.0" — WebFetch summarization over a 495k-char file.
- M2 Event data store max retention: provider 2555 vs AWS 3,653/2,557.
- M3 Default trail log encryption: SSE-KMS ([9]) vs SSE-S3 ([1]); always set `kms_key_id`.
- L1 Raw `main` docs may run slightly ahead of 6.70.0.
- L2 `data.aws_cloudtrail_service_account` not researched (out of brief scope).
- L3 WebFetch paraphrases; verbatim warning wording not guaranteed.

## 12. Security note

- None. No instruction-like or prompt-injection text was observed in fetched pages.

## Source Bibliography

All fetched 2026-10-23.

1. https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_event_data_store.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_organization_delegated_admin_account.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
7. https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html
8. https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-kms-key-policy-for-cloudtrail.html
9. https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html
10. https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_channel.html.markdown (HTTP 404)
12. c:\agents\agents-factory\workspace\aws-terraform\_family_facts_v6.md (F1–F5, F7, F11, F13–F15)
