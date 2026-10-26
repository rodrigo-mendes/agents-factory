# Always-Do — Secondary Indexes and Capacity

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 3. Secondary Indexes

Inline `global_secondary_index` needs `name` and `projection_type` (`ALL`, `INCLUDE`, `KEYS_ONLY`);
`non_key_attributes` only with `INCLUDE`. The GSI `hash_key`/`range_key` arguments are
marked deprecated on the table page and mutually exclusive with `key_schema`; `key_schema` is required when `hash_key` is not
set. Each `key_schema` block has `attribute_name` and `key_type` (`HASH` or `RANGE`), up to 4 HASH
and 4 RANGE attributes. LSIs have no `key_schema`, need `name`, `projection_type` and `range_key`,
and can only be defined at table creation.

```hcl
resource "aws_dynamodb_table" "orders" {
  name         = "orders"          # example
  billing_mode = "PAY_PER_REQUEST"
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
  attribute {
    name = "status"                # key attribute of the GSI below
    type = "S"
  }
  attribute {
    name = "created_at"            # key attribute of the GSI and LSI below
    type = "S"
  }

  global_secondary_index {
    name            = "status-created"   # example
    projection_type = "ALL"
    key_schema {
      attribute_name = "status"
      key_type       = "HASH"
    }
    key_schema {
      attribute_name = "created_at"
      key_type       = "RANGE"
    }
  }

  local_secondary_index {
    name            = "by-created"       # example
    projection_type = "KEYS_ONLY"
    range_key       = "created_at"
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_table.html.markdown
```

Separate resource `aws_dynamodb_global_secondary_index`: required `table_name`, `index_name`,
`key_schema`, `projection`. `key_schema` needs at least one HASH, HASH before RANGE, each element
with `attribute_name`, `attribute_type` (`S`/`N`/`B`) and `key_type`; any change forces new.
`provisioned_throughput { read_capacity_units, write_capacity_units }` is for `PROVISIONED` tables,
`on_demand_throughput` only for `PAY_PER_REQUEST`. Import ID is `table_name,index_name`.
The table page calls this resource "experimental" while the resource page shows no such warning
(medium confidence); confirm with the user before adopting (see SKILL.md Ask First).

```hcl
resource "aws_dynamodb_global_secondary_index" "by_owner" {
  table_name = aws_dynamodb_table.items.name   # table WITHOUT inline global_secondary_index blocks
  index_name = "by-owner"                      # example
  key_schema = [{
    attribute_name = "owner"                   # example
    attribute_type = "S"
    key_type       = "HASH"
  }]
  projection = {
    projection_type = "ALL"
  }
  provisioned_throughput = {                   # only for PROVISIONED tables
    read_capacity_units  = 5                   # example
    write_capacity_units = 5                   # example
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/dynamodb_global_secondary_index.html.markdown
```

## 4. Auto Scaling for Provisioned Tables

With an App Auto Scaling policy attached, the table ignores capacity drift via
`lifecycle { ignore_changes = [read_capacity, write_capacity] }`. The target needs `max_capacity`,
`min_capacity`, `resource_id`, `scalable_dimension` and `service_namespace = "dynamodb"`. Table
`resource_id` is `table/<name>`; index `resource_id` is `table/<name>/index/<index>` with dimension
`dynamodb:index:ReadCapacityUnits` / `dynamodb:index:WriteCapacityUnits`. The policy `policy_type`
defaults to `StepScaling`; set `TargetTrackingScaling` for DynamoDB.

```hcl
resource "aws_dynamodb_table" "jobs" {
  name           = "jobs"            # example
  billing_mode   = "PROVISIONED"
  read_capacity  = 5                 # example
  write_capacity = 5                 # example
  hash_key       = "id"
  attribute {
    name = "id"
    type = "S"
  }
  lifecycle {
    ignore_changes = [read_capacity, write_capacity]
  }
}

resource "aws_appautoscaling_target" "read" {
  service_namespace  = "dynamodb"
  resource_id        = "table/${aws_dynamodb_table.jobs.name}"
  scalable_dimension = "dynamodb:table:ReadCapacityUnits"
  min_capacity       = 5             # example
  max_capacity       = 100           # example
}

resource "aws_appautoscaling_policy" "read" {
  name               = "jobs-read"   # example
  policy_type        = "TargetTrackingScaling"
  service_namespace  = aws_appautoscaling_target.read.service_namespace
  resource_id        = aws_appautoscaling_target.read.resource_id
  scalable_dimension = aws_appautoscaling_target.read.scalable_dimension
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBReadCapacityUtilization"
    }
    target_value = 70                # value used in the provider page example
  }
}

# Write policy: same shape with scalable_dimension "dynamodb:table:WriteCapacityUnits" and
# predefined_metric_type = "<write metric name>"  # placeholder (metric name not on the provider page) (unverified)
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/appautoscaling_target.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/appautoscaling_policy.html.markdown
```

The provider policy page shows only the read example; the write-capacity metric name does not
appear on it (unverified). Security Hub DynamoDB.1 is the control "Tables should automatically
scale capacity with demand" (https://docs.aws.amazon.com/securityhub/latest/userguide/dynamodb-controls.html). App Auto Scaling manages its service-linked role on first registration; use
`aws_iam_service_linked_role` to own it (see provisioning-aws-iam-v6).
