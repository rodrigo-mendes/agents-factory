# Never-Do — Bus and Rules (Policy vs Permission, Schedules, is_enabled)

hashicorp/aws 6.x · Terraform ~> 1.16 · Pages read 2026-10-23. Names are `# example` values.

## 1. Bus Policy and Permission on One Bus

Both pages state: "The EventBridge bus policy resource (`aws_cloudwatch_event_bus_policy`) is
incompatible with the EventBridge permission resource (`aws_cloudwatch_event_permission`) and will
overwrite permissions."

```hcl
# FRAGMENT — references aws_cloudwatch_event_bus.orders and a policy document defined elsewhere.
# WRONG — both resources manage the same bus
resource "aws_cloudwatch_event_bus_policy" "bad" {
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  policy         = data.aws_iam_policy_document.bus_access.json
}
resource "aws_cloudwatch_event_permission" "bad" {       # WRONG — overwrites / is overwritten
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  statement_id   = "org-access"                          # example
  principal      = "123456789012"                        # example account ID
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_bus_policy.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_permission.html.markdown

# CORRECT — one resource per bus
resource "aws_cloudwatch_event_bus_policy" "orders" {
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  policy         = data.aws_iam_policy_document.bus_access.json
}
```

## 2. Schedule Expression on a Non-Default Bus

The rule page: `schedule_expression` works only on the default event bus.

```hcl
# FRAGMENT — references aws_cloudwatch_event_bus.orders.
# WRONG — schedule on a custom bus
resource "aws_cloudwatch_event_rule" "bad" {
  name                = "nightly"                         # example
  event_bus_name      = aws_cloudwatch_event_bus.orders.name   # WRONG — not the default bus
  schedule_expression = "rate(1 day)"                     # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown

# CORRECT — default bus (omit event_bus_name), or use Scheduler
resource "aws_cloudwatch_event_rule" "nightly" {
  name                = "nightly"                         # example
  schedule_expression = "rate(1 day)"                     # example
}
```

## 3. is_enabled on a Rule

`is_enabled` is deprecated (not removed), defaults to `true`, and conflicts with `state`.

```hcl
# WRONG — deprecated argument
resource "aws_cloudwatch_event_rule" "bad" {
  name       = "r"                                        # example
  is_enabled = false                                      # WRONG — deprecated
  event_pattern = jsonencode({ source = ["com.example"] }) # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown

# CORRECT
resource "aws_cloudwatch_event_rule" "good" {
  name          = "r"                                     # example
  state         = "DISABLED"
  event_pattern = jsonencode({ source = ["com.example"] }) # example
}
```
