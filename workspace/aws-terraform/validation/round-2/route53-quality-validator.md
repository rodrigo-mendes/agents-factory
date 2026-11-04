# Quality validation, round 2: provisioning-aws-route53-v6

Target: `packages/aws-terraform/.apm/skills/provisioning-aws-route53-v6/` (9 files). Validated 2026-10-22. `-v6` suffix not flagged (approved).

Totals: HIGH 0, MEDIUM 2, LOW 6.

Note: WebFetch was not available in this run. Item 2 was checked against the orchestrator's summary of the official page, not a fresh fetch.

## Mechanical checks

- SKILL.md is 158 lines; the largest blueprint is always-do-zones-records at 155 lines (limit 160).
- Internal ids: a grep for F-ids, M-ids and L-ids in shipped text finds them only in the `unverified-and-risks.md` register (U1-U5, M1-M3, L1-L3). No F-id or M-id leaks into SKILL.md or any other blueprint.
- Tag notation: a grep for "confidence," and "(F" finds nothing. All tags read `(medium confidence)` or `(unverified)`.
- `.github/` and absolute paths: none.

## 1. Round-1 findings

| Id | Status | Evidence |
|---|---|---|
| H-1 | FIXED | One rule everywhere: exclude default NS/SOA. SKILL.md:91 and :105, never-do-zones-records:95-98 and :110, eval scenario 3:73. |
| H-2 | FIXED | never-do-zones-records:100-102 and :104-133 now use the real schema. See section 2. |
| M-1 | FIXED, residual in N-1 | The Resolver claim is now plain fact with the resource-page URL at SKILL.md:20 and :82. The M1 register row says "no tag". The scope is still broad, see N-1. |
| M-2 | FIXED, residual LOW | Tagged at always-do-zones-records:10-11, with register row M3 and mapping row at unverified:52. Eval scenario 1:20 still uses the claim untagged (accepts either alias or `region`). |
| M-3 | FIXED | always-do-logging-dnssec:22 now marks the ARN as "example ARN pattern; AWS scope: /aws/route53/*". |
| M-4 | FIXED | unverified:44-54 maps where each tag is used. U3, U4, U5 and M1 are explicitly "registered only for coverage". |
| M-5 | FIXED | Plain tags only (grep clean). |
| M-6 | FIXED, residual LOW | Eval scenario 2:48 is tagged `(medium confidence)`. The must_not at :54 ("establish the chain of trust") is untagged. |
| M-7 | PARTIAL, see N-2 | Each Always Do bullet now has a URL or a back-reference, and the bullets are split (SKILL.md:47-83). Two defects remain. |
| L-1 | FIXED | No F-ids in shipped text. |
| L-2 | PARTIAL | SKILL.md:133-141 now cite the guide and the CHANGELOG separately. The "Upgrade path" line at :143 is still uncited. |
| L-3 | FIXED | SKILL.md:129 cites both the record page and the vpc page. |
| L-4 | NOT FIXED | There is no `aws_cloudwatch_metric_alarm` HCL, yet always-do-patterns:3 says "Each pattern has complete HCL". The alarms bullet is at SKILL.md:80. |
| L-5 | FIXED | Marked as example values at always-do-zones-records:12 and always-do-logging-dnssec:16. |
| L-6 | NOT FIXED | unverified-and-risks.md has no Irresolvable section, no header counts, and no "I: none" note. |
| L-7 | PARTIAL | Fragment notes exist at always-do-zones-records:12 and always-do-logging-dnssec:52. Section 7 (Resolver, lines 118-145) and the never-do HCL have none. They use undeclared `aws_security_group.resolver`, `aws_subnet.a` and `aws_vpc.main`. |

No regressions found.

## 2. `aws_route53_records_exclusive` consistency

Checked against the orchestrator's rule:
- Default NS/SOA must be excluded, because including them causes persistent drift.
- The block is `resource_record_set`, with required `name` and `type`.
- Exactly one of `resource_records[value]` or `alias_target`; `ttl` is required for non-alias.
- `zone_id` is required.
- Import is by `zone_id`.
- Every `aws_route53_record` needs an equivalent block.

