# Always-Do — Sampling Rules and Groups

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23.

## 3. Sampling Rule

Provider page (Required: `priority`, `reservoir_size`, `fixed_rate`, `host`, `http_method`,
`url_path`, `service_name`, `service_type`, `resource_arn`, `version`; `rule_name` is Optional, and is the
resource `id` and import ID):
https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_sampling_rule.html.markdown

AWS statements (https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html and
https://docs.aws.amazon.com/xray/latest/api/API_SamplingRule.html):

- Priority range 1–9999; services evaluate rules in ascending order and use the first match.
- `fixed_rate` is a double 0–1 in the API (the console shows 0–100 %).
- String fields accept `*` (zero or more characters) and `?` (one character).
- The X-Ray SDK only uses rules whose `resource_arn` is `*`; the X-Ray SDK ignores rules that specify `attributes`.
- The sampling decision is made once, typically by the first X-Ray-enabled service; a rule for a downstream service
  "will likely never be applied" — put rules on the root service.
- Default rule: priority 10000, reservoir 1, fixed rate 0.05, lowest priority, cannot be deleted
  (https://docs.aws.amazon.com/xray/latest/devguide/xray-api-configuration.html).

```hcl
resource "aws_xray_sampling_rule" "checkout" {
  rule_name      = "checkout-api" # example
  priority       = 100            # example; 1-9999
  version        = 1              # sampling rule format version
  reservoir_size = 1              # example; requests/second before the fixed rate
  fixed_rate     = 0.05           # example; fraction 0-1
  host           = "*"            # example; wildcard
  http_method    = "*"            # example; wildcard
  url_path       = "/checkout/*"  # example
  service_name   = "checkout"     # example
  service_type   = "*"            # example; wildcard
  resource_arn   = "*"            # example; wildcard
}
```

Limits and uniqueness questions are in the Ask First table of SKILL.md.

## 4. Group

Provider page: Required `group_name`, `filter_expression`; Optional `insights_configuration`
(`insights_enabled` required, `notifications_enabled` optional), `tags`, `region`; exports `arn`, `id`
(= ARN), `tags_all`; import by ARN
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_group.html.markdown).

AWS (https://docs.aws.amazon.com/xray/latest/devguide/xray-console-groups.html): group name max 32
characters, alphanumeric and dashes, case sensitive; groups cannot be renamed; the Default group
cannot be deleted. Insights notifications go to EventBridge, which "does not currently support customer
managed keys" (https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html).

```hcl
resource "aws_xray_group" "errors" {
  group_name        = "checkout-errors"                # example
  filter_expression = "<your X-Ray filter expression>" # placeholder; syntax is not covered by this skill

  insights_configuration {
    insights_enabled      = true  # example
    notifications_enabled = false # example
  }
}
```

Import on Terraform ≥ 1.12.0 uses an `identity { arn }` block; `id = <ARN>` works on Terraform ≥ 1.5
(provider page above).
