# Always-Do — Bucket Foundation (Terraform Block, Bucket, Ownership, BPA)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Terraform Block and S3 Backend

Use `use_lockfile = true` for S3-native locking. `dynamodb_table` is deprecated.
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
    key          = "s3/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true   # S3-native lock; dynamodb_table is deprecated
    encrypt      = true
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
```

## 2. Bucket Resource and Ownership Controls

Use standalone satellite resources — never mix deprecated inline blocks (e.g. `versioning {}`,
`server_side_encryption_configuration {}`) with their satellite resource on the same bucket.
`BucketOwnerEnforced` is the default for new buckets; ACLs are disabled.

```hcl
resource "aws_s3_bucket" "main" {
  bucket = "my-app-data-bucket"
  # force_destroy defaults false — set true only for non-critical / ephemeral buckets;
  # deletes ALL objects including locked ones; only takes effect after a successful apply
  tags = { Name = "my-app-data" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket.html.markdown

resource "aws_s3_bucket_ownership_controls" "main" {
  bucket = aws_s3_bucket.main.id
  rule {
    object_ownership = "BucketOwnerEnforced"   # ACLs disabled; default for new buckets
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_ownership_controls.html.markdown
```

Use `bucket_regional_domain_name` (not the deprecated `bucket_domain_name`) for CloudFront origin
references; the CloudFront distribution itself is covered by provisioning-aws-cloudfront-v6.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket.html.markdown

## 3. Bucket-Level Public Access Block

All four booleans default `false` — set them all explicitly. A missing setting re-exposes public
access when a policy or ACL allows it.

```hcl
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_public_access_block.html.markdown
# Security Hub: S3.8 (bucket-level BPA — High), S3.2/S3.3 (public read/write — Critical)
```

`skip_destroy = true` leaves the block in AWS as unmanaged after destroy — avoid unless required.

## 4. Account-Level Public Access Block

One `aws_s3_account_public_access_block` per account. This resource is **global** —
never set `region` on it and never import with `id@region`; import with `<account_id>` only.
Account-level settings apply to all Regions globally (eventual propagation).

```hcl
data "aws_caller_identity" "current" {}

resource "aws_s3_account_public_access_block" "org" {
  # No region attribute — this resource is global
  account_id = data.aws_caller_identity.current.account_id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_account_public_access_block.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
# Security Hub: S3.1 (account-level BPA — Medium)
# Note: 6.62.0 fixed a create eventual-consistency bug on this resource.
```

S3 applies the most restrictive combination of account-level and bucket-level BPA.
Removing a BPA setting re-exposes existing public policies/ACLs.
