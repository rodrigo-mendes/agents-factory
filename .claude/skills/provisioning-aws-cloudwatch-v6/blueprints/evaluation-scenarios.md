# Evaluation Scenarios — provisioning-aws-cloudwatch-v6

Four scenarios required for a hybrid knowledge skill (canonical, edge, misuse rejection, anti-pattern trap).
Each scenario uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Log Group with Metric Alarm and CIS Pattern

```json
{
  "skills": ["provisioning-aws-cloudwatch-v6"],
  "query": "Generate Terraform for a CloudWatch log group that retains logs for 365 days, a metric filter for root account usage matching the CIS benchmark, and a metric alarm with SNS notification. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69 (or >= 6.0)",
      "Uses use_lockfile = true in the S3 backend; does not include dynamodb_table",
      "Sets retention_in_days = 365 on aws_cloudwatch_log_group",
      "Sets deletion_protection_enabled = false explicitly (not just omitted)",
      "Sets alarm_actions on aws_cloudwatch_metric_alarm to an SNS topic ARN",
      "Sets actions_enabled = true on the metric alarm",
      "Sets treat_missing_data = \"notBreaching\" (or acknowledges it is appropriate for error-only metrics)",
      "Does not set both statistic and extended_statistic on the same alarm",
      "Does not set default_value and dimensions together in metric_transformation"
    ],
    "must_not": [
      "Use dynamodb_table in the S3 backend",
      "Omit retention_in_days on the log group",
      "Leave alarm_actions empty on the metric alarm",
      "Set both statistic and extended_statistic on one alarm",
      "State that the default log group encryption uses a KMS CMK (default is server-side AES-256-GCM)"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Composite Alarm Dependency and Lifecycle

```json
{
  "skills": ["provisioning-aws-cloudwatch-v6"],
  "query": "I have a composite alarm that references two child metric alarms. I need to rename one of the child alarms. What are the Terraform lifecycle considerations and how should I write the alarm_rule?",
  "success_criteria": {
    "must_pass": [
      "States that destroying a child alarm while a composite depends on it will fail",
      "Recommends a two-stage update (update the composite rule first, then destroy the old child) or depends_on",
      "States that alarm_rule must have no leading or trailing whitespace",
      "Shows or recommends trimspace() to wrap the alarm_rule expression",
      "States that changing actions_enabled on a composite alarm forces a new resource"
    ],
    "must_not": [
      "Recommend using a heredoc for alarm_rule without wrapping it in trimspace()",
      "Claim that destroying and recreating a child alarm is safe without updating the composite first",
      "Claim that actions_enabled can be toggled without forcing replacement on composite alarms"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: INFREQUENT_ACCESS with Metric Filter

```json
{
  "skills": ["provisioning-aws-cloudwatch-v6"],
  "query": "Can I use log_group_class = \"INFREQUENT_ACCESS\" on a log group that has a CloudWatch metric filter? It would reduce ingestion costs.",
  "success_criteria": {
    "must_pass": [
      "Explicitly rejects INFREQUENT_ACCESS for log groups that need metric filters",
      "States that metric filters are not supported on INFREQUENT_ACCESS log groups",
      "States that subscription filters are also unsupported on INFREQUENT_ACCESS",
      "Recommends STANDARD class for log groups that require any filter type",
      "Notes that AWS does not allow changing log_group_class after creation, so a class change must be treated as destroy and recreate"
    ],
    "must_not": [
      "Permit INFREQUENT_ACCESS with metric filters",
      "Claim that only subscription filters are unsupported on INFREQUENT_ACCESS (metric filters are also excluded)",
      "Suggest changing log_group_class in-place without noting the immutability constraint"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Composite Covers CloudWatch.15 and Heredoc alarm_rule

```json
{
  "skills": ["provisioning-aws-cloudwatch-v6"],
  "query": "Review this Terraform: aws_cloudwatch_metric_alarm with alarm_actions = [], a composite alarm referencing it with alarm_actions = [sns_arn], and alarm_rule set with a heredoc. Is this correct for Security Hub compliance?",
  "success_criteria": {
    "must_pass": [
      "Rejects alarm_actions = [] on the metric alarm; states CloudWatch.15 evaluates metric alarms independently of composite alarms",
      "States that the composite alarm's alarm_actions do not satisfy CloudWatch.15 for its children",
      "Rejects the heredoc alarm_rule because it keeps a trailing newline that violates the no-whitespace requirement",
      "Provides trimspace() or a one-line string as the correct alternative for alarm_rule",
      "Provides alarm_actions = [sns_arn] on the metric alarm as the correct fix for CloudWatch.15"
    ],
    "must_not": [
      "Accept alarm_actions = [] on the child metric alarm as compliant with CloudWatch.15",
      "Accept the heredoc alarm_rule without noting the trailing whitespace issue",
      "Claim that a composite alarm's actions satisfy CloudWatch.15 for its child metric alarms"
    ]
  }
}
```
