# Route 53 skill evaluation, round 1

Skill: packages/aws-terraform/.apm/skills/provisioning-aws-route53-v6
Method: I read SKILL.md and all 7 blueprints, then answered each scenario myself using only skill content, then judged. No subagents were used.

## Scenario 1, Canonical (7/7 must_pass, 0/4 must_not violated): PASS
Response used: always-do-zones-records.md §1-4 and always-do-logging-dnssec.md §5.
- required_version "~> 1.16" and aws "~> 6.69": PASS. Evidence: the §1 terraform block.
- No region on Route 53 resources: PASS. The us-east-1 pin goes through `provider = aws.us_east_1` on the log group, resource policy and KMS key only.
- Alias block has name, zone_id and evaluate_target_health, with no ttl or records: PASS. Evidence: the `www` record in §3.
- Failover: PASS. `set_identifier`, `failover_routing_policy` PRIMARY and SECONDARY, and `health_check_id` on the primary (§4).
- Log group in us-east-1 with retention_in_days: PASS. Evidence: `provider = aws.us_east_1` and `retention_in_days = 90` (§5).
- aws_cloudwatch_log_resource_policy for route53.amazonaws.com, plus `depends_on` from the query log: PASS (§5).
- use_lockfile = true: PASS (§1 backend).
- must_not items (region on zone/record, alias with ttl, log group outside us-east-1, dynamodb_table): all OK.

## Scenario 2, Edge case (6/6 must_pass, 0/3 must_not violated): PASS, with a wording caveat
- Core Route 53 resources are global and take no region: PASS (SKILL.md Version Context, never-do §1).
- aws_route53_resolver_endpoint and aws_route53_resolver_rule_association accept an optional region, flagged medium confidence: PASS.
  - Caveat: the skill documents the carve-out for the whole `aws_route53_resolver_*` family. Its sources list `resolver_endpoint`, but `resolver_rule_association` appears only in always-do §7 sources.
  - The two names in the criterion are a subset of the skill's claim, which is acceptable.
- DNSSEC KMS key is customer managed, asymmetric ECC_NIST_P256, SIGN_VERIFY, in us-east-1: PASS (always-do §6).
- DNSSEC applies to public zones only: PASS.
- KSK and hosted_zone_dnssec do not publish the DS record at the parent: PASS. The skill flags this as M2, medium confidence.
- Alarms on DNSSECInternalFailure and DNSSECKeySigningKeysNeedingAction: PASS.
- must_not items: all OK. The response states the Resolver carve-out, says DNSSEC is not supported on private zones, and says the chain of trust is not established by these resources.

## Scenario 3, Misuse rejection (4/4 must_pass, 0/2 must_not violated): PASS, with an inconsistency in the skill
- Rejects mixing inline vpc blocks with zone_association ("perpetual difference in plan output"): PASS (never-do-zones §1).
- ignore_changes = [vpc] mentioned only as a workaround: PASS.
- records_exclusive reconciles only on apply and does not prevent out-of-band creation: PASS. Evidence: never-do-zones §4, "reconciles only on apply and does not prevent out-of-band creation".
- Every aws_route53_record must be mirrored, and default NS/SOA excluded: PASS, but the skill contradicts itself here.
  - SKILL.md Ask-First and Never-Do say "default NS/SOA must be excluded".
  - never-do-zones §4 says "excluding the default NS/SOA gives persistent drift".
  - The same section's Alternative says to "mirror every record and default NS/SOA exactly".
  - I could only answer by following SKILL.md, which matches the criterion. The skill does not give one consistent answer.
- must_not items: both OK.

## Scenario 4, Anti-pattern trap (5/5 must_pass, 0/4 must_not violated): PASS
- Rejects region on aws_route53_zone: PASS (never-do-region §1).
- failure_threshold has no documented default, so set it explicitly and do not assume 3: PASS. Evidence: SKILL.md Quick Reference "Not stated in provider doc (unverified) — set explicitly" and U1 "do not state a default".
- Rejects ttl on an alias record: PASS.
- Rejects pinning 6.57.0 (withdrawn) and suggests ~> 6.69: PASS.
- Rejects dynamodb_table and suggests use_lockfile = true: PASS.
- must_not items: all OK.

## Overall
- Pass rate: 4/4 scenarios PASS, 22/22 must_pass, 0/13 must_not violated (100%).

## Fixes needed (short)
1. Resolve the NS/SOA contradiction in never-do-zones-records.md §4. "Excluding the default NS/SOA gives persistent drift" conflicts with SKILL.md "default NS/SOA must be excluded". Align with the provider doc for `aws_route53_records_exclusive`.
2. Scenario 2 criterion 2 is slightly over-specific. It names `resolver_rule_association` specifically. Either reword it to "aws_route53_resolver_* resources" or add that resource to the SKILL.md Version Context source row.
3. Scenario 2 criterion 5 depends on a medium-confidence item (M2). This is fine, but the judge should accept either flagged or unflagged phrasing.
