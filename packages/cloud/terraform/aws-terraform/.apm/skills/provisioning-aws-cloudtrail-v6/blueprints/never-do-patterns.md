# Never-Do Patterns — provisioning-aws-cloudtrail-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-23), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| `event_selector` mixed with `advanced_event_selector` | [never-do-trail](./never-do-trail.md#1-mixing-event_selector-and-advanced_event_selector) |
| `cloud_watch_logs_group_arn` without `:*` | [never-do-trail](./never-do-trail.md#2-cloudwatch-logs-group-arn-without-) |
| Relying on a default log encryption (no `kms_key_id`) | [never-do-trail](./never-do-trail.md#3-relying-on-a-default-log-encryption) |
| Bucket policy without `aws:SourceArn` or with mismatched prefix | [never-do-trail](./never-do-trail.md#4-bucket-policy-without-awssourcearn-or-with-a-mismatched-prefix) |
| HCL for `aws_cloudtrail_channel` (no provider doc) | [never-do-trail](./never-do-trail.md#5-hcl-for-aws_cloudtrail_channel) |
| `data.aws_region.name` (deprecated in 6.0) | [never-do-provider-migration](./never-do-provider-migration.md#1-dataaws_regionname) |
| `suspend = 0` or `1` on the event data store | [never-do-provider-migration](./never-do-provider-migration.md#2-suspend--0-or-1-on-the-event-data-store) |
| `region` on the organization delegated admin account | [never-do-provider-migration](./never-do-provider-migration.md#3-region-on-the-organization-delegated-admin-account) |
| S3 backend with `dynamodb_table` | [never-do-provider-migration](./never-do-provider-migration.md#4-s3-backend-with-dynamodb_table) |
| Pinning withdrawn provider 6.57.0 | [never-do-provider-migration](./never-do-provider-migration.md#5-pinning-version-6570) |
| Changing the event data store KMS key | [never-do-provider-migration](./never-do-provider-migration.md#6-removing-or-changing-the-event-data-store-kms-key) |
