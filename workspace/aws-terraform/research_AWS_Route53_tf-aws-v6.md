# Research — AWS Route 53 with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-22**. Status: **COMPLETE** (unit `route53`, P4 fan-out, flat, no sub-agents).
> Sources: upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`) (F12), the provider
> CHANGELOG, `docs.aws.amazon.com`. Shared facts cited by ID from `_family_facts_v6.md`.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_Route53_aws-v6.x.md` (6.47.0, Terraform 1.7, EOL).

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (1.17.0 stable but not the target) | F1, F2 |
| hashicorp/aws | latest 6.70.0 (2026-10-21); constraint `version = "~> 6.69"`; no 7.x | F3; [3] (CHANGELOG top: 6.71.0 Unreleased, 6.70.0 October 21, 2026) |
| Withdrawn | 6.57.0 — never pin | F4 |
| Region model | **Route 53 is GLOBAL**: `aws_route53_*` and `aws_route53domains_*` take no `region` argument, no `@region` import. Route 53 ARC is also global | F14; [12] |
| Exception (Resolver) | `aws_route53_resolver_endpoint` and `aws_route53_resolver_rule_association` docs list an optional `region` argument ("Defaults to the provider's Region"); `aws_route53_resolver_rule` identity has optional `region`. Resolver is regional despite the `aws_route53_*` prefix — see M1 | [9] [10] [11] |
| Identity import | `identity` blocks need Terraform ≥ 1.12.0 (satisfied by 1.16) | F11 |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
provider "aws" { region = var.region }
# Needed only for us-east-1-pinned dependencies (query-log log group, DNSSEC KMS key).
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}
```
Note: with 6.x Enhanced Region Support, a regional resource (`aws_kms_key`, `aws_cloudwatch_log_group`,
`aws_cloudwatch_log_resource_policy`) may instead set `region = "us-east-1"` without an alias (F5).
The provider docs' own examples still use a provider alias [4][5]; both are valid. Route 53 resources
themselves never get `region` (F14).

## 2. Provider 6.x changes for Route 53

6.0.0 upgrade guide (F13): **no Route 53 entries** — no removed/renamed arguments for any
`aws_route53_*` resource or data source [13].

CHANGELOG 6.48.0 → 6.70.0, Route 53 scope [3]:
- **6.53.0** (2026-07-01) `aws_route53_record`: bug fix — changing `type` no longer forces replacement (#47105).
- **6.54.0** (2026-07-08) new data source `aws_route53profiles_profile` (#48780).
- **6.59.0** `aws_route53domains_registered_domain`: `UpdateDomainContactPrivacy` no longer triggered on `billing_contact` change (#49314).
- **6.67.0** `aws_route53_record`: new env var `TF_AWS_ROUTE53_RECORD_BATCH_READS` (experimental batched/cached reads) (#48525).
- **6.70.0** `aws_route53domains_delegation_signer_record`: **breaking** change to import ID format; fix for null Flags/PublicKey on `.uk`/`.co.uk` (#50522). Out of core scope, but relevant for DS records at a Route 53 Domains registrar.
- No Route 53 entries in 6.48.0–6.52.0, 6.55.0–6.58.0, 6.60.0–6.66.0, 6.68.0, 6.69.x (see L1).

## 3. `aws_route53_zone` [1]

- Required: `name`.
- Optional: `comment` (default **"Managed by Terraform"**); `delegation_set_id` (conflicts with `vpc` — delegation sets are public-only); `enable_accelerated_recovery` (default `false`; to turn off, explicitly write `false`, removing the argument is not enough); `force_destroy` (destroys **all** records on zone destroy, including records managed outside Terraform); `tags`; `vpc` blocks (`vpc_id` required, `vpc_region` optional, defaults to provider region).
- A zone with at least one `vpc` block is private. "Private zones require at least one VPC association at all times."
- **WARNING**: in-line `vpc` blocks and `aws_route53_zone_association` for the same zone ID cannot be mixed — "otherwise it will cause a perpetual difference in plan output". Workaround: `lifecycle { ignore_changes = [vpc] }`.
- Subdomain delegation needs an `NS` `aws_route53_record` in the parent zone plus the subdomain zone.
- Attributes: `arn`, `zone_id`, `name_servers`, `primary_name_server`, `tags_all`.
- Timeouts: create/update/delete 30m.
- Import: zone ID (`terraform import aws_route53_zone.x Z123...`); identity (≥1.12): `zone_id` required, `account_id` optional.

## 4. `aws_route53_zone_association` [6]

- Required: `zone_id`, `vpc_id`. Optional: `vpc_region` (defaults to provider region). Attributes: `id`, `owning_account`. Timeouts create/delete 30m.
- Private zones only. Docs advise against this resource "unless you need explicit association ordering"; prefer in-line `vpc` blocks.
- Cross-account: use `aws_route53_vpc_association_authorization`.
- Import: `ZONE_ID:VPC_ID`, or `ZONE_ID:VPC_ID:REGION` when the VPC is in another region; identity: `zone_id`, `vpc_id` (+ optional `vpc_region`, `account_id`).

## 5. `aws_route53_record` [2]

- Required: `zone_id`, `name`, `type` (A, AAAA, CAA, CNAME, DS, HTTPS, MX, NAPTR, NS, PTR, SOA, SPF, SRV, SSHFP, SVCB, TLSA, TXT).
- **Alias vs records**: `alias` conflicts with `ttl` and `records`; exactly one of `records` or `alias`. Non-alias records need `ttl` + `records`. Alias block requires `name`, `zone_id`, `evaluate_target_health`. Alias TTL is fixed (60 s per provider doc) — omit `ttl`.
- TXT values > 255 chars (e.g. DKIM): insert `\"\"` inside the string to split.
- `allow_overwrite` (default `false`): lets create overwrite an existing record (e.g. the zone's auto-created NS/SOA) without import; does not prevent later overwrites; docs: "not recommended for most environments".
- `set_identifier`: required with any of `cidr`, `failover`, `geolocation`, `geoproximity`, `latency`, `multivalue_answer`, `weighted`. Each routing policy conflicts with every other one.
  - `weighted_routing_policy { weight }`
  - `latency_routing_policy { region }`
  - `failover_routing_policy { type = "PRIMARY" | "SECONDARY" }`
  - `geolocation_routing_policy { continent | country (+ subdivision) }` — `country = "*"` is the default record
  - `geoproximity_routing_policy { aws_region | coordinates{latitude,longitude} | local_zone_group, bias (-90..90) }`
  - `cidr_routing_policy { collection_id, location_name }` — `location_name = "*"` is the default
  - `multivalue_answer_routing_policy = true` (boolean, not a block)
- `health_check_id`: optional health check associated with the record.
- Timeouts: create/update/delete 30m.
- Import: `ZONEID_NAME_TYPE` (+ `_SETIDENTIFIER`); empty name → `ZONEID__TYPE`. Identity: `zone_id`, `name`, `type` required; `account_id`, `set_identifier` optional.
- Experimental (6.67.0): `TF_AWS_ROUTE53_RECORD_BATCH_READS=true` caches each zone's record set on first read — out-of-band changes after caching "will not be detected"; no backward-compatibility guarantee. Do not enable for drift-sensitive pipelines.
- Related: `aws_route53_records_exclusive` [14] takes exclusive ownership of a zone's record sets (unlisted sets removed on apply; exclude default NS/SOA or get persistent drift; every `aws_route53_record` in the zone must be mirrored or it drifts; destroying it does not delete records; timeouts 45m; import by `zone_id`).

## 6. `aws_route53_health_check` [7]

- Required: `type` (`HTTP`, `HTTPS`, `HTTP_STR_MATCH`, `HTTPS_STR_MATCH`, `TCP`, `CALCULATED`, `CLOUDWATCH_METRIC`, `RECOVERY_CONTROL`). Endpoint checks need `fqdn` or `ip_address` (with `ip_address`, `fqdn` is sent as `Host`).
- `request_interval`, `failure_threshold`: no default stated in provider doc (U1).
- `regions`: omitted = all valid regions; once set, removing it has no effect.
- `enable_sni`: default `true` for `HTTPS`, `false` otherwise.
- `cloudwatch_alarm_name` / `cloudwatch_alarm_region`, `insufficient_data_health_status` (`Healthy`|`Unhealthy`|`LastKnownStatus`), `child_healthchecks` (CALCULATED), `triggers` (forces in-place update of alarm args).
- Disabled health checks are always treated as healthy — use `invert_healthcheck` to stop routing.
- Import: health check ID (UUID).

## 7. `aws_route53_query_log` [4][15]

- Required: `zone_id`, `cloudwatch_log_group_arn`. Attributes: `arn`, `id`. Import: config ID.
- Constraints: log group **must be in us-east-1**; hosted zone **must be public** (public DNS query logging); a CloudWatch Logs resource policy must allow principal `route53.amazonaws.com` `logs:CreateLogStream` + `logs:PutLogEvents` on `/aws/route53/*`; `aws_route53_query_log` should `depends_on` the `aws_cloudwatch_log_resource_policy`.
- AWS: limit of 10 CloudWatch Logs resource policies per account/region — reuse/edit one rather than creating per zone [15]. CloudWatch keeps logs indefinitely by default → set `retention_in_days`. Logs include resolver IP and EDNS client subnet. One log stream per edge location (`zoneid/EDGE`). Resolvers' cached answers are not logged. No Route 53 charge for query logging.
- Satisfies Security Hub **Route53.2** (§10).

## 8. DNSSEC — `aws_route53_key_signing_key` + `aws_route53_hosted_zone_dnssec` [5][8][16][17]

KSK [5]:
- Required: `hosted_zone_id`, `key_management_service_arn` (unique per KSK in the zone; key **in us-east-1**), `name` (unique within zone). Optional `status` = `ACTIVE` (default) | `INACTIVE`. Timeouts 30m.
- Import: `hosted_zone_id,name` (e.g. `Z1D633PJN98FT9,example`).
- KMS key (AWS [16]): customer managed, **asymmetric `ECC_NIST_P256`**, usage `SIGN_VERIFY`, US East (N. Virginia). Provider example key policy: `dnssec-route53.amazonaws.com` gets `kms:DescribeKey`, `kms:GetPublicKey`, `kms:Sign` with `aws:SourceAccount` = account and `aws:SourceArn` like `arn:aws:route53:::hostedzone/*`; plus `kms:CreateGrant` with `kms:GrantIsForAWSResource = true`; plus root `kms:*`. Example `deletion_window_in_days = 7`.
- Upstream doc defect: example references `aws_route53_zone.test` / `aws_kms_key.test` while declaring `example` (L3).

Zone signing [8]:
- `hosted_zone_id` required; `signing_status` = `SIGNING` (default) | `NOT_SIGNING`. Example takes `hosted_zone_id` from the KSK and `depends_on` it. Import: zone ID.

AWS DNSSEC constraints [17]:
- Public hosted zones only (private zones: use Resolver DNSSEC validation).
- Create CloudWatch alarms on `DNSSECInternalFailure` and `DNSSECKeySigningKeysNeedingAction` ("strongly recommend").
- You own KSK management/rotation; Route 53 manages the ZSK.
- With signing on, Route 53 caps record TTL at one week.
- Multi-vendor (multi-provider) name server setups are unsupported; the parent DNS provider must support DS records or the child zone becomes unresolvable.
- Establishing the chain of trust (DS record at parent) is a separate step not done by these two resources (M2).

## 9. `aws_route53_delegation_set` and Resolver (brief)

Delegation set [18]: optional `reference_name`; attributes `arn`, `id`, `name_servers`; import by ID. Share one set across several public zones for identical NS. Conflicts with private zones (§3).

Resolver (regional — M1):
- `aws_route53_resolver_endpoint` [9]: required `direction` (`INBOUND`|`OUTBOUND`|`INBOUND_DELEGATION`), `ip_address` blocks (`subnet_id`, optional `ip`/`ipv6`), `security_group_ids`; optional `name`, `protocols` (`Do53`|`DoH`|`DoH-FIPS`), `resolver_endpoint_type` (`IPV4`|`IPV6`|`DUALSTACK`), `rni_enhanced_metrics_enabled`/`target_name_server_metrics_enabled` (default `false`), `region`. Import: `rslvr-in-…` ID. Minimum IP count not stated in provider doc (U2).
- `aws_route53_resolver_rule` [10]: required `domain_name`, `rule_type` (`FORWARD`|`SYSTEM`|`RECURSIVE`); `resolver_endpoint_id` and `target_ip { ip|ipv6, port=53, protocol=Do53 }` only for FORWARD. Import `rslvr-rr-…`; identity `id` (+ `account_id`, `region`).
- `aws_route53_resolver_rule_association` [11]: required `resolver_rule_id`, `vpc_id`; optional `name`, `region`. Import `rslvr-rrassoc-…`; identity `id` (+ `account_id`, `region`).

## 10. AWS guidance

Security Hub CSPM Route 53 controls [19]:

| ID | Title | Severity | Resource / Config rule | Terraform lever |
|---|---|---|---|---|
| Route53.1 | Route 53 health checks should be tagged | Low | `AWS::Route53::HealthCheck` / `tagged-route53-healthcheck` (param `requiredTagKeys`) | `tags` on `aws_route53_health_check` (or provider `default_tags`) |
| Route53.2 | Route 53 public hosted zones should log DNS queries | Medium | `AWS::Route53::HostedZone` / `route53-query-logging-enabled` | `aws_route53_query_log` per public zone |

No Security Hub control for DNSSEC exists on that page (do not invent one).

Route 53 DNS best practices [20]:
- Use data-plane features (health checks, ARC routing control) for failover, not control-plane API calls.
- TTL: recommended range 60–172,800 s; 3600–86,400 s for NS/MX and rarely-changing records; 60–120 s for health-checked/failover records; temporarily shorten TTL before critical changes.
- Prefer alias records over CNAME for AWS targets (fewer lookups, lower cost).
- Geolocation/geoproximity/latency: always define a default record, or some clients get no answer.
- Automation: wait for change propagation (`GetChange` → `INSYNC`) when the next step depends on it.
- Delegate from the immediate parent zone, never from a grandparent.
- Keep responses < 512 bytes; multivalue answer returns up to eight healthy IPs.

## 11. Legacy-file claims found wrong or outdated

- `required_version = ">= 1.7"`, `version = "~> 6.0"`, `dynamodb_table` locking → superseded by F1/F3/F7.
- "`failure_threshold = 3` default ... 10-second intervals" — provider doc states no default (U1); not confirmable.
- "`aws_route53_records_exclusive` ... Drift Risk NONE" — wrong: provider doc says it reconciles only on apply, does not prevent out-of-band creation, and mis-mirrored `aws_route53_record`s drift [14].
- "CloudFront `evaluate_target_health = true` causes plan-time error" — not in provider doc (unverified; treat as false until proven).
- "CloudWatch alarm for health check must be in us-east-1" — not confirmed by sources read; `cloudwatch_alarm_region` exists as an argument (unverified, U3).
- "CNAME at apex ... AWS rejects this" — consistent with DNS rules but not verified in this pass (U4).
- "KMS key with `enable_key_rotation = false` ... DNSSEC keys cannot be auto-rotated" — AWS says you own KSK rotation [17]; KMS auto-rotation for asymmetric keys not verified here (U5).
- Missing in legacy: `enable_accelerated_recovery`, 6.53.0 `type` change no longer forces replacement, 6.67.0 batch reads, Resolver regional exception, 10-resource-policy limit.

## 12. Unverified / medium-confidence / limits

- U1: Default `failure_threshold` and allowed `request_interval` values for health checks (provider doc silent).
- U2: Minimum number of `ip_address` blocks on a Resolver endpoint.
- U3: Whether CloudWatch-metric health check alarms must be in a specific region.
- U4: Route 53 API rejection of CNAME at zone apex.
- U5: KMS automatic rotation support for ECC_NIST_P256 DNSSEC keys.
- M1 (medium confidence): Resolver resources are regional (accept `region`) per their own docs [9][10][11], while the enhanced-region guide lists `aws_route53_*` as global without carving out Resolver [12]. Treat F14 as applying to zones/records/health checks/query logs/DNSSEC/delegation sets; recommend the orchestrator amend F14.
- M2 (medium confidence): DS record publication at parent is outside these resources; `aws_route53domains_delegation_signer_record` exists for Route 53 Domains (import ID changed in 6.70.0 [3]) — not researched in depth.
- L1: CHANGELOG scan by keyword through two windows; 6.55.0 header boundary not seen explicitly.
- L2: Routing-policy AWS pages (failover, geoproximity, IP-based) and health-check pricing not fetched; Route 53 Profiles and CIDR collections out of scope.
- L3: Provider DNSSEC KSK example has inconsistent resource names (upstream doc bug).

## 13. Security note

No prompt-injection or instruction-like text observed in fetched pages.

## Source Bibliography

All accessed 2026-10-22.
1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_zone.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_query_log.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_key_signing_key.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_zone_association.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_health_check.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_hosted_zone_dnssec.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_resolver_endpoint.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_resolver_rule.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_resolver_rule_association.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_records_exclusive.html.markdown
15. https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/query-logs.html
16. https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec-cmk-requirements.html
17. https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html
18. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_delegation_set.html.markdown
19. https://docs.aws.amazon.com/securityhub/latest/userguide/route53-controls.html
20. https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html
