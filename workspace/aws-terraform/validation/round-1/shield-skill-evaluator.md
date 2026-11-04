# Evaluation Report: provisioning-aws-shield-v6 (round 1)

Method: no sub-agents. I answered each scenario myself using only SKILL.md and its linked blueprints, then judged the answer.
Files read: SKILL.md, always-do-patterns, always-do-subscription-protection, always-do-detection-response, never-do-patterns, never-do-shield, unverified-and-risks, evaluation-scenarios.

## Scenario 1: Canonical (CloudFront + NLB)

Simulated response (summary):
- A `terraform {}` block with `required_version = "~> 1.16"`, `aws ~> 6.69`, and an S3 backend with `use_lockfile = true`.
- `aws_shield_subscription` with `auto_renew = "ENABLED"`. The answer notes the 1 year commitment with a monthly fee, and that the amount is unverified.
- `aws_shield_protection.cdn` with `resource_arn = aws_cloudfront_distribution.main.arn`.
- `aws_shield_protection.nlb_eip` with `arn:${partition}:ec2:${region}:${account}:eip-allocation/${aws_eip.nlb.id}`.
- No `region` on any `aws_shield_*` resource.

| Criterion | Verdict | Evidence |
|---|---|---|
| required_version ~> 1.16 and aws ~> 6.69 | PASS | subscription §1 HCL |
| aws_shield_subscription plus 1 year commitment and monthly fee | PASS | subscription §1: "Subscribing requires a 1 year commitment with a monthly fee" |
| CloudFront protection by ARN | PASS | subscription §2 `aws_shield_protection.cdn` |
| NLB via EIP allocation ARN | PASS | subscription §2 `nlb_eip` |
| No region on aws_shield_* | PASS | never-do §1 |
| use_lockfile = true | PASS | subscription §1 backend |
| must_not: NLB ARN as resource_arn | OK | not used |
| must_not: region on shield resources | OK | not used |
| must_not: dynamodb_table | OK | not used |

Verdict: PASS (6/6 must_pass, 0 violations).

Note: the backend block has `region = "eu-west-1"`. A strict judge could confuse this with "region on shield resources". The criterion says `aws_shield_*`, so it is not a violation, but the wording could be tightened.

## Scenario 2: Health checks and hosted zones

Simulated response (summary):
- No, not on every protection.
- Health-based detection works with any resource type except Route 53 hosted zones, so the hosted-zone protection gets no association.
- The health check must report healthy when associated, must be relevant to the resource, and must not be deleted while in use.
- Example: `aws_shield_protection_health_check_association.cdn` with `health_check_arn = var.health_check_arn` and `shield_protection_id = aws_shield_protection.cdn.id`.
- Health checks are required for SRT proactive engagement (detection §4 and §6).

| Criterion | Verdict | Evidence |
|---|---|---|
| Works with any type except hosted zones | PASS | detection §4, first sentence |
| Must report healthy and be relevant | PASS | detection §4 |
| Shows the association with health_check_arn and shield_protection_id | PASS | detection §4 HCL |
| Health checks required for proactive engagement | PASS | detection §4: "Health checks are required for SRT proactive engagement" |
| must_not: claim every protection needs one | OK | answer says no |
| must_not: associate with the hosted zone | OK | omitted |

Verdict: PASS (4/4, 0 violations).

Skill issue (minor): the SKILL.md Always Do line reads "Associate a healthy, relevant Route 53 health check with each protection except hosted zones". That implies every non-hosted-zone protection must have one, which reads like a mandate. The sources say only that health-based detection is unavailable for hosted zones, and that health checks are needed for proactive engagement. Suggested rewording: "Associate ... with protections where health-based detection is wanted (required for proactive engagement); never with hosted zones."

## Scenario 3: Misuse rejection (region + automatic response)

