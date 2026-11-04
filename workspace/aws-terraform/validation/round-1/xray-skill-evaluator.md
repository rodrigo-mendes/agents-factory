# Evaluation Report: provisioning-aws-xray-v6 (round 1)

Method: responses written inline from skill content only (no subagents). Skill read from packages/.

## Scenario 1 (canonical): PASS (6/6 must_pass, 0/3 must_not)
Response is built from always-do-foundation §1-2 and always-do-sampling-groups §3-4.
- required_version "~> 1.16" and aws "~> 6.69": PASS. foundation §1 has both.
- All 10 Required sampling-rule args: PASS. The §3 HCL sets all of them, plus rule_name.
- priority in 1-9999 and fixed_rate fraction: PASS. priority = 100, fixed_rate = 0.05.
- aws_xray_group with group_name and filter_expression: PASS.
- aws_xray_encryption_config type KMS with key_id, key marked as defined elsewhere: PASS. Fragment comment "aws_kms_key.xray is defined elsewhere (see provisioning-aws-kms-v6)".
- Example values marked: PASS. Inline "# example" comments.
- must_not: fixed_rate above 1 OK. filter_expression is the placeholder "<your X-Ray filter expression>", with the note "syntax is not covered by this skill", so OK. No dynamodb_table; the S3 backend uses use_lockfile = true, so OK.

## Scenario 2 (edge): PASS (4/4, 0/3)
Response draws on always-do-cross-service §5.
- Lambda Active traces only sampled requests; rate not configurable (1 req/s + 5%): PASS. A 50% rate cannot be set.
- "X-Ray only supports tracing for REST APIs through API Gateway", so an HTTP API is not covered: PASS. The quote is in the table. The HTTP API conclusion is an inference from "REST APIs only", which is reasonable.
- Points to provisioning-aws-lambda-v6 (tracing_config) and provisioning-aws-api-gateway-v6 (xray_tracing_enabled): PASS.
- Role needs xray:PutTraceSegments and xray:PutTelemetryRecords: PASS. Also covered by AWSXRayDaemonWriteAccess.
- must_not: none violated. The skill does not say a custom rule sets the Lambda rate. Its Ask First row says the rate "cannot be set".

## Scenario 3 (misuse): PASS with caveat (4/4, 0/2)
- Removal does not change X-Ray encryption: PASS. Direct quote in never-do-encryption §1 and SKILL.md Never Do.
- "NONE = default encryption; aws/xray is a KMS choice, not the NONE setting": PASS, weakly. The skill says NONE means default encryption. The Ask First row lists "Default encryption (free)" and "AWS managed key aws/xray" as separate options, so the distinction is present. The skill never says in so many words that aws/xray is selected through type = "KMS". It also gives no key_id value for aws/xray. See criterion issue C1.
- Recommends applying type = "NONE": PASS.
- Cites the provider page or the AWS encryption page: PASS. Both are cited.
- must_not: the response does not claim NONE uses aws/xray, and does not claim deletion reverts the config. OK.

## Scenario 4 (anti-pattern trap): PASS (5/5, 0/3)
- 6.57.0 rejected as withdrawn, ~> 6.69 offered: PASS.
- dynamodb_table rejected as deprecated, use_lockfile = true offered: PASS.
- rule_name is Optional and is the id: PASS. SKILL.md Always Do and Quick Reference say so.
- SDK ignores rules with attributes; API Gateway matches original request headers; the example rule is unsupported: PASS. The facts are in the Quick Reference row `attributes` and in sampling §3. "Not supported by the docs" is a mild inference. Note that the skill's Always Do says to set rule_name explicitly, which is consistent with Optional.
- 25 custom rules per region, adjustable: PASS. Ask First "Custom rule count". "Not per account" is a negation, which the skill supports by saying per region.
- must_not: none violated.

## Pass rate
S1 100%, S2 100%, S3 100% (caveat), S4 100%. Overall 4/4 scenarios PASS; 19/19 must_pass, 0/11 must_not violated.

## Flags
- C1 (criterion, S3 must_pass 2): "aws/xray is a KMS choice" is only implied by the skill. The research gives no instruction for how to select aws/xray in Terraform. Either reword to "default encryption (NONE) and aws/xray are separate options" or add the research.
- C2 (criterion, S2 must_pass 2 and S4 must_pass 4): both depend on inference ("REST only" implies HTTP API is not covered; "ignores attributes" implies the rule is unsupported). Acceptable, but could be reworded to quote the source.
- No unsourced or contradictory advice found in the skill.

## Fixes needed
1. Optionally add one sentence to always-do-foundation.md §2 or SKILL.md Ask First stating how aws/xray relates to type (KMS vs NONE), with a source, or relax criterion C1.
2. Nothing else.
