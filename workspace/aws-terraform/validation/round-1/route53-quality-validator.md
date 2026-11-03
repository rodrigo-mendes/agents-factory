# Quality validation, round 1: provisioning-aws-route53-v6

Target: `packages/aws-terraform/.apm/skills/provisioning-aws-route53-v6/` (9 files). Validated 2026-10-22 against the research file, F1-F16, the three policy blueprints and `skill-frontmatter.md`. Reference skill: `provisioning-aws-vpc-v6`. The `-v6` suffix was not flagged, as instructed.

Totals: HIGH 2, MEDIUM 7, LOW 7.

## Mechanical checks

| Check | Result |
|---|---|
| Frontmatter: only `name` + `description`, quoted, contains "Use when", name equals folder | pass; description is about 250 chars |
| SKILL.md length 100-200 | pass, 140 lines (counted with grep) |
| Blueprint files <= 160 lines | pass; max is 152 (always-do-zones-records) |
| Required blueprints present (always/never/unverified/evaluation) | pass; 4 scenarios: canonical, edge, rejection, trap |
| `region` on global `aws_route53_*` in any HCL | none outside `# WRONG` blocks (never-do-region line 15 is the only one) |
| Removed/deprecated args outside `# WRONG` | none found. `dynamodb_table` and `6.57.0` appear only in WRONG blocks or as the warning |
| Legacy wrong claims (research section 11) reproduced | none reproduced. The failure_threshold=3 and CNAME-apex claims appear only as rejections or in the register |
| Absolute paths / `.github/` / BOM | none (the `.github` grep hits were false positives on `raw.githubusercontent`) |
| Register ids U1-U5, M1-M2, L1-L3 exist | yes. See M-4 for orphan and mapping problems |

## HIGH

H-1. `blueprints/never-do-zones-records.md` lines 95-97 and 109-110, against SKILL.md lines 76 and 90, contradict each other on the `aws_route53_records_exclusive` NS/SOA rule.
- Line 96 says "excluding the default NS/SOA gives persistent drift".
- SKILL.md line 76 says "default NS/SOA must be excluded".
- SKILL.md line 90 says "exclude default NS/SOA".
- never-do-zones-records line 109 says "mirror every record and default NS/SOA exactly in `aws_route53_records_exclusive`".
- Research section 5 is ambiguous: "exclude default NS/SOA or get persistent drift". The skill turned this into three incompatible statements, and one of them is a Never-Do row. At least one is a wrong fact.
- Fix: re-read research source [14] and quote the doc sentence verbatim. Then state one rule everywhere, with the same wording in the SKILL.md Ask First row, the Never-Do row and the blueprint.

H-2. `blueprints/never-do-zones-records.md` lines 101-105 give an invalid or ungrounded HCL "WRONG" example for `aws_route53_records_exclusive`.
- The comment "no record_set blocks mirroring aws_route53_record.www / .mx" names an argument or block `record_set`. That name is not in the research or F-facts.
- The resource shown also omits its required schema, so the example may not be valid HCL.
- Line 110 then says "see the provider doc for its argument schema", which confirms the schema was never researched.
- Fix: take the real schema from the page (source [14]) and give a valid WRONG example. Otherwise remove the argument-name claim and show the anti-pattern in prose only.

## MEDIUM

M-1. SKILL.md line 86 (Never Do row 1) and line 67 (Always Do) rest on the Resolver carve-out, which this skill tags `(medium confidence)` (M1).
- Evidence-rule: Never Do rows and their alternatives must be High only. Medium items belong in Ask First or blueprints.
- Row 1's alternative "only `aws_route53_resolver_*` accept it" carries no tag. Line 67 carries the tag, but an Always Do bullet must not hold a medium claim or a caveat.
- F16 rates the Resolver `region` fact as High, while the research (M1) says medium, so the family fact and the skill disagree.
- Fix: ask the orchestrator to settle the confidence. If it is High (F16), drop the tags and keep it in SKILL.md. If it stays medium, move line 67 to Ask First and remove the carve-out from the Never-Do alternative.
- The same claim must carry the same tag in SKILL.md line 20, line 67, line 86, always-do-logging-dnssec line 113 and the eval scenarios.

M-2. always-do-zones-records.md lines 8-9 state that setting `region = "us-east-1"` on a regional resource instead of a provider alias is valid ("both are valid"), with no tag.
- F16 classifies the alias-versus-region equivalence as an inference from F5 (medium confidence).
- The research states it as fact, citing F5. The skill copies it with no tag and no register row.
- evaluation-scenarios.md line 20 builds a must_pass criterion on it.
- Fix: tag it `(medium confidence)` and add an M3 register row plus a mapping row. Alternatively show only the alias form that the provider docs use.

M-3. always-do-logging-dnssec.md lines 21-22: the IAM policy resource `arn:aws:logs:*:*:log-group:/aws/route53/*` is not in the research.
- The research only says "on `/aws/route53/*`". The ARN is not sourced to the query_log page or [15] in the research text.
- The file's Source lines cite those pages, but nothing in the research confirms the ARN form.
- Fix: confirm against the query_log doc example, or tag it.

