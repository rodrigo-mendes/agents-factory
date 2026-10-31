# Always-Do — Cost Intelligence (Anomaly Detection, Cost Category, Cost Allocation Tag)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23. All values marked `# example` are placeholders.
These resources are global per the enhanced-region guide (no `region` argument).

## 6. Anomaly Monitor

Required: `name`, `monitor_type` (`DIMENSIONAL` or `CUSTOM`). `monitor_dimension` is required for
`DIMENSIONAL` (`COST_CATEGORY`, `LINKED_ACCOUNT`, `SERVICE`, `TAG`); `monitor_specification` (JSON expression
string) is required for `CUSTOM`.

```hcl
resource "aws_ce_anomaly_monitor" "services" {
  name              = "service-monitor" # example
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_anomaly_monitor.html.markdown
```

Import: monitor ARN, or `identity { arn }` (Terraform >= 1.12).
AWS quotas page: 1 AWS-managed monitor for AWS services per account; 500 customer managed monitors per
management account.
Source: https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html

## 7. Anomaly Subscription

Required: `name`, `frequency` (`DAILY`, `IMMEDIATE` or `WEEKLY`), `monitor_arn_list`, `subscriber`
(`type` `SNS` or `EMAIL`, `address`). Optional: `account_id`, `threshold_expression`, `tags`.
`threshold_expression` operators: `and`, `or`, `not`, `dimension`, `tags`, `cost_category`; the page examples
use the dimension keys `ANOMALY_TOTAL_IMPACT_ABSOLUTE` and `ANOMALY_TOTAL_IMPACT_PERCENTAGE`.

```hcl
resource "aws_ce_anomaly_subscription" "daily" {
  name             = "daily-anomalies" # example
  frequency        = "DAILY"
  monitor_arn_list = [aws_ce_anomaly_monitor.services.arn]

  subscriber {
    type    = "EMAIL"
    address = "finops@example.com" # example
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_anomaly_subscription.html.markdown
```

SNS subscriber: the page's SNS example grants the `Service` principal `costalerts.amazonaws.com` on the topic.
AWS quotas page: 100 alert subscriptions per account; 10 email recipients and 1 SNS topic per subscription.
Sources: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_anomaly_subscription.html.markdown ;
https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html

Import: subscription ARN, or `identity { arn }` (Terraform >= 1.12).

## 8. Cost Category

No HCL: the nested `rule` syntax is on the page. Required: `name`, `rule` (repeatable), `rule_version`.
Optional: `default_value`, `effective_start` (billing start date; defaults to the first day of the current
month), `split_charge_rule` (`parameter` required only for `FIXED`), `tags`.
Import: cost category ARN, or `identity { arn }` (Terraform >= 1.12).

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_cost_category.html.markdown

## 9. Cost Allocation Tag

Required: `tag_key`, `status` (`Active` or `Inactive`). Exports `id` (the key) and `type`. The page notes it
"can take up to 24 hours for the tag keys to appear on Cost Allocation tag page for activation".

```hcl
resource "aws_ce_cost_allocation_tag" "team" {
  tag_key = "team"   # example
  status  = "Active"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_cost_allocation_tag.html.markdown
```

AWS: activation then takes up to a further 24 hours; the bulk API is `UpdateCostAllocationTagsStatus`; the
`awsApplication` tag is activated automatically. Import: tag key.
Source: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/activating-tags.html
