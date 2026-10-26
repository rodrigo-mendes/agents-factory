# Always-Do — Route 53 Alias, Logging v2, Error Responses

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 7. Route 53 alias to CloudFront

`alias { name, zone_id, evaluate_target_health }` are all required; the block conflicts with `ttl` and
`records`. Public hosted zones only; the record name must be in the distribution's `aliases`. Create A,
plus AAAA when IPv6 is enabled. Evaluate target health: accept the default No. Route 53 is global (no
`region`). Hosted zone management belongs to provisioning-aws-route53-v6.

```hcl
locals {
  # A always; AAAA only when the distribution has is_ipv6_enabled = true
  record_types = toset(concat(["A"], var.ipv6_enabled ? ["AAAA"] : []))
}

resource "aws_route53_record" "cdn" {
  for_each = local.record_types
  zone_id  = var.hosted_zone_id
  name     = "www.example.com"
  type     = each.key
  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id   # Z2FDTNDATAQYW2
    evaluate_target_health = false
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown
# Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-to-cloudfront-distribution.html
```

## 8. Standard logging v2

v2 uses `aws_cloudwatch_log_delivery_source` (`log_type = "ACCESS_LOGS"`, `resource_arn` = distribution
ARN), `aws_cloudwatch_log_delivery_destination` and `aws_cloudwatch_log_delivery`. The delivery API must be
called in us-east-1 (a Firehose destination must also be in us-east-1). Destinations: CloudWatch Logs,
Firehose, S3. Output format is fixed at destination creation; one delivery source per distribution; v2
does not affect legacy logging (use a different bucket or prefix for each); changes take up to 12 hours.
Security Hub CloudFront.5 checks only legacy logging, so v2 alone probably fails it (medium confidence).

```hcl
resource "aws_cloudwatch_log_delivery_source" "cf" {
  provider     = aws.us_east_1
  name         = "cloudfront-main"   # name argument not covered by the research (unverified)
  log_type     = "ACCESS_LOGS"
  resource_arn = aws_cloudfront_distribution.main.arn
}
# aws_cloudwatch_log_delivery_destination and aws_cloudwatch_log_delivery: also with provider = aws.us_east_1;
# their arguments were not researched (unverified)
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
# Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logging.html
```

Legacy V1 (`logging_config.bucket`): the bucket needs a FULL_CONTROL ACL for `awslogsdelivery`;
`prefix` applies to V1 only; `include_cookies` (default false) applies to V1 and V2.

## 9. Custom error responses

`error_code` is required. If you set `response_code` or `response_page_path`, set both.

```hcl
custom_error_response {
  error_code            = 404          # example values below, not a recommendation
  response_code         = 200
  response_page_path    = "/index.html"
  error_caching_min_ttl = 10
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
```
