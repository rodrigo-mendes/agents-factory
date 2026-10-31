# Unverified Claims and Risks — hashicorp/aws 6.x CloudFront

Research date 2026-10-22. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x** is the current stable major as of 2026-10-22 (latest 6.70.0, reference patch
  6.69.0; constraint `~> 6.69` allows 6.70.x). Re-verify when starting new work.
- **Terraform 1.17.0 is stable since 2026-10-21** (no breaking changes) but is not the target; this skill
  stays on `~> 1.16` (1.16.6 released 2026-10-14). Re-verify before moving the constraint.
- **6.57.0 is permanently withdrawn** from GitHub and the Registry: never pin it.
- **v7 is planned** (no 7.x released). When it ships, create a new skill `provisioning-aws-cloudfront-v7`.
- Raw `main` markdown may run slightly ahead of 6.70.0 (L2).

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | `is_ipv6_enabled` default not stated on the provider page | (unverified) — always set explicitly |
| U2 | `price_class` default not stated | (unverified) — always set explicitly; `PriceClass_100` is a cost/coverage choice |
| U3 | Whether the provider accepts `TLSv1.2_2025` / `TLSv1.3_2025` in `minimum_protocol_version` (page gives examples only; AWS supports both) | (unverified) |
| U4 | Cache policy TTL defaults not stated | (unverified) |
| U5 | Managed cache/origin-request policy names to IDs not verified | (unverified) — use the data sources |
| U6 | Legacy claim "mixing `forwarded_values` and `cache_policy_id` causes a provider error" not on the provider page | (unverified) — not reproduced |
| U7 | Legacy claim "CloudFront IAM actions do not support resource-level restrictions": IAM page not fetched | (unverified) — not reproduced |
| U8 | CloudFront Functions AWS quotas (code size, execution time) not fetched; provider allows `code` up to 40960 bytes | (unverified) |
| U9 | Argument names of `aws_cloudwatch_log_delivery_source` `name`, and of the delivery destination and delivery resources, not researched | (unverified) — check the resource pages before use |
| U10 | 5.x to 6.x upgrade steps (latest 5.x, clean plan, `init -upgrade`) not in the CloudFront research; attributed to the 6.0 upgrade guide | (unverified) — check the guide |
| U11 | That S3 website endpoints serve HTTP only: not stated in the research | (unverified) — only the OAC/OAI exclusion is documented |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | WAFv2 ACL for CloudFront assumed `scope = "CLOUDFRONT"` in us-east-1; alias-vs-`region` is an inference from regional scoping | (medium confidence) — see provisioning-aws-waf-v6 |
| M2 | A distribution with only v2 logging probably fails Security Hub CloudFront.5 (inferred from "only evaluates standard logging (legacy)") | (medium confidence) |
| M3 | WebFetch paraphrases page text; verbatim NOTE wording may differ, substance confirmed on raw markdown | (medium confidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG read in two chunks; part of the 6.55.0 section may have been missed |
| L2 | Raw `main` markdown may run slightly ahead of 6.70.0 |
| L3 | Not covered: `aws_cloudfront_vpc_origin`, `continuous_deployment_policy`, `realtime_log_config`, `key_value_store`, multitenant distribution and tenant, trust store, connection function, `monitoring_subscription`, field-level encryption, Lambda@Edge |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Ask First (IPv6 / price class); always-do-foundation.md §2 | U1, U2 |
| (unverified) | SKILL.md Never Do (`minimum_protocol_version`); never-do-security.md §1 | U3 |
| (unverified) | SKILL.md Ask First (managed policy IDs); always-do-origins-policies.md §4 — managed policy IDs | U5 |
| (unverified) | SKILL.md Ask First (Functions vs Lambda@Edge); always-do-origins-policies.md §6 — Functions quota | U8 |
| (unverified) | SKILL.md Ask First (S3 website endpoint) — HTTP-only | U11 |
| (unverified) | SKILL.md 5.x → 6.x Migration — upgrade steps | U10 |
| (medium confidence) | SKILL.md Ask First (WAFv2 and logging v2 provider placement) | M1 |
| (unverified) | always-do-dns-logging.md §8 — logging v2 argument names | U9 |
| (medium confidence) | always-do-foundation.md §1 — WAFv2 alias vs region | M1 |
| (medium confidence) | always-do-dns-logging.md §8 and SKILL.md Ask First (logging) — CloudFront.5 | M2 |

## Source Bibliography

All fetched 2026-10-22. Numbers match the research bibliography.

8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_origin_access_control.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_cache_policy.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_origin_request_policy.html.markdown
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_response_headers_policy.html.markdown
16. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_function.html.markdown
17. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_key_group.html.markdown
17b. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_public_key.html.markdown
18. https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html
19. https://docs.aws.amazon.com/securityhub/latest/userguide/cloudfront-controls.html
20. https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-to-cloudfront-distribution.html
21. https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html
22. https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html
23. https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logging.html
24. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown
Shared version and region facts: the Terraform and provider pages cited inline, read 2026-10-23.
