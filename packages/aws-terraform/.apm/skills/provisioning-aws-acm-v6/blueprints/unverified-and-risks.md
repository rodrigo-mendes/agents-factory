# Unverified Claims and Risks — hashicorp/aws 6.x ACM

Research date 2026-10-22. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** (latest 6.70.0, 2026-10-21; constraint `~> 6.69`).
  Re-verify when starting new work. Source: https://releases.hashicorp.com/terraform-provider-aws/
- **Terraform 1.17.0 is stable (2026-10-21)** with no breaking changes found; this skill targets
  `~> 1.16` (1.16.6). Source: https://releases.hashicorp.com/terraform/
- **6.57.0 is permanently withdrawn**. Any constraint resolving to it fails `terraform init`.
- **v7 is planned**, not released. When v7 ships, create a new skill `provisioning-aws-acm-v7`.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Default `key_algorithm` when omitted — provider page defers to ACM; RequestCertificate default not fetched | (unverified) — expected RSA_2048; set it explicitly |

No I items (no items inferred beyond the research). Legacy-file claims not carried over (private CA
price, CLI error name, Checkov IDs) were unverified in research and are omitted from the skill.

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | Which `aws_acm_certificate` arguments are ForceNew is not listed on the doc page; inferred from AWS immutability | (medium confidence) |
| M2 | Whether the provider example sets `allow_overwrite = true` on validation records — not confirmed | (medium confidence) |
| M3 | Validation resource must be in the same Region as the certificate — inferred from regional scoping | (medium confidence) |
| M5 | Using `region = "us-east-1"` instead of a provider alias for CloudFront certificates — inference from regional scoping (same basis as the WAFv2 scope-CLOUDFRONT rule) | (medium confidence) |
| M4 | Renewal timing conflict: Security Hub ACM.1 remediation (60 days; notices 45/30/7/1) vs ACM user guide (45 days for 198-day certificates; events 30/15/7/3/1). The ACM user guide is treated as authoritative | (medium confidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG read in 3 chunks (0–300k chars of ~495k), 6.71.0-unreleased → 6.28.0; 6.54.0/6.55.0 chunk boundary read with a name filter only |
| L2 | CHANGELOG entries for `aws_route53_record` not reviewed (route53 unit) |
| L3 | ACME certificate automation and CloudFront HTTP validation not covered in Terraform terms |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Quick Reference — default `key_algorithm` row | U1 |
| (medium confidence) | SKILL.md Quick Reference — renewal (198-day certs) row | M4 |
| (medium confidence) | always-do-public-certificates.md §2 — ForceNew arguments | M1 |
| (medium confidence) | always-do-public-certificates.md §3 — validation in the same Region (text and HCL comment) | M3 |
| (medium confidence) | SKILL.md Always Do — CloudFront bullet, same-Region validation | M3 |
| (medium confidence) | always-do-public-certificates.md §2 — `allow_overwrite` fix for wildcard + apex | M2 |
| (medium confidence) | always-do-public-certificates.md §3; never-do-certificates.md §5; SKILL.md Always Do and Never Do CloudFront rows — `region` alternative | M5 |

## Source Bibliography

All fetched 2026-10-22. Numbers match the unit research bibliography.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — region; global services
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.57.0 withdrawn; ACM entries
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate_validation.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/acm_certificate.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acmpca_certificate_authority.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — no ACM entries
8. https://docs.aws.amazon.com/acm/latest/userguide/acm-certificate-characteristics.html
9. https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html
10. https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html
10b. https://docs.aws.amazon.com/acm/latest/userguide/acm-limits.html
11. https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown
13. https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html
14. https://docs.aws.amazon.com/acm/latest/userguide/dns-renewal-validation.html
15. https://docs.aws.amazon.com/securityhub/latest/userguide/acm-controls.html
16. https://docs.aws.amazon.com/acm/latest/userguide/renew-publicly-trusted.html
17. https://releases.hashicorp.com/terraform/ and https://releases.hashicorp.com/terraform-provider-aws/ — versions
18. https://developer.hashicorp.com/terraform/language/backend/s3 and https://developer.hashicorp.com/terraform/language/expressions/version-constraints
