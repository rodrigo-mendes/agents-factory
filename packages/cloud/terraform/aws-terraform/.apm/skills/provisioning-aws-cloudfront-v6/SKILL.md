---
name: provisioning-aws-cloudfront-v6
description: "CloudFront Terraform (aws 6.x, global): distributions, OAC, cache/response headers policies, functions, logging v2. Use when writing HCL for CloudFront. Not for ACM certificates, Route 53 records, WAF."
---

# Provisioning AWS CloudFront with Terraform — hashicorp/aws 6.x

> Version lock: every claim applies to **hashicorp/aws 6.x** (reference 6.69.0/6.70.0) + **Terraform ~> 1.16** only.
> Research date **2026-10-22**. Claims tagged (unverified) or (medium confidence) were not fully confirmed
> against an official page.

## Version Context

| Item | Value | Source (fetched 2026-10-22) |
|---|---|---|
| Terraform CLI | `~> 1.16` (1.16.6 released 2026-10-14); 1.17.0 stable since 2026-10-21, not the target | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | latest 6.70.0; reference patch 6.69.0; constraint `~> 6.69` | https://releases.hashicorp.com/terraform-provider-aws/ |
| aws v7 | Not released — v7 planned | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | **Withdrawn** — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Region | CloudFront is global: no `region` argument, no `@region` import suffix | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| Provider constraint | `~> 6.69` (root modules); a minimum for reusable modules | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable (2026-10-21, no breaking changes) but is not the target; re-verify before moving off `~> 1.16`.
- 6.57.0 is permanently withdrawn; any constraint that resolves to it fails init.
- v7 is planned; it will need a new skill.

**Version lock:** `-v6` = the 6.x major line, reference patch 6.69.0/6.70.0, Terraform ~> 1.16.
A new major (v7) is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Foundation: [terraform block, us-east-1 alias, distribution](./blueprints/always-do-foundation.md)
- Origins/policies: [OAC, policies, custom origin, functions, signing](./blueprints/always-do-origins-policies.md)
- DNS/logging: [Route 53 alias, logging v2, error responses](./blueprints/always-do-dns-logging.md)
- Never-do security: [TLS, viewer protocol, OAI, signers](./blueprints/never-do-security.md)
- Never-do provider/operations: [region, deprecated args, pins](./blueprints/never-do-provider-operations.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `~> 6.69` and `~> 1.16`.** See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-providers).
  Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
- **Use `use_lockfile = true` on the S3 backend** — `dynamodb_table` is deprecated.
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-providers).
  Source: https://developer.hashicorp.com/terraform/language/backend/s3
