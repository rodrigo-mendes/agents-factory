# Always-Do — Budgets (Terraform Block, Budget, Filters, SNS Policy, Budget Action)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23. Values marked `# example` are placeholders; condition operators (`StringEquals`, `ArnLike`) are `# example (operator not taken from a page)` except where an AWS page names them.

## 1. Terraform Block and S3 Backend

Use `use_lockfile = true` for S3-native locking; `dynamodb_table` is deprecated. Root modules use `~>`;
reusable modules set only a minimum (`>=`). No `region` is set on any Cost Management resource.

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
    key          = "cost-management/terraform.tfstate" # example
    region       = "eu-west-1"              # example
    use_lockfile = true
    encrypt      = true
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
```

## 2. Budget With Notifications

`budget_type` and `time_unit` are required; `time_unit` is `MONTHLY`, `QUARTERLY`, `ANNUALLY` or `DAILY`.
Each `notification` needs `comparison_operator`, `notification_type` (`ACTUAL` or `FORECASTED`), `threshold`
and `threshold_type`, plus `subscriber_email_addresses` or `subscriber_sns_topic_arns`. The resource has no
`region` argument (global service).

```hcl
resource "aws_budgets_budget" "monthly" {
  name         = "monthly-cost"   # example
  budget_type  = "COST"
  time_unit    = "MONTHLY"
  limit_amount = "100"            # example
  limit_unit   = "USD"            # example

  notification {
    comparison_operator        = "GREATER_THAN" # example; allowed values are on the resource page
    notification_type          = "ACTUAL"
    threshold                  = 80             # example
    threshold_type             = "PERCENTAGE"   # example; allowed values are on the resource page
    subscriber_email_addresses = ["finops@example.com"] # example
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown
# Source (global, no region): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
```

Import: `AccountID:BudgetName` (`import` block needs Terraform >= 1.5).
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown

## 3. Budget Filter Rules

Rules from the `aws_budgets_budget` page (no HCL: nested block syntax is on the page):

- `cost_filter` conflicts with `filter_expression`; `metrics` conflicts with `cost_types`.
- `filter_expression` requires `metrics`, and `metrics` requires `filter_expression`.
- One root per block: `and`, `or`, `not`, `dimensions`, `tags` or `cost_categories`.
- "`and` and `or` require at least 2 operands", each as its own block; maximum nesting depth 2.
- `ABSENT` is not supported in `match_options`.
- `auto_adjust_data` with `HISTORICAL` requires `historical_options.budget_adjustment_period`.

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown

## 4. SNS Topic Policy for Budgets

AWS documents a policy with principal `budgets.amazonaws.com`, action `SNS:Publish`, condition
`aws:SourceAccount` and `ArnLike` `aws:SourceArn` = `arn:aws:budgets::<account-id>:*` (condition keys per the AWS page). The topic
must be in the same account; subscriptions must be confirmed. Fragment: `aws_sns_topic.budgets` and
`data.aws_caller_identity.current` are defined elsewhere (see provisioning-aws-sns-v6 and provisioning-aws-iam-v6).

```hcl
# Fragment — references a topic and caller identity defined elsewhere
data "aws_iam_policy_document" "budgets_publish" {
  statement {
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.budgets.arn]
    principals {
      type        = "Service"
      identifiers = ["budgets.amazonaws.com"]
    }
    condition {
      test     = "StringEquals" # example (operator not taken from a page)
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:budgets::${data.aws_caller_identity.current.account_id}:*"]
    }
  }
}
# Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-sns-policy.html
```

AWS: encrypted topics need a KMS key policy that grants Budgets (same page).

## 5. Budget Action

Required: `action_threshold` (`action_threshold_type` `PERCENTAGE` or `ABSOLUTE_VALUE`, `action_threshold_value`),
`action_type` (`APPLY_IAM_POLICY`, `APPLY_SCP_POLICY`, `RUN_SSM_DOCUMENTS`), `approval_model` (`AUTOMATIC` or
`MANUAL`), `budget_name`, `definition`, `execution_role_arn`, `notification_type`, `subscriber`
(`subscription_type` `SNS` or `EMAIL`, `address`). The role is used for execution and reversion; roles and
actions must be in the same account.

```hcl
# Fragment — aws_iam_role.budget_action is defined elsewhere (see provisioning-aws-iam-v6)
resource "aws_budgets_budget_action" "apply_policy" {
  budget_name        = aws_budgets_budget.monthly.name
  action_type        = "APPLY_IAM_POLICY"
  approval_model     = "MANUAL"             # example
  notification_type  = "ACTUAL"
  execution_role_arn = aws_iam_role.budget_action.arn

  action_threshold {
    action_threshold_type  = "PERCENTAGE"
    action_threshold_value = 100            # example
  }

  definition {
    iam_action_definition {
      policy_arn = "arn:aws:iam::123456789012:policy/deny-new-spend" # example
      roles      = ["app-role"]                                       # example
    }
  }

  subscriber {
    subscription_type = "EMAIL"
    address           = "finops@example.com" # example
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget_action.html.markdown
```

SSM variant: `ssm_action_definition` needs `action_sub_type` (`STOP_EC2_INSTANCES` or `STOP_RDS_INSTANCES`),
`instance_ids` and `region`; all three are required.

```hcl
# Fragment — replaces the iam_action_definition block inside definition {}
ssm_action_definition {
  action_sub_type = "STOP_EC2_INSTANCES"
  instance_ids    = ["i-0123456789abcdef0"] # example
  region          = "eu-west-1"             # example: where the SSM document runs, NOT a resource region
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget_action.html.markdown
```

Import: `AccountID:ActionID:BudgetName`. Timeouts: create/update/delete 5m.
