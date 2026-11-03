# Quality validation — provisioning-aws-sam-v6 (round 1)

Validator: quality-validator, 2026-10-23. Target: `packages/aws-terraform/.apm/skills/provisioning-aws-sam-v6/` (SKILL.md 207 lines, 10 blueprints, all <= 107 lines).
Compared against: research_AWS_SAM_tf-aws-v6.md, _family_facts_v6.md, hybrid-format-checklist, tag-notation-and-registers, evidence-rule, skill-frontmatter.
Not done: WebFetch spot-check of the two provider pages (no WebFetch tool in this session). Provider-page claims were verified against the research's [P] tags only.

## Counts

HIGH 1 | MEDIUM 2 | LOW 5

## HIGH

H1. SKILL.md:105-107 (Always Do bullet "Use `CAPABILITY_AUTO_EXPAND`") is not limited to what the AWS CreateStack page says.
- The page (research §6) says it is required when a template with macros is created directly "without first reviewing the resulting changes in a change set", and that this "includes the AWS::Include and AWS::Serverless transforms".
- The bullet drops the "without first reviewing ... change set" condition and turns it into an unconditional imperative for `aws_cloudformation_stack`.
- The step "a SAM template in `template_body` therefore needs it" is the research's [I] inference, and the research marks it open as U4 (whether the provider uses change sets).
- unverified-and-risks.md:26 states U4 "affects the need for `CAPABILITY_AUTO_EXPAND`". An Always bullet that depends on an open U-item contradicts the register.
- The same overreach appears in the HCL at always-do-cloudformation.md:67 and in Scenario 4 (evaluation-scenarios.md:92).
- Fix: keep the bullet to AWS's literal statement, e.g. "AWS says `CAPABILITY_AUTO_EXPAND` is required when a template using the `AWS::Serverless` transform is created without first reviewing a change set." Move the "needed for provider-created stacks" conclusion to Ask First as `(unverified)` under U4. Alternatively demote the bullet.

## MEDIUM

M1. SKILL.md:141 (Never row 2) cites only the `sam build` page for "`--terraform-project-root-path` or `--terraform-plan-file` ... both require it".
- Research §3.3 sources `--terraform-plan-file` to the start-api page and the getting-started guide, not the build page.
- The blueprint (never-do-sam-cli.md:35-36) and Quick Reference (line 161) cite start-api correctly.
- Fix: add the start-api URL to the row, or split the row.

M2. SKILL.md:34 (Version Context, "Hook status") states an absence claim without a tag.
- The claims are "No preview/beta/deprecation label on the pages read; no 2026 status change stated".
- Evidence-rule row 4 requires `(medium confidence, absence of evidence)` for absence claims. The Ask First row at line 125 tags the same fact `(unverified)`, so the tag differs between places ("same claim, same tag").
- Fix: tag line 34 and line 125 identically and map the tag in the register. U2 is currently the only anchor.

## LOW

L1. SKILL.md:32-33 contain more untagged absence claims in the Version Context table.
- "the five newest releases list no Terraform change" (line 32).
- "Minimum Terraform ... Not stated" (line 33). U1 is tagged only in Ask First, line 124.
- Fix: add `(medium confidence, absence of evidence)` or point to U1.

L2. SKILL.md:123 (Ask First row 2) body says "Inference, not an AWS recommendation", but the tag is plain `(unverified)`.
- Rows at lines 128-129 use `(unverified, inference)`.
- The register maps it to U8, which also notes inference.
- Fix: use `(unverified, inference)` for consistency.

L3. always-do-cloudformation.md:101 and never-do-cloudformation.md:54 put the unverified attribute `parameters` inside `ignore_changes` in a CORRECT block.
- It is tagged `(unverified)` and registered as U10, so it is compliant.
- No Always or Never row depends on the attribute name. Always bullet 18 (SKILL.md:114) and Never row 7 (line 146) name only `lifecycle { ignore_changes }`.
- Consider labelling the CORRECT block as illustrative so a reader does not copy it as confirmed.

L4. SKILL.md:40 and unverified-and-risks.md:14 give the v7 quote (the F18 quote) with no URL at that line.
- The URL appears at line 192, and the register's bibliography lists the upgrade guide.
- Fix: add an inline link.

