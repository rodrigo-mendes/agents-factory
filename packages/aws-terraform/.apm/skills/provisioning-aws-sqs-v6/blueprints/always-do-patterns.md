# Always-Do Patterns — provisioning-aws-sqs-v6

Index of the always-do blueprints, split by topic. Each pattern has complete HCL and cites its
official source (fetched 2026-10-23). Values marked `# example` are placeholders.

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and standard queue | [always-do-queues](./always-do-queues.md#1-terraform-block-and-standard-queue) |
| 2 | Encryption (SSE-SQS, SSE-KMS) and tags | [always-do-queues](./always-do-queues.md#2-encryption-and-tags) |
| 3 | FIFO queue and high-throughput FIFO | [always-do-queues](./always-do-queues.md#3-fifo-queue) |
| 4 | Queue policy with explicit `Version` | [always-do-policies](./always-do-policies.md#4-queue-policy-with-explicit-version) |
| 5 | SNS producer policy | [always-do-policies](./always-do-policies.md#5-sns-producer-policy) |
| 6 | Encrypted queue with AWS service producers | [always-do-policies](./always-do-policies.md#6-encrypted-queue-with-service-producers) |
| 7 | Dead-letter queue, redrive and redrive allow policy | [always-do-dlq](./always-do-dlq.md#7-dead-letter-queue-and-redrive) |
| 8 | Import by queue URL | [always-do-dlq](./always-do-dlq.md#8-import) |
