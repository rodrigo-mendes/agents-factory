# Always-Do — Global Tables v2, Satellite Resources, Testing

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 6. Global Tables V2 Replicas

The `aws_dynamodb_global_table` page says: to manage Global Tables V2 (version 2019.11.21) use the
`replica` configuration block of `aws_dynamodb_table`. Replica arguments: `region_name` (required),
`kms_key_arn` (changing it recreates the replica), `point_in_time_recovery` (default false),
`deletion_protection_enabled` (default false), `propagate_tags` (default false; tags flow table to
replica only, replica drift is not detected), `consistency_mode` (`EVENTUAL` default, or `STRONG`).
`global_table_witness { region_name }` is only valid with exactly one `replica` whose
`consistency_mode = "STRONG"`; other combinations fail to provision. Whether replicas also need
streams enabled is not stated on the cited pages (unverified).

```hcl
resource "aws_dynamodb_table" "global" {
  name         = "profiles"          # example
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  replica {
    region_name                 = "eu-central-1"  # example
    point_in_time_recovery      = true
    deletion_protection_enabled = true
    propagate_tags              = true
    consistency_mode            = "EVENTUAL"
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_global_table.html.markdown
```

When managing replicas with `aws_dynamodb_table_replica` instead (use provider aliases per region;
required `global_table_arn`; import `table-name:main-region`), do not declare `replica` blocks and
set `lifecycle { ignore_changes = [replica] }` on the table.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table_replica.html.markdown

## 7. Satellite Resources

```hcl
# Resource policy: 20 KB limit including whitespace; index permissions go in the base table policy.
resource "aws_dynamodb_resource_policy" "orders" {
  resource_arn = aws_dynamodb_table.orders.arn   # table or stream ARN
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::111122223333:role/orders-reader" } # example
      Action    = ["dynamodb:GetItem"]                                     # example
      Resource  = aws_dynamodb_table.orders.arn
    }]
  })
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_resource_policy.html.markdown

# Kinesis streaming destination: one destination per table; stream in the same account and region.
resource "aws_dynamodb_kinesis_streaming_destination" "orders" {
  table_name = aws_dynamodb_table.orders.name
  stream_arn = aws_kinesis_stream.orders.arn   # stream defined elsewhere
  # approximate_creation_date_time_precision accepts MILLISECOND or MICROSECOND;
  # its default is not stated (unverified)
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_kinesis_streaming_destination.html.markdown

# Contributor insights: required table_name; optional index_name.
resource "aws_dynamodb_contributor_insights" "orders" {
  table_name = aws_dynamodb_table.orders.name
  # The valid values of the mode argument are not listed (unverified)
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_contributor_insights.html.markdown

# Table export to S3: PITR must be enabled on the table; destroy only removes it from state.
resource "aws_dynamodb_table_export" "orders" {
  table_arn     = aws_dynamodb_table.orders.arn   # forces new
  s3_bucket     = "my-export-bucket"              # example; forces new
  export_format = "DYNAMODB_JSON"                 # default; or ION
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table_export.html.markdown
```

`aws_dynamodb_table_item` requires `table_name`, `hash_key` and `item` (JSON including the key
attributes), plus `range_key` when the table has one. It is "not meant to be used for managing large
amounts of data". Import ID is `table_name,hash_value[,range_value]` (since 6.52.0).
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table_item.html.markdown

## 8. terraform test

`.tftest.hcl` files live in `tests/`; `run` blocks use `command = plan`; `mock_provider "aws"` keeps
CI free of real credentials (https://developer.hashicorp.com/terraform/language/tests/mocking).

```hcl
# tests/orders.tftest.hcl
mock_provider "aws" {}

run "protects_table" {                # example run name
  command = plan
  assert {
    # example assertion; aws_dynamodb_table.orders is defined in the module under test
    condition     = aws_dynamodb_table.orders.deletion_protection_enabled == true
    error_message = "deletion protection must be enabled"  # example
  }
}
# Source: https://developer.hashicorp.com/terraform/language/tests
# Source: https://developer.hashicorp.com/terraform/language/tests/mocking
```

CI commands: `terraform init -backend=false`, `terraform validate -json`,
`terraform plan -detailed-exitcode -input=false -out=tfplan` (exit 0 no changes, 1 error, 2 changes).
Source: https://developer.hashicorp.com/terraform/cli/commands/plan
