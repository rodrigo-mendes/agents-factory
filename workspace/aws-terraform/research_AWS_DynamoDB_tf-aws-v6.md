# Research — AWS DynamoDB with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `dynamodb`, P4 fan-out, single researcher, no sub-agents).
> Registry pages render JS-only (F12); upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`) is the authoritative source for resource docs.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_DynamoDB_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL). Claims found wrong in it are listed in §9.
> DynamoDB is a **regional** service: every in-scope resource accepts optional `region` and imports with `id@region` (F5); none is in the F14 global list.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (1.16.6); 1.17.0 stable but not the target | F1, F2 |
| hashicorp/aws | latest 6.70.0 (CHANGELOG: released 2026-10-21; top heading "6.71.0 (Unreleased)"); constraint `~> 6.69` | F3; [8] |
| Withdrawn | 6.57.0 — never pin | F4 |
| Per-resource `region` | regional resources only; changing it forces replacement | F5 |
| Identity import | `identity` block needs Terraform >= 1.12.0 (satisfied by 1.16) | F11 |
| Constraint style | root `~>`, reusable modules `>=` only | F6 |
| S3 backend | `use_lockfile = true`; `dynamodb_table` locking is **deprecated** — do not create a DynamoDB lock table for new state backends | F7 |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

## 2. Provider 6.x changes for DynamoDB

6.0.0 upgrade guide (F13) [9], checked 2026-10-23: **no item mentions DynamoDB or Application Auto Scaling** — no removed/renamed arguments for `aws_dynamodb_*` or `aws_appautoscaling_*`. Only the generic `region` addition (F5) applies.

CHANGELOG 6.48.0 → 6.70.0, DynamoDB scope [8] (2026-10-23) — no breaking changes:
- 6.52.0 (2026-06-24): `aws_dynamodb_table_item` new **list resource**, Resource Identity support and **import support** (#48520).
- 6.57.1 (2026-07-29): `aws_dynamodb_table` no longer **replaces** the table when `warm_throughput` values decrease (#49032). Use >= 6.57.1 (and never 6.57.0, F4) when tuning warm throughput.
- 6.67.0 (2026-09-30): `list-resource/aws_dynamodb_table_replica` eventual-consistency fix on replace (#50133).
- No DynamoDB entries seen in 6.48.0–6.51.0, 6.53.0, 6.54.0, 6.56.0–6.70.0 (except above). 6.55.0 only partly visible (L1).

## 3. aws_dynamodb_table

Source [11] (2026-10-23).

### Keys and attributes
- Required: `name` (unique per region), `attribute` (set), `hash_key` (must also be an `attribute`; **forces new**). Table `range_key` optional, **forces new**.
- `attribute.type`: `S` | `N` | `B`.
- NOTE: define attributes **only** for table, LSI and GSI key attributes — "Adding attributes not used in these scenarios causes an infinite plan loop." Attributes of GSIs managed by the separate `aws_dynamodb_global_secondary_index` need not be defined on the table.

### Capacity
- `billing_mode`: `PROVISIONED` (**default**) | `PAY_PER_REQUEST`. Always set it explicitly.
- `read_capacity` / `write_capacity`: required when `PROVISIONED` (same for each GSI).
- With an App Auto Scaling policy attached: `lifecycle { ignore_changes = [read_capacity, write_capacity] }`.
- Docs warn Auto Scaling can also cause drift on inline `global_secondary_index` blocks and point to `aws_dynamodb_global_secondary_index` for finer GSI lifecycle control (§4).
- `on_demand_throughput { max_read_request_units, max_write_request_units }` — set >= 1 to cap, `-1` to remove (table and GSI).
- `warm_throughput { read_units_per_second, write_units_per_second }` — minimum and default 12000 / 4000. On the base table read units cannot be decreased; on a GSI both may go up or down. Setting both explicitly to their default/minimum values causes reported diffs — omit instead. Decrease no longer forces replacement since 6.57.1 (§2).

### Secondary indexes
- `global_secondary_index`: `name` (required), `projection_type` (required: `ALL` | `INCLUDE` | `KEYS_ONLY`), `non_key_attributes` (only with `INCLUDE`), `read_capacity`/`write_capacity`, `on_demand_throughput`, `warm_throughput`.
  - **6.x: GSI `hash_key`/`range_key` are deprecated** and mutually exclusive with `key_schema`; `key_schema` is required if `hash_key` is not set. Each `key_schema` block: `attribute_name`, `key_type` (`HASH`|`RANGE`); up to 4 HASH and 4 RANGE attributes (multi-attribute keys).
- `local_secondary_index`: `name`, `projection_type`, `range_key` (all required), `non_key_attributes` (only with `INCLUDE`). **No `key_schema`**; LSIs can only be defined at table creation.

### Data protection
- `ttl { enabled, attribute_name }`: `enabled` default `false`; `attribute_name` required when enabled and must not be set otherwise.
- `point_in_time_recovery { enabled, recovery_period_in_days }`: `enabled` required (block absent ⇒ false); may take ~10 min on new tables; `recovery_period_in_days` optional, default 35. The provider page states no range; AWS states **1–35 days** [20].
- `server_side_encryption { enabled, kms_key_arn }`:
  - Default (block absent or `enabled = false`): **AWS owned key** ("DEFAULT" in console).
  - `enabled = true` without `kms_key_arn`: **AWS managed key `alias/aws/dynamodb`** ("KMS" in console).
  - `kms_key_arn`: only for keys other than `alias/aws/dynamodb` (customer managed); not populated for default keys.
- `deletion_protection_enabled`: default `false`.
- `stream_enabled`; `stream_view_type` = `KEYS_ONLY` | `NEW_IMAGE` | `OLD_IMAGE` | `NEW_AND_OLD_IMAGES` (only when streams are enabled).
- `table_class`: `STANDARD` (default) | `STANDARD_INFREQUENT_ACCESS`.

### Global Tables v2 — `replica` blocks
- `region_name` (required); `kms_key_arn` (**changing it recreates the replica**; same default-key caveat); `point_in_time_recovery` (default false); `deletion_protection_enabled` (default false); `propagate_tags` (default false; tags flow table→replica only, replica drift not detected, switching to false leaves replica tags unmanaged); `consistency_mode` = `EVENTUAL` (default) | `STRONG` (MRSC).
- `global_table_witness { region_name }`: only with exactly **one** `replica` having `consistency_mode = "STRONG"`; other combinations fail to provision.
- **Never mix** `replica` blocks with `aws_dynamodb_table_replica`; when using that resource set `lifecycle { ignore_changes = [replica] }` on the table.
- Global Tables V1 → `aws_dynamodb_global_table` (§7).

### Restore / import from S3
- `restore_backup_arn`, `restore_date_time`, `restore_source_name`, `restore_source_table_arn` (required cross-region), `restore_to_latest_time`.
- `import_table { input_format (CSV|DYNAMODB_JSON|ION), input_compression_type (GZIP|ZSTD|NONE), input_format_options.csv, s3_bucket_source { bucket, bucket_owner, key_prefix } }`.

### Timeouts and import
- Timeouts: create 30m, update 60m, delete 10m (custom values below internal defaults are ignored).
- Import ID: table **name** (`GameScores`); identity block (>= 1.12): `name` + optional `account_id`, `region`.

## 4. aws_dynamodb_global_secondary_index

Source [12] (2026-10-23).
- Required: `table_name`, `index_name`, `key_schema`, `projection`.
- `key_schema`: >= 1 HASH, HASH before RANGE; each element `attribute_name`, `attribute_type` (`S`|`N`|`B`), `key_type`; any change **forces new**.
- `provisioned_throughput { read_capacity_units, write_capacity_units }` required for `PROVISIONED` tables; `on_demand_throughput` only for `PAY_PER_REQUEST`; `warm_throughput` (both fields required in block).
- **Never mix** with inline `global_secondary_index` blocks on the same table ("conflicts, perpetual differences, and Global Secondary Indexes being overwritten"); migrate by one resource per block + import.
- Import `table_name,index_name`; identity `table_name` + `index_name`. Timeouts 30m/60m/10m.
- Maturity: the table page calls it "experimental"; the resource page itself shows no experimental warning or opt-in (M1).

## 5. Auto scaling (aws_appautoscaling_target / _policy)

Sources [13][14] (2026-10-23).
- Target required: `max_capacity`, `min_capacity`, `resource_id`, `scalable_dimension`, `service_namespace = "dynamodb"`.
  - Table: `resource_id = "table/<name>"`, `dynamodb:table:ReadCapacityUnits` / `dynamodb:table:WriteCapacityUnits`.
  - Index: `resource_id = "table/<name>/index/<index>"`, `dynamodb:index:ReadCapacityUnits` / `…WriteCapacityUnits`.
  - App Auto Scaling auto-manages the service-linked role on first registration (use `aws_iam_service_linked_role` to own it). Targets created before 2023-03-20 may lack `arn` and cannot take tags.
  - Import `service-namespace/resource-id/scalable-dimension`; identity (`service_namespace`, `resource_id`, `scalable_dimension`).
- Policy required: `name`, `resource_id`, `scalable_dimension`, `service_namespace`; `policy_type` defaults to `StepScaling` — set `TargetTrackingScaling` for DynamoDB; example uses `predefined_metric_type = "DynamoDBReadCapacityUtilization"`, `target_value = 70`. `DynamoDBWriteCapacityUtilization` is not shown on this page (U1). Import `service-namespace/resource-id/scalable-dimension/policy-name`.
- Pair with table `ignore_changes` (§3).

## 6. Satellite resources

- **aws_dynamodb_table_item** [15]: required `table_name`, `hash_key`, `item` (JSON incl. key attrs); `range_key` if table has one. "Not meant to be used for managing large amounts of data"; non-letter chars are stripped from attribute names internally (collisions error). Import `table_name,hash_value[,range_value]` (since 6.52.0); prefer identity when keys contain commas; B keys base64; needs `dynamodb:DescribeTable` + `GetItem`.
- **aws_dynamodb_kinesis_streaming_destination** [16]: required `stream_arn` (same account+region), `table_name`; `approximate_creation_date_time_precision` = `MILLISECOND` | `MICROSECOND` (default not stated, U2). One destination per table. Import `table_name,stream_arn`.
- **aws_dynamodb_contributor_insights** [17]: required `table_name`; optional `index_name`, `mode` (values not listed, U3). Import `name:<table>/index:<index>/<account>`.
- **aws_dynamodb_resource_policy** [18]: required `resource_arn` (table or stream), `policy`; optional `confirm_remove_self_resource_access`. 20 KB limit incl. whitespace; index permissions go in the base table policy. Exports `revision_id`. Import by `resource_arn`.
- **aws_dynamodb_table_replica** [19]: required `global_table_arn`; use provider aliases per region; import `table-name:main-region` (main table region).
- **aws_dynamodb_table_export** (brief) [21]: required `s3_bucket`, `table_arn` (both force new); `export_type` `FULL_EXPORT` (default) | `INCREMENTAL_EXPORT` (needs `incremental_export_specification`); `export_format` `DYNAMODB_JSON` (default) | `ION`; **PITR must be enabled**; destroy only removes from state. Import by export ARN.
- **Backups** (brief): on-demand backup resource not fetched this run (L3); Security Hub DynamoDB.4 expects AWS Backup plan coverage (§8).

## 7. aws_dynamodb_global_table (legacy V1)

Source [22] (2026-10-23). Exactly what the docs say:
- "Manages DynamoDB Global Tables V1 (version 2017.11.29)"; "To instead manage DynamoDB Global Tables V2 (version 2019.11.21), use the `replica` configuration block" of `aws_dynamodb_table`.
- Warns "There are many restrictions before you can properly create DynamoDB Global Tables in multiple regions."
- Required `name` (must match underlying table names), `replica { region_name }`. Timeouts 1m each. Import by name.
- The page does **not** use the word "deprecated"; preferring V2 for new work is the documented direction, not a removal notice.

## 8. AWS guidance

Security Hub DynamoDB controls [23] (2026-10-23):

| ID | Title | Severity | Config rule | Terraform lever |
|---|---|---|---|---|
| DynamoDB.1 | Tables should automatically scale capacity with demand | Medium | `dynamodb-autoscaling-enabled` (optional params min capacity 1–40000, target util 20–90) | `PAY_PER_REQUEST`, or PROVISIONED + appautoscaling target/policy |
| DynamoDB.2 | Tables should have PITR enabled | Medium | `dynamodb-pitr-enabled` | `point_in_time_recovery { enabled = true }` (+ replicas) |
| DynamoDB.3 | DAX clusters encrypted at rest | Medium | `dax-encryption-enabled` | DAX (out of scope); cannot enable after creation |
| DynamoDB.4 | Tables should be present in a backup plan | Medium | `dynamodb-resources-protected-by-backup-plan` (`backupVaultLockCheck`) | AWS Backup plan/selection |
| DynamoDB.5 | Tables should be tagged | Low | `tagged-dynamodb-table` (`requiredTagKeys` up to 6) | `tags` / `default_tags`, `propagate_tags` on replicas |
| DynamoDB.6 | Tables should have deletion protection enabled | Medium | `dynamodb-table-deletion-protection-enabled` | `deletion_protection_enabled = true` |
| DynamoDB.7 | DAX clusters encrypted in transit (TLS) | Medium | `dax-tls-endpoint-encryption` | DAX (out of scope) |

Note: Security Hub has **no DynamoDB control requiring a customer managed KMS key** for tables.

AWS best practices:
- Encryption at rest is always on; key types: AWS owned (default, free), AWS managed, customer managed (KMS charges); switchable at any time. With a sort key, some range-boundary sort-key values are stored in plaintext in table metadata. [24]
- Preventative security: IAM roles (no stored credentials), least-privilege IAM policies, IAM conditions for fine-grained access, VPC endpoint + `aws:sourceVpce`, consider client-side encryption (AWS Database Encryption SDK), no sensitive data in primary key names/values (use `pk`/`sk`). [25]
- PITR: recovery period 1–35 days; price does not depend on the period; restore always creates a **new table**; deleting a PITR table creates a 35-day system backup `<table>$DeletedTableBackup`. Decreasing the period immediately drops older restore points. [20]

## 9. Unverified / medium-confidence items, coverage limits, legacy corrections

- U1 `DynamoDBWriteCapacityUtilization` metric type — not shown on the provider page (AWS App Auto Scaling docs not fetched).
- U2 `approximate_creation_date_time_precision` default — not stated.
- U3 `aws_dynamodb_contributor_insights` `mode` valid values — not listed.
- U4 TTL deletion timing (legacy "within 48 hours") — not re-verified this run.
- M1 `aws_dynamodb_global_secondary_index` maturity — table page says "experimental", resource page shows no such warning.
- M2 WebFetch paraphrases warning text; substance confirmed on raw markdown.
- L1 CHANGELOG 6.55.0 only partially visible (chunk boundary).
- L2 Raw `main` markdown may run slightly ahead of 6.70.0 (F12).
- L3 Not fetched: `aws_dynamodb_table` data source, on-demand backup, DAX, AWS DynamoDB global tables / MRSC user-guide pages.

Legacy file claims found wrong (`workspace/terraform/research_AWS_DynamoDB_aws-v6.x.md`):
1. Calls the default AWS-owned key `alias/aws/dynamodb` — wrong: `alias/aws/dynamodb` is the **AWS managed** key; the default is the AWS owned key [11][24].
2. `aws_dynamodb_global_secondary_index` example uses `name`, `hash_key`, `range_key`, `projection_type`, `read_capacity` — wrong schema: actual args are `index_name`, `key_schema`, `projection`, `provisioned_throughput` [12].
3. `required_version = ">= 1.7"`, `~> 6.0` and S3 backend `dynamodb_table` locking — superseded (F1, F3, F7).
4. Claims Security Hub/compliance "requires" CMK for tables — no DynamoDB Security Hub control requires CMK [23] (HIPAA/PCI claims unverified).
5. Says `recovery_period_in_days` is "new in v6.x" — the 6.0.0 upgrade guide has no DynamoDB items; introduction version unverified.

## 10. Security note

None — no instruction-like or injected text observed in fetched pages.

## Source Bibliography

All fetched 2026-10-23.

1. https://releases.hashicorp.com/terraform/ (via F1)
2. https://raw.githubusercontent.com/hashicorp/terraform/v1.16/CHANGELOG.md (via F1)
3. https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md (via F2)
4. https://releases.hashicorp.com/terraform-provider-aws/ (via F3)
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown (via F5)
6. https://developer.hashicorp.com/terraform/language/expressions/version-constraints (via F6)
7. https://developer.hashicorp.com/terraform/language/backend/s3 (via F7)
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
10. https://github.com/hashicorp/terraform-provider-aws/releases (via F3)
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_global_secondary_index.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/appautoscaling_target.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/appautoscaling_policy.html.markdown
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table_item.html.markdown
16. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_kinesis_streaming_destination.html.markdown
17. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_contributor_insights.html.markdown
18. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_resource_policy.html.markdown
19. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table_replica.html.markdown
20. https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery_Howitworks.html
21. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table_export.html.markdown
22. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_global_table.html.markdown
23. https://docs.aws.amazon.com/securityhub/latest/userguide/dynamodb-controls.html
24. https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html
25. https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices-security-preventative.html
