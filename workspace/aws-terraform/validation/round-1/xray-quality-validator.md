# Quality validation, provisioning-aws-xray-v6 (round 1)

Target: packages/aws-terraform/.apm/skills/provisioning-aws-xray-v6/ (SKILL.md 147 lines + 9 blueprints, all <= 160 lines).
Method: static read against research, facts F1-F19 and the three policy files. WebFetch and Bash were not available, so no live page was re-read. Page-attribution findings come from the research file's own per-claim source markers.
Known G3 decisions (-v6 suffix, page-from-main confidence, bare "medium severity" heading wording) not reported.

## Counts

HIGH 0 | MEDIUM 7 | LOW 9

## HIGH list

None. No wrong claim was found among about 45 sampled claims. The third Never row is a documented fact, but its Instead cell is incompletely sourced (M3).

## MEDIUM

- M1: Always Do identity-import bullet, SKILL.md:80-82. The bullet says "identity-based import of X-Ray resources" and cites only xray_group.
  - The research (section 1) says the requirement is documented on all three X-Ray pages. F11's shared source is the vpc page.
  - The blueprint (always-do-sampling-groups.md:66-67) only covers the group `identity { arn }`. It never shows the rule `{rule_name}` or encryption `{region}` identity.
  - Fix: narrow the bullet to "identity-based import of `aws_xray_group`", or move to a wording the cited page fully supports.
- M2: Priority bullet, SKILL.md:59-61. It makes two claims (range 1-9999, ascending evaluation) and cites only xray-console-sampling.
  - Per the research the 1-9999 range comes from API_SamplingRule; the console page supports ascending order.
  - Fix: cite API_SamplingRule for the range, or split the bullet. The blueprint (sampling-groups:12-15) cites both pages correctly.
- M3: Never row 3, ✅ cell (SKILL.md:105, never-do-encryption.md:11-12, hub index row).
  - The ❌ side is solid: the provider NOTE is quoted verbatim and sourced to the provider page.
  - The Instead cell, "Apply type = NONE to return to default encryption", cites only the encryption console page.
  - The research attributes "Set NONE to return to default encryption" to the pair of pages [15][11]. The second is xray-api-configuration, which the skill does not cite for this claim.
  - Applying it through Terraform joins two sources: the provider page defines `NONE` as "default encryption", and the AWS page says to set NONE.
  - So it is a documented AWS fact plus a provider mapping, not a pure inference. It is not provably wrong, so not HIGH. The Never ✅ cell must be a High, sourced fact, so cite both pages or confirm the sentence is on the encryption page.
  - The CORRECT block reuses resource label "cmk" for `type = "NONE"`, which reads oddly.
  - The WRONG comment "leaves the customer managed key configured in X-Ray" is a mild extension of the NOTE. Reword to the NOTE's own wording.
- M4: SKILL.md:53, "Set `rule_name` explicitly".
  - The recommendation to set it explicitly is untagged and unsourced; the provider marks `rule_name` Optional.
  - The bullet also has two claims (explicit setting; it is id and import ID).
  - Fix: keep only the sourced claim ("`rule_name` is the resource `id` and the import ID"), or move the recommendation to Ask First / a tagged note.
- M5: Cross-service bullet, SKILL.md:77-79, plus always-do-cross-service.md:10-12.
  - The bullet covers three services but cites only the Lambda page.
  - The "Terraform knob" column (`tracing_config`, `xray_tracing_enabled`, `tracing_configuration`) has no provider-page source and no tag. It is deferred to sibling skills, but is not marked as such.
  - Fix: cite the sibling skills, mark the column "(see the owning skill)", or narrow the bullet to one claim and one URL.
- M6: evaluation-scenarios.md:67. Scenario 3 must_pass requires "aws/xray is a KMS choice, not the NONE setting".
  - The shipped skill never states this. The Ask First encryption row only lists the options, and the foundation blueprint says only "NONE means default encryption".
  - The skill cannot satisfy its own judge criterion. Add a sourced sentence to the encryption blueprint, or drop the criterion.
- M7: SKILL.md:20, 127, 131. The "Regional service: each in-scope resource documents optional `region`" row cites the enhanced-region guide. That statement is made by the three resource pages.
  - Migration line 131 ("optional `region` on every X-Ray resource") sits under the block-level "Source: version-6-upgrade" line, which does not state it.
  - Fix: cite the three resource pages or the enhanced-region guide per statement.

## LOW

