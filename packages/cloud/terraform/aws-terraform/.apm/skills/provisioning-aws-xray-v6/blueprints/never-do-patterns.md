# Never-Do Patterns — provisioning-aws-xray-v6

Index of the never-do blueprints. Each entry has a `# WRONG` block, the documented reason with its
source (read 2026-10-23), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| Pinning withdrawn provider 6.57.0 | [never-do-provider-migration](./never-do-provider-migration.md#1-pinning-version-6570) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-provider-migration](./never-do-provider-migration.md#2-s3-backend-with-dynamodb_table) |
| Removing `aws_xray_encryption_config` expecting to change encryption | [never-do-encryption](./never-do-encryption.md#1-removing-the-encryption-config-to-revert) |
