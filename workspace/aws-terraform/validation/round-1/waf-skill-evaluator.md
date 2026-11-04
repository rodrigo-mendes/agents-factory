# Evaluation report: provisioning-aws-waf-v6 (round 1)

Method: single-pass self-simulation (no subagents). Responses written using only SKILL.md and the 6 linked blueprints (foundation, resources, attach-logging, never-do-web-acl, never-do-attachment-scope, never-do-limits-provider). Date 2026-10-22.

## Overall: 4/4 scenarios PASS (19/19 must_pass, 12/12 must_not OK)

## Scenario 1: Regional web ACL, logging, ALB (PASS, 7/7, must_not 4/4 OK)
Simulated response: terraform block with `required_version = "~> 1.16"`, `version = "~> 6.69"`, S3 backend `use_lockfile = true`. Web ACL `scope = "REGIONAL"`, `default_action { allow {} }`, `visibility_config`. Inline managed rule with `override_action { count {} }` (later `none {}`), name/vendor via variables. Rate rule `limit = var.rate_limit` validated `>= 10`. Separate-resource variant `aws_wafv2_web_acl_rule` with `web_acl_arn` plus `lifecycle { ignore_changes = [rule] }`. `aws_wafv2_web_acl_association` with `resource_arn`/`web_acl_arn`. Logging config pointing at a destination named `aws-waf-logs-*`.
- must_pass: all PASS. Evidence: foundation §1, §2; resources §5; attach §6, §7, §8.
- must_not: all OK (no `action` on a rule-group statement, no `web_acl_id`/`scope` on the rule resource, no WCU hard-coding, no `dynamodb_table`).
- Notes: skill gives no concrete managed group name (variables only) and no log-destination resource, so the response had to leave those as variables. This is consistent with the criteria but makes the output less runnable. Criterion 5 is conditional and trivially satisfied.

## Scenario 2: CloudFront scope (PASS, 5/5, must_not 3/3 OK)
Simulated response: alias `aws.us_east_1`, web ACL with `provider = aws.us_east_1` and `scope = "CLOUDFRONT"`, and `aws_cloudfront_distribution.web_acl_id = aws_wafv2_web_acl.cloudfront.arn`. States never to use `aws_wafv2_web_acl_association` for CloudFront (never-do-attachment-scope §5). Labels `region = "us-east-1"` as an inference (medium confidence). Defers the distribution to provisioning-aws-cloudfront-v6. Does not claim the backend must be in us-east-1 (never-do-limits §10 calls it unverified and unrelated).
- Weakness: the pointer to provisioning-aws-cloudfront-v6 appears only as an HCL comment in foundation §3, so a judge relying on prose could miss it. Low risk.

## Scenario 3: HTTP API and legacy limits (PASS, 4/4, must_not 3/3 OK)
Simulated response: rejects `aws_apigatewayv2_stage` ("REST only; HTTP is unsupported"). Corrects the limits: hard max is 5,000 WCU and 1,500 is a pricing threshold, with validation `<= 5000`. Rate minimum is 10, with validation `>= 10`. Suggests a REST API stage ARN and provisioning-aws-api-gateway-v6.
- Notes: the skill offers no alternative for protecting an HTTP API (e.g. fronting it with CloudFront), and I did not invent one. The "points to provisioning-aws-api-gateway-v6" evidence is again only an HCL comment (never-do-attachment-scope §6).

## Scenario 4: web_acl_rule args and inline mixing (PASS, 4/4, must_not 2/2 OK)
Simulated response: rejects `web_acl_id` and `scope`. Says the argument is `web_acl_arn` and `scope` is not an argument. The parent needs `lifecycle { ignore_changes = [rule] }`. Lists inline limitations (deletion-ordering errors, spurious diffs from unpredictable order, coupled updates that may recreate all rules). Gives a corrected snippet or says to keep all rules inline.
- Notes: the skill's wording "ignore_changes = [rule]" also silences the inline rules on the same ACL. It offers "keep everything inline" as the alternative but does not say that ignoring `rule` while retaining inline blocks is awkward. The response had to stay neutral on this; it is a skill-content gap, not a failure.

## Criterion and skill issues (none blocking)
1. S1 must_pass #5 is conditional ("If rules are managed with ..."), so it cannot fail when the response uses inline rules. Consider making it unconditional.
2. S2/S3 pointers to sibling skills live only in code comments. Fix: add one prose line to the Never-Do/Always-Do text in `SKILL.md` (e.g. "CloudFront distribution: provisioning-aws-cloudfront-v6; REST API stages: provisioning-aws-api-gateway-v6").
3. `blueprints/always-do-foundation.md` §2 uses inline `rule` while `always-do-attach-logging.md` §6 uses separate resources, and no single example combines managed group + rate rule + logging + association. An integrated worked example would help S1 produce runnable output.
4. No criterion demands advice the research never gives. All criteria trace to cited sections.

## Fixes needed (short)
- Add prose cross-references to provisioning-aws-cloudfront-v6 and provisioning-aws-api-gateway-v6 in `SKILL.md`.
- Optional: unconditional wording for S1 criterion 5; add an end-to-end regional example in `blueprints/always-do-attach-logging.md`.

Caveat: self-simulated by the same model that read the skill, so pass rates are likely optimistic versus an independent forked run.
