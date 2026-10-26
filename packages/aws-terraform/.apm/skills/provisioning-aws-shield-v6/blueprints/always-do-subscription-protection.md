# Always-Do — Subscription, Protections, Protection Groups

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. Terraform Block and Subscription

Shield Advanced is global: no `region` on any `aws_shield_*` resource and no `@region` import.
Subscribe each account you want to protect; Shield Standard needs no subscription.
Subscribing requires a 1 year commitment with a monthly fee — get approval first (see Ask First).

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
    bucket       = "my-tf-state"              # placeholder
    key          = "shield/terraform.tfstate" # placeholder
    region       = "eu-west-1"                # placeholder
    use_lockfile = true   # dynamodb_table is deprecated
    encrypt      = true                       # placeholder
  }
}

resource "aws_shield_subscription" "this" {
  auto_renew = "ENABLED"   # default; ENABLED | DISABLED
  # Inference from destroy semantics (medium confidence), only after approval:
  # skip_destroy = true
  # lifecycle { prevent_destroy = true }
}
```

Destroy sets `auto_renew = DISABLED`, which AWS permits only in the last 30 days; to unsubscribe
outside that window contact AWS Support. Import: `import { to = aws_shield_subscription.this, id = "<account-id>" }`.

Sources:
- https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_subscription.html.markdown
- https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
- https://developer.hashicorp.com/terraform/language/backend/s3

## 2. Protections

Shield Advanced does not protect resources automatically. Supported on the provider page:
CloudFront distributions, Elastic Load Balancing load balancers, Global Accelerator accelerators,
Elastic IP addresses, Route 53 hosted zones. Per AWS, an NLB is protected only through its Elastic
IP association, so use the EIP allocation ARN.

```hcl
data "aws_partition" "current" {}
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

resource "aws_shield_protection" "cdn" {
  name         = "cdn"
  resource_arn = aws_cloudfront_distribution.main.arn
  tags         = { Name = "cdn" }
}

resource "aws_shield_protection" "nlb_eip" {
  name         = "nlb-eip"
  resource_arn = "arn:${data.aws_partition.current.partition}:ec2:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:eip-allocation/${aws_eip.nlb.id}"
}
```

`data.aws_region.current.region` is used because `name` is deprecated since 6.0. Import uses the
protection `id`. The resource exports `id` and `arn`.

Sources:
- https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection.html.markdown
- https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html
- https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown

## 3. Protection Groups

`protection_group_id`, `aggregation` and `pattern` are required. `members` is required when
`pattern = "ARBITRARY"` and must not be set otherwise; `resource_type` is required when
`pattern = "BY_RESOURCE_TYPE"` and must not be set otherwise. Enum values below come from the
page examples only (medium confidence).

```hcl
resource "aws_shield_protection_group" "arbitrary" {
  protection_group_id = "web-tier"
  aggregation         = "MAX"          # examples: MAX, MEAN, SUM
  pattern             = "ARBITRARY"    # examples: ALL, ARBITRARY, BY_RESOURCE_TYPE
  members             = [aws_shield_protection.cdn.resource_arn]
}

resource "aws_shield_protection_group" "eips" {
  protection_group_id = "all-eips"
  aggregation         = "SUM"
  pattern             = "BY_RESOURCE_TYPE"
  resource_type       = "ELASTIC_IP_ALLOCATION"
}
```

Exports `protection_group_arn` and `tags_all`; import by `protection_group_id`.

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection_group.html.markdown
