# Never-Do — Certificates (state secrets, pinning, CNAMEs, provider traps)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 1. private_key on an imported certificate

`private_key` is stored in state and conflicts with `private_key_wo`.

```hcl
# WRONG — private key lands in state
resource "aws_acm_certificate" "bad" {
  certificate_body = var.certificate_pem
  private_key      = var.private_key_pem   # WRONG
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown

# CORRECT — write-only argument (Terraform >= 1.11)
resource "aws_acm_certificate" "good" {
  certificate_body       = var.certificate_pem
  private_key_wo         = var.private_key_pem
  private_key_wo_version = 1
}
```

## 2. Pinning ACM certificates

Renewal generates a new key pair, so a pinned certificate breaks at renewal. If pinning is required,
import your own certificate, or pin to Amazon roots / the private CA root. Custom trust stores should
include all Amazon roots (+ Starfield G2). No HCL applies; the fix is outside Terraform.
Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html

## 3. Deleting validation CNAMEs

ACM auto-renews only while the certificate is in use and the CNAME remains; deleting the CNAME stops
renewal. The token works in any Region, so the same record validates replacement and multi-Region
copies.

```hcl
# WRONG — removing the records (e.g. dropping this resource) while the certificate is in use
# resource "aws_route53_record" "validation" { ... }   # deleted

# CORRECT — keep the for_each records for the certificate's lifetime
resource "aws_route53_record" "validation" {
  for_each = {
    for dvo in aws_acm_certificate.this.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }
  zone_id = data.aws_route53_zone.this.zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.record]
}
# Source: https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html
```

## 4. Pinning version 6.57.0

```hcl
# WRONG — withdrawn from GitHub and the Registry
required_providers { aws = { source = "hashicorp/aws", version = "6.57.0" } }   # WRONG

# CORRECT
required_providers { aws = { source = "hashicorp/aws", version = "~> 6.69" } }
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
```

## 5. CloudFront certificate outside us-east-1

```hcl
# WRONG — default provider Region is not us-east-1
resource "aws_acm_certificate" "cf" {
  domain_name       = "cdn.example.com"
  validation_method = "DNS"
}

# CORRECT
resource "aws_acm_certificate" "cf" {
  provider          = aws.us_east_1   # region = "us-east-1" is an alternative (medium confidence)
  domain_name       = "cdn.example.com"
  validation_method = "DNS"
}
# Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html
```

This applies to viewer HTTPS; for CloudFront-to-ELB origin HTTPS any Region works.

## 6. validation_method on an imported certificate

`validation_method` must not be set for imported certificates.

```hcl
# WRONG
resource "aws_acm_certificate" "bad" {
  certificate_body  = var.certificate_pem
  validation_method = "DNS"   # WRONG
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown
```

## 7. Legacy version and backend settings

```hcl
# WRONG — superseded
terraform {
  required_version = ">= 1.7"
  backend "s3" { dynamodb_table = "locks" }   # deprecated
}

# CORRECT — bucket/key/region are placeholders
terraform {
  required_version = "~> 1.16"
  backend "s3" {
    bucket       = "example-state-bucket"
    key          = "acm/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
```
