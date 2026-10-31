# Never-Do Patterns — provisioning-aws-lambda-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (pages read 2026-10-23), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| `filename`, `s3_bucket` and `image_uri` combined on one function | [never-do-function](./never-do-function.md#1-multiple-code-sources-on-one-function) |
| `source_kms_key_arn` with `image_uri` | [never-do-function](./never-do-function.md#2-source-kms-key-on-an-image-function) |
| `source_code_hash` used to detect out-of-band changes | [never-do-function](./never-do-function.md#3-relying-on-source_code_hash-for-out-of-band-changes) |
| More than five `layers` | [never-do-function](./never-do-function.md#4-more-than-five-layers) |
| `starting_position` on an SQS mapping | [never-do-events](./never-do-events.md#1-starting-position-on-an-sqs-mapping) |
| `maximum_concurrency` below 2 | [never-do-events](./never-do-events.md#2-maximum-concurrency-below-2) |
| `provisioned_poller_config` on SQS or streams | [never-do-events](./never-do-events.md#3-provisioned-pollers-on-sqs-or-streams) |
| Empty `destination_config` on event invoke config | [never-do-events](./never-do-events.md#4-empty-event-invoke-destination-block) |
| Function timeout above the SQS visibility timeout | [never-do-events](./never-do-events.md#5-function-timeout-above-the-queue-visibility-timeout) |
| Deleting the execution role before VPC ENI cleanup | [never-do-access-provider](./never-do-access-provider.md#1-deleting-the-execution-role-before-vpc-cleanup) |
| S3-principal permission without `source_account` | [never-do-access-provider](./never-do-access-provider.md#2-s3-principal-permission-without-source-account) |
| Pinning withdrawn provider 6.57.0 | [never-do-access-provider](./never-do-access-provider.md#3-pinning-provider-6570) |
