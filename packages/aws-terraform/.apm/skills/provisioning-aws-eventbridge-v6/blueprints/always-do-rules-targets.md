# Always-Do — Rules and Targets (Rule, Retry, DLQ, Input Transformer, Lambda Permission)

hashicorp/aws 6.x · Terraform ~> 1.16 · Pages read 2026-10-23. All names, ARNs, patterns and numbers
are `# example` values.

## 3. Rule

Set `state` (not `is_enabled`). At least one of `event_pattern` or `schedule_expression` is required.
`event_bus_name` takes a name or ARN and defaults to `default`. `schedule_expression` works only on
the default bus. Filter patterns on `source` and `detail-type`; add `account`/`region` to limit
cross-account/Region matches (AWS patterns page).

```hcl
# FRAGMENT — references aws_cloudwatch_event_bus.orders from always-do-foundation §2.
resource "aws_cloudwatch_event_rule" "order_created" {
  name           = "order-created"                          # example
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  state          = "ENABLED"   # ENABLED (default) | DISABLED | ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS
  event_pattern = jsonencode({
    source        = ["com.example.orders"]                  # example
    "detail-type" = ["OrderCreated"]                        # example
  })
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown
# Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-patterns-best-practices.html
```

## 4. Target with Retry, DLQ and Input Transformer

Defaults: 24 hours and up to 185 attempts, with exponential backoff and jitter; after that the event is
dropped (AWS retry page). The DLQ must be a standard SQS queue in the rule's Region. The console
grants the queue policy automatically but the API does not, so grant it manually (AWS DLQ page; for
the policy itself see provisioning-aws-sqs-v6). `input`, `input_path` and
`input_transformer` are mutually exclusive; `input_template` must be valid JSON, escaped for JSON and
Terraform; `input_paths` allows at most 100 pairs, dot notation, and keys cannot start with "AWS".
The target's `event_bus_name` must match the rule's bus. The provider page says to set
permissions with `aws_lambda_permission` to invoke a Lambda function; the AWS page says Lambda accepts
either an IAM execution role (`role_arn`) or a resource-based policy. This pattern uses the resource-based policy.

```hcl
# FRAGMENT — references aws_lambda_function.handler and aws_sqs_queue.target_dlq,
# defined elsewhere (see provisioning-aws-lambda-v6, provisioning-aws-sqs-v6).
resource "aws_cloudwatch_event_target" "handler" {
  rule           = aws_cloudwatch_event_rule.order_created.name
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  target_id      = "order-handler"                          # example
  arn            = aws_lambda_function.handler.arn

  retry_policy {
    maximum_event_age_in_seconds = 3600   # example
    maximum_retry_attempts       = 10     # example
  }
  dead_letter_config {
    arn = aws_sqs_queue.target_dlq.arn    # standard queue, same Region
  }
  input_transformer {
    input_paths    = { orderId = "$.detail.orderId" }        # example; dot notation
    input_template = "{\"orderId\": <orderId>}"              # example; valid JSON, escaped
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_target.html.markdown
# Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html
# Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html

resource "aws_lambda_permission" "from_events" {
  statement_id  = "AllowEventBridgeInvoke"                  # example
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "events.amazonaws.com"
  # (medium confidence) source_arn = the rule ARN is inferred from the AWS Lambda sample
  # (principal events.amazonaws.com, condition AWS:SourceArn = rule ARN); the provider page does not state the mapping.
  source_arn    = aws_cloudwatch_event_rule.order_created.arn
}
# Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html

# The DLQ queue policy is not shown here: grant it per the AWS DLQ page
# (https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html).
```

Rule ARN form in resource policies: `rule/<bus-name>/<rule-name>` on a custom bus, `rule/<rule-name>`
on the default bus (AWS resource-based policies page).
