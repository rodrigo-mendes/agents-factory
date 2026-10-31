# Never-Do — Provider, region and event data store

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. data.aws_region.name

`name` is deprecated in 6.0; use `.region`.

```hcl
# WRONG
locals {
  trail_arn = "arn:aws:cloudtrail:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:trail/org-audit"
}

# CORRECT
locals {
  trail_arn = "arn:aws:cloudtrail:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:trail/org-audit"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
```

## 2. suspend = 0 or 1 on the event data store

`aws_cloudtrail_event_data_store.suspend` accepts only `""`, `true` or `false` after the
nullable-boolean change.

```hcl
# WRONG
suspend = 1

# CORRECT
suspend = false
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
```

## 3. region on the organization delegated admin account

`aws_cloudtrail_organization_delegated_admin_account` is global: no `region` argument, no
`@region` import.

```hcl
# WRONG
resource "aws_cloudtrail_organization_delegated_admin_account" "bad" {
  account_id = var.delegated_account_id
  region     = "eu-west-1"   # WRONG — global resource
}

# CORRECT
resource "aws_cloudtrail_organization_delegated_admin_account" "good" {
  account_id = var.delegated_account_id
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
```

## 4. S3 backend with dynamodb_table

Deprecated; use native locking.

```hcl
# WRONG
backend "s3" { dynamodb_table = "tf-locks" }

# CORRECT
backend "s3" { use_lockfile = true }
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
```

## 5. Pinning version 6.57.0

Withdrawn from GitHub and the Registry.

```hcl
# WRONG
aws = { source = "hashicorp/aws", version = "6.57.0" }

# CORRECT
aws = { source = "hashicorp/aws", version = "~> 6.69" }
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
```

## 6. Removing or changing the event data store KMS key

AWS: once a KMS key is associated with an event data store it cannot be removed or changed. Choose
the key before the first apply.

```hcl
# WRONG — plan to swap the key on an existing store
kms_key_id = var.new_key_arn

# CORRECT — decide the key at creation
kms_key_id = var.eds_kms_key_arn
# Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html
```
