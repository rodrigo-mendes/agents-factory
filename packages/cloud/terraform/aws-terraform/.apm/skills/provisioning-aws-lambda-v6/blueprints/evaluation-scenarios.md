# Evaluation Scenarios — provisioning-aws-lambda-v6

Five scenarios (canonical, edge, misuse rejection, anti-pattern trap x2). Each uses
`success_criteria: { must_pass, must_not }` for LLM-as-judge scoring.

---

## Scenario 1 — Canonical: SQS-triggered function

```json
{
  "skills": ["provisioning-aws-lambda-v6"],
  "query": "Generate Terraform for a Zip Lambda function triggered by an SQS queue, with an execution role, a managed log group, JSON logging and partial batch responses. hashicorp/aws 6.x, Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and aws version ~> 6.69",
      "Uses exactly one code source and sets handler and runtime for the Zip package",
      "Trust policy allows lambda.amazonaws.com sts:AssumeRole; role allows logs:CreateLogGroup, CreateLogStream, PutLogEvents",
      "Manages /aws/lambda/<function_name> with aws_cloudwatch_log_group and sets logging_config with log_format",
      "Sets function_response_types = [\"ReportBatchItemFailures\"] on the event source mapping",
      "Does not set starting_position on the SQS mapping",
      "Marks example values (names, memory, timeout) as examples"
    ],
    "must_not": [
      "Set filename together with image_uri or s3_bucket",
      "Set scaling_config.maximum_concurrency below 2",
      "Cite registry.terraform.io pages as sources"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Function URL with authorization NONE

```json
{
  "skills": ["provisioning-aws-lambda-v6"],
  "query": "I want a public Lambda function URL with authorization_type NONE and I will destroy it later. What should I know in aws provider 6.x?",
  "success_criteria": {
    "must_pass": [
      "States authorization_type is required and accepts AWS_IAM or NONE",
      "States that with NONE the provider adds lambda:InvokeFunctionUrl and lambda:InvokeFunction permissions at create",
      "States those policies are not removed from AWS when the URL resource is destroyed",
      "Asks the user to confirm public exposure before using NONE",
      "Mentions Security Hub Lambda.1 (public access) as a related control"
    ],
    "must_not": [
      "Claim destroying the function URL removes the permissions the provider added",
      "Choose NONE without asking"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: computed maximum_concurrency

```json
{
  "skills": ["provisioning-aws-lambda-v6"],
  "query": "Set scaling_config maximum_concurrency = min(var.reserved_concurrent_executions, 1000) on my SQS event source mapping, with reserved_concurrent_executions defaulting to -1.",
  "success_criteria": {
    "must_pass": [
      "Rejects the expression: maximum_concurrency must be >= 2 and the computed value can be below 2 or -1",
      "States maximum_concurrency applies to SQS only and values above 1000 need a quota request",
      "Offers a fixed or validated value of at least 2"
    ],
    "must_not": [
      "Accept min(reserved, 1000) as valid",
      "Apply scaling_config.maximum_concurrency to Kinesis or DynamoDB sources"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: stale runtime claims

```json
{
  "skills": ["provisioning-aws-lambda-v6"],
  "query": "Our standards say: allow runtimes dotnet8 and others as a permanent list, and java11 is approaching EOL so ban it. Encode that in a Terraform variable validation.",
  "success_criteria": {
    "must_pass": [
      "Notes runtime support is time-sensitive and points to the Lambda runtimes page with the date read (2026-10-23)",
      "States dotnet8 deprecates on 2026-11-10 and is not a safe allow-list value",
      "States java11 stays supported until 2027-06-30 and java11.al2023 is listed as supported to 2029, so it is not approaching EOL",
      "Does not hard-code a runtime allow-list as a fixed rule; asks the user how the list is maintained"
    ],
    "must_not": [
      "Include dotnet8 in a permanent allow-list",
      "Call java11 approaching EOL",
      "Present python3.10 as long-term safe (deprecates 2026-10-31)"
    ]
  }
}
```

---

## Scenario 5 — Anti-Pattern Trap: VPC function and role cleanup

```json
{
  "skills": ["provisioning-aws-lambda-v6"],
  "query": "Attach my Lambda to private subnets and remove the old execution role and its VPC policy in the same change.",
  "success_criteria": {
    "must_pass": [
      "States deleting the execution role before the ENI is deleted prevents cleanup",
      "States removing VPC config can take up to 20 minutes to delete the ENI",
      "Does not delete the role in the same change as the VPC removal, and waits for the ENI to be gone",
      "Keeps the role and VPC policy attachment until the function is destroyed",
      "Asks which subnets to use and notes Security Hub Lambda.5 expects at least 2 AZs for VPC functions"
    ],
    "must_not": [
      "Delete the role in the same change as the VPC removal",
      "Claim the ENI is deleted immediately when vpc_config is removed"
    ]
  }
}
```
