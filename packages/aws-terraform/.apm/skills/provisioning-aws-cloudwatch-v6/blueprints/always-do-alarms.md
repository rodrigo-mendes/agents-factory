# Always-Do — Alarms (Metric Alarm, Composite Alarm, CIS Filters)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 3. Metric Alarm with Required Actions

`alarm_actions` is required for Security Hub CloudWatch.15 (High). `actions_enabled = true` is
required for CloudWatch.17 (High). Both are evaluated on **metric** alarms independently — a parent
composite alarm does **not** satisfy these controls for its children.

```hcl
resource "aws_sns_topic" "alerts" {
  name = "prod-alerts"
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "cpu-high"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300               # 5 minutes; must be 10/20/30 or a multiple of 60
  statistic           = "Average"         # cannot combine with extended_statistic
  threshold           = 80
  treat_missing_data  = "missing"         # default; use "breaching" for continuous metrics
  actions_enabled     = true              # CloudWatch.17: keep true
  alarm_actions       = [aws_sns_topic.alerts.arn]  # CloudWatch.15: required
  ok_actions          = [aws_sns_topic.alerts.arn]
  tags = { Environment = "prod" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_metric_alarm.html.markdown
# Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html
```

## 4. Composite Alarm with trimspace()

Use `trimspace()` around `alarm_rule`. The TF docs require no leading or trailing whitespace; a
heredoc keeps a trailing newline that causes a silent validation error.

`actions_enabled` defaults to `true` but **changing it forces a new resource** on composite alarms.
Composite alarms cannot run EC2 or Auto Scaling actions; only SNS/investigation/OpsItems/incidents.

```hcl
resource "aws_cloudwatch_composite_alarm" "app_health" {
  alarm_name    = "app-health"
  # trimspace() strips the trailing newline that a heredoc would add
  alarm_rule    = trimspace(
    "ALARM(${aws_cloudwatch_metric_alarm.cpu_high.alarm_name}) OR ALARM(${aws_cloudwatch_metric_alarm.error_rate.alarm_name})"
  )
  actions_enabled = true  # changing this forces replace; set once and leave
  alarm_actions   = [aws_sns_topic.alerts.arn]
  # NOTE: child metric alarms also need alarm_actions for CloudWatch.15
  tags = { Environment = "prod" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_composite_alarm.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html
```

## 5. CIS Metric Filter and Alarm Pattern

CloudWatch.1–14 require a CIS metric filter on the CloudTrail log group plus an alarm and SNS
notification for each control. The pattern below shows the root-usage filter (CloudWatch.1) as a
template. Repeat for the other 13 controls (unauthorized API calls, console sign-in without MFA, etc.).

Use `treat_missing_data = "notBreaching"` for error-only metrics (fires only when the event occurs).

```hcl
resource "aws_cloudwatch_log_group" "cloudtrail" {
  name              = "/aws/cloudtrail/management"
  retention_in_days = 365
  deletion_protection_enabled = false
}

resource "aws_cloudwatch_log_metric_filter" "root_usage" {
  name           = "RootUsage"
  pattern        = "{ $.userIdentity.type = \"Root\" && $.userIdentity.invokedBy NOT EXISTS && $.eventType != \"AwsServiceEvent\" }"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name

  metric_transformation {
    name      = "RootUsageCount"
    namespace = "CISBenchmark"
    value     = "1"
    # do not combine default_value and dimensions — they conflict
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_metric_filter.html.markdown

resource "aws_cloudwatch_metric_alarm" "root_usage" {
  alarm_name          = "cis-root-usage"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "RootUsageCount"
  namespace           = "CISBenchmark"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"    # error-only metric: only fires on actual event
  actions_enabled     = true              # CloudWatch.17
  alarm_actions       = [aws_sns_topic.alerts.arn]  # CloudWatch.15
}
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html
# (U1) CIS benchmark version mapping per control was not extracted per individual control
