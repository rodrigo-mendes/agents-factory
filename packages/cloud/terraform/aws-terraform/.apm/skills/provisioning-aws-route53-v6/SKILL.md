---
name: provisioning-aws-route53-v6
description: "Route 53 Terraform (aws 6.x, global): zones, records, routing policies, health checks, query logging, DNSSEC, Resolver. Use when writing HCL for Route 53. Not for ACM, CloudFront, VPC."
---

# Provisioning AWS Route 53 with Terraform — hashicorp/aws 6.x

> Version lock: `-v6` = 6.x major line, reference patch 6.69.0/6.70.0 + **Terraform ~> 1.16** only.
> Research date **2026-10-22**. Claims tagged (unverified) or (medium confidence) were not fully
> confirmed against an official page.

## Version Context

| Item | Value | Source (fetched 2026-10-22) |
|---|---|---|
| Terraform CLI | `~> 1.16`; 1.17.0 is stable (2026-10-23) but not the target | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | latest **6.70.0** (2026-10-23); constraint `~> 6.69`; no 7.x | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | **Withdrawn** — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Region model | Route 53 is **global**: `aws_route53_*` and `aws_route53domains_*` take no `region`, no `@region` import | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| Resolver exception | `aws_route53_resolver_endpoint`, `_rule` and `_rule_association` document an optional `region` on their resource pages; the region guide does not classify Resolver (other `aws_route53_resolver_*` resources were not checked) (medium confidence) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_resolver_endpoint.html.markdown |
| 6.0.0 upgrade guide | No Route 53 entries (no removed/renamed arguments) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable since 2026-10-21; this skill stays on `~> 1.16`. Re-verify before moving.
- 6.57.0 is permanently withdrawn; v7 is planned and will be a new skill.

