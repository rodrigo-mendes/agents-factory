# Always-Do — Security (Subscription Filter, Data Protection, Terraform Test)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 6. Subscription Filter with Recursion Guard

Never subscribe a log group that is part of its own delivery workflow — Lambda, Step Functions,
Fargate, VPC flow logs. Doing so creates a feedback loop where log events trigger more events.
For account-level policies, exclude delivery groups with `selection_criteria`.

For Kinesis destinations: provide `role_arn`. For Lambda: omit `role_arn` and use
`aws_lambda_permission`. For Firehose: AWS supports it, but the TF page names only Kinesis/Lambda
(M2); infer the same `role_arn` requirement as Kinesis.

Use `aws:SourceArn` (preferred) and `aws:SourceAccount` in the Kinesis/Firehose trust policy to
mitigate the confused-deputy problem.

```hcl
resource "aws_cloudwatch_log_subscription_filter" "to_kinesis" {
  name            = "app-logs-to-kinesis"
  log_group_name  = aws_cloudwatch_log_group.app.name
  # Do NOT subscribe: /aws/lambda/*, Step Functions, VPC flow log groups (recursion risk)
  filter_pattern  = ""    # empty string matches all events
  destination_arn = aws_kinesis_stream.log_sink.arn
  role_arn        = aws_iam_role.cw_to_kinesis.arn   # required for Kinesis
  distribution    = "ByLogStream"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_subscription_filter.html.markdown
# Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions-recursion-prevention.html

# IAM role — confused-deputy mitigation
resource "aws_iam_role" "cw_to_kinesis" {
  name = "cloudwatch-to-kinesis"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "logs.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        # aws:SourceArn (preferred): full log-group ARN scope
        ArnEquals    = { "aws:SourceArn" = "arn:aws:logs:${var.region}:${var.account_id}:log-group:${aws_cloudwatch_log_group.app.name}:*" }
        StringEquals = { "aws:SourceAccount" = var.account_id }
      }
    }]
  })
}
# Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions-confused-deputy.html
```

## 7. Data Protection Policy

One policy per log group. `Version` must be exactly `"2021-06-01"`. Each statement needs either
`Audit` (with `FindingsDestination`) or `Deidentify` (`MaskConfig {}`).

Data ingested **before** the policy is created is **not masked**. Only principals with
`logs:Unmask` can see raw data at any egress point (Logs Insights, metric filters, subscription
filters).

```hcl
resource "aws_cloudwatch_log_data_protection_policy" "pii" {
  log_group_name = aws_cloudwatch_log_group.app.name
  policy_document = jsonencode({
    Name    = "pii-protection"
    Version = "2021-06-01"
    Statement = [
      {
        Sid            = "audit-pii"
        DataIdentifier = ["arn:aws:dataprotection::aws:data-identifier/EmailAddress"]
        Operation      = {
          Audit = {
            FindingsDestination = {
              CloudWatchLogs = { LogGroup = "/security/data-protection-findings" }
            }
          }
        }
      },
      {
        Sid            = "mask-pii"
        DataIdentifier = ["arn:aws:dataprotection::aws:data-identifier/EmailAddress"]
        Operation      = { Deidentify = { MaskConfig = {} } }
      }
    ]
  })
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_data_protection_policy.html.markdown
# Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html
```

## 8. Terraform Test and CI

Use `mock_provider "aws"` with `command = plan` for CI-safe unit tests (no real AWS calls).

```hcl
# tests/cloudwatch.tftest.hcl
mock_provider "aws" {}

run "log_group_has_retention" {
  command = plan
  assert {
    condition     = aws_cloudwatch_log_group.app.retention_in_days > 0
    error_message = "retention_in_days must be set and non-zero"
  }
}

run "alarm_has_actions" {
  command = plan
  assert {
    condition     = length(aws_cloudwatch_metric_alarm.cpu_high.alarm_actions) > 0
    error_message = "alarm_actions required for CloudWatch.15"
  }
}
```

CI pipeline commands:
```bash
terraform init -backend=false
terraform validate -json
terraform plan -detailed-exitcode -input=false -out=tfplan
# exit 0: no changes; exit 1: error; exit 2: changes present
terraform test -filter=tests/cloudwatch.tftest.hcl
```
# Source: https://developer.hashicorp.com/terraform/language/tests
# Source: https://developer.hashicorp.com/terraform/cli/commands/plan
