# Quality validation, round 1: provisioning-aws-cloudfront-v6

Date 2026-10-22. Target: `packages/aws-terraform/.apm/skills/provisioning-aws-cloudfront-v6/` (SKILL.md plus 9 blueprints).
Rubric: hybrid-format-checklist, tag-notation-and-registers, evidence-rule, skill-frontmatter. Grounding: research_AWS_CloudFront_tf-aws-v6.md and F1-F16.

Counts: HIGH 0, MEDIUM 7, LOW 8. Overall grade: B+ (accurate, well grounded, but not strict-clean).
Paths below are relative to the skill directory. "BP" means `blueprints/`.

## Objective checks (verified with grep and line counts)

| Check | Result |
|---|---|
| Line counts | SKILL.md 146 (within 100-200). Blueprints: dns-logging 67, foundation 98, origins-policies 146, patterns 16, eval 103, never-patterns 17, provider-ops 93, security 90, unverified 79. All are at or under 160. |
| Frontmatter | Only `name` and `description`. The description is quoted, under 300 characters (grep passes with a limit of 298), and contains "Use when". The name equals the folder. |
| Absolute paths, `.github`, relative dates, BOM | None found. The `dynamodb_table` hits are all in deprecation context or in a WRONG block. |
| Anchors | All 25 intra-skill anchors resolve. This includes the underscore anchors `#1-relying-on-the-default-minimum_protocol_version`, `#4-trusted_signers-instead-of-trusted_key_groups` and `#2-forwarded_values`, and the comma-bearing `#3-oai-for-new-s3-origins-and-oac-on-website-endpoints`. |
| Research section 9 (legacy claims) not reproduced | Pass. Grep for `2022_q3`, `10 KB` and `1 ms` returns nothing. `TLSv1` is stated as the provider default. `PriceClass_100` is labelled a cost/coverage choice. U6 and U7 are recorded only as "not reproduced". |
| `minimum_protocol_version` default | Correct and consistent: SKILL.md:52, :89 and :108, foundation:48 and :86, security:7. All say `TLSv1`, settable only with `cloudfront_default_certificate = false`. |
| U9 tag | Pass. `name` of `aws_cloudwatch_log_delivery_source` is tagged `(unverified)` at BP/always-do-dns-logging.md:42 and :47. Register U9 and the mapping row exist. |
| HCL validity | Pass. No removed or deprecated argument appears outside `# WRONG` blocks. `forwarded_values`, `etag`, `region`, OAI and `trusted_signers` appear only in WRONG blocks. |
| Sibling skills named in prose | `provisioning-aws-s3-v6`, `-route53-v6`, `-acm-v6` and `-waf-v6` do not yet exist in `packages/aws-terraform/.apm/skills/`. See LOW-8. |

## Grounding sample (35 claims)

