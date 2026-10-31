# Never-Do — Web ACL (inline rules, rule actions, JSON rules)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 1. Mixing inline rules with separate rule resources

Inline `rule` blocks have known limitations: deletion-ordering errors (a rule must be detached before a
referenced IP set or rule group is deleted), spurious diffs ("AWS returns rules in an unpredictable
order") and coupled updates (modifying one inline rule may recreate all rules). Using
`aws_wafv2_web_acl_rule` or `aws_wafv2_web_acl_rule_group_association` with the same web ACL requires
`ignore_changes = [rule]`.

```hcl
# WRONG — separate rule resource on a web ACL that has no ignore_changes
resource "aws_wafv2_web_acl" "bad" {
  name  = "bad"
  scope = "REGIONAL"
  default_action {
    allow {}
  }
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "bad"
    sampled_requests_enabled   = true
  }
  # WRONG — missing lifecycle { ignore_changes = [rule] }
}
resource "aws_wafv2_web_acl_rule" "bad" {
  name        = "extra"
  priority    = 5
  web_acl_arn = aws_wafv2_web_acl.bad.arn
  # ...
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown

# CORRECT — add to the web ACL
#   lifecycle {
#     ignore_changes = [rule]
#   }
# or keep every rule inline and do not use the separate resources.
```

## 2. Action on a rule-group statement

`action` is only for statements that do not reference a rule group. Rule-group statements use
`override_action`: one of `count` or `none`.

```hcl
# WRONG — action on a managed rule group statement
rule {
  name     = "managed"
  priority = 10
  action {              # WRONG
    block {}
  }
  statement {
    managed_rule_group_statement {
      name        = var.managed_rule_group_name
      vendor_name = var.managed_rule_group_vendor
    }
  }
  # ...
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown

# CORRECT
rule {
  name     = "managed"
  priority = 10
  override_action {
    none {}             # or count {} while tuning
  }
  # statement and visibility_config as in always-do-foundation §2
}
```

## 3. JSON rules and drift

`rule_json` on a web ACL conflicts with `rule` and has "no drift detection at this time". On a rule group
the argument is `rules_json` (not `rule_json`), also conflicting with `rule` and without drift detection.
Importing with `rules_json` set causes a one-time in-place update. `statement` supports 3 levels of
nesting; use `rule_json` for deeper nesting.

```hcl
# WRONG — both rule and rule_json on one web ACL; wrong name on a rule group
resource "aws_wafv2_web_acl" "bad" {
  # ...
  rule_json = file("rules.json")   # WRONG — conflicts with inline rule
  rule {
    name = "inline"                # WRONG
    # ...
  }
}
resource "aws_wafv2_rule_group" "bad" {
  # ...
  rule_json = file("rules.json")   # WRONG — argument is rules_json
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_rule_group.html.markdown

# CORRECT — web ACL: rule_json only; rule group: rules_json only
resource "aws_wafv2_rule_group" "good" {
  # ...
  rules_json = file("rules.json")
}
```