- **Omit `region` on CloudFront resources** (global service); ACM certificates for viewers must be in us-east-1.
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-providers).
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
- **Set `minimum_protocol_version` explicitly** (`TLSv1.2_2021` or newer) — the provider default is `TLSv1`.
  See [foundation §2](./blueprints/always-do-foundation.md#2-distribution-with-s3-origin-and-oac).
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
- **Use OAC (`origin_access_control_id`) for S3 origins** with `signing_behavior = "always"`.
  See [origins §3](./blueprints/always-do-origins-policies.md#3-oac-and-s3-bucket-policy).
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_origin_access_control.html.markdown
- **Condition the S3 bucket policy on `AWS:SourceArn`** of the distribution (principal `cloudfront.amazonaws.com`).
  See [origins §3](./blueprints/always-do-origins-policies.md#3-oac-and-s3-bucket-policy).
  Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html
- **Use `viewer_protocol_policy` `redirect-to-https` or `https-only`** (CloudFront.3).
  See [foundation §2](./blueprints/always-do-foundation.md#2-distribution-with-s3-origin-and-oac).
  Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudfront-controls.html
- **Pass the WAFv2 ACL ARN to `web_acl_id`** (WAF Classic takes the ID).
  See [foundation §2](./blueprints/always-do-foundation.md#2-distribution-with-s3-origin-and-oac).
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
- **Use `cache_policy_id` / `origin_request_policy_id`**, not `forwarded_values`.
  See [origins §4](./blueprints/always-do-origins-policies.md#4-cache-origin-request-and-response-headers-policies).
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
- **Set `create_before_destroy = true` on response headers policies** used by a distribution in the same configuration.
  See [origins §4](./blueprints/always-do-origins-policies.md#4-cache-origin-request-and-response-headers-policies).
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_response_headers_policy.html.markdown
- **Use `https-only` and `["TLSv1.2"]` on custom origins** (CloudFront.9, .10).
  See [origins §5](./blueprints/always-do-origins-policies.md#5-custom-origin-and-origin-group).
  Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudfront-controls.html
- **End public key `encoded_key` with a newline.** See [origins §6](./blueprints/always-do-origins-policies.md#6-functions-and-signed-urls).
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_public_key.html.markdown
- **Prefer `trusted_key_groups`** (CloudFront.17). See [origins §6](./blueprints/always-do-origins-policies.md#6-functions-and-signed-urls).
  Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudfront-controls.html
- **Create A alias records, plus AAAA when IPv6 is enabled**, with the distribution `domain_name` and `hosted_zone_id`.
  See [dns §7](./blueprints/always-do-dns-logging.md#7-route-53-alias-to-cloudfront).
  Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-to-cloudfront-distribution.html
- **Set both `response_code` and `response_page_path`** in a `custom_error_response` when using either.
  See [dns §9](./blueprints/always-do-dns-logging.md#9-custom-error-responses).
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| IPv6 and price class | `is_ipv6_enabled` and `price_class` (`PriceClass_All` / `_200` / `_100`) have no stated default (unverified); IPv6 needs both A and AAAA records | "Enable IPv6? Which price class (cost vs edge coverage)?" |
| Logging v1 vs v2 | v2: separate delivery resources, us-east-1 API, destinations CloudWatch Logs / Firehose / S3, format fixed at destination creation, up to 12 h to apply. Security Hub CloudFront.5 checks only legacy logging, so v2 alone probably fails it (medium confidence) | "Use legacy `logging_config` (CloudFront.5), v2, or both with different buckets/prefixes?" |
| `retain_on_delete` | Disables the distribution instead of deleting it; you must delete it manually | "Should destroy leave the distribution disabled instead of waiting for deletion?" |
| `wait_for_deployment` | Default `true`; deployment takes about 15 minutes; `false` skips the wait | "Should Terraform wait for Deployed state?" |
| Geo restriction | `restriction_type` `none`, `whitelist`, `blacklist` with ISO 3166-1 alpha-2 `locations` | "Any country allow/deny list?" |
| OAI to OAC migration | Bucket policy with both statements, switch origin, remove OAI statement after full deploy | "Is an existing OAI origin being migrated?" |
| WAFv2 and logging v2 provider placement | WAFv2 scope `CLOUDFRONT` requires the provider to target us-east-1 ([wafv2_web_acl docs, per the provider docs](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown)); using an `aws.us_east_1` alias vs `region = "us-east-1"` on the resource is an inference (medium confidence); logging v2 delivery API is called in us-east-1 | "Alias or per-resource `region` for the us-east-1 dependencies?" |
| Managed cache/origin-request policy IDs | Names-to-IDs not verified (unverified); the `aws_cloudfront_cache_policy` data source looks them up | "Use a managed policy (data source lookup) or a custom policy resource?" |
| S3 website endpoint origin | Cannot use OAC or OAI; configure as a custom origin with `custom_origin_config` (`origin_protocol_policy` is required there). That website endpoints serve HTTP only is not in the research (unverified) | "Is the bucket a website endpoint? Which `origin_protocol_policy`?" |
| Functions vs Lambda@Edge | Functions: `cloudfront-js-1.0` / `cloudfront-js-2.0`, max 2 associations per behavior; Lambda@Edge not covered by this skill; Functions AWS quotas unverified (U8) | "Is edge compute needed, and which kind?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Omit `minimum_protocol_version` — provider default is `TLSv1`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown)) | Set `TLSv1.2_2021` or newer (CloudFront.15) |
| Use `allow-all`, `http-only` origins or `SSLv3`. ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/cloudfront-controls.html)) | `redirect-to-https`, `https-only`, `["TLSv1.2"]` |
| Use an OAI for new S3 origins — AWS marks it legacy, not recommended. ([source](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)) | OAC with `origin_access_control_id` |
| Use OAC or OAI on an S3 website endpoint. ([source](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)) | Configure the website endpoint as a custom origin |
| Set `region` on CloudFront resources (global). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown)) | Omit `region` |
| Use a viewer certificate outside us-east-1. ([source](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html)) | Request or import the ACM certificate in us-east-1 |
| Use `forwarded_values` — deprecated (not removed in 6.x). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown)) | `cache_policy_id` and/or `origin_request_policy_id` |
| Set `etag` on `aws_cloudfront_response_headers_policy` — computed only since 6.0. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | Omit it |
| Use `trusted_signers`. ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/cloudfront-controls.html)) | `trusted_key_groups` (CloudFront.17) |
| Give a public key `encoded_key` without a trailing newline — perpetual recreate. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_public_key.html.markdown)) | End the value with a newline |
| S3 backend with `dynamodb_table` — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |
| Pin `6.57.0` — withdrawn. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` |

## Quick Reference

Sources fetched 2026-10-22.

| Aspect | Value | Source |
|---|---|---|
| Required blocks | `enabled`, `origin`, `default_cache_behavior`, `restrictions`, `viewer_certificate` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown |
| `minimum_protocol_version` default | `TLSv1`; settable only with `cloudfront_default_certificate = false` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown |
| Security policies | SSLv3, TLSv1, TLSv1_2016, TLSv1.1_2016, TLSv1.2_2018, TLSv1.2_2019, TLSv1.2_2021, TLSv1.2_2025, TLSv1.3_2025 | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html |
| Hosted zone ID | `Z2FDTNDATAQYW2` (always) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown |
| Deployment time | about 15 minutes; `wait_for_deployment` default `true` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown |
| ACM certificate Region | us-east-1 for viewer HTTPS | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html |
| Logging v2 Region | CloudWatch Logs delivery API in us-east-1 | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logging.html |
| OAC | `signing_protocol = "sigv4"`; docs recommend `signing_behavior = "always"` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_origin_access_control.html.markdown |
| Function | `runtime` `cloudfront-js-1.0` or `cloudfront-js-2.0`; `code` 1-40960 bytes; import by `name` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_function.html.markdown |
| Route 53 alias | `alias` block fields all required; fixed 60 s TTL | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown |
| Security Hub controls | CloudFront.1, .3, .4, .5, .6, .7, .8, .9, .10, .12, .13, .14, .15, .16, .17 | https://docs.aws.amazon.com/securityhub/latest/userguide/cloudfront-controls.html |
| Identity import | `identity` block needs Terraform >= 1.12 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown |

## 5.x → 6.x Migration (CloudFront)

Changes in 6.0.0 that affect CloudFront work
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-22):

- **`aws_cloudfront_key_value_store`**: use `name` to reference the resource name; `id` now holds the ID the AWS API returns.
- **`aws_cloudfront_response_headers_policy`**: `etag` is computed only — remove any configured value.
- No CloudFront data source changes; no changes to `aws_route53_record` alias or `aws_s3_bucket_policy`.

6.48.0 → 6.70.0 has no breaking CloudFront changes. Additions: `aws_cloudfront_function` tags (6.49.0),
`origin_mtls_config` on custom origins (6.51.0), `aws_cloudfront_key_value_store` tags (6.54.0)
([CHANGELOG](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)).
Upgrade path (from the 6.0 upgrade guide): move to latest 5.x, get a clean plan, set `~> 6.69`, run `terraform init -upgrade`
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)). (unverified) — the guide's exact upgrade steps are not confirmed here; check the guide.

## External Resources

All fetched 2026-10-22.

- Provider CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- Enhanced region support: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
- aws_cloudfront_distribution: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
- Restricting access to S3 (OAC): https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html
- Security Hub CloudFront controls: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudfront-controls.html
- Standard logging: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logging.html
- Terraform S3 backend: https://developer.hashicorp.com/terraform/language/backend/s3
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
