# Unverified Claims and Risks — hashicorp/aws 6.x DynamoDB

Research date 2026-10-23. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** as of 2026-10-23 (latest 6.70.0, released
  2026-10-21; the CHANGELOG top heading is "6.71.0 (Unreleased)"). Re-verify when starting new work.
  Source: https://releases.hashicorp.com/terraform-provider-aws/
- **Terraform 1.17.0 is stable since 2026-10-21** (no breaking changes, no validate/S3-backend/
  lock-file/`required_version` changes). It is not the target of this skill (`~> 1.16`, 1.16.6);
  re-verify before moving. Source: https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md
- **6.57.0 is permanently withdrawn** from GitHub and the Registry; never pin it.
- **v7 is planned**, none released. When v7 ships, create a new skill `provisioning-aws-dynamodb-v7`.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Write-capacity App Auto Scaling metric type — the provider policy page shows only the read example (`DynamoDBReadCapacityUtilization`); the write metric name does not appear on it | (unverified) — confirm the metric name against AWS docs before use |
| U2 | `aws_dynamodb_kinesis_streaming_destination` `approximate_creation_date_time_precision` default — not stated | (unverified) — set it explicitly or ask |
| U3 | `aws_dynamodb_contributor_insights` `mode` valid values — not listed | (unverified) — do not set `mode` without confirming |
| U4 | TTL deletion timing — not re-verified | (unverified) — do not promise a deletion deadline |
| U5 | Provider version that introduced `recovery_period_in_days` — the 6.0.0 upgrade guide has no DynamoDB items | (unverified) — do not call it new in any version |
| U7 | Whether `replica` blocks require `stream_enabled` on the table — not stated on the cited pages | (unverified) — check the table page before use |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | `aws_dynamodb_global_secondary_index` maturity — the table page says "experimental", the resource page shows no such warning | (medium confidence) — Ask First |
| M2 | "No Security Hub DynamoDB control requires a customer managed key" — absence of evidence: the controls DynamoDB.1, .2, .4, .5, .6 do not mention one; DynamoDB.3 and .7 concern DAX and were not read for key requirements | (medium confidence, absence of evidence) — Ask First |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG 6.55.0 only partially visible; no DynamoDB entries seen in the other versions 6.48.0-6.70.0 except those cited in SKILL.md |
| L2 | Raw `main` markdown may run slightly ahead of 6.70.0 |
| L3 | Not fetched: `aws_dynamodb_table` data source, on-demand backup resource, DAX, AWS Global Tables / MRSC user-guide pages |

## Tag to Register Mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) | SKILL.md Ask First - separate global index resource row | M1 |
| (medium confidence) | always-do-indexes-capacity.md section 3 - separate GSI resource maturity | M1 |
| (unverified) | SKILL.md Ask First - settings the docs leave open (write-capacity metric) | U1 |
| (unverified) | always-do-indexes-capacity.md section 4 - write-capacity metric type | U1 |
| (unverified) | SKILL.md Ask First - settings the docs leave open (Kinesis precision) | U2 |
| (unverified) | always-do-replication-satellites.md section 7 - Kinesis precision default | U2 |
| (unverified) | SKILL.md Ask First - settings the docs leave open (contributor insights mode) | U3 |
| (unverified) | always-do-replication-satellites.md section 7 - contributor insights `mode` | U3 |
| (unverified) | SKILL.md Ask First - settings the docs leave open (TTL timing) | U4 |
| (unverified) | always-do-foundation.md section 2 - TTL deletion timing | U4 |
| (unverified) | SKILL.md migration section - `recovery_period_in_days` introduction version | U5 |
| (unverified) | always-do-replication-satellites.md section 6 - replica streams | U7 |
| (medium confidence, absence of evidence) | SKILL.md Ask First - encryption key row | M2 |
| (medium confidence) | evaluation-scenarios.md scenario 2 - separate global index resource | M1 |
| (medium confidence, absence of evidence) | evaluation-scenarios.md scenario 3 - customer managed key | M2 |
| (unverified) | evaluation-scenarios.md scenario 5 - write metric, Kinesis precision, `mode` values, TTL timing | U1-U4 |

## Source Bibliography

All fetched 2026-10-23 unless noted.

1. https://releases.hashicorp.com/terraform/ — Terraform 1.16.6; 1.17.0 stable
2. https://raw.githubusercontent.com/hashicorp/terraform/v1.16/CHANGELOG.md — 1.16.x changes
3. https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md — 1.17.0 changes
4. https://releases.hashicorp.com/terraform-provider-aws/ — latest 6.70.0
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — per-resource `region`
6. https://developer.hashicorp.com/terraform/language/expressions/version-constraints — `~>` for root, `>=` for modules
7. https://developer.hashicorp.com/terraform/language/backend/s3 — `use_lockfile`; `dynamodb_table` deprecated
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.57.0 withdrawn; 6.52.0, 6.57.1, 6.67.0 DynamoDB entries
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — no DynamoDB items
10. https://github.com/hashicorp/terraform-provider-aws/releases — release list
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown — table arguments
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_global_secondary_index.html.markdown — separate GSI resource
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/appautoscaling_target.html.markdown — scaling target
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/appautoscaling_policy.html.markdown — scaling policy
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table_item.html.markdown — table item
16. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_kinesis_streaming_destination.html.markdown — Kinesis destination
17. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_contributor_insights.html.markdown — contributor insights
18. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_resource_policy.html.markdown — resource policy
19. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table_replica.html.markdown — table replica
20. https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery_Howitworks.html — PITR 1-35 days
21. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table_export.html.markdown — table export
22. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_global_table.html.markdown — Global Tables V1
23. https://docs.aws.amazon.com/securityhub/latest/userguide/dynamodb-controls.html — DynamoDB.1-7
24. https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html — key types
25. https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices-security-preventative.html — preventative security
26. https://developer.hashicorp.com/terraform/language/tests — `terraform test`
27. https://developer.hashicorp.com/terraform/cli/commands/plan — `-detailed-exitcode`
