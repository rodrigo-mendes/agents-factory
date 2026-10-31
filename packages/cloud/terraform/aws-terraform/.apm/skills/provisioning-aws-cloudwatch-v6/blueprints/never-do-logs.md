# Never-Do — Log Group Anti-Patterns

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. DELIVERY Class Misuse

The `DELIVERY` class is **only for AWS Lambda logs going to S3 or Firehose**. Using it for
non-Lambda workloads (application logs, CloudTrail, VPC flow logs, etc.) is incorrect. AWS limits
the class definition to that single use case, and it forces 2-day retention ignoring any
`retention_in_days` value you set.

```hcl
# WRONG — DELIVERY class is not for general-purpose log groups
resource "aws_cloudwatch_log_group" "app" {
  name              = "/app/prod"
  log_group_class   = "DELIVERY"   # WRONG: not a Lambda S3/Firehose delivery group
  retention_in_days = 365           # ignored; forced to 2 on DELIVERY class
}

# CORRECT — use STANDARD for application logs
resource "aws_cloudwatch_log_group" "app" {
  name                        = "/app/prod"
  log_group_class             = "STANDARD"
  retention_in_days           = 365
  deletion_protection_enabled = false
}
```
Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Log_Classes.html

## 2. INFREQUENT_ACCESS with Filters

`INFREQUENT_ACCESS` log groups do **not** support metric filters, subscription filters, Live Tail,
anomaly detection, field indexing, EMF, or Container/Lambda Insights ingestion. Using these
features on an IA group will fail at the AWS API level.

```hcl
# WRONG — metric filters fail on INFREQUENT_ACCESS
resource "aws_cloudwatch_log_group" "app" {
  name            = "/app/prod"
  log_group_class = "INFREQUENT_ACCESS"
}

resource "aws_cloudwatch_log_metric_filter" "errors" {
  name           = "AppErrors"
  pattern        = "ERROR"
  log_group_name = aws_cloudwatch_log_group.app.name  # WILL FAIL at apply time
  metric_transformation {
    name      = "AppErrorCount"
    namespace = "App"
    value     = "1"
  }
}

# CORRECT — use STANDARD for groups that need filters
resource "aws_cloudwatch_log_group" "app" {
  name                        = "/app/prod"
  log_group_class             = "STANDARD"   # required for metric and subscription filters
  retention_in_days           = 365
  deletion_protection_enabled = false
}
```
Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Log_Classes.html

## 3. Log Group Class Is Immutable

AWS states: "After a log group is created, its log class can't be changed." The Terraform provider
page does not document whether changing `log_group_class` triggers ForceNew (medium confidence, M1).
Treat any `log_group_class` change as requiring destroy and recreate.

```hcl
# WRONG — attempting to change log_group_class in-place
# (behavior under plan is medium confidence; AWS API will reject it)
resource "aws_cloudwatch_log_group" "app" {
  name            = "/app/prod"
  log_group_class = "STANDARD"   # was INFREQUENT_ACCESS — change requires destroy/recreate
}

# CORRECT — rename the group or use a new name, then migrate
# If the group has critical data, export it first, then recreate with the target class.
```
Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Log_Classes.html
(M1) TF provider page is silent on ForceNew for log_group_class changes.

## 4. Omitting deletion_protection_enabled

Removing `deletion_protection_enabled` from the Terraform configuration is **not** the same as
disabling deletion protection. If the value was previously `true`, AWS rejects deletion with
`ValidationException: Disable deletion protection first`.

```hcl
# WRONG — omitting the argument when protection may be enabled
resource "aws_cloudwatch_log_group" "app" {
  name              = "/app/prod"
  retention_in_days = 365
  # deletion_protection_enabled omitted — if protection is on, terraform destroy will fail
}

# CORRECT — always set explicitly when the group must be destroyable
resource "aws_cloudwatch_log_group" "app" {
  name                        = "/app/prod"
  retention_in_days           = 365
  deletion_protection_enabled = false   # explicit false required; omission is not equivalent
}
```
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_group.html.markdown
Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/protecting-log-groups-from-deletion.html
