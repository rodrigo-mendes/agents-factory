# Always-Do — Foundation (Terraform Block, S3 Backend, Bus, Bus Policy, Archive)

hashicorp/aws 6.x · Terraform ~> 1.16 · Pages read 2026-10-23. All names, ARNs and day counts are `# example` values.

## 1. Terraform Block and S3 Backend

Use `use_lockfile = true` for S3-native locking; `dynamodb_table` is deprecated. Root modules use `~>`;
reusable modules set only a minimum.

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
    bucket       = "my-tf-state"                  # example
    key          = "eventbridge/terraform.tfstate" # example
    region       = "eu-west-1"                    # example
    use_lockfile = true
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
```

## 2. Bus, Bus Policy and Archive

Bus page: `name` is required and cannot contain `/`; `kms_key_identifier` takes a CMK key ARN, KeyId,
alias or alias ARN; `dead_letter_config { arn }` is an SQS queue. Security Hub EventBridge.2 checks
that buses are tagged; EventBridge.3 checks that custom buses have a resource-based policy.
The bus policy and `aws_cloudwatch_event_permission` are incompatible on one bus — this file uses the policy resource.

```hcl
# FRAGMENT — references aws_sqs_queue.bus_dlq, aws_kms_key.events and
# data.aws_iam_policy_document.bus_access, which are defined elsewhere
# (see provisioning-aws-sqs-v6, provisioning-aws-iam-v6).
resource "aws_cloudwatch_event_bus" "orders" {
  name               = "orders"                       # example
  description        = "Order domain events"          # example
  kms_key_identifier = aws_kms_key.events.arn         # CMK
  dead_letter_config {
    arn = aws_sqs_queue.bus_dlq.arn                   # SQS queue
  }
  log_config {
    include_detail = "NONE"   # NONE | FULL
    level          = "ERROR"  # OFF | ERROR | INFO | TRACE
  }
  tags = { Environment = "prod" }                     # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_bus.html.markdown
# Source (bus DLQ with CMK): https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html

resource "aws_cloudwatch_event_bus_policy" "orders" {
  event_bus_name = aws_cloudwatch_event_bus.orders.name   # defaults to "default" if omitted
  policy         = data.aws_iam_policy_document.bus_access.json   # fragment: defined elsewhere
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_bus_policy.html.markdown
# Source (controls): https://docs.aws.amazon.com/securityhub/latest/userguide/eventbridge-controls.html
```

Bus DLQ notes from the AWS DLQ page: the queue policy `aws:SourceArn` is the bus ARN and the queue
must be in the same Region.

Archive: `name` (at most 48 characters) and `event_source_arn` (bus ARN) are required. If
`event_pattern` is omitted, all events are archived. If `retention_days` is omitted, events are
archived indefinitely.

```hcl
resource "aws_cloudwatch_event_archive" "orders" {
  name             = "orders-archive"                    # example
  event_source_arn = aws_cloudwatch_event_bus.orders.arn
  retention_days   = 30                                  # example; omit to keep events indefinitely
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_archive.html.markdown
```
