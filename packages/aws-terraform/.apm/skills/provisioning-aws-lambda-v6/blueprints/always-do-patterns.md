# Always-Do Patterns — provisioning-aws-lambda-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL (fragments are marked) and cites
its official source (provider pages read 2026-10-23).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) | [always-do-function](./always-do-function.md#1-terraform-block-and-provider-constraint) |
| 2 | Execution role (trust policy and log permissions) | [always-do-function](./always-do-function.md#2-execution-role) |
| 3 | Zip function with managed log group and `logging_config` | [always-do-function](./always-do-function.md#3-zip-function-with-managed-log-group) |
| 4 | Container image function | [always-do-function-config](./always-do-function-config.md#4-container-image-function) |
| 5 | VPC attachment and role retention | [always-do-function-config](./always-do-function-config.md#5-vpc-attachment) |
| 6 | Environment variables and KMS | [always-do-function-config](./always-do-function-config.md#6-environment-variables-and-kms) |
| 7 | Tracing and dead-letter config | [always-do-function-config](./always-do-function-config.md#7-tracing-and-dead-letter-queue) |
| 8 | Alias and provisioned concurrency | [always-do-invocation](./always-do-invocation.md#8-alias-and-provisioned-concurrency) |
| 9 | Permission with `source_arn` / `source_account` | [always-do-invocation](./always-do-invocation.md#9-permission) |
| 10 | Function URL (`AWS_IAM` / `NONE`) | [always-do-invocation](./always-do-invocation.md#10-function-url) |
| 11 | Event invoke config | [always-do-invocation](./always-do-invocation.md#11-event-invoke-config) |
| 12 | SQS event source mapping | [always-do-events-layers](./always-do-events-layers.md#12-sqs-event-source-mapping) |
| 13 | Layer version | [always-do-events-layers](./always-do-events-layers.md#13-layer-version) |
| 14 | Code signing config | [always-do-events-layers](./always-do-events-layers.md#14-code-signing-config) |
