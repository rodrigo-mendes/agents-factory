# Evaluation Report: provisioning-aws-cloudfront-v6 (round 1)

Method: no subagents. I read SKILL.md and all 7 linked blueprints, answered each scenario using only skill content, then judged. Scenarios 1-4 are all in blueprints/evaluation-scenarios.md.

## Scenario 1 - Canonical (S3 + OAC + ACM + Route 53): PASS (8/8 must_pass, 0/4 must_not violated)

Response, condensed: terraform block with `required_version = "~> 1.16"`, aws `~> 6.69`, S3 backend with `use_lockfile = true`. Providers: default plus `aws.us_east_1` alias. ACM certificate with `provider = aws.us_east_1`. OAC with `signing_behavior = "always"` and `signing_protocol = "sigv4"`. Distribution with `origin_access_control_id` and no `s3_origin_config`. Bucket policy for `cloudfront.amazonaws.com` with `AWS:SourceArn` set to the distribution ARN. `viewer_certificate` with `sni-only` and `TLSv1.2_2021`. `viewer_protocol_policy = "redirect-to-https"`. `is_ipv6_enabled = true` and `price_class = "PriceClass_100"`. A and AAAA alias records using `domain_name` and `hosted_zone_id`.

| Criterion | Verdict | Evidence |
|---|---|---|
| required_version, aws ~> 6.69, use_lockfile | PASS | always-do-foundation §1 `required_version = "~> 1.16"`, `version = "~> 6.69"`, `use_lockfile = true` |
| OAC always + origin_access_control_id, no s3_origin_config | PASS | foundation §2 `# no s3_origin_config`; origins §3 `signing_behavior = "always"` |
| Bucket policy with cloudfront.amazonaws.com and AWS:SourceArn | PASS | origins §3 `identifiers = ["cloudfront.amazonaws.com"]`, `variable = "AWS:SourceArn"` |
| ACM with us-east-1 alias, no region on CF | PASS | never-do-provider §1 `provider = aws.us_east_1`. The ACM snippet is in a never-do file. |
| minimum_protocol_version + sni-only | PASS | foundation §2 `minimum_protocol_version = "TLSv1.2_2021"`, `ssl_support_method = "sni-only"` |
| redirect-to-https | PASS | foundation §2 |
| Route 53 alias with domain_name and hosted_zone_id | PASS | dns §7 |
| is_ipv6_enabled and price_class explicit | PASS | foundation §2 |
| must_not (OAI, omit min protocol, region on distribution, dynamodb_table) | all OK | none of these appear in the response |

Note: the skill has no complete ACM resource and no DNS validation recipe in the always-do files. The only ACM snippet sits in never-do-provider §1, and ACM is delegated to provisioning-aws-acm-v6. This is acceptable for the scenario. It is a minor discoverability gap.

## Scenario 2 - Edge (WAF, logging v2, region): PASS (5/5, 0/2 violated)

| Criterion | Verdict | Evidence |
|---|---|---|
| web_acl_id takes the ARN | PASS | foundation §2 `web_acl_id = var.web_acl_arn  # WAFv2: the ARN (aws_wafv2_web_acl.x.arn), not the ID` |
| Scope CLOUDFRONT in us-east-1, medium confidence on alias vs region | PASS | foundation §1: "the alias-vs-region choice for WAFv2 is an inference, (medium confidence)"; unverified-and-risks M1 |
| Delivery API in us-east-1, Firehose in us-east-1 | PASS | dns §8 "delivery API must be called in us-east-1 (a Firehose destination must also be in us-east-1)" |
| log_delivery_source with ACCESS_LOGS and resource_arn | PASS | dns §8 HCL |
| CloudFront.5 legacy-only, medium confidence | PASS | dns §8 "probably fails it (medium confidence)"; M2 |
| must_not: v2 replaces legacy | OK | the skill says "v2 does not affect legacy logging" |
| must_not: delivery destination args stated as fact | OK | the skill marks them (unverified), U9. The response must not invent arguments, and it complies by staying within the skill. |

