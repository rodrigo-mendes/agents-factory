# Always-Do — Import, Private CA, Data Source

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 4. Imported certificate with private_key_wo

`private_key_wo` is write-only (Terraform >= 1.11) and requires `private_key_wo_version`; bumping the
version triggers the update. `private_key` is stored in state and conflicts with `private_key_wo`.
Do not set `validation_method` or `options.certificate_transparency_logging_preference` on imported
certificates. Imported certificates are not eligible for managed renewal — re-import before expiry.

```hcl
resource "aws_acm_certificate" "imported" {
  certificate_body       = var.certificate_pem
  certificate_chain      = var.chain_pem
  private_key_wo         = var.private_key_pem
  private_key_wo_version = 1            # bump to push a new key

  tags = { Name = "imported-app" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown
# Source: https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html
```

For CloudFront with imported certificates, renew/reimport at least 24h before `NotAfter`;
propagation can take up to 24h
(https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html).
ACM.2: imported RSA keys under 2048 bits must be deleted (key length is immutable after import).

## 5. Private CA-issued certificate

`certificate_authority_arn` and `domain_name` are required. `early_renewal_duration` accepts an RFC
3339 duration subset (e.g. `P90D`) or a Go duration (`2160h`) and has no effect if under 60 days.
Private certificates default to 395 days validity; managed renewal starts 60 days before expiry. The
signing algorithm family must match the CA key algorithm family (RSA vs ECDSA).

```hcl
resource "aws_acm_certificate" "private" {
  domain_name               = "internal.example.com"
  certificate_authority_arn = aws_acmpca_certificate_authority.this.arn
  early_renewal_duration    = "P90D"

  tags = { Name = "internal.example.com" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown
# Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-certificate-characteristics.html
```

`aws_acmpca_certificate_authority`: required `certificate_authority_configuration` (`key_algorithm`,
`signing_algorithm`, `subject`). A new CA is `PENDING_CERTIFICATE` — sign
`certificate_signing_request` and install with `aws_acmpca_certificate_authority_certificate`.
Quota: 200 private CAs per Region; deleted CAs count until the restoration period ends
(https://docs.aws.amazon.com/acm/latest/userguide/acm-limits.html). The CA arguments above are from
https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acmpca_certificate_authority.html.markdown.

## 6. Data source lookup

`statuses` defaults to `ISSUED` only; `most_recent` defaults to `false`, which errors if more than
one certificate matches (`true` sorts by NotBefore); `tags` is an exact match; `domain` errors if no
match. ACM does not return all key types by default: set `key_types` to find certificates of other
key types (the allowed values are not listed in the research).

```hcl
data "aws_acm_certificate" "this" {
  domain      = "app.example.com"
  types       = ["AMAZON_ISSUED"]
  most_recent = true
  # key_types = [...]   # required to match key types ACM does not return by default
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/acm_certificate.html.markdown
```

## 7. Importing an existing certificate

The import ID is the certificate ARN. Region-qualified import uses `<arn>@<region>`.

```hcl
import {
  id = "arn:aws:acm:eu-west-1:111122223333:certificate/EXAMPLE"   # Terraform >= 1.5
  to = aws_acm_certificate.this
}

import {
  to       = aws_acm_certificate.this
  identity = { arn = "arn:aws:acm:eu-west-1:111122223333:certificate/EXAMPLE" }   # Terraform >= 1.12
}
# CLI: terraform import aws_acm_certificate.this <arn>
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown
```

`aws_acm_certificate_validation` has no import section.
