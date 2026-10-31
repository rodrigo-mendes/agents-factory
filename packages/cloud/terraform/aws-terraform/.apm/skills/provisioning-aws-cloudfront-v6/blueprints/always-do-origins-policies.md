# Always-Do — Origins, OAC, Policies, Functions, Signing

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 3. OAC and S3 bucket policy

Required: `name`, `origin_access_control_origin_type` (`s3` | `lambda` | `mediapackagev2` | `mediastore`),
`signing_behavior` (docs recommend `always`), `signing_protocol = "sigv4"`. S3 Object Ownership must be
Bucket owner enforced. S3 website endpoints cannot use OAC or OAI: configure them as a custom origin.

```hcl
resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = "s3-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"   # guarantees HTTPS to S3
  signing_protocol                  = "sigv4"
}

data "aws_iam_policy_document" "oac_read" {
  statement {
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    actions   = ["s3:GetObject"]            # add s3:PutObject for writes
    resources = ["arn:aws:s3:::${var.bucket_name}/*"]
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "site" {   # regional resource: S3 provider/region applies
  bucket = var.bucket_name
  policy = data.aws_iam_policy_document.oac_read.json
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_origin_access_control.html.markdown
# Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html
```

For SSE-KMS add a KMS key policy statement for the same principal (`kms:Decrypt`, `kms:Encrypt`,
`kms:GenerateDataKey*`) with the same `AWS:SourceArn` condition. Delete the distribution before the
S3 bucket origin. Bucket creation belongs to provisioning-aws-s3-v6.

## 4. Cache, origin request and response headers policies

`default_cache_behavior` takes `cache_policy_id` (preferred) and/or `origin_request_policy_id`.
Cache policy requires `name`, `min_ttl` and `parameters_in_cache_key_and_forwarded_to_origin`
(`cookies_config`, `headers_config`, `query_strings_config`). Managed policy names-to-IDs are not
verified (unverified): look them up with the `aws_cloudfront_cache_policy` data source, do not hardcode IDs.

```hcl
resource "aws_cloudfront_cache_policy" "static" {
  name    = "static-assets"
  min_ttl = 0
  parameters_in_cache_key_and_forwarded_to_origin {
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true
    cookies_config       { cookie_behavior = "none" }
    headers_config       { header_behavior = "none" }
    query_strings_config { query_string_behavior = "none" }
  }
}

resource "aws_cloudfront_response_headers_policy" "security" {
  name = "security-headers"   # etag is computed only since 6.0: never set it
  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000   # example value, not a recommendation
      override                   = true
      include_subdomains         = true       # example value, not a recommendation
    }
    content_type_options { override = true }
    frame_options {
      frame_option = "DENY"
      override     = true
    }
  }
  lifecycle { create_before_destroy = true }   # must detach from distributions before delete
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_cache_policy.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_response_headers_policy.html.markdown
```

Attach with `response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id` in the
behavior. Origin request policy requires `name`, `cookies_config`, `headers_config`, `query_strings_config`.

## 5. Custom origin and origin group

CloudFront.9 fails on `http-only` (and `match-viewer` + `allow-all`); CloudFront.10 fails on `SSLv3`.
`origin_group` needs exactly two `member` blocks (first is primary); it satisfies CloudFront.4.

```hcl
origin {
  domain_name = var.alb_domain_name
  origin_id   = "alb"
  custom_origin_config {
    http_port              = 80
    https_port             = 443
    origin_protocol_policy = "https-only"
    origin_ssl_protocols   = ["TLSv1.2"]
  }
}

origin_group {
  origin_id = "primary-with-failover"
  failover_criteria { status_codes = [500, 502, 503, 504] }   # example value, not a recommendation
  member { origin_id = "alb" }
  member { origin_id = "s3-site" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudfront-controls.html
```

## 6. Functions and signed URLs

`aws_cloudfront_function`: `name` (1-64 chars, `[A-Za-z0-9_-]`), `runtime` (`cloudfront-js-1.0` |
`cloudfront-js-2.0`), `code` (1-40960 bytes per provider; AWS quota unverified (U8)); `publish` default
`true`. Max 2 `function_association` per behavior. Import by `name`.
Prefer `trusted_key_groups` (CloudFront.17) over `trusted_signers`. `encoded_key` of a public key must
end with a newline, otherwise every run plans a recreate.

```hcl
resource "aws_cloudfront_function" "redirect" {
  name    = "viewer-redirect"
  runtime = "cloudfront-js-2.0"
  code    = file("${path.module}/redirect.js")
}

resource "aws_cloudfront_public_key" "signer" {
  name        = "signer"
  encoded_key = "${trimspace(file("${path.module}/public.pem"))}\n"   # must end with a newline
}

resource "aws_cloudfront_key_group" "signers" {
  name  = "signers"
  items = [aws_cloudfront_public_key.signer.id]
}
# in a cache behavior: function_association { event_type = "viewer-request" function_arn = aws_cloudfront_function.redirect.arn }
# in a cache behavior: trusted_key_groups = [aws_cloudfront_key_group.signers.id]
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_function.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_public_key.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_key_group.html.markdown
```