Simulated response (summary):
- Reject `region`. Shield Advanced is global and no `aws_shield_*` page documents a region argument.
- Automatic response is not mandatory. It is legacy since 2026-03-26, when the Anti-DDoS Managed Rule Group in AWS WAF became the default, so ask before using it.
- Preferred design is the Anti-DDoS managed rule group in `aws_wafv2_web_acl` (provisioning-aws-waf-v6).
- If used, it adds a 150-WCU rule group and needs a WAFv2 web ACL on the resource.
- Do not add `region` during the upgrade either.

| Criterion | Verdict | Evidence |
|---|---|---|
| Rejects region (global, undocumented) | PASS | SKILL.md Never Do row 1 |
| Treats automatic response as legacy since 2026-03-26 and asks first | PASS | Ask First row |
| Points to the Anti-DDoS managed rule group in aws_wafv2_web_acl (provisioning-aws-waf-v6) | PASS | Ask First row |
| Needs a WAFv2 web ACL and adds a 150-WCU rule group | PASS | Ask First row: "adds a 150-WCU rule group and needs a WAFv2 web ACL" |
| must_not: add region | OK | |
| must_not: say automatic response is mandatory | OK | |

Verdict: PASS (4/4, 0 violations).

Note: the 150-WCU and WAFv2 facts appear only in the SKILL.md Ask First table. There is no blueprint HCL for `aws_shield_application_layer_automatic_response`. This is acceptable because it is legacy, but the action values (COUNT/BLOCK) are only in the Quick Reference.

## Scenario 4: Anti-pattern trap (6.57.0, dynamodb_table, destroy, $3,000)

Simulated response (summary):
- No, not correct.
- 6.57.0 is withdrawn. Use `~> 6.69`.
- `dynamodb_table` is deprecated. Use `use_lockfile = true`.
- `terraform destroy` only sets `auto_renew = DISABLED`, which AWS permits only in the last 30 days. Otherwise contact AWS Support. It does not unsubscribe immediately.
- I cannot confirm $3,000 per month. Only a 1 year commitment with a monthly fee is documented, and the amount is unverified.
- Ask before changing the subscription. Consider `skip_destroy` and `prevent_destroy`, flagged as an inference with medium confidence.

| Criterion | Verdict | Evidence |
|---|---|---|
| Rejects 6.57.0 and recommends ~> 6.69 | PASS | Never Do row; never-do §6 |
| Rejects dynamodb_table and recommends use_lockfile | PASS | never-do §5 |
| Destroy sets auto_renew = DISABLED, last 30 days only, otherwise AWS Support | PASS | subscription §1: "AWS permits only in the last 30 days; to unsubscribe outside that window contact AWS Support" |
| Does not confirm $3,000 | PASS | unverified-and-risks U2 |
| Suggests asking before changing the subscription | PASS | Ask First: "Is a 1-year Shield Advanced commitment approved...?" and "Should the production subscription get skip_destroy..." |
| must_not (all four) | OK | none violated |

Verdict: PASS (5/5, 0 violations).

Note: the "ask before changing" criterion is covered by the Ask First table only indirectly. Both Ask First questions concern subscribing and destroy protection, which is close enough.

## Summary

| Scenario | must_pass | must_not violated | Verdict |
|---|---|---|---|
| 1 Canonical | 6/6 | 0 | PASS |
| 2 Health checks | 4/4 | 0 | PASS |
| 3 Misuse rejection | 4/4 | 0 | PASS |
| 4 Anti-pattern trap | 5/5 | 0 | PASS |
| **Overall** | **19/19 (100%)** | **0** | **4/4 PASS** |

## Fixes needed (all minor, none blocking)

1. SKILL.md Always Do, health check bullet: reword "with each protection except hosted zones", which sounds mandatory (see Scenario 2).
2. evaluation-scenarios.md, Scenario 1: add "region" to the clarification "no region on `aws_shield_*`" (backend `region` is allowed). Current wording is fine, but the backend block may confuse a judge.
3. Optional: add a short HCL example for `aws_shield_application_layer_automatic_response` in a blueprint, or an explicit note that none is provided. S3 only has Quick Reference data.

No criterion demands advice the research does not give. No criterion bugs.

Limitation: this was a self-simulated run, not an independent sub-agent run, so it may be biased toward passing.
