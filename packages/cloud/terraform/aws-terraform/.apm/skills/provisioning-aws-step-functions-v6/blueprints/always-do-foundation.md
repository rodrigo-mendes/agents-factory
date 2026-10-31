# Always-Do — Foundation (Terraform Block, Execution Role)

hashicorp/aws 6.x · Terraform ~> 1.16 · Pages read 2026-10-23.

Scaffolding note (unverified): JSON policy structure (`Version`, `Effect`, condition operators,
`Resource` forms) and the IAM resource types are not quoted on the pages cited below. The service
principals, action names and condition keys are the cited facts. IAM role authoring itself belongs to
`provisioning-aws-iam-v6`.

## 1. Terraform Block and S3 Backend

Root modules use `~>` for providers; reusable modules set only a minimum
(https://developer.hashicorp.com/terraform/language/expressions/version-constraints).
Use `use_lockfile = true`; `dynamodb_table` is deprecated
(https://developer.hashicorp.com/terraform/language/backend/s3).

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69" # root module; a reusable module sets only a minimum such as ">= 6.0"
    }
  }
  backend "s3" {
    bucket       = "my-tf-state"                   # example
    key          = "step-functions/terraform.tfstate" # example
    region       = "eu-west-1"                     # example
    use_lockfile = true
  }
}
```

Commit `.terraform.lock.hcl`; `terraform init -upgrade` moves provider versions
(https://developer.hashicorp.com/terraform/language/files/dependency-lock).

## 2. IAM Execution Role

Trust principal is `states.amazonaws.com` with `sts:AssumeRole`; AWS recommends the confused-deputy
conditions `aws:SourceArn` and `aws:SourceAccount`
(https://docs.aws.amazon.com/step-functions/latest/dg/procedure-create-iam-role.html).
IAM resources are global and take no `region` argument
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown).

```hcl
locals {
  region     = "eu-west-1"    # example
  account_id = "123456789012" # example
}

resource "aws_iam_role" "sfn" {
  name = "order-workflow-sfn" # example
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "states.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = local.account_id }
        ArnLike      = { "aws:SourceArn" = "arn:aws:states:${local.region}:${local.account_id}:stateMachine:*" }
      }
    }]
  })
}
```

Logging actions, on `Resource = "*"` because they do not support resource scoping
(https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html):

```hcl
# Fragment: attaches to aws_iam_role.sfn above.
resource "aws_iam_role_policy" "sfn_logging" {
  name = "logging" # example
  role = aws_iam_role.sfn.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogDelivery", "logs:CreateLogStream", "logs:GetLogDelivery",
        "logs:UpdateLogDelivery", "logs:DeleteLogDelivery", "logs:ListLogDeliveries",
        "logs:PutLogEvents", "logs:PutResourcePolicy", "logs:DescribeResourcePolicies",
        "logs:DescribeLogGroups"
      ]
      Resource = "*"
    }]
  })
}
```

X-Ray actions, also on `*`; no X-Ray for Distributed Map child executions
(https://docs.aws.amazon.com/step-functions/latest/dg/concepts-xray-tracing.html):

```hcl
# Fragment: attaches to aws_iam_role.sfn above.
resource "aws_iam_role_policy" "sfn_xray" {
  name = "xray" # example
  role = aws_iam_role.sfn.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["xray:PutTraceSegments", "xray:PutTelemetryRecords", "xray:GetSamplingRules", "xray:GetSamplingTargets"]
      Resource = "*"
    }]
  })
}
```

Grant each integrated service (Lambda, SQS, SNS, DynamoDB) the specific action on the specific ARN
(https://docs.aws.amazon.com/step-functions/latest/dg/connect-lambda.html and
https://docs.aws.amazon.com/step-functions/latest/dg/procedure-create-iam-role.html).
`.sync` integrations need additional events/describe permissions
(https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html).