Caveat: the response can only show the destination and delivery resources by name, with no arguments. That is correct behavior but makes the answer incomplete for the user. See fix 2.

## Scenario 3 - Misuse rejection (OAC on S3 website endpoint): PASS (3/3, 0/2 violated)

Response, condensed: S3 website endpoints cannot use OAC or OAI. Configure the website endpoint as a custom origin (`custom_origin_config`, with the `https-only` / TLSv1.2 pattern). Do not set `origin_access_control_id` on it.

| Criterion | Verdict | Evidence |
|---|---|---|
| States website endpoints cannot use OAC or OAI | PASS | origins §3 "S3 website endpoints cannot use OAC or OAI: configure them as a custom origin"; SKILL Never Do row |
| Recommends custom_origin_config | PASS | never-do-security §3 "S3 website endpoint: custom_origin_config instead" |
| No origin_access_control_id on it | PASS | the response gives no such snippet |
| must_not: OAC works, or OAI fallback | OK | neither claim is made |

Gap, not a failure: the skill has no HCL example for a website-endpoint origin. The response had to adapt the §5 ALB `custom_origin_config` snippet. The skill also gives no guidance on `origin_protocol_policy` for website endpoints, which only serve HTTP. The skill's `https-only` rule (CloudFront.9) would conflict with that, and the skill never addresses it. Its own rule would give a broken origin here. I did not penalize the response because the criteria do not require it.

## Scenario 4 - Anti-pattern trap (legacy snippet review): PASS (4/4, 0/3 violated)

| Criterion | Verdict | Evidence |
|---|---|---|
| Reject forwarded_values, use cache_policy_id / origin_request_policy_id | PASS | SKILL Never Do; never-do-provider §2 |
| Correct the default assumption: it is TLSv1 | PASS | SKILL "the provider default is `TLSv1`"; never-do-security §1 |
| trusted_key_groups over trusted_signers (CloudFront.17) | PASS | never-do-security §4 |
| Reject etag, computed only since 6.0.0 | PASS | never-do-provider §3 |
| must_not: accept TLSv1.2_2021 as default, accept etag, claim forwarded_values removed | all OK | the skill says "deprecated (not removed in 6.x)" |

## Pass rate

| Scenario | must_pass | must_not OK | Verdict |
|---|---|---|---|
| 1 | 8/8 | 4/4 | PASS |
| 2 | 5/5 | 2/2 | PASS |
| 3 | 3/3 | 2/2 | PASS |
| 4 | 4/4 | 3/3 | PASS |
| Overall | 20/20 must_pass (100%) | 11/11 | 4/4 scenarios PASS |

## Criteria quality flags

- No criterion demands advice the research never gives. All 20 are traceable to a specific skill passage.
- S2 must_not 2 ("unresearched argument names ... as verified fact") is judgeable only because the skill carries the U9 tag. It is fine.
- S1 criterion "no s3_origin_config" is a negative check inside a must_pass. That is acceptable but could be a must_not.
- S4 query says "assume TLSv1.2_2021 is the default". It is a good trap, and the skill's explicit default statement is what makes it testable.

## Fixes needed (short, none blocking)

1. Add a website-endpoint custom-origin HCL example and a note on `origin_protocol_policy` for it (website endpoints are HTTP-only). Put it in always-do-origins-policies §3 or §5. It resolves the tension with the "https-only" rule.
2. Research the arguments of `aws_cloudwatch_log_delivery_destination` and `aws_cloudwatch_log_delivery` (U9). Scenario 2 answers are incomplete without them.
3. Optional: a one-line ACM pointer (`aws_acm_certificate` plus validation, us-east-1) in always-do-foundation. It currently appears only in a WRONG/CORRECT example in never-do-provider.
