# Never-Do Patterns — provisioning-aws-sqs-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-23), and the correct alternative. One entry per row of the
SKILL.md Never Do table.

| Anti-pattern | Blueprint |
|---|---|
| Queue policy without `Version = "2012-10-17"` | [never-do-policies-access](./never-do-policies-access.md#1-queue-policy-without-explicit-version) |
| `Principal` `"*"` in a queue policy without a restricting condition | [never-do-policies-access](./never-do-policies-access.md#2-public-principal-in-a-queue-policy) |
| AWS managed key for service producers | [never-do-policies-access](./never-do-policies-access.md#3-aws-managed-key-with-service-producers) |
| `maxReceiveCount` as a string | [never-do-queue-config](./never-do-queue-config.md#4-maxreceivecount-as-a-string) |
| FIFO queue name without `.fifo` | [never-do-queue-config](./never-do-queue-config.md#5-fifo-name-without-fifo-suffix) |
| `perMessageGroupId` without `messageGroup` scope | [never-do-queue-config](./never-do-queue-config.md#6-permessagegroupid-without-messagegroup-scope) |
| FIFO/standard type mismatch between source and DLQ | [never-do-queue-config](./never-do-queue-config.md#7-dlq-type-mismatch) |
| DLQ in another account or Region | [never-do-queue-config](./never-do-queue-config.md#8-dlq-in-another-account-or-region) |
