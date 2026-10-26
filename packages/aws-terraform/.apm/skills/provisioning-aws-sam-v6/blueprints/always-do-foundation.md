# Always-Do — Foundation (terraform block, backend)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23.

## 1. Terraform block and S3 backend

Root modules use `~>` for providers; reusable modules set only a minimum (`>=`)
(https://developer.hashicorp.com/terraform/language/expressions/version-constraints). The S3 backend uses
`use_lockfile = true`; `dynamodb_table` is deprecated (https://developer.hashicorp.com/terraform/language/backend/s3).

```hcl
# Fragment: root module. Backend values are placeholders; other backend arguments are omitted.
terraform {
  required_version = "~> 1.16"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }

  backend "s3" {
    bucket       = "example-terraform-state" # example
    key          = "sam/terraform.tfstate"   # example
    region       = "eu-west-1"               # example
    use_lockfile = true
  }
}
```

The SAR stack stores `NoEcho` values in state in plaintext since 6.52.0, so the backend holding this state
must be secured (CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md).
