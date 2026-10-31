# Always-Do — Provider Constraint, Execution Role, Function, Log Group

hashicorp/aws 6.x · Terraform ~> 1.16 · Provider and family pages read 2026-10-23.
Every `# example` value is a placeholder to replace.

## 1. Terraform block and provider constraint

Root modules use `~>` for providers (https://developer.hashicorp.com/terraform/language/expressions/version-constraints).
Lambda is regional: every Lambda resource accepts an optional `region`; changing it forces replacement
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown).

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }
}
# Source: https://releases.hashicorp.com/terraform-provider-aws/ (latest 6.70.0, read 2026-10-23)
```

## 2. Execution role

Fragment — shows only the Lambda-specific parts; the rest of IAM belongs to `provisioning-aws-iam-v6`.
The `aws_iam_role` / `aws_iam_role_policy` argument shapes below are standard IAM scaffolding not read from an
IAM page (unverified); the policy documents omit the `Version` element, so add `Version = "2012-10-17"`
(unverified, standard IAM scaffolding) when you complete them. For SQS consume permissions use
`provisioning-aws-sqs-v6`; do not guess actions here.
The trust policy must allow `lambda.amazonaws.com` to call `sts:AssumeRole`; logging needs
`logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`. The default log group is
`/aws/lambda/<function-name>`.
Source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html

```hcl
# fragment
resource "aws_iam_role" "lambda" {
  name = "orders-fn-role" # example
  assume_role_policy = jsonencode({
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "logs" {
  name = "logs" # example
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
      Resource = "<log-resource-arn-pattern>" # placeholder
    }]
  })
}
```

Trim permissions before production; IAM Access Analyzer can generate a policy from activity
(https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html).

## 3. Zip function with managed log group

Required: `function_name`, `role`, and exactly one code source (`filename`, `s3_bucket` + `s3_key`, or
`image_uri`). `handler` and `runtime` are required when `package_type = "Zip"`. `architectures` accepts
`x86_64` (default) or `arm64`; `memory_size` 128–32768 MB (default 128); `timeout` 1–900 s (default 3).
`logging_config` requires `log_format` (`Text` or `JSON`).
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown

The examples on that page create the log group named `/aws/lambda/<function_name>` and add `depends_on`
to the function; the page does not state it is mandatory (medium confidence).

```hcl
# fragment — references aws_iam_role.lambda from §2
resource "aws_cloudwatch_log_group" "orders" {
  name              = "/aws/lambda/orders-fn" # example
  retention_in_days = 14                      # example
}

resource "aws_lambda_function" "orders" {
  function_name = "orders-fn"           # example
  role          = aws_iam_role.lambda.arn
  filename      = "build/orders.zip"    # example
  package_type  = "Zip"                 # default
  handler       = "app.handler"         # example
  runtime       = "python3.14"          # example; runtime support is time-sensitive
  architectures = ["arm64"]
  publish       = true                  # default false; `version` and `qualified_arn` reflect the published version
  memory_size   = 256                   # example
  timeout       = 30                    # example

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"      # example
    system_log_level      = "INFO"      # example
    log_group             = aws_cloudwatch_log_group.orders.name # the page's example passes the group name
  }

  depends_on = [aws_cloudwatch_log_group.orders]
}
```

`source_code_hash` is a provider-only synthetic value; `code_sha256` (Base64 SHA-256 of the zip, or the
image digest) reflects out-of-band changes. Tags set on the function override provider `default_tags` on
key match. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown
