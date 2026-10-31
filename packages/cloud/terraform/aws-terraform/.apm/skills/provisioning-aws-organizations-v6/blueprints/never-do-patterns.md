# Never-Do Patterns — provisioning-aws-organizations-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-23), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| `region` argument or `@region` import on Organizations resources | [never-do-organization](./never-do-organization.md#1-region-on-organizations-resources) |
| Removing `FullAWSAccess` without a replacement | [never-do-organization](./never-do-organization.md#2-removing-fullawsaccess) |
| Using the RCP limits (5120 chars / 5 attached) for SCPs | [never-do-organization](./never-do-organization.md#3-rcp-limits-applied-to-scps) |
| Expecting SCPs to restrict the management account | [never-do-organization](./never-do-organization.md#4-scp-expected-to-restrict-the-management-account) |
| `role_name` without `ignore_changes` | [never-do-organization](./never-do-organization.md#5-role_name-without-ignore_changes) |
| Treating policy `skip_destroy` as last-SCP protection | [never-do-organization](./never-do-organization.md#6-skip_destroy-misread) |
| Reading the deprecated `status` attribute | [never-do-provider](./never-do-provider.md#1-deprecated-status-attribute) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-provider](./never-do-provider.md#2-s3-backend-with-dynamodb_table) |
| Pinning withdrawn provider 6.57.0 | [never-do-provider](./never-do-provider.md#3-pinning-version-6570) |
