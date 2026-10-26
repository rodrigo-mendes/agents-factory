# Never-Do — Provider Arguments and Migration (Removed Args, Deprecated Backend, Withdrawn Version)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. aws_eip with vpc = true

The `vpc` argument was removed in 6.0. Using it causes a provider error.

```hcl
# WRONG — removed in 6.0
resource "aws_eip" "bad" {
  vpc        = true   # WRONG — argument removed in hashicorp/aws 6.0
  depends_on = [aws_internet_gateway.main]
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown

# CORRECT
resource "aws_eip" "nat" {
  domain     = "vpc"
  depends_on = [aws_internet_gateway.main]
}
```

## 2. aws_flow_log with log_group_name

`log_group_name` was removed in 6.0. Use `log_destination` (log group ARN) +
`log_destination_type = "cloud-watch-logs"`.

```hcl
# WRONG — removed in 6.0
resource "aws_flow_log" "bad" {
  vpc_id         = aws_vpc.main.id
  traffic_type   = "ALL"
  iam_role_arn   = aws_iam_role.flow_logs.arn
  log_group_name = "/aws/vpc/flow-logs"   # WRONG — removed in 6.0
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown

# CORRECT
resource "aws_flow_log" "vpc" {
  vpc_id               = aws_vpc.main.id
  traffic_type         = "ALL"
  iam_role_arn         = aws_iam_role.flow_logs.arn
  log_destination_type = "cloud-watch-logs"
  log_destination      = aws_cloudwatch_log_group.flow_logs.arn
}
```

## 3. S3 Backend with dynamodb_table

`dynamodb_table` is deprecated and will be removed in a future minor version.
Use `use_lockfile = true` for S3-native locking.

```hcl
# WRONG — dynamodb_table is deprecated
terraform {
  backend "s3" {
    bucket         = "my-tf-state"
    key            = "vpc/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-locks"   # WRONG — deprecated
    encrypt        = true
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3

# CORRECT
terraform {
  backend "s3" {
    bucket       = "my-tf-state"
    key          = "vpc/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true   # needs s3:GetObject/PutObject/DeleteObject
    encrypt      = true
  }
}
```

## 4. Pinning Version 6.57.0

6.57.0 was withdrawn from GitHub and the Terraform Registry. Any constraint that resolves to it
will fail `terraform init`.

```hcl
# WRONG — withdrawn release; init will fail
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "= 6.57.0" }
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

# CORRECT
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```
