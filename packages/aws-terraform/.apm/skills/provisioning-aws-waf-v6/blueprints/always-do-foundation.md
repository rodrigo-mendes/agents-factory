# Always-Do — Foundation (Terraform block, Web ACL, CLOUDFRONT scope)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 1. Terraform block and providers

Root modules use `~>` for providers. Use `use_lockfile = true` on the S3 backend (`dynamodb_table`
is deprecated). The us-east-1 alias is only needed for `scope = "CLOUDFRONT"`.

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
    bucket       = "example-tfstate"          # placeholder, no claim
    key          = "waf/terraform.tfstate"    # placeholder, no claim
    region       = "eu-west-1"                # placeholder, no claim
    use_lockfile = true
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints

provider "aws" {
  region = var.region # placeholder variable, no claim
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown
```

## 2. Regional web ACL

`default_action`, `scope` and `visibility_config` are required; `scope` forces a new resource. A managed
rule group uses `override_action`, not `action`. Start in count mode, then switch to `none {}` after
tuning with production traffic. Do not hard-code WCU numbers of managed groups.

```hcl
resource "aws_wafv2_web_acl" "regional" {
  name  = "app-regional"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "managed-baseline"
    priority = 10 # lower numbers are evaluated first

    override_action {
      count {} # tune first; later: none {}
    }

    statement {
      managed_rule_group_statement {
        name        = var.managed_rule_group_name
        vendor_name = var.managed_rule_group_vendor
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "managed-baseline"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "app-regional"
    sampled_requests_enabled   = true
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown
# Source: https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-testing.html
```

The `capacity` attribute reports the WCUs in use; read it to track the web ACL budget.

## 3. CLOUDFRONT scope

CLOUDFRONT-scope resources need the provider on us-east-1. The CloudFront distribution takes the ACL
ARN through `web_acl_id` — never through an association. Setting `region = "us-east-1"` on the WAF
resource instead of the alias is an inference from the `region` model (medium confidence).

```hcl
resource "aws_wafv2_web_acl" "cloudfront" {
  provider = aws.us_east_1
  name     = "app-cloudfront"
  scope    = "CLOUDFRONT"

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "app-cloudfront"
    sampled_requests_enabled   = true
  }
}

resource "aws_cloudfront_distribution" "site" {
  # ... distribution arguments: see provisioning-aws-cloudfront-v6
  web_acl_id = aws_wafv2_web_acl.cloudfront.arn
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
# Source: https://docs.aws.amazon.com/waf/latest/APIReference/API_CreateWebACL.html
```
