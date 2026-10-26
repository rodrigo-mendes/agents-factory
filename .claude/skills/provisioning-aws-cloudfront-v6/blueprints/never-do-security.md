# Never-Do — TLS, Viewer Protocol, Origins, OAI

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 1. Relying on the default minimum_protocol_version

The provider default is `TLSv1` (settable only when `cloudfront_default_certificate = false`).
Security Hub CloudFront.15 accepts `TLSv1.2_2021`, `TLSv1.2_2025`, `TLSv1.3_2025` (custom certificates only).
Whether the provider validates the 2025 values is not stated (unverified, U3); AWS supports both.

```hcl
# WRONG — minimum_protocol_version omitted: TLSv1 applies
viewer_certificate {
  acm_certificate_arn = var.certificate_arn
  ssl_support_method  = "sni-only"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown

# CORRECT
viewer_certificate {
  acm_certificate_arn      = var.certificate_arn
  ssl_support_method       = "sni-only"
  minimum_protocol_version = "TLSv1.2_2021"
}
# Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html
```

## 2. allow-all viewer protocol and insecure origin protocols

Violates CloudFront.3 (`allow-all`), CloudFront.9 (`http-only`, or `match-viewer` + `allow-all`) and
CloudFront.10 (`SSLv3` in `origin_ssl_protocols`).

```hcl
# WRONG
default_cache_behavior { viewer_protocol_policy = "allow-all" }
custom_origin_config {
  http_port = 80
  https_port = 443
  origin_protocol_policy = "http-only"
  origin_ssl_protocols = ["SSLv3", "TLSv1.2"]
}
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudfront-controls.html

# CORRECT
default_cache_behavior { viewer_protocol_policy = "redirect-to-https" }
custom_origin_config {
  http_port = 80
  https_port = 443
  origin_protocol_policy = "https-only"
  origin_ssl_protocols = ["TLSv1.2"]
}
```

## 3. OAI for new S3 origins, and OAC on website endpoints

AWS labels OAI "legacy, not recommended": it lacks opt-in Regions, SSE-KMS and `PUT`/`POST`/`DELETE`.
S3 website endpoints cannot use OAC or OAI.

```hcl
# WRONG — OAI path for a new S3 origin
origin {
  domain_name = var.s3_origin_domain_name
  origin_id   = "s3-site"
  s3_origin_config { origin_access_identity = aws_cloudfront_origin_access_identity.old.cloudfront_access_identity_path }
}
# Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html

# CORRECT — OAC (see always-do-origins-policies §3); S3 website endpoint: custom_origin_config instead
origin {
  domain_name              = var.s3_origin_domain_name
  origin_id                = "s3-site"
  origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
}
```

OAI to OAC migration: bucket policy with both statements, switch the origin, remove the OAI statement
after the distribution is fully deployed. OAC `signing_behavior = "never"` requires a public bucket.

## 4. trusted_signers instead of trusted_key_groups

Security Hub CloudFront.17 requires trusted key groups.

```hcl
# WRONG
default_cache_behavior { trusted_signers = ["self"] }
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudfront-controls.html

# CORRECT
default_cache_behavior { trusted_key_groups = [aws_cloudfront_key_group.signers.id] }
```
