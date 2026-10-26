# Never-Do — Provider and Migration

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 5. S3 Backend with `dynamodb_table`

`dynamodb_table` is deprecated and will be removed in a future provider version.

```hcl
# WRONG — deprecated locking
backend "s3" {
  bucket         = "my-tf-state"
  key            = "iam/terraform.tfstate"
  region         = "eu-west-1"
  dynamodb_table = "tf-locks"   # deprecated
}
```

```hcl
# CORRECT — native S3 locking
backend "s3" {
  bucket       = "my-tf-state"
  key          = "iam/terraform.tfstate"
  region       = "eu-west-1"
  use_lockfile = true
  encrypt      = true
}
```
Source: https://developer.hashicorp.com/terraform/language/backend/s3

## 6. Pinning Version 6.57.0

6.57.0 is permanently withdrawn from GitHub and the Registry. Any constraint that resolves to it
will fail `terraform init`.

```hcl
# WRONG
aws = { source = "hashicorp/aws", version = "6.57.0" }   # withdrawn — init fails

# CORRECT
aws = { source = "hashicorp/aws", version = "~> 6.69" }
```
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
