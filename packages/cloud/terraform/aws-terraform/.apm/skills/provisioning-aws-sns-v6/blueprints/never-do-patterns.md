# Never-Do Patterns — provisioning-aws-sns-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-23), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| Bare account ID as topic-policy Principal | [never-do-access-kms](./never-do-access-kms.md#1-bare-account-id-as-principal) |
| `alias/aws/sns` for AWS service publishers | [never-do-access-kms](./never-do-access-kms.md#2-aws-managed-key-for-aws-service-publishers) |
| Source conditions in the key policy for EventBridge | [never-do-access-kms](./never-do-access-kms.md#3-sourceaccount-and-sourcearn-conditions-for-eventbridge) |
| Destroying a topic with an active archive policy | [never-do-access-kms](./never-do-access-kms.md#4-destroying-a-topic-with-an-active-archive-policy) |
| FIFO topic with email, SMS, mobile or HTTP(S) subscriptions | [never-do-subscriptions](./never-do-subscriptions.md#1-fifo-topic-with-email-sms-mobile-or-http-subscriptions) |
| Subscription provider outside the topic region | [never-do-subscriptions](./never-do-subscriptions.md#2-subscription-provider-outside-the-topic-region) |
| Topic account provider for same-region cross-account SQS | [never-do-subscriptions](./never-do-subscriptions.md#3-topic-account-provider-for-same-region-cross-account-sqs) |
| Relying on destroy for unconfirmed email or HTTP(S) subscriptions | [never-do-subscriptions](./never-do-subscriptions.md#4-relying-on-destroy-for-unconfirmed-email-or-https-subscriptions) |
