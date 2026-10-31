# Never-Do — Provider Migration (6.0 Region Changes, Backend Locking, Withdrawn Version)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Reading Bucket Region via region Attribute

In 6.0, `region` on `aws_s3_bucket` means Enhanced Region Support. Use `bucket_region`
to read the bucket's home region.

```hcl
# WRONG — .region is Enhanced Region Support in 6.x
output "bucket_home_region_wrong" {
  value = aws_s3_bucket.main.region   # WRONG — not the bucket's home region
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown

# CORRECT
output "bucket_home_region" {
  value = aws_s3_bucket.main.bucket_region
}
```

## 2. region on Account Public Access Block

`aws_s3_account_public_access_block` is a **global** resource. Never set `region`
and never import with `id@region`.

```hcl
# WRONG — region on a global resource
resource "aws_s3_account_public_access_block" "bad" {
  region            = "eu-west-1"   # WRONG — global resource
  account_id        = "111122223333"
  block_public_acls = true
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown

# CORRECT — no region attribute
resource "aws_s3_account_public_access_block" "main" {
  account_id              = data.aws_caller_identity.current.account_id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
# Import: terraform import aws_s3_account_public_access_block.main 111122223333
# NOT: 111122223333@eu-west-1
```

## 3. Deprecated aws_region Name Attribute

`data.aws_region` attribute `name` is deprecated in 6.0. Use `region`.

```hcl
data "aws_region" "current" {}

# WRONG
locals {
  region_name = data.aws_region.current.name   # WRONG — deprecated in 6.0
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown

# CORRECT
locals {
  region_name = data.aws_region.current.region
}
```

## 4. S3 Backend with dynamodb_table

`dynamodb_table` is deprecated. Use `use_lockfile = true` for S3-native locking.

```hcl
# WRONG — dynamodb_table is deprecated
terraform {
  backend "s3" {
    bucket         = "my-tf-state"
    key            = "s3/terraform.tfstate"
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
    key          = "s3/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true
    encrypt      = true
  }
}
```

## 5. Pinning Version 6.57.0

6.57.0 was withdrawn from GitHub and the Registry.

```hcl
# WRONG — withdrawn release
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
