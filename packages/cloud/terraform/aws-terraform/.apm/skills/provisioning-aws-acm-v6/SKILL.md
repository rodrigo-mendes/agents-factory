---
name: provisioning-aws-acm-v6
description: "ACM Terraform (aws 6.x): certificates, DNS validation, imports, private CA, us-east-1 certs for CloudFront. Use when writing HCL for ACM. Not for CloudFront distributions, Route 53 records."
---

# Provisioning AWS ACM with Terraform — hashicorp/aws 6.x

> Version lock: `-v6` = **6.x major line**, reference patch 6.69.0/6.70.0, **Terraform ~> 1.16**.
> Research date **2026-10-22**. Claims tagged (unverified) or (medium confidence) were not fully
> confirmed against an official page.

## Version Context

| Item | Value | Source (fetched 2026-10-22) |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (1.16.6); 1.17.0 stable but not the target | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | latest 6.70.0 (2026-10-23); constraint `~> 6.69`; no 7.x | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | **Withdrawn** — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Region | ACM is regional; optional `region` (default = provider region), change forces replacement, import `id@region` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| Write-only / identity | `private_key_wo` needs Terraform >= 1.11.0; `identity` import needs >= 1.12.0 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown |
| Public cert validity | 198 days | https://docs.aws.amazon.com/acm/latest/userguide/acm-certificate-characteristics.html |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable (2026-10-21), no breaking changes found; it is not the target of this skill.
- 6.57.0 is permanently withdrawn; v7 is planned and not released.

