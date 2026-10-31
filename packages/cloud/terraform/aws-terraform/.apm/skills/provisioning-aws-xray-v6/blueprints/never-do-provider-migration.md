# Never-Do — Provider Version and Backend

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23.

## 1. Pinning Version 6.57.0

6.57.0 was withdrawn from GitHub and the Registry.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

```hcl
# WRONG — withdrawn version
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "6.57.0" } # WRONG
  }
}

# CORRECT
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

## 2. S3 Backend with dynamodb_table

`dynamodb_table` is deprecated; native locking uses `use_lockfile = true`.
Source: https://developer.hashicorp.com/terraform/language/backend/s3

```hcl
# WRONG — fragment, deprecated locking argument
backend "s3" {
  bucket         = "my-tf-state"            # example
  key            = "xray/terraform.tfstate" # example
  region         = "eu-west-1"              # example
  dynamodb_table = "tf-locks"               # WRONG — deprecated; example name
}

# CORRECT — fragment
backend "s3" {
  bucket       = "my-tf-state"            # example
  key          = "xray/terraform.tfstate" # example
  region       = "eu-west-1"              # example
  use_lockfile = true
}
```
