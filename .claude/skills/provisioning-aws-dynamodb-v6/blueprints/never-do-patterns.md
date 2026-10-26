# Never-Do Patterns — provisioning-aws-dynamodb-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-23), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| `attribute` blocks for non-key attributes (infinite plan loop) | [never-do-table-indexes](./never-do-table-indexes.md#1-defining-attributes-that-are-not-key-attributes) |
| Inline `global_secondary_index` mixed with `aws_dynamodb_global_secondary_index` | [never-do-table-indexes](./never-do-table-indexes.md#2-mixing-inline-global_secondary_index-with-the-separate-resource) |
| Inline GSI `hash_key` / `range_key` (deprecated in 6.x) | [never-do-table-indexes](./never-do-table-indexes.md#3-inline-gsi-hash_key-and-range_key) |
| `warm_throughput` set to its default values (reported diffs) | [never-do-table-indexes](./never-do-table-indexes.md#4-setting-warm_throughput-to-its-default-values) |
| `kms_key_arn` pointing at `alias/aws/dynamodb` | [never-do-table-indexes](./never-do-table-indexes.md#5-kms_key_arn-set-to-the-aws-managed-key) |
| `replica` blocks mixed with `aws_dynamodb_table_replica` | [never-do-replication-provider](./never-do-replication-provider.md#1-mixing-replica-blocks-with-aws_dynamodb_table_replica) |
| `aws_dynamodb_table_item` for large amounts of data | [never-do-replication-provider](./never-do-replication-provider.md#2-bulk-data-in-aws_dynamodb_table_item) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-replication-provider](./never-do-replication-provider.md#3-s3-backend-with-dynamodb_table) |
| Pinning withdrawn provider 6.57.0 | [never-do-replication-provider](./never-do-replication-provider.md#4-pinning-version-6570) |
