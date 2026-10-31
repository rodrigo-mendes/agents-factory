# Evaluation Scenarios — provisioning-aws-eventbridge-v6

Four scenarios (canonical, edge, misuse rejection, anti-pattern trap). Each uses
`success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Custom Bus, Rule, Lambda Target with DLQ

```json
{
  "skills": ["provisioning-aws-eventbridge-v6"],
  "query": "Generate Terraform for a custom EventBridge bus, a rule matching order events, and a Lambda target with a retry policy and a DLQ. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Uses use_lockfile = true in the S3 backend; no dynamodb_table",
      "Uses aws_cloudwatch_event_* resources and sets event_bus_name on the rule and the target to the custom bus",
      "Sets state (not is_enabled) on the rule",
      "Filters event_pattern on source and detail-type",
      "Uses a standard SQS queue in the same Region as the DLQ and notes the queue policy must be granted manually",
      "Gives the Lambda target a permission path: aws_lambda_permission with principal events.amazonaws.com, or role_arn with an execution role",
      "Marks example values (names, ARNs, numbers) as examples and marks referenced-elsewhere resources as a fragment"
    ],
    "must_not": [
      "Use is_enabled",
      "Use a FIFO queue as the DLQ",
      "Leave the Lambda target with no permission path (no resource-based policy and no role_arn)",
      "Set role_arn on a CloudWatch Logs target"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Scheduling a Job

```json
{
  "skills": ["provisioning-aws-eventbridge-v6"],
  "query": "I need a nightly job at 02:00 Madrid time. Should I use an EventBridge rule with a cron expression or something else?",
  "success_criteria": {
    "must_pass": [
      "States that AWS calls scheduled rules a legacy feature and recommends EventBridge Scheduler",
      "Uses aws_scheduler_schedule with flexible_time_window, schedule_expression, schedule_expression_timezone and a target with role_arn",
      "States that scheduled rules use UTC+0 only and work only on the default bus",
      "Asks the user to choose between Scheduler and a scheduled rule, or recommends Scheduler"
    ],
    "must_not": [
      "Put schedule_expression on a rule attached to a custom bus",
      "Omit role_arn in the Scheduler target block",
      "Claim scheduled rules are removed from AWS"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Policy and Permission on One Bus

```json
{
  "skills": ["provisioning-aws-eventbridge-v6"],
  "query": "Can I manage cross-account access to one bus with both aws_cloudwatch_event_bus_policy and aws_cloudwatch_event_permission?",
  "success_criteria": {
    "must_pass": [
      "Rejects using both resources on the same bus",
      "States the policy resource is incompatible with the permission resource and will overwrite permissions",
      "Recommends picking one resource per bus",
      "Asks which accounts or organization need access if the request is under-specified"
    ],
    "must_not": [
      "Silently permit both resources on one bus",
      "State that principal = \"*\" is fine without a condition"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Deprecated, Required and Mutually Exclusive Arguments

```json
{
  "skills": ["provisioning-aws-eventbridge-v6"],
  "query": "Review this Terraform: a rule with is_enabled = true, a target with both input and input_transformer, a DLQ pointing at a FIFO queue, and an S3 backend with dynamodb_table. Is this correct for aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Flags is_enabled as deprecated (not removed) and replaces it with state",
      "Rejects combining input and input_transformer because input, input_path and input_transformer are mutually exclusive",
      "Rejects the FIFO queue as DLQ and recommends a standard SQS queue in the same Region",
      "Rejects dynamodb_table as deprecated and provides use_lockfile = true",
      "Does not state that is_enabled was removed"
    ],
    "must_not": [
      "Accept is_enabled without noting the deprecation",
      "Accept the FIFO DLQ",
      "Accept dynamodb_table without noting its deprecated status"
    ]
  }
}
```
