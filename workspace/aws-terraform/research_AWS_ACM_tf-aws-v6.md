# Research — AWS Certificate Manager (ACM) with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-22**. Status: **COMPLETE** (unit `acm`, P4 fan-out, flat — no sub-agents).
> Registry pages render JS-only (F12); upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`)
> is the authoritative source for resource docs. Shared facts cited by ID from `_family_facts_v6.md`.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_ACM_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL).
> ACM is a **regional** service (not in the F14 global list) — `region` argument applies (F5).

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (1.16.6); 1.17.0 stable but not the target | F1, F2 |
| hashicorp/aws | latest 6.70.0 (2026-10-21); constraint `~> 6.69`; no 7.x | F3; [2] |
| Withdrawn | 6.57.0 — never pin | F4 |
| Region | All in-scope ACM/ACM PCA resources and `data.aws_acm_certificate` accept optional `region` (default = provider region); changing it forces replacement; import `id@region` | F5; [3][4][5][6] |
| Write-only args | `private_key_wo` requires Terraform >= 1.11.0 — satisfied by 1.16 | [3] |
| Identity import | `identity { arn = ... }` requires Terraform >= 1.12.0 — satisfied by 1.16 | F11; [3][6] |
| ACM validity | Public ACM certificates are valid for **198 days** | [8] |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```
Root modules use `~>`; reusable modules set only a minimum (F6). State backend: S3 with `use_lockfile = true`; `dynamodb_table` is deprecated (F7).

## 2. Provider 6.x changes for ACM

6.0.0 upgrade guide (F13) [7]: **no** `aws_acm_*` or `aws_acmpca_*` entries — no removed/renamed ACM arguments in v6. Enhanced Region Support (`region`) applies (F5).

