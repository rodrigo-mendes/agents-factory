# Always-Do — Roles, Policies, and Exclusive Management

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Terraform Block and S3 Backend

Use `use_lockfile = true` for S3-native locking. `dynamodb_table` is deprecated (will be removed).
Root modules pin `~> 6.69`; reusable modules use `>= 6.0`.

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }
  backend "s3" {
    bucket       = "my-tf-state"
    key          = "iam/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true   # S3-native lock; dynamodb_table is deprecated
    encrypt      = true
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
```

Commit `.terraform.lock.hcl`. For cross-platform CI hashes:
```
terraform providers lock -platform=linux_amd64 -platform=darwin_arm64
```
Source: https://developer.hashicorp.com/terraform/language/files/dependency-lock

## 2. Policy Document Patterns

Both `jsonencode()` and `data.aws_iam_policy_document` are first-class choices — official resource
pages present them as equal options. Neither is recommended over the other.

```hcl
# Option A: jsonencode()
resource "aws_iam_role" "lambda_exec" {
  name = "lambda-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role.html.markdown

# Option B: data.aws_iam_policy_document
# Use &{aws:username} for AWS policy variables, NOT ${...} (Terraform would interpolate it)
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec_b" {
  name               = "lambda-exec-b"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/iam_policy_document.html.markdown

# Scoped least-privilege policy (IAM.1: no Action * on Resource *)
resource "aws_iam_policy" "s3_read" {
  name   = "s3-read-only"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:ListBucket"]
      Resource = [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*",
      ]
    }]
  })
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_policy.html.markdown
```

Note: `aws_iam_policy.description` **forces new** — choose it carefully.

## 3. Inline Policies with Exclusive Management

`inline_policy` on `aws_iam_role` is **deprecated since 5.68.0** (not new in 6.x, not removed).
Use `aws_iam_role_policy` plus `aws_iam_role_policies_exclusive` for Terraform-exclusive control.

**WARNING:** include every co-managed `aws_iam_role_policy` name in `policy_names`, or it will be
removed on apply. Anything not listed is purged.

```hcl
resource "aws_iam_role" "app" {
  name               = "app-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  # Do NOT use inline_policy or managed_policy_arns (both deprecated)
}

resource "aws_iam_role_policy" "app_s3" {
  name   = "app-s3-inline"
  role   = aws_iam_role.app.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject"]
      Resource = "arn:aws:s3:::my-bucket/*"
    }]
  })
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policy.html.markdown

# Enforce exclusive inline policy management — removes any inline policy not listed
resource "aws_iam_role_policies_exclusive" "app" {
  role_name    = aws_iam_role.app.name
  policy_names = [aws_iam_role_policy.app_s3.name]  # include ALL co-managed names
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policies_exclusive.html.markdown
```

## 4. Managed Policy Attachments with Exclusive Management

`managed_policy_arns` on `aws_iam_role` is **deprecated since 5.72.0** (not new in 6.x, not removed).
Use `aws_iam_role_policy_attachment` plus `aws_iam_role_policy_attachments_exclusive`. Never mix with `aws_iam_policy_attachment` on the same role.

```hcl
resource "aws_iam_role_policy_attachment" "app_managed" {
  role       = aws_iam_role.app.name
  policy_arn = aws_iam_policy.s3_read.arn
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policy_attachment.html.markdown

# Enforce exclusive managed-policy management — detaches any unlisted managed policy
resource "aws_iam_role_policy_attachments_exclusive" "app" {
  role_name   = aws_iam_role.app.name
  policy_arns = [aws_iam_role_policy_attachment.app_managed.policy_arn]  # include ALL co-managed ARNs
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policy_attachments_exclusive.html.markdown
```
