# Never-Do — Scheduler, Backend, Withdrawn Version

hashicorp/aws 6.x · Terraform ~> 1.16 · Pages read 2026-10-23 (S3 backend page, provider
CHANGELOG, Scheduler page). Names and ARNs are `# example` values.

## 1. Scheduler Target without role_arn

`role_arn` in the `target` block of `aws_scheduler_schedule` is required — Scheduler always uses an
execution role.

```hcl
# FRAGMENT — references var.target_arn and aws_iam_role.scheduler, defined elsewhere.
# WRONG
resource "aws_scheduler_schedule" "bad" {
  name                = "bad"                             # example
  schedule_expression = "rate(2 hours)"                   # example
  flexible_time_window { mode = "OFF" }
  target {
    arn = var.target_arn                                  # WRONG — role_arn missing
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/scheduler_schedule.html.markdown

# CORRECT
resource "aws_scheduler_schedule" "good" {
  name                = "good"                            # example
  schedule_expression = "rate(2 hours)"                   # example
  flexible_time_window { mode = "OFF" }
  target {
    arn      = var.target_arn
    role_arn = aws_iam_role.scheduler.arn
  }
}
```

## 2. S3 Backend with dynamodb_table

`dynamodb_table` is deprecated; the S3 backend has native locking.

```hcl
# WRONG
terraform {
  backend "s3" {
    bucket         = "my-tf-state"                        # example
    key            = "eventbridge/terraform.tfstate"      # example
    region         = "eu-west-1"                          # example
    dynamodb_table = "tf-locks"                           # WRONG — deprecated
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3

# CORRECT
terraform {
  backend "s3" {
    bucket       = "my-tf-state"                          # example
    key          = "eventbridge/terraform.tfstate"        # example
    region       = "eu-west-1"                            # example
    use_lockfile = true
  }
}
```

## 3. Pinning Version 6.57.0

Provider 6.57.0 was withdrawn from GitHub and the Registry.

```hcl
# WRONG
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "6.57.0" }   # WRONG — withdrawn
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

# CORRECT
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```