CHANGELOG [2], ACM-scope entries (no breaking changes found):
- 6.47.0 (2026-05-27, pre-range context): `aws_acm_certificate` adds `private_key_wo` + `private_key_wo_version` (#44414).
- 6.51.0 (2026-06-17): new **list resource** `aws_acm_certificate` (#48283); fix `subject_alternative_names` update for **imported** certificates (#48362); `aws_acmpca_certificate_authority` no longer hangs when creating over quota (#48365).
- 6.33.0 (2026-02-18, pre-range context): `aws_acmpca_certificate_authority` (+ data source) add `revocation_configuration.crl_configuration.custom_path` (#46487).
- 6.52.0 → 6.70.0: no ACM/ACM PCA entries found (see L1).

## 3. `aws_acm_certificate`

Source: [3] (2026-10-22). Three mutually distinct modes:

**Amazon-issued (public) certificate**
- `domain_name` (Required); `subject_alternative_names` (Optional).
- `validation_method` (Optional) — `DNS` or `EMAIL`; must **not** be set for imported certificates.
- `key_algorithm` (Optional) — provider doc defers allowed values to ACM. ACM can **request** only `RSA_2048`, `EC_prime256v1`, `EC_secp384r1`; `RSA_1024`, `RSA_3072`, `RSA_4096`, `EC_secp521r1` are **import-only** [8]. Default when omitted: (unverified — expected RSA_2048, see U1).
- `options` block: `certificate_transparency_logging_preference` = `ENABLED` | `DISABLED` (conflicts with `private_key`/`private_key_wo`, i.e. not settable on imported certs); `export` = `ENABLED` | `DISABLED` (default `DISABLED`; exportable certs incur extra charges) [3].
- `validation_option` block: `domain_name` (Required), `validation_domain` (Required; must equal or be a superdomain of `domain_name`) — used with EMAIL validation [3].

**Imported certificate**
- `certificate_body` (Required); `certificate_chain` (Optional).
- `private_key` (Optional) — stored in state; conflicts with `private_key_wo`.
- `private_key_wo` (Optional, write-only, TF >= 1.11) — requires `private_key_wo_version`; bumping `private_key_wo_version` triggers the update [3].
- Imported certs are **not** auto-renewed (NOT ELIGIBLE for managed renewal) [3][9].

**Private CA-issued certificate**
- `certificate_authority_arn` (Required) + `domain_name` (Required); `subject_alternative_names` (Optional).
- `early_renewal_duration` (Optional) — RFC 3339 duration subset (e.g. `P90D`) or Go duration (`2160h`); **no effect if under 60 days**. Private cert default validity 395 days; managed renewal starts 60 days before expiry [3].
- Signing algorithm family must match the CA's key algorithm family (RSA vs ECDSA) [8].

**Common**: `region` (F5); `tags` (provider `default_tags` with matching keys are overridden; `tags_all` exported).

**Attributes**: `id` = `arn`; `domain_name`; `domain_validation_options` (set only for `DNS`; objects with `domain_name`, `resource_record_name`, `resource_record_type`, `resource_record_value`); `not_before`, `not_after`; `status`; `type`; `pending_renewal`; `renewal_eligibility`; `renewal_summary` (`renewal_status`, `renewal_status_reason`); `validation_emails` (EMAIL only) [3].

**Documented notes** [3]:
- The resource **does not wait** for issuance — use `aws_acm_certificate_validation`.
- Set `lifecycle { create_before_destroy = true }` when replacing a certificate that is in use (e.g. by `aws_lb_listener`).
- No `timeouts` section.

**Import**: ID = certificate ARN; `import { id = "<arn>" }` (TF >= 1.5) or `import { identity = { arn = "<arn>" } }` (TF >= 1.12); CLI `terraform import aws_acm_certificate.x <arn>` [3]. Region-qualified import `<arn>@<region>` per F5.

**Immutability (AWS)**: domain names cannot be added to or removed from an existing certificate — a new certificate must be requested [10]. After an EMAIL-validated cert is created it cannot switch to DNS — delete and recreate [11]. Treat `domain_name`/`subject_alternative_names`/`validation_method` changes as replacement (forces-new flags not explicitly listed on the provider page — M1).

## 4. `aws_acm_certificate_validation`

Source: [4] (2026-10-22).
- `certificate_arn` (Required); `region` (Optional, F5).
- `validation_record_fqdns` (Optional) — only valid for DNS-validated certificates; adds sanity checks and an explicit dependency on the validation records.
- **WARNING** (provider doc): implements part of the validation workflow, does **not** represent a real AWS entity; changing/deleting it alone has no immediate effect.
- EMAIL mode: declare only `certificate_arn`; the resource acts as a waiter for manual approval.
- `timeouts { create }` — default **75m**.
- Attribute `id` = time at which the certificate was issued. No import section.
- Pattern: downstream consumers (e.g. `aws_lb_listener`) reference `aws_acm_certificate_validation.<n>.certificate_arn` so they wait for issuance (doc example) [4].

## 5. DNS validation with `aws_route53_record` (for_each)

Pattern from the provider doc example [4] (Route 53 is global per F14 — no `region`, no provider alias needed for the record):

```hcl
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
```
- For SANs in other hosted zones, select `zone_id` per domain (doc "alternative domains" example) [4].
- `allow_overwrite` defaults `false`; provider doc: "not recommended for most environments" [12]. A wildcard and its apex produce an **identical** CNAME name/value [11] — whether the doc example sets `allow_overwrite = true` to handle this was not confirmed (M2).
- AWS: the CNAME must stay in place — ACM auto-renews only while the cert is in use and the CNAME remains; deleting the CNAME stops renewal. The token works in any Region, so the same record validates replacement certs and multi-Region copies. Validation times out after **72 hours** (`VALIDATION_TIMED_OUT`); status may stay pending up to 30 minutes after records are created; CNAME chains > 5 fail [11].
- ACM cannot be asked programmatically to create the Route 53 record itself — create it via Route 53 (here: Terraform) [11].

## 6. CloudFront certificates must be in us-east-1

CloudFront docs [13]: to use an ACM certificate for viewer HTTPS, "request (or import) the certificate in the US East (N. Virginia) Region (`us-east-1`)". For CloudFront→ELB origin HTTPS, any Region works. ECDSA with CloudFront: `prime256v1` or `secp384r1`; RSA up to 4096 (ACM-issued RSA is up to 2048; larger must be imported). One cert across several distributions requires the same "Supported HTTP versions" setting.

Two valid Terraform options in 6.x:
```hcl
provider "aws" { alias = "us_east_1"  region = "us-east-1" }
resource "aws_acm_certificate" "cf" {
  provider          = aws.us_east_1      # classic alias (still supported, F5/pilot)
  # region          = "us-east-1"        # alternative: Enhanced Region Support (F5)
  domain_name       = "cdn.example.com"
  validation_method = "DNS"
  lifecycle { create_before_destroy = true }
}
```
The matching `aws_acm_certificate_validation` must target the same Region (same provider alias or same `region`) (medium confidence — M3, inferred from F5 regional scoping).

HTTP validation exists only via CloudFront Distribution Tenants; such certs are `ManagedBy = CLOUDFRONT` and usable only through CloudFront; HTTP validation does not support wildcards [8].

## 7. `aws_acmpca_certificate_authority` (brief)

Source: [6]. Required `certificate_authority_configuration` (`key_algorithm`, `signing_algorithm`, `subject`). `type` default `SUBORDINATE` (`ROOT`|`SUBORDINATE`); `usage_mode` default `GENERAL_PURPOSE` (`SHORT_LIVED_CERTIFICATE` = 7-day validity); `permanent_deletion_time_in_days` default 30 (7–30); `enabled` default `true`; `key_storage_security_standard` default `FIPS_140_2_LEVEL_3_OR_HIGHER`. New CA is `PENDING_CERTIFICATE` — sign `certificate_signing_request` and install with `aws_acmpca_certificate_authority_certificate`. Import by CA ARN (`id` TF>=1.5 / `identity.arn` TF>=1.12). Quota: 200 private CAs per Region; deleted CAs count until restoration period ends [10b]. CA pricing: (unverified — U2).

## 8. `data "aws_acm_certificate"`

Source: [5]. Arguments: `domain` (optional; error if no match), `statuses` (default **`ISSUED` only**; values `PENDING_VALIDATION`, `ISSUED`, `INACTIVE`, `EXPIRED`, `VALIDATION_TIMED_OUT`, `REVOKED`, `FAILED`), `types` (`AMAZON_ISSUED`, `PRIVATE`, `IMPORTED`), `key_types` (ACM does not return all key types by default), `most_recent` (default `false` → **error if more than one match**; `true` sorts by NotBefore), `tags` (exact match), `region` (F5). Attributes: `arn`/`id`, `status`, `certificate`, `certificate_chain`, `tags`. For CloudFront lookups, query in us-east-1.

## 9. Renewal behavior

- Managed renewal eligibility [9]: ELIGIBLE if associated with an AWS service (ELB, CloudFront…) or exported; private certs via ACM RequestCertificate when exported/associated. NOT ELIGIBLE: private certs issued via AWS Private CA `IssueCertificate`, imported certs, expired certs, ACME-issued certs. ARN stays the same on renewal; certs are regional — same-domain certs in several Regions renew independently.
- DNS-validated [14]: for 198-day certs, ACM checks renewal criteria **45 days** before expiry (cert in use by an AWS service + all CNAMEs publicly resolvable). Older 395-day certs renew 60 days before expiry and receive 198-day validity. If validation fails, AWS Health + EventBridge events at 30, 15, 7, 3 and 1 days before expiry.
- EMAIL-validated: human action required for renewal [15][10].
- Renewal generates a **new key pair** — never pin ACM certificates [10].
- CloudFront with imported certs: renew/reimport at least 24h before `NotAfter`; propagation can take up to 24h [13].

## 10. AWS guidance

### Security Hub CSPM controls [15]
| ID | Title | Severity | Config rule | Parameters |
|---|---|---|---|---|
| ACM.1 | Imported and ACM-issued certificates should be renewed after a specified time period | **Medium** | `acm-certificate-expiration-check` (change-triggered + periodic) | `daysToExpiration` 14–365, default **30** |
| ACM.2 | RSA certificates managed by ACM should use a key length of at least 2,048 bits | **High** | `acm-certificate-rsa-check` | none |
| ACM.3 | ACM certificates should be tagged | **Low** | `tagged-acm-certificate` (custom) | `requiredTagKeys` (1–6 keys, no default) |

ACM.2: ACM-issued RSA is already >= 2048; imported keys < 2048 must be deleted (key length immutable after import). ACM.1 remediation text cites "60 days" DNS check and notices at 45/30/7/1 days — conflicts with the ACM user guide (45 days; events 30/15/7/3/1) — see M4.

### ACM best practices [10]
- Account-level separation (prod certs in separate accounts); otherwise restrict `kms:CreateGrant` (optionally by `kms:EncryptionContext:aws:acm:arn`).
- Ephemeral test environments: use one wildcard cert instead of a cert per environment (quota 2,500 certs/Region; 5,000 requests per 365 days) [10][10b].
- Include all Amazon roots (+ Starfield G2) in custom trust stores.
- Do **not** pin ACM certificates; if pinning is required, import your own cert or pin to Amazon roots / private CA root.
- Prefer DNS validation (email: up to 8 emails per domain, 72h to act).
- Domain name privacy: public certs are logged to public CT logs — no sensitive data in names.
- Turn on CloudTrail before using ACM.
- Quota: 10 domain names per ACM-issued cert by default (up to 100 via increase); not applicable to imported certs [10b].

### Derived Terraform rules (Three-Tier)
- Always: DNS validation + `aws_route53_record` for_each + `aws_acm_certificate_validation`; reference the validation resource's `certificate_arn` downstream; `create_before_destroy = true`; `private_key_wo` (not `private_key`) for imports; CloudFront certs in us-east-1; tags (ACM.3).
- Ask-first: EMAIL validation; `export = ENABLED` (extra cost); `certificate_transparency_logging_preference = DISABLED`; `allow_overwrite = true`; import-only algorithms.
- Never: `private_key` in state; pinning ACM certs; deleting validation CNAMEs of in-use certs; pinning provider 6.57.0.

## 11. Unverified / medium-confidence items and limits

- **U1** Default `key_algorithm` when omitted (provider page defers to ACM; RequestCertificate default RSA_2048 not fetched). (unverified)
- **U2** AWS Private CA monthly price (legacy "$400/month") not fetched. (unverified)
- **U3** Legacy CLI error name "ResourceInUseException" when deleting an in-use cert — not confirmed. (unverified)
- **U4** Legacy Checkov IDs CKV_AWS_233/234 — third-party, outside source hierarchy. (unverified)
- **M1** Which `aws_acm_certificate` arguments are ForceNew is not listed on the doc page; inferred from AWS immutability [10][11]. (medium confidence)
- **M2** Whether the provider example sets `allow_overwrite = true` on validation records — summary did not show it; doc of `allow_overwrite` says not recommended. (medium confidence)
- **M3** Validation resource must be in the same Region as the certificate (inferred from F5). (medium confidence)
- **M4** Renewal timing conflict: Security Hub ACM.1 remediation (60 days; 45/30/7/1) vs ACM user guide (45 days for 198-day certs; 30/15/7/3/1). The ACM user guide is treated as authoritative. (medium confidence)
- **L1** CHANGELOG read in 3 chunks (0–300k chars of ~495k), covering 6.71.0-unreleased → 6.28.0; the 6.54.0/6.55.0 chunk boundary was visible but read with a name filter only.
- **L2** CHANGELOG entries for `aws_route53_record` not reviewed (belongs to the route53 unit).
- **L3** ACME certificate automation (new ACM feature) and CloudFront HTTP validation not covered in Terraform terms.

### Legacy-file claims found wrong or outdated
1. Terraform `>= 1.7` / `~> 6.0` / S3 `dynamodb_table` locking — superseded (F1, F3, F7).
2. "`allow_overwrite = true` is required" — provider doc says default `false`, "not recommended for most environments" [12].
3. Puts `provider = aws.us_east_1` on `aws_route53_record` — Route 53 is global (F14); harmless but unnecessary.
4. "Notable v6 change: 198-day validity" — an AWS service change, not a provider change; and the v6 upgrade guide has no ACM entries [7][8].
5. CloudWatch alarm comment "ACM renewal starts at 45 days" is correct only for 198-day certs; 395-day private certs renew at 60 days [3][14].
6. `key_algorithm` allowlist omits nothing for requests, but legacy implies RSA 3072/4096 are unavailable entirely — they are import-only [8].

## 12. Security note

No prompt-injection or AI-directed instruction text was observed in any fetched page (all fetches 2026-10-22).

## Source Bibliography

All accessed 2026-10-22.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown (via F5/F14)
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acm_certificate_validation.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/acm_certificate.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/acmpca_certificate_authority.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
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
