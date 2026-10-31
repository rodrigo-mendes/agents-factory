# Never-Do Patterns — provisioning-aws-step-functions-v6

Index of the never-do blueprints. Each entry has a `# WRONG` block, the documented reason with its
page (read 2026-10-23), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| `log_destination` ARN without the `:*` suffix | [never-do-configuration](./never-do-configuration.md#1-log-destination-arn-without-a-trailing-wildcard-suffix) |
| `name` and `name_prefix` together | [never-do-configuration](./never-do-configuration.md#2-setting-name-and-name_prefix-together) |
| Alias routing to an alias or an unpublished revision | [never-do-configuration](./never-do-configuration.md#3-alias-routing-to-an-alias-or-an-unpublished-revision) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-configuration](./never-do-configuration.md#4-s3-backend-with-dynamodb_table) |
| Pinning withdrawn provider 6.57.0 | [never-do-configuration](./never-do-configuration.md#5-pinning-version-6570) |
| `kms:ViaService` on the execution role | [never-do-iam-asl](./never-do-iam-asl.md#6-kmsviaservice-on-the-execution-role) |
| `.sync` / `.waitForTaskToken` in an EXPRESS state machine | [never-do-iam-asl](./never-do-iam-asl.md#7-sync-or-waitfortasktoken-in-an-express-state-machine) |
| `States.ALL` mixed with other names or not in the last retrier/catcher (it does not catch `States.DataLimitExceeded` or `States.Runtime`) | [never-do-iam-asl](./never-do-iam-asl.md#8-statesall-that-is-not-alone-and-last) |
| Unqualified Lambda ARN in IAM when invoking a version or alias | [never-do-iam-asl](./never-do-iam-asl.md#9-unqualified-lambda-arn-in-iam-when-invoking-a-version-or-alias) |
| Logging delivery actions scoped to a log group | [never-do-iam-asl](./never-do-iam-asl.md#10-scoping-logging-delivery-actions-to-a-log-group) |