M-4. `unverified-and-risks.md` mapping (lines 43-51) has orphan and mismatched rows.
- U3, U4 and U5 are mapped to "Unverified Items table above". That is the register itself, not a place where the skill uses the tag. U3 (CloudWatch alarm region), U4 (CNAME at apex) and U5 (KMS rotation) appear in no SKILL.md or blueprint claim.
- Policy requires every tag used in the skill to have a row, and no orphan rows. These three are either orphans or must be surfaced where the skill makes a related claim.
- Surfacing them is justified: Always Do tells the reader to alias instead of CNAME, the DNSSEC HCL has no `enable_key_rotation`, and the health-check guidance says nothing about alarm region.
- Tags used in the text are not in the mapping with their actual locations: SKILL.md line 67 (medium), always-do-logging-dnssec lines 51 and 113 (inline "M2" / "M1" forms) and the eval scenario text.
- The mapping header is `Tag text | Where | Register id`, but the policy requires "Tag text used in the skill".
- Fix: add real where-used rows, and note U3-U5 as "register only, no claim made".

M-5. The tag notation is non-standard.
- always-do-logging-dnssec.md line 51 reads "(medium confidence, M2)". Line 113 reads "(F16, medium confidence M1)", which is not plain parentheses.
- Policy requires exactly `(medium confidence)` / `(unverified)`, so a tag grep misses these.
- Fix: write `(medium confidence)` and put the register id in the mapping only.

M-6. M2 is stated as plain fact in the eval scenarios.
- evaluation-scenarios.md lines 48 and 54 require "do not publish the DS record" and forbid "establish the chain of trust" with no tag. The SKILL.md Ask First DNSSEC row says nothing about the DS step.
- Research M2 is medium confidence. The tags are inconsistent.
- Fix: add a medium tag in SKILL.md and the eval scenarios, or mention the DS step only in Ask First.

M-7. SKILL.md Always Do bullets violate the evidence rule on form. This applies to all 11 bullets, and the points below name the worst ones.
- They carry no inline URL (the rule says one per bullet). They point only to blueprint anchors.
- Bullets 8 and 9 (lines 61 and 63) bundle 4+ claims each: log group, policy, `depends_on` and `retention_in_days`. The rule says one High claim per bullet.
- Bullet 7 (line 59) bundles Route53.1 tagging with the TTL guidance.
- Fix: split the bullets, add one URL each, move the caveats to Ask First.

## LOW

L-1. The blueprints reference internal ids `F14`, `F16` and `M1`, e.g. always-do-zones-records line 7, never-do-region line 8 and line 9, and always-do-logging line 113. These resolve only in `workspace/aws-terraform/_family_facts_v6.md`, which does not ship with the skill. The VPC reference skill has zero F-id leakage. Replace them with inline source URLs.

L-2. SKILL.md lines 116-124 ("5.x → 6.x Migration") cite the upgrade guide as the source for the whole section. Only the first bullet comes from the guide. The 6.53.0, 6.54.0, 6.67.0 and 6.70.0 items come from the CHANGELOG (research [3]). Cite the right source per bullet. "Upgrade path: `terraform init -upgrade`" comes from F8, not cited.

L-3. The Quick Reference "Record import" row (line 114) cites the `route53_record` page for "identity blocks need Terraform >= 1.12.0". That fact is F11, sourced to the vpc doc page. The research ties it to F11 without citing the record page. Cite F11's source.

L-4. always-do-logging-dnssec.md §6 says "Create CloudWatch alarms on `DNSSECInternalFailure` and `DNSSECKeySigningKeysNeedingAction`", and SKILL.md has an Always Do bullet on it. Neither has HCL, although always-do-patterns.md says "Each pattern has complete HCL". Add an `aws_cloudwatch_metric_alarm` example. That example would need its region and namespace verified, and it is not covered by the research.

L-5. `retention_in_days = 90` (always-do-logging-dnssec line 16) and `ttl = 3600` and `ttl = 60` in the HCL are illustrative values, unsourced and untagged. Mark them "illustrative" in the comments.

L-6. `unverified-and-risks.md` has no `Irresolvable (I1..)` section and no header counts. The headings "Unverified Items", "Medium-Confidence Items" and "Coverage Limits" do not follow the policy names or counts. Add the sections, or add a note "I: none".

L-7. In the HCL, `aws_vpc.main`, `aws_lb.main`, `aws_subnet.a`, `aws_security_group.resolver` and `aws_iam` are undeclared references. This is fine as a fragment, but no comment says so. Add a one-line note, as the reference skill does.

## Sampled claims

34 claims sampled. 27 are grounded, 7 are not. The 7 are H-1, H-2, M-1, M-2, M-3, M-6 and L-3.

Grounded examples: required_version and provider constraint (F1, F3); 6.57.0 withdrawn (F4); `use_lockfile` (F7); the vpc/zone_association perpetual-diff warning (research section 3); alias conflicts with `ttl`/`records`; the `set_identifier` list; record types; health check types; U1 (no stated default); the 10-policy limit; `ECC_NIST_P256`/`SIGN_VERIFY`; KMS policy principals and conditions; KSK and `signing_status` defaults; Route53.1 Low and Route53.2 Medium; TTL ranges; geolocation `country = "*"` and cidr `location_name = "*"`; query log must be us-east-1 and public.

## Recommended fix order

H-1, H-2, M-1, M-4, M-2, M-5, M-7, the rest.
