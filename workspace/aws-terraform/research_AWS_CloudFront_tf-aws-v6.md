# Research — AWS CloudFront with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-22**. Status: **COMPLETE** (unit `cloudfront`, P4 fan-out, flat — no sub-agents).
> Resource docs come from the upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`), because Registry pages render JS-only (F12).
> Coverage checklist only (not a source): `workspace/terraform/research_AWS_CloudFront_aws-v6.x.md` (6.47.0, Terraform 1.9). Claims in it that I found wrong are listed in §9.
> Family facts are cited by ID from `_family_facts_v6.md` (F1–F15) and were not re-researched.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI target | `required_version = "~> 1.16"` (1.17.0 is stable but is not the target) | F1, F2 |
| hashicorp/aws | latest is 6.70.0 (released 2026-10-21 per CHANGELOG); constraint `~> 6.69` | F3; [8] |
| Withdrawn | 6.57.0. Never pin it | F4 |
| Global service | CloudFront resources take **no `region` argument** and no `@region` import suffix (F14). The `aws_cloudfront_distribution` page documents no `region` argument [11] | F14, F5 |
| Identity import | `aws_cloudfront_distribution` supports an `identity` block (`id` required, `account_id` optional). This needs Terraform ≥ 1.12 (F11), which 1.16 satisfies [11] | F11 |

Recommended constraint block: identical to the VPC pilot (`required_version = "~> 1.16"`, `version = "~> 6.69"`), per F1, F3 and F6. For the backend, use the S3 backend with `use_lockfile = true`, not `dynamodb_table` (F7).

Region-bound dependencies (these are not CloudFront resources, so they DO need a provider in us-east-1):
- ACM certificates for viewer HTTPS must be requested or imported in **us-east-1**. An ELB origin certificate can be in any Region [21]. Use an `aws.us_east_1` provider alias, or set the ACM resource's own `region = "us-east-1"` (F5: regional resources accept `region`).
- A WAFv2 web ACL for CloudFront must exist in the "WAF Global (CloudFront) region" [11]. In practice that means `scope = "CLOUDFRONT"` in us-east-1 (medium confidence, M1: the us-east-1 wording comes from the legacy file and is not on the fetched provider page).
- Standard logging v2: the CloudWatch Logs delivery API must be called in **us-east-1**, even for cross-Region destinations. A Firehose destination must be in us-east-1 [23].

## 2. Provider 6.x changes for CloudFront

6.0.0 upgrade guide (F13) [9]:
- `aws_cloudfront_key_value_store`: use `name` to reference the resource name. `id` now holds the ID that the AWS API returns.
- `aws_cloudfront_response_headers_policy`: `etag` is now computed only. Remove any configured value.
- No CloudFront data source changes. No changes to `aws_route53_record` alias or `aws_s3_bucket_policy`.

CHANGELOG 6.48.0 → 6.70.0, CloudFront scope [8]. There are no breaking changes in this range.
- 6.49.0: `aws_cloudfront_function` adds `tags` and `tags_all` (#47916).
- 6.51.0: `aws_cloudfront_distribution` (and the multitenant distribution) adds `origin.custom_origin_config.origin_mtls_config` (#46421). `aws_cloudfront_distribution_tenant` now honours configured timeouts, but managed certificate issuance keeps a fixed 3-hour timeout (#47839).
- 6.54.0: `aws_cloudfront_key_value_store` adds `tags` (#48458). `aws_cloudfront_multitenant_distribution` gets fixes for default tags, taint on failed Create, `etag` on import and on tags-only updates, and waiting for deployment on Update (#48782, #48783).
- 6.55.0 → 6.70.0: no CloudFront entries seen (see L1).

## 3. aws_cloudfront_distribution [11]

**Required:** `enabled`, `origin` (one or more), `default_cache_behavior` (exactly one), `restrictions`, `viewer_certificate`.

**Top-level optional arguments:**

| Argument | Default / values | Notes |
|---|---|---|
| `aliases` | — | Alternate domain names (CNAMEs). Each one must be covered by a SAN in the attached certificate (exact match or a wildcard at the same level) [21] |
| `is_ipv6_enabled` | no default stated (U1) | If true, create both A and AAAA Route 53 alias records [20] |
| `http_version` | default `http2`; `http1.1`, `http2`, `http2and3`, `http3` | All distributions that share one certificate must use the same HTTP-versions option [21] |
| `price_class` | `PriceClass_All` \| `PriceClass_200` \| `PriceClass_100`; no default stated (U2) | — |
| `web_acl_id` | — | **WAFv2: pass the ACL ARN** (`aws_wafv2_web_acl.x.arn`). WAF Classic: pass the ID. Credentials need `waf:GetWebACL` |
| `wait_for_deployment` | `true` | Set `false` to skip waiting for `InProgress` → `Deployed` |
| `retain_on_delete` | `false` | Disables the distribution instead of deleting it. You must then delete it manually |
| `staging` | `false` | — |
| `continuous_deployment_policy_id` | — | Set only on the production distribution |
| `default_root_object`, `comment`, `tags` | — | Needed for Security Hub CloudFront.1 and CloudFront.14 |

**NOTE** [11]: "CloudFront distributions take about 15 minutes to reach a deployed state after creation or modification." Deletes are blocked during that window. Use `retain_on_delete` to remove an enabled distribution without waiting.

**`origin`:**
- Required: `domain_name`, `origin_id`. Optional: `origin_path`, `custom_header`, `origin_access_control_id`.
- `connection_attempts` 1–3 (default 3). `connection_timeout` 1–10 s (default 10). `response_completion_timeout` must be ≥ `origin_read_timeout` (0 or omitted = no maximum).
- `s3_origin_config { origin_access_identity }` is the legacy OAI path. S3 origins should use `origin_access_control_id` or `s3_origin_config`.
- `custom_origin_config`:
  - Required: `http_port`, `https_port`, `origin_protocol_policy` (`http-only` \| `https-only` \| `match-viewer`), `origin_ssl_protocols` (`SSLv3`, `TLSv1`, `TLSv1.1`, `TLSv1.2`).
  - Optional: `ip_address_type` (`ipv4` \| `ipv6` \| `dualstack`), `origin_keepalive_timeout` (default 5, max 60), `origin_read_timeout` (default 30, max 60), `origin_mtls_config { client_certificate_arn }` (6.51.0).
- `vpc_origin_config`: `vpc_origin_id` required; optional `owner_account_id`, keepalive and read timeouts (1–60).
- `origin_shield`: `enabled` required; `origin_shield_region` optional.
- `origin_group`: `origin_id`, `failover_criteria { status_codes }`, and exactly two `member` blocks (the first is the primary). Satisfies CloudFront.4.

**Cache behaviors** (`default_cache_behavior` max 1; `ordered_cache_behavior` list, evaluated top-down with the first at precedence 0):
- Required: `allowed_methods`, `cached_methods`, `target_origin_id`, `viewer_protocol_policy` (`allow-all` \| `https-only` \| `redirect-to-https`). `path_pattern` is required in ordered behaviors only.
- `default_cache_behavior` requires either `cache_policy_id` (preferred) or `forwarded_values`.
- **`forwarded_values` is deprecated.** Use `cache_policy_id` and/or `origin_request_policy_id` instead. It is deprecated, not removed in 6.x.
- Optional: `response_headers_policy_id`, `compress` (default `false`), `min_ttl` (default 0), `default_ttl`, `max_ttl`, `realtime_log_config_arn`, `field_level_encryption_id`, `smooth_streaming`, `grpc_config { enabled }`.
- `function_association`: max 2 (`viewer-request` \| `viewer-response`, `function_arn`).
- `lambda_function_association`: max 4 (four event types, `lambda_arn`, `include_body` default false).
- `trusted_key_groups` (key group IDs) is preferred over `trusted_signers` (account IDs or `self`). See CloudFront.17.
- TTL NOTE: to get "Use origin cache headers" without a cache policy, set min 0, max 31536000, default 86400.

**`custom_error_response`:**
- `error_code` is required. Optional: `error_caching_min_ttl`, `response_code`, `response_page_path`.
- NOTE: if you set `response_code` or `response_page_path`, you must set both.

**`restrictions { geo_restriction }`:**
- `restriction_type` is `none` \| `whitelist` \| `blacklist`.
- `locations` is required: ISO 3166-1 alpha-2 codes; `[]` is allowed when the type is `none`.

**`viewer_certificate`:**
- Set exactly one of: `acm_certificate_arn` ("must be in US-EAST-1"), `cloudfront_default_certificate = true`, or `iam_certificate_id`.
- `ssl_support_method` is `sni-only` \| `vip` \| `static-ip`. It is required with ACM or IAM certificates. `vip` uses a dedicated IP and may cost extra.
- `minimum_protocol_version`:
  - **Default `TLSv1`.** Settable only when `cloudfront_default_certificate = false`.
  - With the default certificate, `TLSv1` must be used.
  - With `sni-only`, use `TLSv1` or later.
  - **Set `TLSv1.2_2021` or newer explicitly.**
- AWS security policies [22]: SSLv3, TLSv1, TLSv1_2016, TLSv1.1_2016, TLSv1.2_2018, TLSv1.2_2019, TLSv1.2_2021, **TLSv1.2_2025**, **TLSv1.3_2025**. TLSv1.3_2025 is TLS 1.3 only. Quantum-safe key exchange is TLS 1.3 only.
- Whether the provider validates TLSv1.2_2025 / TLSv1.3_2025: the page lists examples, not an enum (U3).

**`logging_config` (legacy V1, max 1):**
- `bucket` enables V1. The bucket needs a FULL_CONTROL ACL for `awslogsdelivery`.
- `prefix` applies to V1 only. `include_cookies` (default false) applies to V1 and V2.
- Standard logging **v2** is configured with separate `aws_cloudwatch_log_delivery_source` (`log_type = "ACCESS_LOGS"`, `resource_arn` = the distribution ARN), `aws_cloudwatch_log_delivery_destination` and `aws_cloudwatch_log_delivery` resources [11][23].
- v2 facts [23]:
  - Destinations: CloudWatch Logs, Firehose, S3.
  - The output format is fixed when the destination is created (delete and recreate to change it).
  - One delivery source per distribution.
  - v2 does not affect legacy logging. Use a different bucket or prefix for each.
  - Changes take up to 12 hours.
- Security Hub CloudFront.5 checks **only legacy** logging [19]. A distribution with only v2 logging may therefore fail CloudFront.5 (medium confidence, M2).

**Other blocks:** `cache_tag_config { header_name }`, `connection_function_association { id }`, `viewer_mtls_config { mode = required|optional, trust_store_config { trust_store_id, advertise_trust_store_ca_names, ignore_certificate_expiry } }`.

**Attributes:**
- `id`, `arn`, `domain_name`, `etag`, `status`, `caller_reference`, `logging_v1_enabled`, `last_modified_time`, `in_progress_validation_batches`, `tags_all`.
- `hosted_zone_id` is always `Z2FDTNDATAQYW2`.

**Import:** distribution ID (`E74FTE3EXAMPLE`), via an `import` block or `terraform import`; `identity` with Terraform ≥ 1.12.

## 4. aws_cloudfront_origin_access_control (OAC) and why OAI is legacy

- Provider [12]:
  - Required: `name`, `origin_access_control_origin_type` (`s3` \| `lambda` \| `mediapackagev2` \| `mediastore`), `signing_behavior` (`always` \| `never` \| `no-override`; docs recommend `always`), `signing_protocol` (`sigv4` only).
  - `description` defaults to "Managed by Terraform". Attributes: `id`, `arn`, `etag`. Import by `id` (`E327GJI25M56DG`). No NOTE block.
  - Attach it with `origin.origin_access_control_id`, and omit `s3_origin_config`.
- AWS [18]:
  - AWS recommends OAC because it supports S3 in all Regions (including opt-in Regions launched after Dec 2022), SSE-KMS, and dynamic `PUT`/`DELETE`.
  - OAI (labelled "legacy, not recommended") lacks opt-in Regions, SSE-KMS, `PUT`/`POST`/`DELETE`, and Regions launched after Jan 2023. In SigV4-only Regions, OAI does not support `POST`.
  - Security Hub CloudFront.13 adds that OAI lacks granular policy configuration [19].
- OAC requirements and caveats [18]:
  - S3 Object Ownership must be **Bucket owner enforced** (the default for new buckets).
  - **S3 website endpoints cannot use OAC or OAI.** Configure them as a custom origin.
  - OAC does not support origin redirect through Lambda@Edge.
  - Multi-Region Access Points need a different OAC setup.
  - HTTPS from CloudFront to S3 is guaranteed only with `signing_behavior = "always"`.
  - `never` requires a public bucket.
  - `no-override` requires `Authorization` in the cache policy of every behavior that uses that S3 origin.
- **S3 bucket policy for OAC** [18]:
  - Principal: `Service = cloudfront.amazonaws.com`. Action: `s3:GetObject` (add `s3:PutObject` for writes). Resource: `arn:aws:s3:::<bucket>/*`.
  - Condition: `StringEquals` on `AWS:SourceArn = arn:aws:cloudfront::<account>:distribution/<id>`. In Terraform, use `aws_cloudfront_distribution.x.arn`.
  - For SSE-KMS, add a KMS key policy statement for the same principal (`kms:Decrypt`, `kms:Encrypt`, `kms:GenerateDataKey*`) with the same `AWS:SourceArn` condition.
  - The bucket policy is regional (`aws_s3_bucket_policy`), so the S3 provider or region applies.
- **OAI → OAC migration** [18]:
  1. Update the bucket policy with two statements, one for the OAC service principal and one for the OAI principal `arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity <id>`.
  2. Switch the origin to OAC.
  3. After the distribution is fully deployed, remove the OAI statement.
- Deletion order [18]: delete the distribution before the S3 bucket origin.

## 5. Policies, functions and signing

**`aws_cloudfront_cache_policy`** [13]:
- Required: `name`, `min_ttl`, and `parameters_in_cache_key_and_forwarded_to_origin` (`cookies_config`, `headers_config`, `query_strings_config` all required; `enable_accept_encoding_brotli` and `enable_accept_encoding_gzip` optional). Optional: `default_ttl`, `max_ttl`, `comment`.
- Behaviors: cookie `none|whitelist|allExcept|all`; header `none|whitelist`; query string `none|whitelist|allExcept|all`; `items` lists the names.
- No TTL defaults are stated (U4). Attributes: `id`, `arn`, `etag`. Import by policy ID.
- The managed policy ID `658327ea-f89d-4fab-a63d-7e88639e58f6` appears as the import example, but the page does not identify it as CachingOptimized. Look managed policies up with the `aws_cloudfront_cache_policy` data source rather than hardcoding IDs (U5).

**`aws_cloudfront_origin_request_policy`** [14]:
- Required: `name`, `cookies_config`, `headers_config`, `query_strings_config`.
- Header behavior `none|whitelist|allViewer|allViewerAndWhitelistCloudFront|allExcept`; cookie and query-string behaviors `none|whitelist|all|allExcept`.
- Import by ID.

**`aws_cloudfront_response_headers_policy`** [15]:
- `name` is required. Blocks: `cors_config` (allow_credentials, allow_headers, allow_methods, allow_origins and `origin_override` all required), `custom_headers_config`, `remove_headers_config`, `security_headers_config`, `server_timing_headers_config { enabled, sampling_rate 0–100 }`.
- `security_headers_config` sub-blocks: `strict_transport_security { access_control_max_age_sec, override, include_subdomains?, preload? }`, `content_security_policy`, `frame_options { frame_option = DENY|SAMEORIGIN }`, `content_type_options`, `referrer_policy`, `xss_protection` (`report_uri` cannot be set with `mode_block`). Each sub-block requires `override`.
- `etag` is computed only (6.0).
- **NOTE:** a policy must be detached from all distributions before it can be deleted. Set `create_before_destroy = true` on the policy when the distribution is in the same configuration.
- Import by ID.

**`aws_cloudfront_function`** [16]:
- Required: `name` (1–64 chars, `[A-Za-z0-9_-]`), `runtime` (`cloudfront-js-1.0` \| `cloudfront-js-2.0`), `code` (1–40960 bytes).
- Optional: `publish` (default `true`, publishes to LIVE), `comment`, `key_value_store_associations` (AWS allows 1 per function), `tags` (6.49.0).
- Attributes: `arn`, `etag` (DEVELOPMENT), `live_stage_etag`, `status`.
- WARNING: you cannot delete a function while it is associated with a cache behavior.
- **Import by `name`**.

**`aws_cloudfront_public_key`** [17b]:
- `encoded_key` is required. `name` or `name_prefix` (they conflict; the name is generated if both are omitted). `comment`.
- **`encoded_key` must end with a newline**, otherwise every run plans a recreate (perpetual diff).
- Attributes: `id`, `etag`, `caller_reference`. Import by ID (`K3D5EWEUDCCXON`).

**`aws_cloudfront_key_group`** [17]:
- Required: `name`, `items` (public key IDs). Optional: `comment`. Attributes: `id`, `etag`. Import by ID.
- Reference it from `trusted_key_groups`.

## 6. Route 53 alias to CloudFront

- `aws_route53_record` [24]:
  - The `alias { name, zone_id, evaluate_target_health }` arguments are all **required**, and the block conflicts with `ttl` and `records` (fixed 60 s TTL).
  - Use `name = aws_cloudfront_distribution.x.domain_name` and `zone_id = aws_cloudfront_distribution.x.hosted_zone_id` (`Z2FDTNDATAQYW2`) [11].
  - Import as `ZONEID_name_TYPE`; `identity` with Terraform ≥ 1.12.
- AWS [20]:
  - Public hosted zones only.
  - The record name must be listed in the distribution's alternate domain names.
  - Create **A**, plus **AAAA** when IPv6 is enabled.
  - Evaluate target health: accept the default **No**.
  - Route 53 does not charge for alias queries to CloudFront.
- Route 53 is global (F14): no `region`.

## 7. AWS guidance and Security Hub CloudFront controls [19]

| Control | Severity | Check → Terraform setting |
|---|---|---|
| CloudFront.1 | High | Default root object when using S3 origins → `default_root_object` |
| CloudFront.3 | Medium | No `allow-all` in any behavior → `viewer_protocol_policy = "redirect-to-https"` or `"https-only"` |
| CloudFront.4 | Low | Origin group with ≥ 2 origins → `origin_group` |
| CloudFront.5 | Medium | Standard logging (**legacy**) enabled → `logging_config.bucket` (see M2) |
| CloudFront.6 | Medium | WAF Classic or WAFv2 web ACL associated → `web_acl_id` (WAFv2 ARN) |
| CloudFront.7 | Low | Custom SSL/TLS certificate (not the default certificate) → `acm_certificate_arn` |
| CloudFront.8 | Low | SNI for the custom certificate → `ssl_support_method = "sni-only"` |
| CloudFront.9 | Medium | Encrypted traffic to custom origins: fails on `http-only`, or on `match-viewer` + `allow-all` → `origin_protocol_policy = "https-only"` |
| CloudFront.10 | Medium | No `SSLv3` in `origin_ssl_protocols` → `["TLSv1.2"]` |
| CloudFront.12 | High | S3 origin points to an existing bucket (periodic check; prevents bucket takeover) |
| CloudFront.13 | Medium | OAC on S3 origins → `origin_access_control_id` |
| CloudFront.14 | Low | Tagged (`requiredTagKeys`, up to 6) → `tags` or provider `default_tags` |
| CloudFront.15 | Medium | Recommended TLS policy ∈ {`TLSv1.2_2021`, `TLSv1.2_2025`, `TLSv1.3_2025`} (custom certificates only) → `minimum_protocol_version` |
| CloudFront.16 | Medium | OAC for Lambda function URL origins → OAC with `origin_access_control_origin_type = "lambda"` |
| CloudFront.17 | Medium | Trusted key groups, not trusted signers → `trusted_key_groups` |

Control IDs .2 and .11 do not appear on the page (retired or not listed).

More AWS guidance [18][21][22]:
- Prefer ACM public certificates in us-east-1.
- Renew imported certificates at least 24 h before `NotAfter`.
- ACM-issued RSA keys go up to 2048 bits. ECDSA uses prime256v1 or secp384r1.

## 8. Unverified / medium-confidence items and coverage limits

- U1 `is_ipv6_enabled` default: not stated on the provider page. Always set it explicitly.
- U2 `price_class` default: not stated. Always set it explicitly.
- U3 Whether the provider accepts `TLSv1.2_2025` / `TLSv1.3_2025` in `minimum_protocol_version`: the page gives examples only. AWS supports both [22].
- U4 Cache policy TTL defaults: not stated.
- U5 Managed cache/origin-request policy names ↔ IDs: not verified. Use the data sources.
- U6 The legacy claim "mixing `forwarded_values` and `cache_policy_id` causes a provider error" is not stated on the provider page.
- U7 The legacy claim "CloudFront IAM actions do not support resource-level restrictions": the CloudFront IAM page was not fetched.
- U8 CloudFront Functions AWS quotas (the legacy file says 10 KB code and 1 ms): not fetched. The provider allows `code` up to 40960 bytes.
- M1 The WAFv2 ACL "Global (CloudFront) region" is assumed to be us-east-1 with `scope = "CLOUDFRONT"`. WAFv2 docs were not fetched in this unit; see the waf unit.
- M2 A distribution with only v2 logging probably fails CloudFront.5. This is inferred from "only evaluates standard logging (legacy)".
- M3 WebFetch paraphrases page text, so verbatim NOTE wording may differ slightly. The substance was confirmed on the raw markdown.
- L1 CHANGELOG read in two 100k-character chunks: 6.70.0 → partially 6.55.0, then 6.54.0 → 6.40.0. Part of the 6.55.0 section may have been missed.
- L2 Raw `main` markdown may run slightly ahead of 6.70.0 (F12).
- L3 Not covered: `aws_cloudfront_vpc_origin`, `continuous_deployment_policy`, `realtime_log_config`, `key_value_store`, multitenant distribution and tenant, trust store, connection function, `monitoring_subscription`, field-level encryption, and Lambda@Edge.

## 9. Legacy-file claims found wrong or outdated (6.47.0 checklist)

1. Its `minimum_protocol_version` validation list includes `TLSv1.2_2022_q3`, which is not an AWS security policy [22]. It also omits `TLSv1.2_2025` and `TLSv1.3_2025`, which Security Hub CloudFront.15 accepts [19].
2. Its examples imply `TLSv1.2_2021` as a default. The provider default is **`TLSv1`** [11]. You must set the value explicitly.
3. Its backend uses `dynamodb_table`, which is deprecated; use `use_lockfile = true` (F7). It also uses `required_version = ">= 1.9"` and `~> 6.0`; the target is `~> 1.16` / `~> 6.69` (F1, F3).
4. It states "CloudFront Functions code size 10 KB". The provider accepts `code` up to 40960 bytes and offers runtime `cloudfront-js-2.0` [16]. The AWS quota was not verified (U8).
5. It treats `aws_cloudfront_response_headers_policy` without noting the 6.0 change that `etag` is computed only [9]. It also omits the `create_before_destroy` delete-ordering NOTE [15].
6. Its variable defaults `price_class` to `PriceClass_100` as if that were a recommendation. The provider states no default (U2), so this is a cost or coverage choice, not a fact.

## 10. Security note

- No prompt-injection or instruction-like text was observed in any fetched page.

## Source Bibliography

All fetched 2026-10-22.

8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown (via F5/F14)
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

Family facts F1–F7, F11–F15: `c:\agents\agents-factory\workspace\aws-terraform\_family_facts_v6.md` (sources dated there).
