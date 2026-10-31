# Never-Do — Targets (Logs Role, Input, DLQ, Permissions, role_arn)

hashicorp/aws 6.x · Terraform ~> 1.16 · Pages read 2026-10-23. Names and ARNs are `# example` values.
All HCL here is a FRAGMENT: it references rules, queues, functions and roles defined elsewhere.

## 1. role_arn on a CloudWatch Logs Target

AWS resource-based policies page ("Important" box): CloudWatch Logs targets use resource-based
policies, so do not set `role_arn`. The logs policy grants `events.amazonaws.com` and
`delivery.logs.amazonaws.com` the actions `logs:CreateLogStream` and `logs:PutLogEvents`.

```hcl
# WRONG
resource "aws_cloudwatch_event_target" "bad_logs" {
  rule     = aws_cloudwatch_event_rule.r.name
  arn      = "arn:aws:logs:eu-west-1:123456789012:log-group:/events/example"   # example
  role_arn = aws_iam_role.events.arn                      # WRONG for Logs targets
}
# Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html

# CORRECT — no role_arn; permissions come from a resource-based policy on the log group
resource "aws_cloudwatch_event_target" "logs" {
  rule = aws_cloudwatch_event_rule.r.name
  arn  = "arn:aws:logs:eu-west-1:123456789012:log-group:/events/example"       # example
}
```

## 2. More Than One Input Argument

`input` (JSON), `input_path` (JSONPath) and `input_transformer` are mutually exclusive.

```hcl
# WRONG
resource "aws_cloudwatch_event_target" "bad_input" {
  rule      = aws_cloudwatch_event_rule.r.name
  arn       = aws_lambda_function.handler.arn
  input     = jsonencode({ a = 1 })                       # example
  input_transformer {                                     # WRONG — second input argument
    input_paths    = { id = "$.detail.id" }               # example
    input_template = "{\"id\": <id>}"                     # example
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_target.html.markdown

# CORRECT — exactly one
resource "aws_cloudwatch_event_target" "good_input" {
  rule  = aws_cloudwatch_event_rule.r.name
  arn   = aws_lambda_function.handler.arn
  input = jsonencode({ a = 1 })                           # example
}
```

## 3. FIFO or Other-Region DLQ

The DLQ must be a standard SQS queue (FIFO not supported) in the same Region as the rule.

```hcl
# WRONG
resource "aws_cloudwatch_event_target" "bad_dlq" {
  rule = aws_cloudwatch_event_rule.r.name
  arn  = aws_lambda_function.handler.arn
  dead_letter_config {
    arn = aws_sqs_queue.fifo_queue.arn                    # WRONG — FIFO queue (or a queue in another Region)
  }
}
# Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html

# CORRECT
resource "aws_cloudwatch_event_target" "good_dlq" {
  rule = aws_cloudwatch_event_rule.r.name
  arn  = aws_lambda_function.handler.arn
  dead_letter_config {
    arn = aws_sqs_queue.standard_same_region.arn          # standard queue, same Region
  }
}
```

## 4. Lambda or SNS Target with No Permission Path

The provider target page says to set permissions with `aws_lambda_permission` or
`aws_sns_topic_policy` to invoke a Lambda function or SNS topic. The AWS page says Lambda, SNS and SQS
accept either an IAM execution role or a resource-based policy, and that without an execution role
EventBridge uses resource-based policies on the target. So the target needs one of the two paths.

```hcl
# WRONG — Lambda target with no resource-based policy and no role_arn
resource "aws_cloudwatch_event_target" "bad_lambda" {
  rule = aws_cloudwatch_event_rule.r.name
  arn  = aws_lambda_function.handler.arn
}                                                          # WRONG — no permission path at all
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_target.html.markdown
# Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html

# CORRECT — resource-based policy path (minimal; the always-do rules-targets §4 pattern also sets source_arn
# with a (medium confidence) mapping). The alternative is role_arn with an execution role.
resource "aws_cloudwatch_event_target" "good_lambda" {
  rule = aws_cloudwatch_event_rule.r.name
  arn  = aws_lambda_function.handler.arn
}
resource "aws_lambda_permission" "events" {
  statement_id  = "AllowEventBridge"                      # example
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "events.amazonaws.com"
}
```

## 5. Missing role_arn on Targets That Require It

`role_arn` is required for `ecs_target` and for targets that are EC2 instances, Kinesis data
streams, Step Functions state machines, or an event bus in another account/Region.

```hcl
# WRONG — Step Functions target without a role
resource "aws_cloudwatch_event_target" "bad_sfn" {
  rule = aws_cloudwatch_event_rule.r.name
  arn  = aws_sfn_state_machine.flow.arn                   # WRONG — role_arn missing
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_target.html.markdown

# CORRECT
resource "aws_cloudwatch_event_target" "good_sfn" {
  rule     = aws_cloudwatch_event_rule.r.name
  arn      = aws_sfn_state_machine.flow.arn
  role_arn = aws_iam_role.events.arn
}
```
