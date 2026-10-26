# Evaluation Scenarios — provisioning-aws-step-functions-v6

Five scenarios (canonical, edge, misuse rejection, anti-pattern trap, unverified handling).
Each uses `success_criteria: { must_pass, must_not }` for LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Standard State Machine With Logging, Tracing and Alias

```json
{
  "skills": ["provisioning-aws-step-functions-v6"],
  "query": "Write Terraform for a Standard Step Functions state machine that invokes a Lambda, logs to CloudWatch, has X-Ray tracing, publishes a version and has a live alias. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and aws version ~> 6.69",
      "Role trust principal is states.amazonaws.com with sts:AssumeRole",
      "log_destination ends with :*",
      "Logging policy includes logs:CreateLogStream on Resource \"*\"",
      "Sets tracing_configuration enabled = true and grants the X-Ray actions",
      "Sets publish = true and points aws_sfn_alias at state_machine_version_arn with weight 100",
      "Uses jsonencode() or templatefile() for definition",
      "Marks example values and marks HCL referencing external resources as a fragment"
    ],
    "must_not": [
      "Use an aws_sfn_state_machine_version resource",
      "Use a definition_substitutions argument",
      "Put delivery.logs.amazonaws.com in the role trust policy"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Customer Managed Key With Logging

```json
{
  "skills": ["provisioning-aws-step-functions-v6"],
  "query": "Encrypt the state machine with a customer managed KMS key and keep CloudWatch logging working. What goes in the key policy and the execution role?",
  "success_criteria": {
    "must_pass": [
      "Sets encryption_configuration type = CUSTOMER_MANAGED_KMS_KEY with kms_key_id",
      "Key policy allows delivery.logs.amazonaws.com only kms:Decrypt (AWS asks only kms:Decrypt for that principal)",
      "Execution role gets kms:Decrypt and kms:GenerateDataKey scoped by kms:EncryptionContext:aws:states:stateMachineArn",
      "Role gets kms:GenerateDataKey with kms:EncryptionContext:SourceArn for logging",
      "Refers key policy authoring to provisioning-aws-kms-v6"
    ],
    "must_not": [
      "Add kms:ViaService to the execution role",
      "Grant delivery.logs.amazonaws.com Encrypt or GenerateDataKey in the key policy"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Nonexistent Version Resource and Substitutions Argument

```json
{
  "skills": ["provisioning-aws-step-functions-v6"],
  "query": "Create two aws_sfn_state_machine_version resources and feed them to an alias, and use definition_substitutions for the Lambda ARN.",
  "success_criteria": {
    "must_pass": [
      "States that no provider page was found for an aws_sfn_state_machine_version resource (absence of evidence) and that versions come from publish = true or the aws_sfn_state_machine_versions data source",
      "States that definition_substitutions is not listed on the aws_sfn_state_machine page (absence of evidence) and offers templatefile() or jsonencode()",
      "Shows an alias using version ARNs from state_machine_version_arn or the data source"
    ],
    "must_not": [
      "Emit an aws_sfn_state_machine_version resource",
      "Emit definition_substitutions"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Express With .sync, Bad Log ARN, States.ALL First

```json
{
  "skills": ["provisioning-aws-step-functions-v6"],
  "query": "Review: an EXPRESS state machine with an ecs:runTask.sync task, log_destination set to the bare log group ARN, a Retry list whose first retrier has States.ALL together with Lambda.ServiceException, and an S3 backend with dynamodb_table. Is it correct?",
  "success_criteria": {
    "must_pass": [
      "Rejects .sync on Express; recommends Standard for Run a Job",
      "Rejects the log group ARN without :*; shows ARN followed by :*",
      "Rejects States.ALL mixed with other names in ErrorEquals or in a non-last retrier; puts it alone in the last retrier",
      "Rejects dynamodb_table as deprecated; shows use_lockfile = true"
    ],
    "must_not": [
      "Accept .sync under type EXPRESS",
      "Accept log_destination without :*",
      "Accept dynamodb_table without noting it is deprecated"
    ]
  }
}
```

---

## Scenario 5 — Unverified Handling: Versions on Update and Definition Diffs

```json
{
  "skills": ["provisioning-aws-step-functions-v6"],
  "query": "If I keep publish = true and change the definition, will Terraform publish a new version every time? Will reformatting the JSON cause a diff?",
  "success_criteria": {
    "must_pass": [
      "States the page documents publishing a version during creation and that publishing on each update is unverified",
      "States that perpetual diffs from definition formatting are unverified",
      "Suggests checking with terraform plan before relying on either behavior"
    ],
    "must_not": [
      "Assert that every update publishes a new version",
      "Assert that formatting changes never produce a diff"
    ]
  }
}
```
