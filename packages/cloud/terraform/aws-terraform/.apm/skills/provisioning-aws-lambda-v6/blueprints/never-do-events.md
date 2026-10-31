# Never-Do — Event Source Mappings and Event Invoke Config

hashicorp/aws 6.x · Terraform ~> 1.16 · Provider pages read 2026-10-23. Every `# example` value is a
placeholder. All HCL here is a fragment (references defined elsewhere).

Mapping page: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_event_source_mapping.html.markdown

## 1. Starting position on an SQS mapping

`starting_position` (`LATEST`, `TRIM_HORIZON`, `AT_TIMESTAMP`) is documented for Kinesis and must not be set for SQS.

```hcl
# WRONG — fragment
resource "aws_lambda_event_source_mapping" "bad" {
  function_name     = aws_lambda_function.orders.arn
  event_source_arn  = var.queue_arn # placeholder
  starting_position = "LATEST"      # WRONG — must not be set for SQS
}

# CORRECT — fragment
resource "aws_lambda_event_source_mapping" "good" {
  function_name    = aws_lambda_function.orders.arn
  event_source_arn = var.queue_arn # placeholder
}
```

## 2. Maximum concurrency below 2

`scaling_config.maximum_concurrency` must be ≥ 2 and applies to SQS only; values above 1000 need a quota
request. A computed value such as `min(var.reserved, 1000)` can fall below 2 (or equal -1), which
breaks the "must be ≥ 2" rule on the page.

```hcl
# WRONG — fragment
resource "aws_lambda_event_source_mapping" "bad" {
  function_name    = aws_lambda_function.orders.arn
  event_source_arn = var.queue_arn # placeholder
  scaling_config {
    maximum_concurrency = min(var.reserved_concurrent_executions, 1000) # WRONG — may be < 2
  }
}

# CORRECT — fragment
resource "aws_lambda_event_source_mapping" "good" {
  function_name    = aws_lambda_function.orders.arn
  event_source_arn = var.queue_arn # placeholder
  scaling_config {
    maximum_concurrency = 10 # example; >= 2
  }
}
```

## 3. Provisioned pollers on SQS or streams

`provisioned_poller_config` (`maximum_pollers` 1–2000, `minimum_pollers` 1–200) is "Only valid for Amazon
MSK or self-managed Apache Kafka sources." (mapping page, read 2026-10-23).

```hcl
# WRONG — fragment
resource "aws_lambda_event_source_mapping" "bad" {
  function_name    = aws_lambda_function.orders.arn
  event_source_arn = var.queue_arn # placeholder
  provisioned_poller_config {      # WRONG — not for SQS
    minimum_pollers = 1
    maximum_pollers = 5
  }
}

# CORRECT — for SQS, use scaling_config { maximum_concurrency } (>= 2) instead
```

## 4. Empty event invoke destination block

In `aws_lambda_function_event_invoke_config`, set at least one of `on_success` / `on_failure` inside
`destination_config`, otherwise remove the block; an empty block causes perpetual differences.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function_event_invoke_config.html.markdown

```hcl
# WRONG — fragment
resource "aws_lambda_function_event_invoke_config" "bad" {
  function_name = aws_lambda_function.orders.function_name
  destination_config {} # WRONG — perpetual differences
}

# CORRECT — fragment
resource "aws_lambda_function_event_invoke_config" "good" {
  function_name = aws_lambda_function.orders.function_name
  destination_config {
    on_failure {
      destination = var.failure_queue_arn # placeholder
    }
  }
}
```

## 5. Function timeout above the queue visibility timeout

For SQS sources the function timeout must not exceed the queue visibility timeout (CreateFunction fails
or duplicates occur on update).
Source: https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html

```hcl
# WRONG — fragment: queue visibility timeout is 60 s (example)
resource "aws_lambda_function" "bad" {
  function_name = "orders-fn" # example
  role          = aws_iam_role.lambda.arn
  timeout       = 300         # example — WRONG: exceeds the 60 s visibility timeout
}

# CORRECT — fragment
resource "aws_lambda_function" "good" {
  function_name = "orders-fn" # example
  role          = aws_iam_role.lambda.arn
  timeout       = 60          # example — not above the queue visibility timeout
}
```
