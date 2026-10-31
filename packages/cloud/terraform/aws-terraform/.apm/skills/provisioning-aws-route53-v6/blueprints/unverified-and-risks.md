# Unverified Claims and Risks — hashicorp/aws 6.x Route 53

Research date 2026-10-22. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** as of 2026-10-22 (latest 6.70.0, reference
  6.69.0/6.70.0). Re-verify when starting new work or after 30 days.
  Source: https://releases.hashicorp.com/terraform-provider-aws/
- **Terraform 1.17.0 is stable since 2026-10-21** (no breaking changes) but is not the target of this
  skill, which stays on `~> 1.16`. Re-verify before moving the CLI constraint.
  Source: https://releases.hashicorp.com/terraform/
- **6.57.0 is permanently withdrawn** from GitHub and the Registry — never pin it.
- **v7 is planned**, not released. When v7 ships, create a new skill `provisioning-aws-route53-v7`.
- `aws_route53domains_delegation_signer_record` had a breaking import ID change in 6.70.0; patch-level
  changes can affect Route 53 Domains work.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Default `failure_threshold` and allowed `request_interval` values for health checks — provider doc silent | (unverified) — always set explicitly; do not state a default |
| U2 | Minimum number of `ip_address` blocks on a Resolver endpoint | (unverified) |
| U3 | Whether CloudWatch-metric health check alarms must be in a specific region | (unverified) — `cloudwatch_alarm_region` exists as an argument |
| U4 | Route 53 API rejection of CNAME at zone apex | (unverified) |
| U5 | KMS automatic rotation support for ECC_NIST_P256 DNSSEC keys | (unverified) |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | Resolver resources document `region` on their resource pages while the enhanced-region guide lists `aws_route53_*` as global without classifying Resolver | (medium confidence) — checked on three resource pages (endpoint, rule, rule association); other `aws_route53_resolver_*` resources not checked |
| M2 | DS record publication at the parent is outside these resources; `aws_route53domains_delegation_signer_record` exists for Route 53 Domains | (medium confidence) — not researched in depth |
| M3 | A regional resource may set `region = "us-east-1"` instead of a provider alias (inferred from Enhanced Region Support; provider docs' examples use an alias) | (medium confidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG scan by keyword through two windows; 6.55.0 header boundary not seen explicitly |
| L2 | Routing-policy AWS pages (failover, geoproximity, IP-based) and health-check pricing not fetched; Route 53 Profiles and CIDR collections out of scope |
| L3 | Provider DNSSEC KSK example has inconsistent resource names (upstream doc bug) |

## Tag to Register Mapping

| Tag | File and section | Register id |
|---|---|---|
| (unverified) | SKILL.md, Quick Reference — health check `failure_threshold`/`request_interval` defaults | U1 |
| (unverified) | blueprints/always-do-logging-dnssec.md, §7 Delegation sets and Resolver — minimum `ip_address` count | U2 |
| (medium confidence) | SKILL.md, Version Context and Always Do — Resolver `region` beyond the three checked resources | M1 |
| (medium confidence) | blueprints/always-do-logging-dnssec.md, §6 DNSSEC — DS record publication | M2 |
| (medium confidence) | blueprints/evaluation-scenarios.md, Scenario 2 — DS record criterion | M2 |
| (medium confidence) | blueprints/always-do-zones-records.md, §1 Terraform block and providers — `region` instead of alias | M3 |

U3, U4 and U5 are not tagged anywhere in the skill text; they are registered only for coverage.

## Source Bibliography

All accessed 2026-10-22. Numbers match the unit research bibliography.

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
21. https://developer.hashicorp.com/terraform/language/backend/s3 — `use_lockfile`; `dynamodb_table` deprecated
22. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown — identity import requires Terraform >= 1.12.0
(14, also fetched 2026-10-22, is the `aws_route53_records_exclusive` page: `resource_record_set` schema, exclude default NS/SOA.)
