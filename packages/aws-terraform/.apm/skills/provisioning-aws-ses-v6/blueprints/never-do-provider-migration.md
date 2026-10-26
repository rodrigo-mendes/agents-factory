# Never-Do — Provider and Backend (Withdrawn Version, Deprecated Backend Option)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources dated 2026-10-23.

## 1. Pinning version 6.57.0

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

## 2. S3 backend with dynamodb_table

`dynamodb_table` is deprecated; `use_lockfile = true` is the S3 backend's native locking.

```hcl
# WRONG — deprecated
terraform {
  backend "s3" {
    bucket         = "my-tf-state"          # example
    key            = "ses/terraform.tfstate" # example
    region         = "eu-west-1"            # example
    dynamodb_table = "terraform-locks"      # WRONG — deprecated
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3

# CORRECT
terraform {
  backend "s3" {
    bucket       = "my-tf-state"          # example
    key          = "ses/terraform.tfstate" # example
    region       = "eu-west-1"            # example
    use_lockfile = true
  }
}
```
