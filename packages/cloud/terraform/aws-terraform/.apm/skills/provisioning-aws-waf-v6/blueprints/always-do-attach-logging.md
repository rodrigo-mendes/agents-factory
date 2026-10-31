# Always-Do — Attach and Log (separate rules, association, logging)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 6. Separate rules on a web ACL

When `aws_wafv2_web_acl_rule` or `aws_wafv2_web_acl_rule_group_association` manage rules, the parent web
ACL must carry `lifecycle { ignore_changes = [rule] }` to prevent drift. The rule resource requires
`name`, `priority`, `statement`, `visibility_config` and `web_acl_arn`. Identity import needs Terraform
>= 1.12.0.

```hcl
resource "aws_wafv2_web_acl" "app" {
  name  = "app"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "app"
    sampled_requests_enabled   = true
  }

  lifecycle {
    ignore_changes = [rule]
  }
}

resource "aws_wafv2_web_acl_rule" "rate" {
  name        = "rate-limit"
  priority    = 20
  web_acl_arn = aws_wafv2_web_acl.app.arn

  action {
    count {} # tune in count mode first
  }

  statement {
    rate_based_statement {
      limit                 = var.rate_limit # >= 10, see always-do-resources §5
      evaluation_window_sec = 300
      aggregate_key_type    = "IP"
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "rate-limit"
    sampled_requests_enabled   = true
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_rule.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown
```

## 7. Web ACL association

Required: `resource_arn`, `web_acl_arn`. Supported: ALB, API Gateway stage (REST only), Cognito User Pool,
AppSync GraphQL API, App Runner service, Amplify application, Bedrock AgentCore Gateway, Verified
Access instance. The create timeout defaults to 5m. AWS limits AssociateWebACL to one call every 2 s
per account/Region, and an association right after creating the web ACL may briefly fail as
"unavailable" while the change propagates.

```hcl
resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = var.alb_arn
  web_acl_arn  = aws_wafv2_web_acl.app.arn
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_association.html.markdown
# Source: https://docs.aws.amazon.com/waf/latest/developerguide/limits.html
```

## 8. Logging configuration

Required: `log_destination_configs` (Firehose, CloudWatch log group or S3 bucket ARN) and `resource_arn`
(web ACL ARN). The destination name must be prefixed with `aws-waf-logs-`. WAFv2 tries to create or
update a generic Log Resource Policy named `AWSWAF-LOGS`; manage a specific resource policy to avoid
CloudWatch Logs policy limits. The research maps Security Hub WAF.11 (logging enabled) to this resource.

```hcl
resource "aws_wafv2_web_acl_logging_configuration" "app" {
  resource_arn            = aws_wafv2_web_acl.app.arn
  log_destination_configs = [var.waf_log_destination_arn] # name starts with aws-waf-logs-

  redacted_fields {
    single_header {
      name = "authorization" # lowercase
    }
  }

  logging_filter {
    default_behavior = "KEEP"

    filter {
      behavior    = "DROP"
      requirement = "MEETS_ANY"

      condition {
        action_condition {
          action = "ALLOW"
        }
      }
    }
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_logging_configuration.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/waf-controls.html
```
