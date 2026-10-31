# Never-Do — Replicas, Table Items, Backend, Provider Version

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. Mixing replica blocks with aws_dynamodb_table_replica

The table page: never mix `replica` blocks with the `aws_dynamodb_table_replica` resource. When
using that resource, set `lifecycle { ignore_changes = [replica] }` on the table.

```hcl
resource "aws_dynamodb_table" "bad" {
  name         = "profiles"        # example
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
  replica {                        # WRONG - inline replica ...
    region_name = "eu-central-1"   # example
  }
}
resource "aws_dynamodb_table_replica" "also_bad" {   # WRONG - ... plus a replica resource
  provider         = aws.other_region               # example alias
  global_table_arn = aws_dynamodb_table.bad.arn
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown

# CORRECT - replica blocks only (blueprint always-do-replication-satellites section 6), or
# aws_dynamodb_table_replica only, with ignore_changes = [replica] on the table.
```

## 2. Bulk data in aws_dynamodb_table_item

The resource page: `aws_dynamodb_table_item` is "not meant to be used for managing large amounts
of data".

```hcl
# WRONG - one Terraform resource per row of a large dataset
resource "aws_dynamodb_table_item" "rows" {
  for_each   = { for r in local.million_rows : r.id => r }   # WRONG
  table_name = aws_dynamodb_table.orders.name
  hash_key   = aws_dynamodb_table.orders.hash_key
  item       = jsonencode(each.value)
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table_item.html.markdown

# CORRECT - keep the resource to a few seed items
resource "aws_dynamodb_table_item" "seed" {
  table_name = aws_dynamodb_table.orders.name  # table defined elsewhere
  hash_key   = aws_dynamodb_table.orders.hash_key
  item       = jsonencode({ pk = { S = "config" } })  # example; item JSON must include the key attributes
}
```

## 3. S3 backend with dynamodb_table

Terraform docs: S3 backend `dynamodb_table` locking is deprecated; `use_lockfile = true` is the
native S3 lock. Do not create a DynamoDB lock table for new state backends.

```hcl
# WRONG
terraform {
  backend "s3" {
    bucket         = "my-tf-state"      # example
    key            = "app/terraform.tfstate" # example
    region         = "eu-west-1"        # example
    dynamodb_table = "tf-locks"         # WRONG - deprecated
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3

# CORRECT
terraform {
  backend "s3" {
    bucket       = "my-tf-state"        # example
    key          = "app/terraform.tfstate" # example
    region       = "eu-west-1"          # example
    use_lockfile = true
  }
}
```

## 4. Pinning version 6.57.0

Provider 6.57.0 was withdrawn from GitHub and the Registry; never pin it.

```hcl
# WRONG
required_providers {
  aws = { source = "hashicorp/aws", version = "6.57.0" }   # WRONG - withdrawn
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

# CORRECT - root module
required_providers {
  aws = { source = "hashicorp/aws", version = "~> 6.69" }
}
```
