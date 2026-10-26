# Always-Do — Resources (IP set, rule group, rate-based rule)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 4. IP set and rule group

IP set: `scope` and `ip_address_version` are required; addresses are CIDR (all IPv4/IPv6 ranges except
`/0`), max 10,000 per set. `name`, `scope` and `ip_address_version` force a new resource.

`name` is optional on web ACL, rule group and IP set (a random name is generated if omitted).

Rule group: `capacity` (required) and `scope` force a new resource, so size capacity with headroom up
front (hard max 5,000 WCU per the AWS quota page, not the provider page). The JSON argument is
`rules_json` (no drift detection). Attaching a rule group to a web ACL can be done with
`aws_wafv2_web_acl_rule_group_association` (see Coverage Limits L4).

```hcl
resource "aws_wafv2_ip_set" "blocked" {
  name               = "blocked-ips"
  scope              = "REGIONAL"
  ip_address_version = "IPV4"
  addresses          = var.blocked_cidrs # CIDR notation; no /0
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_ip_set.html.markdown

resource "aws_wafv2_rule_group" "custom" {
  name     = "custom-rules"
  scope    = "REGIONAL"
  capacity = var.rule_group_capacity # immutable: size with headroom

  rule {
    name     = "block-listed-ips"
    priority = 1

    action {
      block {}
    }

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.blocked.arn
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "block-listed-ips"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "custom-rules"
    sampled_requests_enabled   = true
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_rule_group.html.markdown
# Source: https://docs.aws.amazon.com/waf/latest/developerguide/limits.html
```

## 5. Rate-based rule

`limit` is required; the AWS minimum is 10. `evaluation_window_sec` is one of 60, 120, 300, 600
(default 300) and `aggregate_key_type` defaults to `IP`. The window is how far back WAF looks, not how
often it checks. The `limit` bounds (minimum 10) come from the AWS quota page, not the provider page. A
rule group allows 4 rate-based rules; a web ACL allows 10. Use `rate_based_statement` at the top level
of a rule; it cannot be nested.

```hcl
variable "rate_limit" {
  type = number
  validation {
    condition     = var.rate_limit >= 10
    error_message = "AWS WAF rate-based rule limit minimum is 10."
  }
}

# Statement fragment, used inside a rule (see always-do-attach-logging §6)
statement {
  rate_based_statement {
    limit                 = var.rate_limit
    evaluation_window_sec = 300
    aggregate_key_type    = "IP"
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown
# Source: https://docs.aws.amazon.com/waf/latest/developerguide/limits.html
```
