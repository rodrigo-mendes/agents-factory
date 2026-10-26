# Never-Do — Budgets and Region (Region, Conflicts, Operands, Tags, Role)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23. Values marked `# example` are placeholders.

## 1. Region argument on Cost Management resources

Budgets, Billing, Cost Explorer, Cost Optimization Hub, CUR, Data Exports and Savings Plans are global: no
`region` argument and no `@region` import.

```hcl
# WRONG — global service, no region argument
resource "aws_budgets_budget" "bad" {
  name         = "monthly-cost" # example
  budget_type  = "COST"
  time_unit    = "MONTHLY"
  limit_amount = "100"          # example
  limit_unit   = "USD"          # example
  region       = "us-east-1"    # WRONG
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown

# CORRECT — omit region
resource "aws_budgets_budget" "good" {
  name         = "monthly-cost" # example
  budget_type  = "COST"
  time_unit    = "MONTHLY"
  limit_amount = "100"          # example
  limit_unit   = "USD"          # example
}
```

`ssm_action_definition.region`, `s3_region` and the exported Savings Plans `region` attribute are not the resource region.

## 2. Mixing conflicting budget arguments

The `aws_budgets_budget` page documents conflicts: `cost_filter` with `filter_expression`, and `metrics`
with `cost_types`. `filter_expression` requires `metrics`.

```hcl
# WRONG — documented conflicts (fragment, other required arguments omitted)
resource "aws_budgets_budget" "bad" {
  cost_filter {
    name   = "Service"
    values = ["Amazon Elastic Compute Cloud - Compute"] # example
  }
  filter_expression {} # WRONG: conflicts with cost_filter (body omitted)
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown

# CORRECT — one mechanism per pair (fragment)
resource "aws_budgets_budget" "good" {
  cost_filter {
    name   = "Service"
    values = ["Amazon Elastic Compute Cloud - Compute"] # example
  }
  # use cost_types (not metrics) with cost_filter
}
```

## 3. Fewer than two operands in and or or

"`and` and `or` require at least 2 operands", each as its own block. One root per block.

```hcl
# WRONG — and with a single operand (fragment, body omitted)
filter_expression {
  and {
    # only one operand — WRONG
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown

# CORRECT — give 2+ operands, or use a single dimensions/tags/cost_categories root (see the page for block syntax)
```

## 4. Budget tags as cost allocation tags

AWS: "AWS Budgets does not support tags for cost allocation".

```hcl
# WRONG — expecting budget tags to be cost allocation tags
resource "aws_budgets_budget" "bad" {
  name         = "monthly-cost" # example
  budget_type  = "COST"
  time_unit    = "MONTHLY"
  limit_amount = "100"          # example
  limit_unit   = "USD"          # example
  tags         = { team = "payments" } # WRONG as a cost-allocation mechanism
}
# Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html

# CORRECT — activate the tag key
resource "aws_ce_cost_allocation_tag" "team" {
  tag_key = "team" # example
  status  = "Active"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_cost_allocation_tag.html.markdown
```

## 5. Execution role in another account

`execution_role_arn` is used for execution and reversion; roles and actions must be in the same account.

```hcl
# WRONG — role from a different account (fragment, other arguments omitted)
resource "aws_budgets_budget_action" "bad" {
  account_id         = "111111111111"                            # example
  execution_role_arn = "arn:aws:iam::222222222222:role/actions"  # WRONG: example, different account
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget_action.html.markdown

# CORRECT — role in the action's account (fragment)
resource "aws_budgets_budget_action" "good" {
  account_id         = "111111111111"                            # example
  execution_role_arn = "arn:aws:iam::111111111111:role/actions"  # example, same account
}
```
