# Always-Do Patterns — provisioning-aws-cloudtrail-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL and cites its official
source (fetched 2026-10-23).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`), S3 backend with `use_lockfile`, `.region` | [always-do-trail](./always-do-trail.md#1-terraform-block-and-region) |
| 2 | Dedicated log bucket, public access block, access logging, bucket policy with `aws:SourceArn` | [always-do-trail](./always-do-trail.md#2-log-bucket-hardening-and-bucket-policy) |
| 3 | Multi-region trail with validation, `kms_key_id`, CloudWatch Logs `:*`, `depends_on` | [always-do-trail](./always-do-trail.md#3-the-trail) |
| 4 | KMS key policy statements (encrypt, decrypt, describe) | [always-do-kms-lake](./always-do-kms-lake.md#4-kms-key-policy-for-the-trail) |
| 5 | Event data store with CMK, retention and termination protection | [always-do-kms-lake](./always-do-kms-lake.md#5-event-data-store-cloudtrail-lake) |
| 6 | Organization delegated admin (global, no `region`) | [always-do-kms-lake](./always-do-kms-lake.md#6-organization-delegated-administrator-global) |
| 7 | `terraform test` with `mock_provider` and CI commands | [always-do-kms-lake](./always-do-kms-lake.md#7-terraform-test-and-ci) |
