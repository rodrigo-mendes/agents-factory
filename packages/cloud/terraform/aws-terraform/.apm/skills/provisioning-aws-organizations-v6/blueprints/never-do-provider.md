# Never-Do — Provider and Terraform (status, dynamodb_table, withdrawn version)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. Deprecated status Attribute

`status` on the organization and account attributes is deprecated; use `state`.

```hcl
# WRONG
output "account_status" {
  value = aws_organizations_account.member["prod"].status   # WRONG: deprecated
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown

# CORRECT
output "account_state" {
  value = aws_organizations_account.member["prod"].state
}
```

## 2. S3 Backend with dynamodb_table

`dynamodb_table` is deprecated; use S3-native locking.

```hcl
# WRONG
terraform {
  backend "s3" {
    bucket         = "my-tf-state"
    key            = "organizations/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf-locks"   # WRONG: deprecated
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3

# CORRECT
terraform {
  backend "s3" {
    bucket       = "my-tf-state"
    key          = "organizations/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}
```

## 3. Pinning Version 6.57.0

6.57.0 was withdrawn from GitHub and the Registry.

```hcl
# WRONG
required_providers {
  aws = { source = "hashicorp/aws", version = "6.57.0" }   # WRONG: withdrawn
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

# CORRECT
required_providers {
  aws = { source = "hashicorp/aws", version = "~> 6.69" }
}
```
