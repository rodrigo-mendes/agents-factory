# Always-Do Patterns — provisioning-aws-sns-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL and cites its official
source (fetched 2026-10-23). Values marked `# example` are placeholders.

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) | [always-do-topic](./always-do-topic.md#1-terraform-block-and-provider) |
| 2 | Standard topic with a customer managed key and tags | [always-do-topic](./always-do-topic.md#2-standard-topic-with-a-customer-managed-key) |
| 3 | FIFO topic (`.fifo`, throughput scope at creation) | [always-do-topic](./always-do-topic.md#3-fifo-topic) |
| 4 | Key policy for AWS service publishers | [always-do-topic](./always-do-topic.md#4-key-policy-for-aws-service-publishers) |
| 5 | Delivery status logging and data protection policy | [always-do-topic](./always-do-topic.md#5-delivery-status-logging-and-data-protection) |
| 6 | Topic policy (root ARN principal, TLS deny) | [always-do-access-delivery](./always-do-access-delivery.md#6-topic-policy) |
| 7 | SQS subscription with a DLQ | [always-do-access-delivery](./always-do-access-delivery.md#7-sqs-subscription-with-a-dlq) |
| 8 | Cross-region or cross-account subscription providers | [always-do-access-delivery](./always-do-access-delivery.md#8-cross-region-or-cross-account-subscription) |
| 9 | Firehose and HTTPS subscriptions | [always-do-access-delivery](./always-do-access-delivery.md#9-firehose-and-https-subscriptions) |
