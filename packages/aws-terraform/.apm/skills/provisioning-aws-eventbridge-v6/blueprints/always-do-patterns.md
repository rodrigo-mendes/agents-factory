# Always-Do Patterns — provisioning-aws-eventbridge-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL and cites its official
source (read dates in each file header). HCL that references resources defined elsewhere is marked as a fragment.

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and S3 backend with `use_lockfile` | [always-do-foundation](./always-do-foundation.md#1-terraform-block-and-s3-backend) |
| 2 | Custom bus (tags), bus policy, archive | [always-do-foundation](./always-do-foundation.md#2-bus-bus-policy-and-archive) |
| 3 | Rule with `event_pattern` and `state` | [always-do-rules-targets](./always-do-rules-targets.md#3-rule) |
| 4 | Target with retry policy, DLQ, input transformer, Lambda permission | [always-do-rules-targets](./always-do-rules-targets.md#4-target-with-retry-dlq-and-input-transformer) |
| 5 | Connection and API destination | [always-do-scheduler-integrations](./always-do-scheduler-integrations.md#5-connection-and-api-destination) |
| 6 | Scheduler schedule and group | [always-do-scheduler-integrations](./always-do-scheduler-integrations.md#6-scheduler-schedule-and-group) |
| 7 | Pipe (brief) | [always-do-scheduler-integrations](./always-do-scheduler-integrations.md#7-pipe-brief) |
