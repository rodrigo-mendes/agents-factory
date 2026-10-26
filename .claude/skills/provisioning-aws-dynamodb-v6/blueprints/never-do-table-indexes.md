# Never-Do — Table, Indexes, Throughput, Encryption

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. Defining attributes that are not key attributes

The table page: define attributes only for table, LSI and GSI key attributes — "Adding attributes
not used in these scenarios causes an infinite plan loop."

```hcl
# WRONG - "payload" is not a key attribute of the table, an LSI or a GSI
resource "aws_dynamodb_table" "bad" {
  name         = "bad"             # example
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  attribute {
    name = "pk"
    type = "S"
  }
  attribute {
    name = "payload"               # WRONG - infinite plan loop
    type = "S"
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown

# CORRECT - only key attributes
resource "aws_dynamodb_table" "good" {
  name         = "good"            # example
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  attribute {
    name = "pk"
    type = "S"
  }
}
```

## 2. Mixing inline global_secondary_index with the separate resource

The index resource page: mixing inline `global_secondary_index` blocks with
`aws_dynamodb_global_secondary_index` on the same table causes "conflicts, perpetual differences,
and Global Secondary Indexes being overwritten". Migrate by one resource per block plus import.

```hcl
resource "aws_dynamodb_table" "bad" {
  name         = "items"           # example
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  attribute {
    name = "pk"
    type = "S"
  }
  global_secondary_index {         # WRONG - inline block on the same table
    name            = "by-owner"   # example
    projection_type = "ALL"
    key_schema {
      attribute_name = "owner"
      key_type       = "HASH"
    }
  }
}
resource "aws_dynamodb_global_secondary_index" "also_bad" { # WRONG - second mechanism
  table_name = aws_dynamodb_table.bad.name
  index_name = "by-status"         # example
  key_schema = [{ attribute_name = "status", attribute_type = "S", key_type = "HASH" }]
  projection = { projection_type = "ALL" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_global_secondary_index.html.markdown

# CORRECT - one mechanism per table: all inline (blueprint always-do-indexes-capacity section 3)
# or only aws_dynamodb_global_secondary_index resources with no inline blocks.
```

## 3. Inline GSI hash_key and range_key

The table page marks the inline GSI `hash_key` and `range_key` deprecated and mutually exclusive with
`key_schema`; `key_schema` is required when `hash_key` is not set.

```hcl
# WRONG - deprecated arguments inside an inline global_secondary_index
global_secondary_index {
  name            = "by-owner"     # example
  hash_key        = "owner"        # WRONG - deprecated
  range_key       = "created_at"   # WRONG - deprecated
  projection_type = "ALL"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown

# CORRECT
global_secondary_index {
  name            = "by-owner"     # example
  projection_type = "ALL"
  key_schema {
    attribute_name = "owner"
    key_type       = "HASH"
  }
  key_schema {
    attribute_name = "created_at"
    key_type       = "RANGE"
  }
}
```

## 4. Setting warm_throughput to its default values

The table page: setting both `warm_throughput` values explicitly to their default/minimum values
(12000 read, 4000 write) causes reported diffs.

```hcl
# WRONG - both values equal the default/minimum
warm_throughput {
  read_units_per_second  = 12000   # WRONG - reported diffs
  write_units_per_second = 4000    # WRONG - reported diffs
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown

# CORRECT - omit the block (the table page says to omit instead)
```

## 5. kms_key_arn set to the AWS managed key

The table page: `kms_key_arn` is only for keys other than `alias/aws/dynamodb` (customer managed
keys). `enabled = true` without `kms_key_arn` already selects the AWS managed key `alias/aws/dynamodb`.

```hcl
# WRONG - pointing kms_key_arn at the AWS managed key alias
server_side_encryption {
  enabled     = true
  kms_key_arn = "arn:aws:kms:eu-west-1:111122223333:alias/aws/dynamodb" # example, WRONG
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown

# CORRECT - AWS managed key: omit kms_key_arn; customer managed key: pass its own key ARN
server_side_encryption {
  enabled     = true
  kms_key_arn = var.kms_key_arn    # customer managed key
}
```
