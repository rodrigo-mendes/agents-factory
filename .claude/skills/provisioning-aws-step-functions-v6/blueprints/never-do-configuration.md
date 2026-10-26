# Never-Do — Terraform Configuration

hashicorp/aws 6.x · Terraform ~> 1.16 · Pages read 2026-10-23. Scaffolding (unverified): ASL
structure and IAM JSON form are not quoted on the cited pages; see the note in always-do-state-machine.

State machine arguments: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown

## 1. Log destination ARN without a trailing wildcard suffix

`log_destination` is a CloudWatch log group ARN that must end with `:*`.

```hcl
# WRONG — log group ARN as-is
logging_configuration {
  log_destination = aws_cloudwatch_log_group.sfn.arn # fragment: defined elsewhere
  level           = "ERROR"                          # example
}

# CORRECT — ARN followed by :*
logging_configuration {
  log_destination = "${aws_cloudwatch_log_group.sfn.arn}:*"
  level           = "ERROR" # example
}
```

## 2. Setting name and name_prefix together

`name_prefix` conflicts with `name`.

```hcl
# WRONG
resource "aws_sfn_state_machine" "bad" {
  name        = "order-workflow" # example
  name_prefix = "order-"         # example — conflicts with name
  role_arn    = aws_iam_role.sfn.arn # fragment: defined elsewhere
  definition  = local.definition     # fragment: defined elsewhere
}

# CORRECT — one of the two
resource "aws_sfn_state_machine" "good" {
  name       = "order-workflow" # example
  role_arn   = aws_iam_role.sfn.arn
  definition = local.definition
}
```

## 3. Alias routing to an alias or an unpublished revision

AWS: aliases point only to versions, not to other aliases or unpublished revisions
(https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-alias.html).
Version ARNs come from `state_machine_version_arn` (with `publish = true`) or the data source
`aws_sfn_state_machine_versions`
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_alias.html.markdown).

```hcl
# WRONG — an alias ARN is not a version ARN
resource "aws_sfn_alias" "bad" {
  name = "blue" # example
  routing_configuration {
    state_machine_version_arn = aws_sfn_alias.live.arn # another alias
    weight                    = 100
  }
}
resource "aws_sfn_alias" "bad_unpublished" {
  name = "green" # example
  routing_configuration {
    state_machine_version_arn = aws_sfn_state_machine.draft.arn # state machine ARN (unpublished revision), not a version ARN
    weight                    = 100
  }
}

# CORRECT — a published version ARN
resource "aws_sfn_alias" "good" {
  name = "blue" # example
  routing_configuration {
    state_machine_version_arn = aws_sfn_state_machine.main.state_machine_version_arn # fragment: publish = true
    weight                    = 100
  }
}
```

## 4. S3 backend with dynamodb_table

`dynamodb_table` is deprecated (https://developer.hashicorp.com/terraform/language/backend/s3).

```hcl
# WRONG
backend "s3" {
  bucket         = "my-tf-state"   # example
  key            = "sfn/terraform.tfstate" # example
  region         = "eu-west-1"     # example
  dynamodb_table = "tf-locks"      # example — deprecated
}

# CORRECT
backend "s3" {
  bucket       = "my-tf-state"   # example
  key          = "sfn/terraform.tfstate" # example
  region       = "eu-west-1"     # example
  use_lockfile = true
}
```

## 5. Pinning version 6.57.0

aws 6.57.0 was withdrawn from GitHub and the Registry
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md).

```hcl
# WRONG
required_providers {
  aws = { source = "hashicorp/aws", version = "6.57.0" }
}

# CORRECT
required_providers {
  aws = { source = "hashicorp/aws", version = "~> 6.69" }
}
```
