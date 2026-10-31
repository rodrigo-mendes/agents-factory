# Never-Do Patterns — provisioning-aws-eventbridge-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (read dates in each file header), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| Bus policy and permission resources on one bus | [never-do-bus-and-rules](./never-do-bus-and-rules.md#1-bus-policy-and-permission-on-one-bus) |
| `schedule_expression` on a non-default bus | [never-do-bus-and-rules](./never-do-bus-and-rules.md#2-schedule-expression-on-a-non-default-bus) |
| `is_enabled` on a rule (deprecated) | [never-do-bus-and-rules](./never-do-bus-and-rules.md#3-is_enabled-on-a-rule) |
| `role_arn` on a CloudWatch Logs target | [never-do-targets](./never-do-targets.md#1-role_arn-on-a-cloudwatch-logs-target) |
| `input`, `input_path`, `input_transformer` together | [never-do-targets](./never-do-targets.md#2-more-than-one-input-argument) |
| FIFO or other-Region queue as DLQ | [never-do-targets](./never-do-targets.md#3-fifo-or-other-region-dlq) |
| Lambda or SNS target with no permission path | [never-do-targets](./never-do-targets.md#4-lambda-or-sns-target-with-no-permission-path) |
| Missing `role_arn` where it is required | [never-do-targets](./never-do-targets.md#5-missing-role_arn-on-targets-that-require-it) |
| Scheduler target without `role_arn` | [never-do-scheduler-and-versions](./never-do-scheduler-and-versions.md#1-scheduler-target-without-role_arn) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-scheduler-and-versions](./never-do-scheduler-and-versions.md#2-s3-backend-with-dynamodb_table) |
| Pinning withdrawn provider 6.57.0 | [never-do-scheduler-and-versions](./never-do-scheduler-and-versions.md#3-pinning-version-6570) |
