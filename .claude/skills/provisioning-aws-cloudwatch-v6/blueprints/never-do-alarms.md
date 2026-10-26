# Never-Do — Alarm Anti-Patterns

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Child Alarm with Empty Actions

Security Hub CloudWatch.15 (High) evaluates **metric** alarms independently. A parent composite
alarm having `alarm_actions` does **not** satisfy CloudWatch.15 for its children. Silencing child
alarms and alerting only from the composite is a documented legacy pattern that fails this control.

```hcl
# WRONG — composite actions do not satisfy CloudWatch.15 for child alarms
resource "aws_cloudwatch_metric_alarm" "cpu" {
  alarm_name          = "cpu-high"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_actions       = []              # WRONG: CloudWatch.15 FAILED for this alarm
  actions_enabled     = true
}

resource "aws_cloudwatch_composite_alarm" "app" {
  alarm_name    = "app-health"
  alarm_rule    = trimspace("ALARM(${aws_cloudwatch_metric_alarm.cpu.alarm_name})")
  alarm_actions = [aws_sns_topic.alerts.arn]  # does NOT satisfy CloudWatch.15 for children
}

# CORRECT — each metric alarm must have its own alarm_actions
resource "aws_cloudwatch_metric_alarm" "cpu" {
  alarm_name          = "cpu-high"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_actions       = [aws_sns_topic.alerts.arn]  # CloudWatch.15: required on metric alarm
  actions_enabled     = true
}
```
Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html

## 2. Heredoc alarm_rule

The TF docs for `aws_cloudwatch_composite_alarm` state: `alarm_rule` must have **no leading or
trailing whitespace**. A heredoc (`<<-EOT … EOT`) keeps a trailing newline, which violates this
requirement.

```hcl
# WRONG — heredoc adds trailing newline
resource "aws_cloudwatch_composite_alarm" "app" {
  alarm_name = "app-health"
  alarm_rule = <<-EOT
    ALARM(cpu-high) OR ALARM(error-rate)
  EOT
  # The trailing newline from the heredoc violates the whitespace restriction
}

# CORRECT — use trimspace() or a one-line string
resource "aws_cloudwatch_composite_alarm" "app" {
  alarm_name = "app-health"
  alarm_rule = trimspace(
    "ALARM(${aws_cloudwatch_metric_alarm.cpu_high.alarm_name}) OR ALARM(${aws_cloudwatch_metric_alarm.error_rate.alarm_name})"
  )
}
```
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_composite_alarm.html.markdown

## 3. statistic and extended_statistic Together

The TF page includes a NOTE: `statistic` and `extended_statistic` cannot both be set on the same
alarm. Setting both causes a provider-level validation error.

```hcl
# WRONG — cannot set both statistic and extended_statistic
resource "aws_cloudwatch_metric_alarm" "p99_latency" {
  alarm_name          = "p99-latency"
  # ...
  statistic           = "Average"   # WRONG: conflicts with extended_statistic
  extended_statistic  = "p99"       # WRONG: cannot combine with statistic
}

# CORRECT — use one or the other
resource "aws_cloudwatch_metric_alarm" "p99_latency" {
  alarm_name         = "p99-latency"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 3
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = 60
  extended_statistic  = "p99"       # percentile: extended_statistic only; omit statistic
  threshold           = 500
  alarm_actions       = [aws_sns_topic.alerts.arn]
  actions_enabled     = true
}
```
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_metric_alarm.html.markdown

## 4. metric_query with Top-Level Metric Params

The TF page NOTE: when any `metric_query` block is present, do **not** set `metric_name`,
`namespace`, `period`, or `statistic` at the alarm level. Doing so causes a provider error.
Without `metric_query`, those four fields are required (or use `extended_statistic` in place of
`statistic`).

```hcl
# WRONG — top-level metric params conflict with metric_query
resource "aws_cloudwatch_metric_alarm" "error_rate" {
  alarm_name          = "error-rate"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 5
  metric_name         = "Errors"      # WRONG when metric_query blocks are present
  namespace           = "AWS/Lambda"  # WRONG
  period              = 60            # WRONG
  statistic           = "Sum"         # WRONG
  metric_query {
    id          = "e1"
    return_data = true
    expression  = "m1"
  }
}

# CORRECT — all metric params inside metric_query blocks
resource "aws_cloudwatch_metric_alarm" "error_rate" {
  alarm_name          = "error-rate"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 5
  # no top-level metric_name / namespace / period / statistic
  metric_query {
    id = "m1"
    metric {
      metric_name = "Errors"
      namespace   = "AWS/Lambda"
      period      = 60
      stat        = "Sum"
    }
  }
  metric_query {
    id          = "e1"
    return_data = true   # exactly one query must have return_data = true
    expression  = "m1"
  }
  alarm_actions = [aws_sns_topic.alerts.arn]
  actions_enabled = true
}
```
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_metric_alarm.html.markdown
