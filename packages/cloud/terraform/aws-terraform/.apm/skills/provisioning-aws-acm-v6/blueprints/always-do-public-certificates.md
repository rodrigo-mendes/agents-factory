# Always-Do — Public Certificates (Terraform block, DNS validation, CloudFront)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 1. Terraform block and provider constraint

Root modules use `~>`; reusable modules set only a minimum. S3 backend: `use_lockfile = true`
(`dynamodb_table` is deprecated). ACM is regional, so `region` applies.

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
```

## 2. Public certificate with DNS validation

`aws_acm_certificate` does not wait for issuance. `aws_acm_certificate_validation` waits
(`timeouts.create` default 75m). Route 53 is global — the record needs no `provider` alias and no
`region`. Downstream consumers reference the validation resource's `certificate_arn`.

Changing `domain_name`, `subject_alternative_names` or `validation_method` is treated as replacement
(which arguments are ForceNew is not listed on the provider page) (medium confidence).

```hcl
resource "aws_acm_certificate" "this" {
  domain_name       = "app.example.com"
  validation_method = "DNS"
  key_algorithm     = "EC_prime256v1"   # requestable: RSA_2048, EC_prime256v1, EC_secp384r1
  # a data.aws_acm_certificate lookup of this EC certificate must set key_types (see import §6)

  tags = { Name = "app.example.com" }   # Security Hub ACM.3

  lifecycle { create_before_destroy = true }
}

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

resource "aws_acm_certificate_validation" "this" {
  certificate_arn         = aws_acm_certificate.this.arn
  validation_record_fqdns = [for r in aws_route53_record.validation : r.fqdn]
}

resource "aws_lb_listener" "https" {
  # ...
  certificate_arn = aws_acm_certificate_validation.this.certificate_arn   # waits for issuance
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate_validation.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown
```

A wildcard and its apex produce an identical CNAME name/value, which the `for_each` above does not
deduplicate; whether `allow_overwrite = true` is the right fix was not confirmed (medium confidence) —
see the Ask First row on `allow_overwrite` in SKILL.md.

For SANs in other hosted zones, select `zone_id` per domain (the provider doc "alternative domains"
example). `validation_record_fqdns` is valid only for DNS-validated certificates. Keep the CNAME
records while the certificate exists: ACM auto-renews only while the certificate is in use and the
CNAME remains
(https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html).

## 3. CloudFront certificates in us-east-1

For CloudFront viewer HTTPS, request (or import) the certificate in `us-east-1`. Two valid options in
6.x: the classic provider alias, or `region` (Enhanced Region Support); using `region` instead of an
alias is an inference from regional scoping (medium confidence). The matching
`aws_acm_certificate_validation` must target the same Region (medium confidence).

```hcl
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

resource "aws_acm_certificate" "cf" {
  provider          = aws.us_east_1      # classic alias
  # region          = "us-east-1"        # alternative: Enhanced Region Support
  domain_name       = "cdn.example.com"
  validation_method = "DNS"
  lifecycle { create_before_destroy = true }
}

resource "aws_acm_certificate_validation" "cf" {
  provider                = aws.us_east_1   # same Region as the certificate (medium confidence)
  certificate_arn         = aws_acm_certificate.cf.arn
  validation_record_fqdns = [for r in aws_route53_record.cf_validation : r.fqdn]
}
# Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
```

CloudFront with ECDSA: `prime256v1` or `secp384r1`; ACM-issued RSA is up to 2048 (larger must be
imported). The `aws_route53_record.cf_validation` records follow the same `for_each` shape as §2 and
take no alias. Lookups of CloudFront certificates with `data.aws_acm_certificate` query `us-east-1`.
