# Evaluation Scenarios — provisioning-aws-sam-v6

Scenarios cover canonical, edge, misuse rejection and anti-pattern trap. Each uses
`success_criteria: { must_pass, must_not }` for LLM-as-judge scoring.

---

## Scenario 1 — Canonical: SAM CLI local testing of a Terraform project

```json
{
  "skills": ["provisioning-aws-sam-v6"],
  "query": "My Lambda functions and API Gateway are defined in Terraform (hashicorp/aws 6.x, Terraform 1.16). How do I test them locally with the SAM CLI?",
  "success_criteria": {
    "must_pass": [
      "States up front that SAM is not a hashicorp/aws resource and that Terraform still does plan and apply",
      "Uses --hook-name terraform with sam build, sam local invoke, sam local start-api or sam local start-lambda",
      "Mentions Docker for local testing",
      "If artifacts are built inside the Terraform project, adds one sam metadata null_resource per function or layer with a name starting sam_metadata_ and a resource_type of ZIP_LAMBDA_FUNCTION, IMAGE_LAMBDA_FUNCTION or LAMBDA_LAYER",
      "Mentions running terraform apply when a new resource is added",
      "If a terraform block is shown, it uses required_version ~> 1.16 and aws ~> 6.69"
    ],
    "must_not": [
      "Claim the SAM CLI deploys the Terraform project",
      "State a hard minimum Terraform version for the hook as fact",
      "Use dynamodb_table in the S3 backend"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: SAR stack with NoEcho parameters after upgrading

```json
{
  "skills": ["provisioning-aws-sam-v6"],
  "query": "I deploy a Serverless Application Repository app with aws_serverlessapplicationrepository_cloudformation_stack and a secret NoEcho parameter. I am upgrading the provider to 6.70.0. What should I watch for?",
  "success_criteria": {
    "must_pass": [
      "States that since 6.52.0 NoEcho values are stored in state in plaintext and the state backend must be secured",
      "Recommends wrapping the parameter in sensitive()",
      "States that existing resources may need a one-time manual state reconciliation after upgrading",
      "States that capabilities changed from Required to Optional/Computed in 6.52.0",
      "Cites the provider CHANGELOG for the 6.52.0 entries"
    ],
    "must_not": [
      "Claim CloudFormation hiding NoEcho values means state is masked",
      "Claim capabilities is mandatory for the SAR stack",
      "Describe the SAR stack as a nested stack as fact"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: sam deploy for a Terraform project

```json
{
  "skills": ["provisioning-aws-sam-v6"],
  "query": "Can I run sam deploy or sam sync --hook-name terraform to deploy my Terraform-defined Lambda functions?",
  "success_criteria": {
    "must_pass": [
      "Says the SAM CLI Terraform support covers sam build, sam local invoke, sam local start-api and sam local start-lambda",
      "States that the reference pages show no --hook-name option for sam deploy, sam sync or sam validate, without claiming they work with Terraform",
      "Directs provisioning to terraform plan and terraform apply"
    ],
    "must_not": [
      "Claim sam deploy, sam sync or sam validate work with --hook-name terraform",
      "Invent a Terraform option for those commands"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: SAM template through aws_cloudformation_stack

```json
{
  "skills": ["provisioning-aws-sam-v6"],
  "query": "Review: aws_cloudformation_stack with template_body of a 70 KB SAM template, capabilities = [\"CAPABILITY_IAM\"], on_failure = \"ROLLBACK\" and disable_rollback = true, provider pinned to 6.57.0.",
  "success_criteria": {
    "must_pass": [
      "Rejects on_failure together with disable_rollback because they conflict",
      "Rejects the inline template over 51,200 bytes and recommends template_url (up to 460,800 bytes)",
      "Rejects pinning 6.57.0 because it is withdrawn and recommends ~> 6.69",
      "Notes AWS says CAPABILITY_AUTO_EXPAND is required when a template using the AWS::Serverless transform is created without first reviewing the changes in a change set, and treats whether the provider reviews a change set as unverified",
      "States that CloudFormation, not Terraform, runs the transform"
    ],
    "must_not": [
      "Accept both on_failure and disable_rollback",
      "Accept template_body over 51,200 bytes",
      "Accept pinning 6.57.0",
      "Claim Terraform expands the SAM syntax"
    ]
  }
}
```

---

## Scenario 5 — Security Hub CloudFormation controls

```json
{
  "skills": ["provisioning-aws-sam-v6"],
  "query": "Which Security Hub CloudFormation controls apply to my aws_cloudformation_stack and can the resource satisfy them?",
  "success_criteria": {
    "must_pass": [
      "Lists CloudFormation.1 (retired April 2024, low severity), CloudFormation.2 (low severity), CloudFormation.3 (medium severity) and CloudFormation.4 (medium severity)",
      "Maps CloudFormation.4 to iam_role_arn and CloudFormation.2 to stack tags",
      "Says CloudFormation.3 may not be satisfiable from the resource alone because no termination-protection argument was found, tagged (medium confidence, absence of evidence)"
    ],
    "must_not": [
      "Target CloudFormation.1 as an active control",
      "State as fact that the resource has no way to enable termination protection"
    ]
  }
}
```
