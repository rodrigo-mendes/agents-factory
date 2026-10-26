# Never-Do — Provider version and backend

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23.

## 1. Pinning version 6.57.0

aws 6.57.0 was withdrawn from GitHub and the Registry.

```hcl
# WRONG
required_providers {
  aws = { source = "hashicorp/aws", version = "6.57.0" }
}

# CORRECT
required_providers {
  aws = { source = "hashicorp/aws", version = "~> 6.69" }
}
```

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

## 2. S3 backend with dynamodb_table

The S3 backend `dynamodb_table` argument is deprecated; native locking uses `use_lockfile = true`.

```hcl
# WRONG — fragment, other backend arguments omitted (values are examples)
backend "s3" {
  bucket         = "example-terraform-state" # example
  key            = "sam/terraform.tfstate"   # example
  dynamodb_table = "example-locks"           # example
}

# CORRECT
backend "s3" {
  bucket       = "example-terraform-state" # example
  key          = "sam/terraform.tfstate"   # example
  use_lockfile = true
}
```

Source: https://developer.hashicorp.com/terraform/language/backend/s3