| # | Claim (file:line) | Verdict |
|---|---|---|
| 1 | Terraform `~> 1.16` and aws `~> 6.69` (SKILL.md:16-17, foundation:14-18) | OK (F1, F3) |
| 2 | `use_lockfile`; `dynamodb_table` deprecated (SKILL.md:48, foundation:25) | OK (F7) |
| 3 | 6.57.0 withdrawn (SKILL.md:19) | OK (F4) |
| 4 | CloudFront has no `region` and no `@region` (SKILL.md:20, :50) | OK (F14) |
| 5 | ACM viewer certificate must be in us-east-1 (SKILL.md:112) | OK (research §1) |
| 6 | Logging v2 delivery API in us-east-1 (SKILL.md:113, dns-logging:33) | OK |
| 7 | WAFv2 uses an `aws.us_east_1` alias (SKILL.md:50) | See MEDIUM-1 |
| 8 | OAC `signing_behavior` always/never/no-override; `sigv4` only (origins:7-8) | OK |
| 9 | OAC bucket policy principal, `AWS:SourceArn` condition and KMS statement (origins:19-33, :43) | OK |
| 10 | S3 website endpoints cannot use OAC or OAI (SKILL.md:92) | OK |
| 11 | Object Ownership must be Bucket owner enforced (origins:8) | OK |
| 12 | `web_acl_id` takes the WAFv2 ARN (SKILL.md:58) | OK |
| 13 | `forwarded_values` deprecated, not removed (SKILL.md:94, provider-ops:31) | OK |
| 14 | `etag` computed only since 6.0 (SKILL.md:95) | OK |
| 15 | `create_before_destroy` on the response headers policy (origins:81) | OK |
| 16 | `origin_group` has exactly two members; satisfies CloudFront.4 (origins:93) | OK |
| 17 | CloudFront.3, .9, .10 mapping (SKILL.md:56, :64, :90) | OK |
| 18 | `trusted_key_groups` preferred; CloudFront.17 (SKILL.md:96) | OK |
| 19 | `encoded_key` must end with a newline (SKILL.md:97) | OK |
| 20 | Function runtime, name, `code` bounds, `publish` default, import by `name` (origins:119-121) | OK |
| 21 | Function max 2 associations (SKILL.md:83) | OK |
| 22 | Route 53 alias fields required; fixed 60 s TTL; `Z2FDTNDATAQYW2` (SKILL.md:110, :116) | OK |
| 23 | Evaluate target health: accept the default No (dns-logging:9) | OK |
| 24 | `include_cookies` default false, V1 and V2; `prefix` V1 only (dns-logging:52-53) | OK |
| 25 | CloudFront.5 checks legacy logging only, so v2 alone probably fails (SKILL.md:78) | OK and tagged M2 |
| 26 | `is_ipv6_enabled` and `price_class` defaults not stated (SKILL.md:77) | OK and tagged U1/U2 |
| 27 | `wait_for_deployment` default true; about 15 minutes (SKILL.md:80, :111) | OK |
| 28 | `retain_on_delete` disables the distribution (SKILL.md:79) | OK |
| 29 | `identity` import needs Terraform >= 1.12 (SKILL.md:118) | OK (F11) |
| 30 | Security policies list (SKILL.md:109) | OK |
| 31 | 6.49.0, 6.51.0 and 6.54.0 additions (SKILL.md:129-131) | OK |
| 32 | Upgrade path "latest 5.x, clean plan, `init -upgrade`" (SKILL.md:132) | See MEDIUM-5 |
| 33 | Failover `status_codes = [500,502,503,504]` (origins:109) | See MEDIUM-2 |
| 34 | 404 to 200 `/index.html` TTL 10 (dns-logging:60-65) | See MEDIUM-3 |
| 35 | HSTS `access_control_max_age_sec = 31536000` (origins:71) | See MEDIUM-4 |

## Findings

### HIGH
None. No wrong facts found. The TLSv1 default, F14 (no `region`) and the research §9 exclusions are all correct.

### MEDIUM

1. **SKILL.md:50-51 (Always Do) states WAFv2 uses the `aws.us_east_1` alias with no medium tag.** Research §1 and register M1/M2 say the alias-vs-`region` choice is an inference (medium confidence). The tag exists only at foundation:10. Evidence rule: Always Do bullets are High only and the same claim must carry the same tag everywhere.
   Fix: split the WAFv2 half into Ask First tagged `(medium confidence)`, or add the tag inline and map it to M1.
2. **BP/always-do-origins-policies.md:109: `status_codes = [500, 502, 503, 504]`.** The research never gives values. The snippet is untagged and not marked as an example, so it reads as a recommendation.
   Fix: add a comment such as `# example values, not in the research (unverified)`, add a register row (a new U10), and add a mapping row.
3. **BP/always-do-dns-logging.md:60-65: 404 to 200 `/index.html` with `error_caching_min_ttl = 10`.** Only the rule "set both `response_code` and `response_page_path`" is researched. The values are illustrative but untagged and not marked as an example.
   Fix: apply the same example-only comment, tag and register row as in finding 2. Also state that this is an SPA pattern the research did not verify.
4. **BP/always-do-origins-policies.md:71-73: HSTS `max-age 31536000`, `override = true`, `include_subdomains = true`.** The research contains 31536000 only as the max TTL for "Use origin cache headers" (research §3). The HSTS values are not grounded and are untagged. The comment at :68 even asserts `etag` guidance next to an unmarked value set.
   Fix: mark the values example-only, or take the value from a security-header source.
