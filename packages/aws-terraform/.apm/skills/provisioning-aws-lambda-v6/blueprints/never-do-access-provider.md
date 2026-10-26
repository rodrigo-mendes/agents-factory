# Never-Do — Execution Role Lifetime, Permissions, Withdrawn Provider Version

hashicorp/aws 6.x · Terraform ~> 1.16 · Pages read 2026-10-23.
Every `# example` value is a placeholder. All HCL here is a fragment (references defined elsewhere).

## 1. Deleting the execution role before VPC cleanup

Removing the VPC configuration can take up to 20 minutes to delete the ENI, and deleting the execution
role before the ENI is deleted prevents cleanup. Keep the role and its VPC policy attachment until the
function is destroyed.
Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html

```hcl
# WRONG — fragment: role and attachment removed from code while the function still has vpc_config
# (resource "aws_iam_role" "lambda" and its VPC policy attachment deleted from the configuration)

# CORRECT — fragment: function references the role, so the role is destroyed after the function
resource "aws_lambda_function" "private" {
  function_name = "orders-private-fn" # example
  role          = aws_iam_role.lambda.arn
  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_sg_id]
  }
  depends_on = [aws_iam_role_policy.vpc_access] # placeholder: your VPC policy attachment
}
```

## 2. S3-principal permission without source account

Security Hub Lambda.1 ("Function policies should prohibit public access", critical severity) fails without
`AWS:SourceAccount` for S3-principal permissions. The permission page lists S3 among the uses of
`source_account`; how the argument maps to that condition is (medium confidence).
Sources: https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html ,
https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_permission.html.markdown

```hcl
# WRONG — fragment
resource "aws_lambda_permission" "bad" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.orders.function_name
  principal     = "s3.amazonaws.com" # WRONG — no source_account (Lambda.1 fails)
  source_arn    = var.bucket_arn     # placeholder
}

# CORRECT — fragment
resource "aws_lambda_permission" "good" {
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.orders.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = var.bucket_arn        # placeholder
  source_account = var.bucket_account_id # placeholder
}
```

## 3. Pinning provider 6.57.0

aws 6.57.0 was withdrawn from GitHub and the Registry.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md (read 2026-10-23)

```hcl
# WRONG
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "6.57.0" } # WRONG — withdrawn
  }
}

# CORRECT
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```
