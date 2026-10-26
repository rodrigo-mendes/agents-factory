# Always-Do Patterns — provisioning-aws-dynamodb-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL and cites its official
source (fetched 2026-10-23).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and S3 backend with `use_lockfile` | [always-do-foundation](./always-do-foundation.md#1-terraform-block-and-s3-backend) |
| 2 | Table keys, explicit `billing_mode`, deletion protection, PITR, encryption, TTL | [always-do-foundation](./always-do-foundation.md#2-table-keys-billing-and-data-protection) |
| 3 | Inline GSI with `key_schema`, LSI, separate GSI resource | [always-do-indexes-capacity](./always-do-indexes-capacity.md#3-secondary-indexes) |
| 4 | App Auto Scaling target and policy with `ignore_changes` | [always-do-indexes-capacity](./always-do-indexes-capacity.md#4-auto-scaling-for-provisioned-tables) |
| 5 | On-demand and warm throughput | [always-do-foundation](./always-do-foundation.md#5-on-demand-and-warm-throughput) |
| 6 | Global Tables V2 with `replica` blocks | [always-do-replication-satellites](./always-do-replication-satellites.md#6-global-tables-v2-replicas) |
| 7 | Resource policy, Kinesis destination, contributor insights, export, table item | [always-do-replication-satellites](./always-do-replication-satellites.md#7-satellite-resources) |
| 8 | `terraform test` with `mock_provider` and CI commands | [always-do-replication-satellites](./always-do-replication-satellites.md#8-terraform-test) |