5. **SKILL.md:132: "Upgrade path: move to latest 5.x, get a clean plan, set `~> 6.69`, run `terraform init -upgrade`".** None of this is in the research. Only `init -upgrade` has a basis (F8). The sentence is untagged and presented as fact.
   Fix: remove it, tag it `(unverified)` with a register row, or cite the upgrade guide after fetching it.
6. **SKILL.md:98 (Never Do) hardcode managed policy IDs rests on U5, an unverified item.** Evidence rule: Never Do rows are High only. The alternative (data source) is fine, but the reason is unverified.
   Fix: move to Ask First, or reword on the High basis only, that the page shows an ID as an import example and does not name it.
   Related: SKILL.md:89's alternative cell embeds U3 (unverified), so the alternative is not wholly High. Move the U3 caveat to Ask First.
7. **SKILL.md Always Do bullets (lines 48-71): no inline URL on any of the 12 bullets.** Evidence rule says one inline URL per bullet. Each bullet links only to a blueprint. Sources exist in the blueprints' `# Source:` comments, so this is a format gap, not an unsupported claim.
   Fix: add one `(source)` link per bullet, as the Never Do table does.

### LOW

1. SKILL.md:93 cites the enhanced-region page for "viewer certificate outside us-east-1". That claim comes from [21] (cnames-and-https-requirements). Split the source.
2. SKILL.md:99 cites only the S3 backend page for "pin 6.57.0". The pin claim comes from the CHANGELOG. Add that source.
3. BP/always-do-foundation.md:56 uses `http_version = "http2and3"`. It is untagged and the research gives only the allowed values, not a recommendation. Mark it as an example, or use the default `http2`.
4. BP/always-do-foundation.md:57 `PriceClass_100` is correctly labelled `(unverified)` and "cost/coverage choice". Add "example" so it cannot be read as a recommendation. The label is acceptable as it stands, but it is the weakest pass.
5. BP/always-do-dns-logging.md:13 comment says "AAAA only when `is_ipv6_enabled = true`", but the `for_each` always creates AAAA. Make the code conditional or fix the comment.
6. Register mapping (BP/unverified-and-risks.md:47-55) is incomplete against the text. U5 is used in SKILL.md:98 and U8 in SKILL.md:83, but the mapping lists only the blueprint locations. U1/U2 are also used in SKILL.md:77 (listed). Add the missing SKILL.md locations. There is no `I` section, and the section headers carry no counts (U1-U9, M1-M3, L1-L3 are consistent when counted manually). There are no orphan rows in the mapping. U4, U6 and U7 are unmapped because the text does not use them as tags, which is acceptable.
7. The "Source (fetched 2026-10-22)" column in SKILL.md:16-17 points to `releases.hashicorp.com` for F1/F3 facts. This matches the family facts, so it is fine, but the 1.16.6 release date 2026-10-14 is not in the cited URL's research row. Cite the CHANGELOG as in F1.
8. SKILL.md:3, origins:45, dns-logging:10 and provider-ops:27 reference `provisioning-aws-s3-v6`, `-route53-v6`, `-acm-v6` and `-waf-v6`. None exists yet in the package. Confirm they will be generated, or reword as "planned".

## Format and register consistency
- Tags: `(unverified)` and `(medium confidence)` use plain parentheses everywhere. There is no bold or bracket variant. The word "medium" is not used for severity.
- The same claim carries the same tag across SKILL.md, blueprints and register for U1, U2, U3, U8, U9, M1 (except finding 1) and M2.
- The evaluation scenarios cover the canonical, edge, rejection and trap cases and match the skill's rules. In scenario 4 the "TLSv1.2_2021 is the default" assumption is a deliberate trap that is rejected.

## Verdict
Passes with no HIGH items. Fix MEDIUM 1-5 before marking VERIFIED. The illustrative values the author flagged (failover codes, 404 to 200, HSTS) are not clearly marked example-only. `PriceClass_100` is the only one handled adequately.