**Version lock:** this skill locks to the **6.x major line** (suffix `-v6`). A new major is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Always-do index: [always-do-patterns](./blueprints/always-do-patterns.md)
- Zones, records, routing, health checks: [always-do-zones-records](./blueprints/always-do-zones-records.md)
- Query logging, DNSSEC, Resolver: [always-do-logging-dnssec](./blueprints/always-do-logging-dnssec.md)
- Never-do index: [never-do-patterns](./blueprints/never-do-patterns.md)
- Never-do zones/records: [never-do-zones-records](./blueprints/never-do-zones-records.md)
- Never-do region/logs/DNSSEC/provider: [never-do-region-logging-dnssec](./blueprints/never-do-region-logging-dnssec.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `~> 1.16` for the CLI and `~> 6.69` for the provider** in root modules; use `use_lockfile = true` on the S3 backend.
  See [zones-records §1](./blueprints/always-do-zones-records.md#1-terraform-block-and-providers).
- **Never set `region` on `aws_route53_*` / `aws_route53domains_*`** — Route 53 is global per the provider region guide
  (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown).
  See [zones-records §1](./blueprints/always-do-zones-records.md#1-terraform-block-and-providers).
- **Use in-line `vpc` blocks for private zones** (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_zone.html.markdown).
  See [zones-records §2](./blueprints/always-do-zones-records.md#2-public-and-private-zones).
- **Keep at least one VPC association on a private zone at all times** (same zone page).
  See [zones-records §2](./blueprints/always-do-zones-records.md#2-public-and-private-zones).
- **Use alias records (not CNAME) for AWS targets** (https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html).
  See [zones-records §3](./blueprints/always-do-zones-records.md#3-records-and-alias-records).
- **Give alias blocks `name`, `zone_id`, `evaluate_target_health` and omit `ttl`** (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown).
  See [zones-records §3](./blueprints/always-do-zones-records.md#3-records-and-alias-records).
- **Split TXT values over 255 chars by inserting `\"\"`** inside the string, e.g. DKIM (same record page).
  See [zones-records §3](./blueprints/always-do-zones-records.md#3-records-and-alias-records).
- **Set `set_identifier` on every routing-policy record** (same record page).
  See [zones-records §4](./blueprints/always-do-zones-records.md#4-routing-policies-and-health-checks).
- **Define a default record for geolocation, geoproximity and latency** (https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html).
  See [zones-records §4](./blueprints/always-do-zones-records.md#4-routing-policies-and-health-checks).
- **Tag health checks** — Security Hub Route53.1 (https://docs.aws.amazon.com/securityhub/latest/userguide/route53-controls.html).
  See [zones-records §4](./blueprints/always-do-zones-records.md#4-routing-policies-and-health-checks).
- **Use 60-120 s TTL on health-checked/failover records** (best-practices page above).
  See [zones-records §4](./blueprints/always-do-zones-records.md#4-routing-policies-and-health-checks).
- **Enable query logging on each public zone** — Security Hub Route53.2 (Security Hub page above).
  See [logging-dnssec §5](./blueprints/always-do-logging-dnssec.md#5-query-logging).
- **Put the query-log group in us-east-1 and allow `route53.amazonaws.com` via a CloudWatch Logs resource policy; `depends_on` it** (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_query_log.html.markdown).
  See [logging-dnssec §5](./blueprints/always-do-logging-dnssec.md#5-query-logging).
- **Set `retention_in_days` on the query-log group** — CloudWatch keeps logs indefinitely by default (https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/query-logs.html).
  See [logging-dnssec §5](./blueprints/always-do-logging-dnssec.md#5-query-logging).
- **Use a customer-managed asymmetric `ECC_NIST_P256` `SIGN_VERIFY` KMS key in us-east-1 for DNSSEC** (https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec-cmk-requirements.html).
  See [logging-dnssec §6](./blueprints/always-do-logging-dnssec.md#6-dnssec).
- **Enable DNSSEC on public zones only** (https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html).
  See [logging-dnssec §6](./blueprints/always-do-logging-dnssec.md#6-dnssec).
- **Create CloudWatch alarms on `DNSSECInternalFailure` and `DNSSECKeySigningKeysNeedingAction`** when DNSSEC is on (DNSSEC page above).
  See [logging-dnssec §6](./blueprints/always-do-logging-dnssec.md#6-dnssec).
- **Set `region` on `aws_route53_resolver_endpoint`, `_rule` and `_rule_association` when needed** — documented on their resource pages; the region guide does not classify Resolver (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_resolver_endpoint.html.markdown) (medium confidence for other Resolver resources).
  See [logging-dnssec §7](./blueprints/always-do-logging-dnssec.md#7-delegation-sets-and-resolver).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| `force_destroy` on a zone | Destroys **all** records on zone destroy, including records managed outside Terraform. | "Should destroying this zone also delete every record in it, including ones created outside Terraform?" |
| `allow_overwrite` on a record | Lets create overwrite an existing record (e.g. auto-created NS/SOA) without import; does not prevent later overwrites; docs: "not recommended for most environments". | "Do you need to overwrite an existing record instead of importing it?" |
| `aws_route53_records_exclusive` | Takes exclusive ownership of a zone's record sets: record sets not explicitly configured are removed; do NOT include the default NS/SOA (persistent drift); every `aws_route53_record` managed alongside needs an equivalent `resource_record_set` block. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_records_exclusive.html.markdown)) | "Should Terraform own every record in this zone exclusively?" |
| `enable_accelerated_recovery` | Default `false`; to turn off, write `false` explicitly — removing the argument is not enough. | "Should accelerated recovery be enabled on this zone?" |
| Zone association vs in-line `vpc` | Docs advise `aws_route53_zone_association` only for explicit association ordering; cross-account needs `aws_route53_vpc_association_authorization`. | "Do you need explicit association ordering or cross-account VPCs?" |
| DNSSEC | You own KSK management/rotation; signing caps record TTL at one week; multi-vendor name servers are unsupported; the parent must support DS records or the child zone becomes unresolvable. | "Is DNSSEC required, and does the parent DNS provider support DS records?" |
| `TF_AWS_ROUTE53_RECORD_BATCH_READS` | Experimental (6.67.0): caches each zone's record set on first read; out-of-band changes are not detected. | "Is this a drift-sensitive pipeline? (If so, leave it unset.)" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `region` on `aws_route53_zone`/`record`/etc. — Route 53 is global. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown)) | Omit `region` on `aws_route53_*` zone and record resources; the Resolver endpoint, rule and rule association pages document `region` |
| Mix in-line `vpc` blocks with `aws_route53_zone_association` for one zone — "perpetual difference in plan output". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_zone.html.markdown)) | Use in-line `vpc` blocks only (workaround: `lifecycle { ignore_changes = [vpc] }`) |
| Combine `alias` with `ttl` or `records`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown)) | Exactly one of `records` or `alias` |
| Omit `set_identifier` on a routing-policy record, or combine two routing policies. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown)) | One policy per record plus `set_identifier` |
| Include the default NS/SOA in `aws_route53_records_exclusive`, or leave a managed `aws_route53_record` without an equivalent `resource_record_set` — persistent drift. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_records_exclusive.html.markdown)) | Exclude default NS/SOA and give each managed record an equivalent `resource_record_set`, or use `aws_route53_record` alone |
| Put the query-log log group outside us-east-1, or log a private zone. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_query_log.html.markdown)) | us-east-1 log group, public zone |
| Enable DNSSEC on a private zone or with a KMS key outside us-east-1. ([source](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html)) | Public zone; us-east-1 `ECC_NIST_P256` key (private zones: Resolver DNSSEC validation) |
| Pin `version = "6.57.0"` — withdrawn. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` |
| S3 backend with `dynamodb_table` — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |

## Quick Reference

Sources fetched 2026-10-22.

| Aspect | Value | Source |
|---|---|---|
| Provider constraint (root) | `~> 6.69` | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| Zone comment default | "Managed by Terraform" | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_zone.html.markdown |
| Record types | A, AAAA, CAA, CNAME, DS, HTTPS, MX, NAPTR, NS, PTR, SOA, SPF, SRV, SSHFP, SVCB, TLSA, TXT | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown |
| Default records | geolocation `country = "*"`; cidr `location_name = "*"` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown |
| Health check types | HTTP, HTTPS, HTTP_STR_MATCH, HTTPS_STR_MATCH, TCP, CALCULATED, CLOUDWATCH_METRIC, RECOVERY_CONTROL | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_health_check.html.markdown |
| Health check `request_interval`/`failure_threshold` defaults | Not stated in provider doc (unverified) — set explicitly | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_health_check.html.markdown |
| Query log limit | 10 CloudWatch Logs resource policies per account/region | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/query-logs.html |
| DNSSEC KSK `status` | `ACTIVE` (default) or `INACTIVE` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_key_signing_key.html.markdown |
| Zone signing `signing_status` | `SIGNING` (default) or `NOT_SIGNING` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_hosted_zone_dnssec.html.markdown |
| Recommended TTL | 60-172,800 s; 3600-86,400 s for NS/MX and rarely-changing records | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html |
| Security Hub Route53.1 | Health checks tagged (Low) | https://docs.aws.amazon.com/securityhub/latest/userguide/route53-controls.html |
| Security Hub Route53.2 | Public zones log DNS queries (Medium) | https://docs.aws.amazon.com/securityhub/latest/userguide/route53-controls.html |
| Record import | `ZONEID_NAME_TYPE` (+ `_SETIDENTIFIER`); identity blocks need Terraform >= 1.12.0 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown ; https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown |

## 5.x → 6.x Migration (Route 53)

([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-22):

- The 6.0.0 upgrade guide has **no Route 53 entries** — no removed/renamed arguments for any `aws_route53_*` resource or data source.
Per the CHANGELOG (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md):

- 6.53.0: changing `type` on `aws_route53_record` no longer forces replacement.
- 6.54.0: new data source `aws_route53profiles_profile`.
- 6.67.0: experimental `TF_AWS_ROUTE53_RECORD_BATCH_READS`.
- 6.70.0: **breaking** import ID format change for `aws_route53domains_delegation_signer_record`.

Upgrade path: set `~> 6.69`, run `terraform init -upgrade`.

## External Resources

All fetched 2026-10-22.

- CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- Enhanced region support: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
- Records exclusive: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_records_exclusive.html.markdown
- Route 53 query logs: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/query-logs.html
- Route 53 DNSSEC: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html
- Route 53 DNS best practices: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html
- Security Hub Route 53 controls: https://docs.aws.amazon.com/securityhub/latest/userguide/route53-controls.html
- Terraform S3 backend: https://developer.hashicorp.com/terraform/language/backend/s3
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
