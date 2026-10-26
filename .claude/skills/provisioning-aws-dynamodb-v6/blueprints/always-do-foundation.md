# Always-Do — Foundation (Terraform Block, S3 Backend, Table)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. Terraform Block and S3 Backend

Root modules pin `~> 6.69`; reusable modules set only a minimum (`>=`). The S3 backend locks with
`use_lockfile = true`; `dynamodb_table` locking is deprecated, so do not create a DynamoDB lock table
for a new state backend.

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }
  backend "s3" {
    bucket       = "my-tf-state"            # example
    key          = "dynamodb/terraform.tfstate" # example
    region       = "eu-west-1"              # example
    use_lockfile = true                     # native S3 locking
    encrypt      = true
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
```

Regional resources accept an optional `region` (DynamoDB is a regional service); changing it forces
replacement.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown

## 2. Table Keys Billing and Data Protection

`name`, `attribute` and `hash_key` are required; `hash_key` must also be an `attribute` and forces
a new table when changed (`range_key` is optional and also forces new). `attribute.type` is `S`, `N`
or `B`. Define `attribute` blocks only for table, LSI and GSI key attributes. `billing_mode`
defaults to `PROVISIONED`, so set it explicitly. `deletion_protection_enabled` defaults to `false`.

```hcl
resource "aws_dynamodb_table" "orders" {
  name         = "orders"            # example
  billing_mode = "PAY_PER_REQUEST"   # default is PROVISIONED; always set explicitly
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }
  attribute {
    name = "sk"
    type = "S"
  }

  deletion_protection_enabled = true # example choice (Ask First); default false; Security Hub DynamoDB.6 checks it

  point_in_time_recovery {
    enabled                 = true   # Security Hub DynamoDB.2 checks PITR
    recovery_period_in_days = 35     # example; provider default is 35, AWS states 1-35
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn    # customer managed key; see provisioning-aws-kms-v6
  }

  ttl {
    enabled        = true
    attribute_name = "expires_at"    # example; required when enabled
    # TTL deletion timing was not verified (unverified)
  }

  tags = {
    Environment = "prod"             # example; Security Hub DynamoDB.5 checks required tag keys
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/dynamodb-controls.html
# Source (PITR 1-35 days): https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery_Howitworks.html
```

Encryption key types, as the table page and AWS describe them:

| `server_side_encryption` | Resulting key |
|---|---|
| block absent or `enabled = false` | AWS owned key (default, "DEFAULT" in console) |
| `enabled = true`, no `kms_key_arn` | AWS managed key `alias/aws/dynamodb` ("KMS" in console) |
| `enabled = true` + `kms_key_arn` | customer managed key |

Sources: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown ;
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html

PITR may take about 10 minutes on new tables (table page above). Restoring from PITR always creates
a new table (https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery_Howitworks.html).

## 5. On-Demand and Warm Throughput

`on_demand_throughput { max_read_request_units, max_write_request_units }`: set >= 1 to cap, `-1`
to remove (table and GSI). `warm_throughput { read_units_per_second, write_units_per_second }`:
minimum and default 12000 / 4000. On the base table read units cannot be decreased; on a GSI both
can go up or down. Use provider >= 6.57.1 when tuning warm throughput (never 6.57.0).

```hcl
resource "aws_dynamodb_table" "events" {
  name         = "events"            # example
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
  on_demand_throughput {
    max_read_request_units  = 1000   # example cap
    max_write_request_units = 500    # example cap
  }
  warm_throughput {
    read_units_per_second  = 20000   # example, above the 12000 minimum
    write_units_per_second = 8000    # example, above the 4000 minimum
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown
# Source (6.57.1 no longer replaces the table when warm_throughput decreases): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
```

Other table arguments: `table_class` is `STANDARD` (default) or `STANDARD_INFREQUENT_ACCESS`;
`stream_enabled` with `stream_view_type` `KEYS_ONLY`, `NEW_IMAGE`, `OLD_IMAGE` or
`NEW_AND_OLD_IMAGES`. Timeouts: create 30m, update 60m, delete 10m. Import ID is the table name.