L5. Always bullet 1 (SKILL.md:62-64) is two claims (`~> 1.16` and `~> 6.69`).
- Its single URL (the version-constraints page) supports only `~>` for root modules. The values 1.16 and 6.69 are family decisions, not on that page.
- Fix: split the bullet or word it as a project policy.

Informational, not counted: SKILL.md is 207 lines. The checklist target is 100-200 and the hard limit is 500. It does not hurt readability.

## Rule checks

1. Never rows (11)
   - SKILL.md has 11 rows, the hub never-do-patterns.md has 11, and the blueprints have 5+4+2 = 11, all one-to-one. Anchors resolve.
   - Each row is a [P] or [A] fact. The Instead cells are sourced: row 4 "omit the flag" is the page's own condition; row 5 is the page's stated mitigation; rows 6-7 follow the page and CHANGELOG notes.
   - No [I] statement is in a Never row. Row 2 has the source defect in M1.
   - Row 7 (stack set `NoEcho`) and Always 18 do not depend on the unverified attribute name (see L3).
   - Row 6 states that `sensitive()` masks only plan/show output, and pairs it with a secured backend.
2. Always Do (18)
   - There are 18 bullets, with no tags and one inline URL each.
   - Bullets 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17 and 18 match their sources. Bullet 1 is L5. Bullet 15 is H1.
3. Scope
   - SAM-is-not-a-provider-resource is stated at SKILL.md:12, before any pattern.
   - Supported commands are only `sam build` and `sam local invoke/start-api/start-lambda` with `--hook-name terraform`.
   - `sam deploy/sync/validate` are never claimed to work. The absence is tagged `(medium confidence, absence of evidence)` and mapped to M3.
   - The minimum Terraform version is not stated; v1.6.0 is given for Terraform Cloud only.
   - No 2026 status change is stated (tagging gap in M2).
4. IDs and tags
   - No F#/M#/U# ids, [I]/[P]/[A] tags or research-process wording in SKILL.md or the pattern blueprints. The ids appear only in the register.
   - Tag notation is plain.
   - Tags and the register are consistent: U1-U12, M1-M3, L1-L4 are present, the mapping covers every in-text tag, and there are no orphans. U10, U11, U12, M3 and L4 are accounted for.
   - Issues: M2 and L2.
5. Placeholders
   - Example and placeholder values are marked `# example`.
   - Backend `bucket`, `key` and `region` are placeholders (always-do-foundation.md:24-26).
   - `sam local` examples omit the resource-ID argument (always-do-sam-cli.md:19-21). The `sam build` ID is an example.
6. Legacy claims: none reproduced.
   - No `>= 1.7`, `~> 6.0` or `dynamodb_table` as correct.
   - SAR `capabilities` is stated as Optional/Computed since 6.52.0.
   - "Nested" appears only in evaluation scenario `must_not`.
   - No claim that Terraform cannot detect drift; the drift row is "page says nothing".
   - The SAM Terraform hook is covered.
7. Dates
   - Shared-fact sources are dated 2026-10-23.
   - The Terraform 1.17.0 CHANGELOG is dated 2026-10-22 (register lines 3 and 102).
   - 1.16.7 is dated 2026-10-22, SAM CLI v1.170.0 2026-10-22, and v1.166.2 2026-09-11.
   - All match.
8. Upgrade path and v7
   - The upgrade path matches F17 wording, and the v7 quote matches F18.
   - The 6.52.0 entries (plaintext `NoEcho` in state, one-time manual state reconciliation, `capabilities` Required to Optional/Computed, change-set bug) are all cited to the CHANGELOG.
9. Structure
   - Frontmatter has only `name` and `description`. The description is quoted, about 265 characters, and contains "Use when".
   - `name` equals the folder.
   - Quick Navigation, Version Context (with a Source column), the three-tier sections and Quick Reference are present.
   - There are 5 evaluation scenarios covering canonical, edge, rejection and trap cases.
   - Blueprint files are <= 160 lines and all anchors resolve.

## Claims sampled

About 60 claims were checked: 18 Always bullets, 11 Never rows (including the Instead cells), 13 Ask First rows, 16 Quick Reference rows, 8 Version Context rows, and about 10 HCL and bash comments or example values. All were traced to the research tags. Only H1, M1 and M2 were material mismatches.
