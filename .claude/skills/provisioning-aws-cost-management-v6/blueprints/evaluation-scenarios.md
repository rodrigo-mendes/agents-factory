# Evaluation Scenarios — provisioning-aws-cost-management-v6

Four scenarios (canonical, edge, misuse rejection, anti-pattern trap).
Each scenario uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Monthly Budget with SNS and Anomaly Detection

```json
{
  "skills": ["provisioning-aws-cost-management-v6"],
  "query": "Generate Terraform for a monthly cost budget with email and SNS notifications, plus a cost anomaly monitor and daily subscription. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Uses use_lockfile = true in the S3 backend; does not include dynamodb_table",
      "Does not set region on aws_budgets_budget, aws_ce_anomaly_monitor or aws_ce_anomaly_subscription",
      "Gives each budget notification subscriber_email_addresses or subscriber_sns_topic_arns",
      "Grants budgets.amazonaws.com SNS:Publish with aws:SourceAccount and aws:SourceArn conditions",
      "Sets monitor_dimension on a DIMENSIONAL anomaly monitor",
      "Marks example values (emails, names, amounts) as examples"
    ],
    "must_not": [
      "Set region on a Cost Management resource",
      "Use dynamodb_table in the S3 backend",
      "Grant budgets.amazonaws.com publish without source conditions"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: CUR and Data Exports Region Questions

```json
{
  "skills": ["provisioning-aws-cost-management-v6"],
  "query": "Which region do I configure for aws_cur_report_definition and aws_bcmdataexports_export, and what does s3_region mean?",
  "success_criteria": {
    "must_pass": [
      "Quotes that the CUR page says the service is only available in us-east-1 currently",
      "Labels configuring the provider for us-east-1 as an inference (medium confidence) and asks before applying it",
      "States the Data Exports page states no region requirement and us-east-1 appears only in the AWS bucket-policy ARN (medium confidence)",
      "States s3_region is the bucket region, not a resource region",
      "States there is no resource-level region argument; s3_region and ssm_action_definition.region are not the resource region"
    ],
    "must_not": [
      "Set region on aws_cur_report_definition or aws_bcmdataexports_export",
      "State as fact that Data Exports requires a us-east-1 provider"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Cancelling a Savings Plan with Destroy

```json
{
  "skills": ["provisioning-aws-cost-management-v6"],
  "query": "I bought a Savings Plan with Terraform by mistake. Can I just run terraform destroy to cancel it? Which resource name do I use?",
  "success_criteria": {
    "must_pass": [
      "States an active plan cannot be cancelled or deleted; only queued plans can be deleted",
      "States destroying an active plan only removes it from state",
      "Uses the resource name aws_savingsplans_savings_plan",
      "Notes provider support is best effort (6.62.0 note)",
      "Recommends confirming commitment and offering ID before apply"
    ],
    "must_not": [
      "Claim terraform destroy cancels an active Savings Plan",
      "Use the resource name savingsplans_plan"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Legacy Claims and Removed Requirements

```json
{
  "skills": ["provisioning-aws-cost-management-v6"],
  "query": "Review this: aws_cur_report_definition without s3_prefix, aws_budgets_budget with both cost_filter and filter_expression, a filter_expression and block with one operand, and 'budgets cost $0.01/day each, 5 emails and 10 SNS topics per alert'. Is this right for aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Rejects the missing s3_prefix as required since 6.0 and cites the upgrade guide",
      "Rejects mixing cost_filter with filter_expression as a documented conflict",
      "Rejects a single-operand and block: and/or require at least 2 operands",
      "Corrects pricing: monitoring and notifications free; $0.10/day per action-enabled budget after the first two (AWS pricing page)",
      "Corrects limits: up to 10 email addresses and one SNS topic per alert (AWS best-practices page)"
    ],
    "must_not": [
      "Accept a CUR definition without s3_prefix for 6.x",
      "Accept cost_filter together with filter_expression",
      "Repeat the $0.01/day or 5 emails and 10 topics figures"
    ]
  }
}
```
