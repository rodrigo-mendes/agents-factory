# Always-Do — Foundation (Terraform Block, S3 Backend, VPC, Subnets)

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
    key          = "vpc/terraform.tfstate"
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

## 2. VPC and Public/Private Subnets

Use `for_each` over AZ maps. `enable_dns_hostnames = true` is required for private hosted zones
and ECS service discovery (default is false).

```hcl
locals {
  public_subnets = {
    "eu-west-1a" = "10.0.0.0/24"
    "eu-west-1b" = "10.0.1.0/24"
    "eu-west-1c" = "10.0.2.0/24"
  }
  private_subnets = {
    "eu-west-1a" = "10.0.10.0/24"
    "eu-west-1b" = "10.0.11.0/24"
    "eu-west-1c" = "10.0.12.0/24"
  }
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true   # default true; explicit for clarity
  enable_dns_hostnames = true   # default false — needed for private DNS
  tags = { Name = "main" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown

resource "aws_subnet" "public" {
  for_each                = local.public_subnets
  vpc_id                  = aws_vpc.main.id
  cidr_block              = each.value
  availability_zone       = each.key
  map_public_ip_on_launch = true   # default false
  tags = { Name = "public-${each.key}" }
}

resource "aws_subnet" "private" {
  for_each          = local.private_subnets
  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value
  availability_zone = each.key
  tags = { Name = "private-${each.key}" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/subnet.html.markdown
```
