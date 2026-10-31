# Always-Do — Key Basics (Terraform Block, aws_kms_key, aws_kms_alias)

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
    key          = "kms/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true   # S3-native lock; dynamodb_table is deprecated
    encrypt      = true
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
```

## 2. aws_kms_key

Symmetric encryption key with rotation and production lifecycle guard. Security Hub KMS.3 requires
`prevent_destroy` and a 30-day deletion window. KMS.4 requires `enable_key_rotation = true` on
symmetric `AWS_KMS` keys.

```hcl
resource "aws_kms_key" "app" {
  description              = "Application encryption key for ${var.env}"
  key_usage                = "ENCRYPT_DECRYPT"   # default; explicit for clarity
  customer_master_key_spec = "SYMMETRIC_DEFAULT"  # default; supports auto-rotation

  enable_key_rotation     = true   # KMS.4: required for symmetric AWS_KMS keys
  # rotation_period_in_days omitted → AWS uses 365 days on enable.
  # Set 90–2560 for a custom period; must have enable_key_rotation = true first.
  # Provider docs state no default for this argument.
  # Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown
  # Source: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html

  deletion_window_in_days = 30     # KMS.3: maximum window; default is also 30
  is_enabled              = true   # default; explicit for clarity

  tags = {
    Name        = "app-${var.env}"
    Environment = var.env
    ManagedBy   = "terraform"
  }

  lifecycle {
    prevent_destroy = true   # KMS.3: blocks accidental terraform destroy in production
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html
```

Key attributes exported: `arn`, `key_id`, `tags_all`.
Timeout: only `create`, default 2 minutes; a shorter custom timeout is ignored.

**Destroy behaviour:** destroying the resource schedules deletion after `deletion_window_in_days`.
During the waiting period the key is "Pending deletion": it cannot be used and is not rotated.
Use `prevent_destroy = true` for production keys. Disabling the key (`is_enabled = false`) is
reversible and is safer than scheduling deletion.
Source: https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html

**Immutability (medium confidence):** `KeySpec`, `KeyUsage`, `Origin`, and `MultiRegion` cannot be
changed after key creation per the AWS API (M1). Whether the provider plans a replacement or returns
an error for changes to these arguments is not documented on the resource page.
Source: https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateKey.html

## 3. aws_kms_alias

```hcl
resource "aws_kms_alias" "app" {
  name          = "alias/app-${var.env}"   # must start with alias/; never alias/aws/
  target_key_id = aws_kms_key.app.key_id
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_alias.html.markdown

# Alternatively, use name_prefix (conflicts with name — use one or the other, not both)
resource "aws_kms_alias" "app_prefix" {
  name_prefix   = "alias/app-"            # provider appends a unique suffix
  target_key_id = aws_kms_key.app.key_id
}
```

AWS alias rules (from CreateAlias API):
- Pattern: `alias/[a-zA-Z0-9/_-]+`, 1–256 characters.
- `alias/aws/` prefix is reserved for AWS managed keys.
- An alias is unique per account and Region; points to one key at a time.
- A key can have multiple aliases. Alias and key must be in the same account and Region.
- Renaming an alias is not supported: delete and recreate.
- `UpdateAlias` can only retarget to a key of the same type and key usage.
Source: https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateAlias.html
