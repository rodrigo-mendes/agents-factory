# Quality validation — provisioning-aws-cost-management-v6 (round 1)

Date: 2026-10-23. Target: packages/aws-terraform/.apm/skills/provisioning-aws-cost-management-v6/ (SKILL.md + 9 blueprints).
Method: full read of all 10 files against the research file, family facts F1-F19 and the three policy files. About 60 claims sampled.
Limits: WebFetch was not available, so the live spot-check of budgets_budget and cur_report_definition was NOT done. Rows were verified against the research text only. `scripts/verify_skill.py` was not run (no shell). The VPC reference skill was not opened.

## Counts
HIGH 0 · MEDIUM 13 · LOW 12

Line counts (grep): SKILL.md 152, always-do-budgets 158, always-do-reporting-commitments 154, always-do-cost-intelligence 78, never-do-budgets-and-region 117, never-do-reporting-migration 107, evaluation-scenarios 104, unverified-and-risks 95, always-do-patterns 19, never-do-patterns 17. All are within limits. Frontmatter is valid: name equals folder, quoted description of about 276 characters containing "Use when".

## Never rows (10), checked against the research text
All 10 rows are one-to-one across SKILL.md lines 93-102, never-do-patterns (hub) and the 10 blueprint sections. None carries a tag. Each is High, sourced, and has a ✅ Instead cell.

| # | Row | Verdict |
|---|---|---|
| 1 | `region` | Pass. See the region analysis below. |
| 2 | `cost_filter`/`filter_expression`, `metrics`/`cost_types` | Pass. Research §3 "Conflicts (documented)". Inference noted at L-6. |
| 3 | `and`/`or` with fewer than 2 operands | Pass. Quote matches research §3. |
| 4 | Budget tags as cost-allocation tags | The quote is sourced to the best-practices page. The Instead cell has no source in SKILL.md (M-7). |
| 5 | `execution_role_arn` from another account | Pass. Research §4. |
| 6 | CUR without `s3_prefix` | Pass. Sourced to the 6.0 guide. |
| 7 | `ATHENA` misuse | Pass. Research §7.1. |
| 8 | Destroying an active Savings Plan | Pass. Research §8 WARNING. |
| 9 | Pin 6.57.0 | Pass. F4, High. |
| 10 | `dynamodb_table` | Pass. F7. |

**`region` row analysis.** The row does NOT rest only on absence. SKILL.md line 93 cites the enhanced-region-support guide's global list (F14, High). That list positively names Budgets, Billing, Cost Explorer, Cost Optimization Hub, CUR, Data Exports and Savings Plans as having no `region` argument and no `@region` import. It can stay in Never Do. The absence-flavoured "documents no region" wording appears only in headers and intros (L-1). It does not feed the row.

## MEDIUM

- **M-1** SKILL.md:22. The Version Context row says the `identity` block is "documented on" four named resource pages, but cites only the vpc page. The vpc page cannot state this. Cite the four pages (research [3][4][5][8]) or drop the list.
- **M-2** SKILL.md:51, 21, 110. `~> 6.69` is cited to the version-constraints page, which does not state it. That value comes from the releases page (F3). Line 51 also bundles two claims (root `~>` plus reusable `>=`). Split the bullet and cite each claim to the page that states it. Likewise `~> 1.16` is a skill decision, not a page statement (line 110 says "this skill").
- **M-3** SKILL.md:113. The "Not the resource region" row cites only the budget_action page. `s3_region` (CUR page, Data Exports page) and the Savings Plans exported `region` (savings plan page) are stated on other pages. Split the row or add the URLs.
- **M-4** SKILL.md:114. The action import format `AccountID:ActionID:BudgetName` is on the budget_action page, but the row cites only budgets_budget.
- **M-5** SKILL.md:119. "SNS topic in the same account" is cited to budgets-best-practices. The research attributes it to the budgets-sns-policy page [19]. The "10 emails and one SNS topic per alert" part is correctly cited.
- **M-6** SKILL.md:83-87 (Ask First). Row 83 states "cannot be cancelled or deleted" and "best effort" with no URL and no tag. Row 84 states "up to 24 hours" with no URL. Row 86 states "SNS topic must be in the same account" as untagged fact with no URL. Add inline sources.
- **M-7** SKILL.md:96 and never-do-budgets-and-region.md:78. The Instead cell ("Activate tag keys with `aws_ce_cost_allocation_tag`") has no source in the SKILL row. The blueprint sentence "Tags on a budget do not activate anything" goes beyond the quoted AWS sentence and has no source. Cite the ce_cost_allocation_tag page in the row. Delete or source the extra sentence.
- **M-8** SKILL.md:134, 136-137. Line 134 says the guide has "only in-scope entry" (an absence claim) untagged, while line 135 tags the same absence. Tag them consistently. Lines 136-137 (CHANGELOG 6.62.0 and 6.48-6.70.0) have no CHANGELOG URL; the section's only Source line is the upgrade guide.
- **M-9** always-do-budgets.md:47, 50. The example values `comparison_operator = "GREATER_THAN"` and `threshold_type = "PERCENTAGE"` are not in the research. They are marked as examples and are plausible, but unsourced. The comment "confirm allowed values on the page" defers verification to the reader. Research gives only the ACTUAL/FORECASTED enum for `notification_type`. Fetch the allowed values from the page and cite them, or remove the values.
- **M-10** always-do-budgets.md:92 and always-do-reporting-commitments.md:50, 55, 68, 73. The `StringEquals` (SourceAccount) and `StringLike` (SourceArn) operators are not in the research, which gives only `ArnLike` for the SNS policy. They are marked as examples, but the CUR bucket policy is an AWS-documented policy. Take the operators from the AWS pages (cur-s3, budgets-sns-policy) and drop the "confirm on the AWS page" comments.
- **M-11** always-do-reporting-commitments.md:101. `query_statement = "SELECT 1"` is a marked placeholder with no source. It is probably rejected at apply, because Data Exports queries must select from a CUR 2.0 table. A hybrid skill's only Data Exports HCL should not use a probably-invalid value. Use a documented query from the page, or an obviously fake template string such as `"<query from the aws_bcmdataexports_export page>"`.
- **M-12** Research-process wording in shipped text (rule 3). No F#/M#/U# ids appear outside the register. However, SKILL.md:85 and :87, and register rows U2 and U5, say "was not checked", "was not read" and "only the current page was read". HCL comments say "confirm on the AWS page" (always-do-budgets 47/50/92, reporting 50/55). Ask First row 87 (Cost Explorer API pricing) asks the user about a claim nobody made. Reword as a state of the docs, or drop it.
- **M-13** always-do-reporting-commitments.md:141. "The `savingsplans_plan` page name does not exist" is an untagged absence claim (a 404) with no URL. Tag it `(medium confidence, absence of evidence)` with a register row, or cite the 404 URL with its date.

