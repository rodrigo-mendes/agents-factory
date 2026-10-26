# Never-Do — Subscriptions (FIFO Endpoints, Provider Region, Confirmation)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23. Names, ARNs and emails are `# example`.

## 1. FIFO Topic with Email, SMS, Mobile or HTTP Subscriptions

FIFO topics cannot deliver to email, mobile, SMS or HTTP(S); such endpoints cannot subscribe and
return errors. FIFO topics deliver to SQS FIFO and SQS standard queues; to reach Lambda, go through an
SQS queue.

```hcl
# WRONG — email on a FIFO topic
resource "aws_sns_topic_subscription" "bad" {
  topic_arn = aws_sns_topic.orders_fifo.arn
  protocol  = "email"                  # WRONG
  endpoint  = "ops@example.com"        # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown
# Source: https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html

# CORRECT — SQS endpoint
resource "aws_sns_topic_subscription" "ok" {
  topic_arn = aws_sns_topic.orders_fifo.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.orders_fifo.arn
}
```

Lambda functions: see `provisioning-aws-lambda-v6`.

## 2. Subscription Provider Outside the Topic Region

The subscription must use a provider in the topic's region, or creation fails.

```hcl
# WRONG — default provider is eu-west-1, topic is in us-east-1 (examples)
resource "aws_sns_topic_subscription" "bad" {
  topic_arn = "arn:aws:sns:us-east-1:123456789012:orders-events" # example
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.orders.arn
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown

# CORRECT — add `provider = aws.queue_account_topic_region` (an alias configured with the topic's region; see always-do-access-delivery §8)
```

## 3. Topic Account Provider for Same-Region Cross-Account SQS

For cross-account, same-region SQS subscriptions use the queue account's provider; otherwise Terraform
creates the subscription, keeps no state and recreates it on every apply.

```hcl
# WRONG — provider of the topic's account for a queue in another account
resource "aws_sns_topic_subscription" "bad" {
  provider  = aws.topic_account           # WRONG (placeholder alias for the topic's account)
  topic_arn = "arn:aws:sns:us-east-1:123456789012:orders-events" # example
  protocol  = "sqs"
  endpoint  = "arn:aws:sqs:us-east-1:210987654321:orders"        # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown

# CORRECT — the queue account's provider, e.g. aws.queue_account_topic_region (see always-do-access-delivery §8)
```

## 4. Relying on Destroy for Unconfirmed Email or HTTP(S) Subscriptions

As the docs state: Terraform cannot remove an unconfirmed partially supported subscription; destroy
removes it from state only and it stays in AWS. "You cannot unsubscribe to a subscription that is
pending confirmation." Confirmation can happen outside Terraform, such as through the email link. A
subscription imported after confirmation can be deleted by Terraform; deleting a topic deletes its
subscriptions. `pending_confirmation` shows the status.

```hcl
# WRONG — assuming `terraform destroy` removes this while it is unconfirmed
resource "aws_sns_topic_subscription" "ops_email" {
  topic_arn = aws_sns_topic.orders.arn
  protocol  = "email"
  endpoint  = "ops@example.com" # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown

# CORRECT — confirm it first (outside Terraform if needed), check
#   aws_sns_topic_subscription.ops_email.pending_confirmation, then manage or import it
```
