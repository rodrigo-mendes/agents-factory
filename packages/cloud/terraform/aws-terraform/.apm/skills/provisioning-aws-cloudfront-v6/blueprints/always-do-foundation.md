# Always-Do — Foundation (Terraform Block, us-east-1 Alias, Distribution)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 1. Terraform block and providers

CloudFront resources take no `region` argument (global service). Dependencies outside CloudFront
(ACM certificate for viewers, WAFv2 web ACL with `scope = "CLOUDFRONT"`, CloudWatch Logs delivery
for standard logging v2) need us-east-1: use an `aws.us_east_1` provider alias, or the resource's
own `region = "us-east-1"` (the alias-vs-region choice for WAFv2 is an inference, (medium confidence)).
The documented fact: WAFv2 scope `CLOUDFRONT` requires the provider to target us-east-1.
Certificate lifecycle: see provisioning-aws-acm-v6.

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
    bucket       = "my-tf-state"
    key          = "cloudfront/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true   # S3-native lock; dynamodb_table is deprecated
    encrypt      = true
  }
}

provider "aws" {
  region = "eu-west-1"   # regional dependencies (e.g. the S3 origin bucket)
}

provider "aws" {
  alias  = "us_east_1"   # ACM (viewer cert), WAFv2 CLOUDFRONT scope, logging v2
  region = "us-east-1"
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
```

Commit `.terraform.lock.hcl` (providers only). Root modules use `~>`; reusable modules set a minimum.

## 2. Distribution with S3 origin and OAC

Required blocks: `enabled`, `origin`, `default_cache_behavior`, `restrictions`, `viewer_certificate`.
Set `is_ipv6_enabled` and `price_class` explicitly (defaults not stated, (unverified)).
Set `minimum_protocol_version` explicitly: the provider default is `TLSv1`.

```hcl
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true            # default not stated (unverified); set explicitly
  comment             = "static site"
  default_root_object = "index.html"    # Security Hub CloudFront.1 (S3 origins)
  http_version        = "http2and3"      # allowed: http1.1, http2, http2and3, http3; default http2
  price_class         = "PriceClass_100" # example value, not a recommendation; default not stated (unverified)
  aliases             = var.aliases      # each must be covered by a SAN in the certificate
  web_acl_id          = var.web_acl_arn  # WAFv2: the ARN (aws_wafv2_web_acl.x.arn), not the ID

  origin {
    domain_name              = var.s3_origin_domain_name
    origin_id                = "s3-site"
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id   # no s3_origin_config
  }

  default_cache_behavior {
    target_origin_id       = "s3-site"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    viewer_protocol_policy = "redirect-to-https"   # CloudFront.3: no allow-all
    cache_policy_id        = aws_cloudfront_cache_policy.static.id
    compress               = true                  # default false
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
      locations        = []   # required; [] allowed when type is none
    }
  }

  viewer_certificate {
    acm_certificate_arn      = var.certificate_arn   # must be in us-east-1
    ssl_support_method       = "sni-only"            # CloudFront.8
    minimum_protocol_version = "TLSv1.2_2021"        # explicit; provider default is TLSv1
  }

  tags = { Name = "static-site" }   # CloudFront.14 (or provider default_tags)
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudfront-controls.html
```

Creation or modification takes about 15 minutes to reach Deployed; deletes are blocked meanwhile.
`wait_for_deployment` defaults to `true`. Attributes: `arn`, `domain_name`, `hosted_zone_id`
(always `Z2FDTNDATAQYW2`), `etag`, `status`. Import by distribution ID (`import` block or
`terraform import`); `identity` import needs Terraform >= 1.12.