## LOW

- **L-1** Absence-flavoured wording about `region`: SKILL.md:11 ("none of the 9 resource pages documents..."), always-do-cost-intelligence.md:4, always-do-reporting-commitments.md:4. It is supported by the guide's global list; rephrase as "global per the enhanced-region guide".
- **L-2** Always Do bullets that carry more than one claim: SKILL.md:57 (operands plus metrics), :63 (same account plus execution/reversion), :71 (resource name plus upfront rule), :51.
- **L-3** evaluation-scenarios.md:88 and :100 reproduce the legacy claims ("$0.01/day", "5 emails and 10 SNS topics") verbatim. They are used as a trap with a corrected `must_not`. Acceptable, but confirm it is intentional.
- **L-4** Register format: the mapping heading is "Tag to Register Mapping" (policy: "Tag to register mapping"). The column header is "Tag text" (policy: "Tag text used in the skill"). The M3 status text "(medium confidence) it is a documentation error" reads as a fact after the tag. No irregular IDs (U-, M-, L- all correct) and no orphan tags. Tags and register are consistent: M1-M6 and U1-U5 are all mapped. Absence tags are present for the 6.0 guide, the CHANGELOG and Security Hub.
- **L-5** never-do-budgets-and-region.md:68. The `and { }` block with a "one operand" comment is an empty block. The CORRECT branch has no HCL.
- **L-6** never-do-budgets-and-region.md:56. "use cost_types (not metrics) with cost_filter" is an inference from the conflict set, not a stated page rule.
- **L-7** SKILL.md:101. "or any non-withdrawn patch" is loosely sourced. Only 6.57.0 is known withdrawn (F4).
- **L-8** Migration section (SKILL.md:131-133) omits two F17 elements: "no deprecation warnings related to the guide" and "the guide states no minimum Terraform version". The wording that is present is exact.
- **L-9** SKILL.md:19. "Not released" for v7 cites only the upgrade guide. "No 7.x release" comes from the releases page (F18).
- **L-10** SKILL.md:24 states 1.17.0 stable (2026-10-21) with no inline URL. It links to the risks blueprint, which has one.
- **L-11** F1 internal date: the F1 text says 1.16.7 was released 2026-10-23, while the skill (per the review brief and F19) says 2026-10-22. The skill matches the brief. Confirm F1 wording.
- **L-12** The spot-check of the live pages could not be done (no WebFetch).

## Rule checklist results

1. Never rows: pass (see table). The `region` row stays in Never Do.
2. Always Do: 13 bullets, High-only, no tags, one URL each. Bullets 51, 57, 71 carry two claims (L-2). Budgets blueprint 158/160 lines and reporting 154/160 lines pass.
3. No F#/M#/U# ids outside the register. Process wording found (M-12). Plain tag notation. Tags and register are consistent, with no orphans.
4. Example values: no wrong value found (HIGH 0). `GREATER_THAN`/`PERCENTAGE` and `StringEquals`/`StringLike` are plausible but unsourced (M-9, M-10). `SELECT 1` is a likely-invalid placeholder (M-11).
5. Citations: M-1, M-3, M-4, M-5. `ssm_action_definition.region`, `s3_region` and the Savings Plans exported `region` are correctly NOT presented as the resource region. The resource name `aws_savingsplans_savings_plan` is correct.
6. Legacy claims: not reproduced as facts. 500 monitors is correctly per management account. SNS same-account, not region (U3). The SNS policy has both `aws:SourceAccount` and `aws:SourceArn`. No $0.01/day budget pricing outside the eval trap (L-3).
7. Dates: shared sources 2026-10-23, 1.17.0 CHANGELOG 2026-10-22, 1.16.7 2026-10-22. Consistent with F19 (L-11 noted).
8. Upgrade path: F17 wording exact. v7 quote matches F18. The `aws_cur_report_definition` `s3_prefix` entry is present at SKILL.md:134.
