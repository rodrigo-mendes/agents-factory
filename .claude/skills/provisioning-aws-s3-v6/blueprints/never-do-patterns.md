# Never-Do Patterns — provisioning-aws-s3-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-14), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| Inline `versioning {}` or `server_side_encryption_configuration {}` mixed with their satellite resource | [never-do-resource-conflicts](./never-do-resource-conflicts.md#1-mixing-inline-arguments-with-satellite-resources) |
| Multiple `aws_s3_bucket_policy` / lifecycle / notification / CORS per bucket | [never-do-resource-conflicts](./never-do-resource-conflicts.md#2-multiple-single-config-resources-per-bucket) |
| `etag = filemd5(...)` on KMS-encrypted or multipart objects | [never-do-resource-conflicts](./never-do-resource-conflicts.md#3-etag-with-kms-or-multipart-objects) |
| `mfa_delete = "Enabled"` combined with lifecycle rules | [never-do-resource-conflicts](./never-do-resource-conflicts.md#4-mfa_delete-with-lifecycle-rules) |
| `acl = "log-delivery-write"` with `BucketOwnerEnforced` ownership | [never-do-ownership-acl](./never-do-ownership-acl.md#1-acl-log-delivery-write-with-bucketownerenforced) |
| `expected_bucket_owner` on satellite resources (deprecated, forces new) | [never-do-ownership-acl](./never-do-ownership-acl.md#2-expected_bucket_owner-on-satellite-resources) |
| Bucket home region read via `.region` instead of `.bucket_region` (6.0) | [never-do-provider-migration](./never-do-provider-migration.md#1-reading-bucket-region-via-region-attribute) |
| `region` set on `aws_s3_account_public_access_block` (global) | [never-do-provider-migration](./never-do-provider-migration.md#2-region-on-account-public-access-block) |
| `data.aws_region.current.name` (deprecated in 6.0) | [never-do-provider-migration](./never-do-provider-migration.md#3-deprecated-aws_region-name-attribute) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-provider-migration](./never-do-provider-migration.md#4-s3-backend-with-dynamodb_table) |
| Pinning withdrawn provider 6.57.0 | [never-do-provider-migration](./never-do-provider-migration.md#5-pinning-version-6570) |
| `bucket_namespace = "account-regional"` with a wrong name suffix | [never-do-naming-endpoints](./never-do-naming-endpoints.md#1-account-regional-namespace-without-correct-suffix) |
| `s3_us_east_1_regional_endpoint = "legacy"` (deprecated, removed in v7) | [never-do-naming-endpoints](./never-do-naming-endpoints.md#2-s3_us_east_1_regional_endpoint-legacy) |