- L-1: SKILL.md:25 and unverified-and-risks.md:14. The v7 quote (matches F18 exactly) has no adjacent URL. The 6.0 guide URL appears only further down.
- L-2: SKILL.md:113. The `~> 6.69` / `~> 1.16` values cite the version-constraints page, which states the rule, not these values (the releases pages do).
- L-3: SKILL.md:116. "Optional in the provider" is attributed to the AWS API page only. Add the provider page.
- L-4: SKILL.md:103. "or any non-withdrawn patch" is unsourced and cuts against the stated `~>` policy. Drop it.
- L-5: HCL values not marked as examples: `host`/`service_type`/`resource_arn = "*"` and `insights_enabled = true` (sampling-groups:31-36, 60). The group `filter_expression` placeholder is correctly marked; the other example values are marked.
- L-6: evaluation-scenarios.md:81. "Legacy Snippet Review" is research-process wording. Rename to "Outdated Snippet Review".
- L-7: unverified-and-risks.md:38. M4 combines two absence claims (CHANGELOG; default rule). The mapping row covers both, but the SKILL.md text tags only the CHANGELOG one. Split or document.
- L-8: SKILL.md:88. The Ask First OpenTelemetry row compresses "OTel SDKs/ADOT for instrumentation, Collector/CloudWatch agent for collection" into "with". It is faithful in substance.
- L-9: SKILL.md:91. "inferred, not stated" is acceptable evidence wording, but a reader may take it as process wording. Consider "(medium confidence)" only.

## Rule-by-rule check

1. Never rows: 3 rows, identical across SKILL.md, never-do-patterns.md and the two blueprints. Rows 1 and 2 are fully High and sourced, including their ✅ cells. Row 3 is the exception: M3 above.
2. Always Do: exactly 12 bullets, no tags, one URL each. The identity-import bullet's source mismatch is M1; M2, M4 and M5 break "one claim and one URL" or the "cites the page that states it" rule.
3. No F#/M#/U# ids or process wording in shipped text, except "Legacy" (L-6). Tag notation is plain parentheses.
   - Tag-to-register consistency: U1-U3 and M1-M5 are all mapped, and every tag in the text has a row. No orphans. M3, M4 and M5 absence tags appear at SKILL.md:129, 130, 122 and in always-do-cross-service.md.
4. Placeholders: the group `filter_expression` is marked "placeholder"; "example" markers are present except for L-5.
5. Dates: shared-fact sources are dated 2026-10-23, and Terraform 1.17.0 CHANGELOG 2026-10-22 at SKILL.md:17 and unverified-and-risks.md:3, 85. ✅
   - The skill states Terraform 1.16.7 as 2026-10-22 (SKILL.md:16, unverified-and-risks.md:8). This matches the brief and the other 20 skills in the family. ✅ It does not confuse release date with read date.
   - F1's literal text says "1.16.7 released 2026-10-23 (re-read)", which contradicts the brief and the family's usage. Recommend the orchestrator reword F1 so authors do not copy a wrong date. This is not a skill defect.
6. Legacy claims: none of the 7 is reproduced as true.
   - NONE = default encryption (correct).
   - Lambda Active is sampled only (correct).
   - 25 rules per region, adjustable (correct).
   - attributes rule: not supported by the docs.
   - REST-only X-Ray via API Gateway (correct).
   - rule_name Optional (correct).
   - Version pins and `dynamodb_table` appear only in Never rows and evaluation traps.
7. Maintenance mode (2026-02-25): the quotes ("will not receive new feature enhancements", "X-Ray is transitioning to OpenTelemetry (OTel) as its primary instrumentation standard") match the research. They appear under Version-lifetime risk, the Version Context table and Ask First, not in Always/Never. ✅
8. Upgrade path wording (SKILL.md:132-134) matches F17 exactly. The v7 quote matches F18. ✅

## Format checks

- Frontmatter: name equals folder; description is quoted, about 255 characters (under 300), and contains "Use when". ✅ Only `name` and `description`. ✅
- SKILL.md is 147 lines with Version Context (Source column), Quick Navigation, Always / Ask First / Never, Quick Reference. ✅
- Evaluation scenarios: 4 (canonical, edge, rejection, trap). ✅
- No absolute paths, `.github/` or relative dates found.
- verify_skill.py was not run (no shell).

## Claims sampled (about 45), result

- Pass: the 12 Always Do bullets, apart from the findings above.
- Pass: Ask First rows (encryption options, key policy U3, one config per region M2, priority U1, name/priority M1, Default rule U2, 25 rules per region, filter-expression edit, Lambda mode).
- Pass: Quick Reference rows 2-12 (apart from L-2 and L-3).
- Pass: HCL comments (checkout example values, `version` as the format version, `reservoir_size`).
- Pass: cross-service table statements (apart from the Terraform knob column, M5).
- Pass: Version Context rows for 1.17.0, 6.70.0, 6.57.0 and the SDK/Daemon maintenance mode.
