# Never-Do — Region, Deprecated Arguments, Provider and Operations

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 1. Setting region on CloudFront resources

CloudFront is global (no `region` argument, no `@region` import suffix). The ACM certificate and
WAFv2 ACL are not CloudFront resources: they need us-east-1.

```hcl
# WRONG — region on a CloudFront resource; certificate from a non-us-east-1 provider
resource "aws_cloudfront_distribution" "bad" {
  region = "eu-west-1"
  # acm_certificate_arn = aws_acm_certificate.eu.arn   # must be in us-east-1
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown

# CORRECT — no region; certificate created with the us-east-1 alias
resource "aws_acm_certificate" "cf" {
  provider    = aws.us_east_1
  domain_name = "www.example.com"
  validation_method = "DNS"
}
# Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html
```

Certificate lifecycle belongs to provisioning-aws-acm-v6; web ACLs to provisioning-aws-waf-v6.

## 2. forwarded_values

`forwarded_values` is deprecated (not removed in 6.x). Use `cache_policy_id` and/or `origin_request_policy_id`.

```hcl
# WRONG
default_cache_behavior {
  forwarded_values {
    query_string = false
    cookies { forward = "none" }
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown

# CORRECT
default_cache_behavior { cache_policy_id = aws_cloudfront_cache_policy.static.id }
```

## 3. Configuring etag on a response headers policy

`etag` is computed only since 6.0.0: remove any configured value. A policy must be detached from all
distributions before deletion: set `create_before_destroy = true` when both are in one configuration.

```hcl
# WRONG
resource "aws_cloudfront_response_headers_policy" "bad" {
  name = "p"
  etag = "E123"   # computed only since 6.0
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown

# CORRECT — omit etag; add lifecycle { create_before_destroy = true }
```

## 4. Public key without trailing newline

`encoded_key` must end with a newline, otherwise every run plans a recreate.

```hcl
# WRONG
encoded_key = trimspace(file("${path.module}/public.pem"))
# CORRECT
encoded_key = "${trimspace(file("${path.module}/public.pem"))}\n"
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_public_key.html.markdown
```

## 5. Deleting a function still associated, or assuming fast deletes

A function cannot be deleted while associated with a cache behavior. Distribution deletes are blocked
while it deploys (about 15 minutes); `retain_on_delete = true` disables the distribution instead of
deleting it and you must delete it manually. Set `wait_for_deployment = false` only to skip waiting.

## 6. Pins and backend

```hcl
# WRONG
version = "6.57.0"   # withdrawn from GitHub and the Registry
backend "s3" { dynamodb_table = "locks" }   # deprecated
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
# Source: https://developer.hashicorp.com/terraform/language/backend/s3

# CORRECT
version = "~> 6.69"
backend "s3" { use_lockfile = true }
```