Every statement agrees:
- SKILL.md:91 (Ask First) and :105 (Never Do).
- never-do-zones-records:93-136, including the schema sentence (lines 100-102), the WRONG block (lines 105-122) and the CORRECT block (lines 125-133).
- Eval scenario 3, lines 73 and 76.

Both HCL blocks are schema-valid:
- `zone_id` is set.
- `resource_record_set` has `name`, `type` and `ttl`.
- `resource_records { value }` has the required `value`.

The WRONG block includes NS and has no equivalent for `aws_route53_record.www`, which is the point of the example.

Omission, not a contradiction: the skill never states "import by `zone_id`". That is optional.

Result: no contradiction, 0 HIGH.

## 3. Fresh grounding sample

26 claims, none of them checked in round 1. 24 grounded, 2 weak. The 2 are N-1 and the LOW row for the constraint source below.

Grounded claims:
- Zone comment default.
- `allow_overwrite` semantics.
- `force_destroy`.
- `enable_accelerated_recovery`.
- Cross-account `vpc_association_authorization`.
- DNSSEC one-week TTL cap.
- Multi-vendor name servers unsupported.
- DS support at the parent.
- 6.53.0 `type` change no longer forces replacement.
- 6.54.0 data source.
- 6.67.0 batch reads.
- 6.70.0 breaking import ID change.
- Terraform 1.17.0 stable (F2).
- No 7.x, v7 planned (F3).
- 6.57.0 withdrawn from GitHub and the Registry (F4).
- Disabled health checks treated as healthy.
- Delegation set conflicts with private zones.
- Reuse one resource policy across zones.
- KSK `status` default.
- ZSK managed by Route 53.
- TXT `\"\"` split.
- Geoproximity default record.
- Subdomain delegation NS record.
- Identity import needs Terraform >= 1.12.0 (F11).
- KMS key policy actions.
- Private zones use Resolver DNSSEC validation.

Tags and register:
- Every tag in the skill text appears in the unverified-and-risks.md mapping (unverified:46-52).
- Register rows U3, U4, U5 and M1 are explicitly declared "registered only for coverage" (unverified:54). I do not count them as orphans.
- The mapping row for the DS record (M2) agrees with the text at always-do-logging-dnssec:51.

## New and residual findings

### MEDIUM

N-1. Resolver `region` scope is over-generalized (SKILL.md:20, :82; Never-Do alternative at :101; never-do-region:9-10).
- The skill says all `aws_route53_resolver_*` resources document an optional `region`, and that "only" they accept it.
- The research verified only three pages: endpoint, rule and rule_association. Other `aws_route53_resolver_*` resources were not checked.
- Research M1 still rates it medium. It was dropped to untagged fact, so the confidence was lowered in the text without more evidence.
- The Never-Do alternative now carries this claim.
- Fix: scope it to the three verified resources, or tag it `(medium confidence)` with a register row. Remove "only" from the Never-Do alternative.

N-2. Always Do bullets still break the one-claim, one-URL rule in two places.
- SKILL.md:47 has no URL at all. It bundles the CLI constraint, the provider constraint and `use_lockfile`.
- SKILL.md:72 bundles three claims: us-east-1 log group, the resource policy and `depends_on`.
- Several bullets use "same page" or "above" back-references instead of an inline URL (:54, :60, :62, :68, :70, :80).
- Fix: add the Terraform constraints and S3 backend URLs to :47, split :72, and use inline URLs.

### LOW

- L-4, L-6, L-7 and L-2: not fully fixed, see the table.
- Eval scenario 1:20 and scenario 2:54 use medium-confidence content untagged.
- SKILL.md:117 cites the generic version-constraints page for `~> 6.69`. That page documents the operator syntax, not this value.

## Round-1 items not fully fixed

- M-7: partial, see N-2.
- L-2: partial.
- L-4: not fixed.
- L-6: not fixed.
- L-7: partial.