**Version lock:** `-v6` = 6.x major line. A new major (v7) is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Public certificates: [terraform block, DNS validation, CloudFront us-east-1](./blueprints/always-do-public-certificates.md)
- Import/private CA/lookup: [private_key_wo, private CA, data source, import](./blueprints/always-do-import-private-lookup.md)
- Never-do: [state secrets, pinning, CNAMEs, provider traps](./blueprints/never-do-certificates.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `~> 1.16` for the CLI and `~> 6.69` for the provider in root modules**; reusable modules set only a minimum.
  See [public §1](./blueprints/always-do-public-certificates.md#1-terraform-block-and-provider-constraint).
- **Use DNS validation with `aws_route53_record` (`for_each`) plus `aws_acm_certificate_validation`.**
  See [public §2](./blueprints/always-do-public-certificates.md#2-public-certificate-with-dns-validation).
- **Reference `aws_acm_certificate_validation.<n>.certificate_arn` downstream** so consumers wait for issuance.
  See [public §2](./blueprints/always-do-public-certificates.md#2-public-certificate-with-dns-validation).
- **Set `lifecycle { create_before_destroy = true }`** when replacing a certificate that is in use.
  See [public §2](./blueprints/always-do-public-certificates.md#2-public-certificate-with-dns-validation).
- **Tag certificates** (Security Hub ACM.3).
  See [public §2](./blueprints/always-do-public-certificates.md#2-public-certificate-with-dns-validation).
- **Request CloudFront viewer certificates in `us-east-1`** with a provider alias (`region = "us-east-1"` is an alternative (medium confidence)); the matching validation resource must target the same Region (medium confidence).
  See [public §3](./blueprints/always-do-public-certificates.md#3-cloudfront-certificates-in-us-east-1).
- **Use `private_key_wo` + `private_key_wo_version` (not `private_key`) for imports.**
  See [import §4](./blueprints/always-do-import-private-lookup.md#4-imported-certificate-with-private_key_wo).
- **Set `certificate_authority_arn` for private CA certificates; `early_renewal_duration` of 60 days or more.**
  See [import §5](./blueprints/always-do-import-private-lookup.md#5-private-ca-issued-certificate).
- **Use `data.aws_acm_certificate` with `most_recent = true` when several certificates match, and set `key_types` for non-default key types** (`tags` is an exact match; ACM does not return all key types by default).
  See [import §6](./blueprints/always-do-import-private-lookup.md#6-data-source-lookup).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| EMAIL validation | Human action required for issuance and renewal; up to 8 emails per domain, 72h to act; cannot switch to DNS later (delete and recreate). ([source](https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html), [source](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html)) | "Is EMAIL validation required, or can DNS validation be used?" |
| `options { export = "ENABLED" }` | Default `DISABLED`; exportable certificates incur extra charges. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown)) | "Must the certificate be exportable, accepting the extra charge?" |
| `certificate_transparency_logging_preference = "DISABLED"` | Public certificates are logged to public CT logs; not settable on imported certificates. ([source](https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html), [source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown)) | "Confirm disabling CT logging is intended." |
| `allow_overwrite = true` on validation records | Default `false`; provider doc: "not recommended for most environments". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown)) | "Is overwriting existing records intended (e.g. a wildcard and its apex produce an identical CNAME)?" |
| Import-only key algorithms | `RSA_1024`, `RSA_3072`, `RSA_4096`, `EC_secp521r1` can only be imported; ACM requests only `RSA_2048`, `EC_prime256v1`, `EC_secp384r1`. ([source](https://docs.aws.amazon.com/acm/latest/userguide/acm-certificate-characteristics.html)) | "Is an imported certificate with this key algorithm acceptable (no managed renewal)?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `private_key` on an imported certificate — stored in state. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown)) | `private_key_wo` + `private_key_wo_version` |
| Pin ACM certificates — renewal generates a new key pair. ([source](https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html)) | Import your own certificate, or pin to Amazon roots / the private CA root |
| Delete the validation CNAME of an in-use certificate — renewal stops. ([source](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html)) | Keep the `aws_route53_record` resources while the certificate exists |
| Pin `version = "6.57.0"` — withdrawn. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` |
| Request a CloudFront viewer certificate outside `us-east-1`. ([source](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html)) | `provider = aws.us_east_1` (`region = "us-east-1"` is an alternative (medium confidence)) |
| Set `validation_method` on an imported certificate. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown)) | Omit it; use `certificate_body` |

## Quick Reference

Sources fetched 2026-10-22.

| Aspect | Value | Source |
|---|---|---|
| Provider constraint (root) | `~> 6.69` | https://releases.hashicorp.com/terraform-provider-aws/ |
| `aws_acm_certificate` modes | Amazon-issued, imported (`certificate_body`), private CA (`certificate_authority_arn`) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown |
| Default `key_algorithm` when omitted | (unverified) — expected RSA_2048; set it explicitly | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown |
| Issuance wait | `aws_acm_certificate` does not wait; `aws_acm_certificate_validation` `timeouts.create` default 75m | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate_validation.html.markdown |
| `validation_record_fqdns` | DNS-validated certificates only | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate_validation.html.markdown |
| Validation timeout (AWS) | 72 hours (`VALIDATION_TIMED_OUT`) | https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html |
| Renewal (198-day certs) | Criteria checked 45 days before expiry; events at 30, 15, 7, 3, 1 days (ACM user guide; Security Hub ACM.1 text differs) (medium confidence) | https://docs.aws.amazon.com/acm/latest/userguide/dns-renewal-validation.html |
| Imported certificates | Not eligible for managed renewal | https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html |
| Security Hub ACM.1/2/3 | ACM.1 Medium (`daysToExpiration` default 30); ACM.2 High (RSA >= 2048); ACM.3 Low (tagged) | https://docs.aws.amazon.com/securityhub/latest/userguide/acm-controls.html |
| Quotas | 10 domain names per ACM-issued certificate by default (up to 100); 2,500 certificates per Region | https://docs.aws.amazon.com/acm/latest/userguide/acm-limits.html |
| Data source `statuses` default | `ISSUED` only; `most_recent` default `false` (error on multiple matches); `key_types` needed because ACM does not return all key types by default | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/acm_certificate.html.markdown |
| Private CA defaults | `type` `SUBORDINATE`; `usage_mode` `GENERAL_PURPOSE`; deletion window 30 days | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acmpca_certificate_authority.html.markdown |

## 5.x → 6.x Migration (ACM)

The 6.0.0 upgrade guide has **no** `aws_acm_*` or `aws_acmpca_*` entries — no removed or renamed ACM arguments
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-22).

- Enhanced Region Support (`region`) applies to ACM resources.
- 6.47.0 added `private_key_wo` + `private_key_wo_version`; 6.51.0 added the `aws_acm_certificate` list resource and fixed `subject_alternative_names` updates on imported certificates.
- 198-day validity is an AWS service change, not a provider change.
- Upgrade path: set `~> 6.69`, run `terraform init -upgrade`.

## External Resources

All fetched 2026-10-22.

- `aws_acm_certificate`: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown
- `aws_acm_certificate_validation`: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate_validation.html.markdown
- `data.aws_acm_certificate`: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/acm_certificate.html.markdown
- ACM best practices: https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html
- ACM DNS validation: https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html
- Security Hub ACM controls: https://docs.aws.amazon.com/securityhub/latest/userguide/acm-controls.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
