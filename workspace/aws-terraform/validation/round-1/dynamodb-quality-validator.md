# Quality validation - provisioning-aws-dynamodb-v6 (round 1)

Validator: quality-validator (inline, no sub-agents). Date: 2026-10-23.
Target: packages/aws-terraform/.apm/skills/provisioning-aws-dynamodb-v6/ (SKILL.md 143 lines; 9 blueprints, all < 130 lines).

Limits of this review:
- WebFetch is NOT available in this run. The spot-check of dynamodb_table and appautoscaling_policy pages was not done live. Never-row facts were checked against the research file's recorded page content, not against the pages. Treat "page states it" as "research records that the page states it".
- Page-from-main confidence convention: not reported (family decision).

## Counts

HIGH 0 | MEDIUM 8 | LOW 9

Grade: structure/format PASS; evidence discipline PASS-WITH-FINDINGS (no wrong facts found, several unsourced/mis-sourced or inference-grade statements).

## Format checks (pass)

- Frontmatter: only name + description; name = folder; description quoted, about 230 chars, contains "Use when". `-v6` approved.
- Anchors and numbering: always-do-foundation 1,2,5; indexes-capacity 3,4; replication-satellites 6,7,8; never-do-table-indexes 1-5; never-do-replication-provider 1-4. All SKILL.md, hub and always-do-patterns anchors resolve (checked by hand against GitHub slug rules, including underscore and 6.57.0 -> 6570 slugs).
- Never rows: 9 in SKILL.md = 9 hub rows = 5 + 4 WRONG blocks. One-to-one, all sourced, no (medium)/(unverified) tags inside Never rows, alternatives mostly High (see M3).
- Plain tag notation everywhere (no bold or bracket variants). No F#/M#-style ids other than register ids M1/M2/U1-U7. No workspace paths.
- Legacy claims (research section 9): 1-5 are NOT reproduced. alias/aws/dynamodb is correctly the AWS managed key; GSI resource args are correct; recovery_period_in_days "new" is explicitly disclaimed (U5); no "CMK required" claim (it is rebutted).
- Section 5 test: Never-row facts 1-9 are each recorded in the research as stated by the cited page (research lines 46, 54, 58, 66-67, 75, 92, 109, 18, 14/F4). Not live-verified.

## Findings

### MEDIUM

M1. Absence claim stated untagged. SKILL.md:74 (Ask First "Encryption key") "no Security Hub DynamoDB control requires a customer managed key"; also evaluation-scenarios.md:67 (must_pass) and :74. Evidence rule: absence of evidence = "(medium confidence, absence of evidence)". Fix: add that tag, register it (new M-id and mapping row), and soften the scenario criteria.

M2. Region claim asserted High by exclusion. SKILL.md:20, always-do-foundation.md:32-33 ("every resource here accepts an optional region ... imports with id@region"). The research derives this from DynamoDB not being in the F14 global list (research line 6), and the enhanced-region guide does not enumerate DynamoDB resources. That is absence/inference, not a page statement. Also id@region is not true for composite-ID imports (GSI `table_name,index_name`, table_item) as shown by the skill's own import IDs. Fix: cite the DynamoDB resource pages' region argument, or tag (medium confidence, absence of evidence); drop the blanket id@region.

M3. Never row alternative is inference. SKILL.md:90 and never-do-replication-provider.md:48-52: "bulk load with import_table". The cited page for the row (table_item) says only "not meant for large amounts of data". No page read says import_table is the bulk-load route, and import_table applies only when creating a table (not into an existing one). The ✅ half of a Never row must be High. Fix: cite the table page for import_table, state its create-time limit, or reduce the alternative to "keep to a few seed items".

M4. Always Do bullets lack the required inline URL and carry multiple claims. SKILL.md:44-66 (12 bullets, each with only a "See blueprint" link). Evidence rule: one High claim per bullet, one inline URL, no caveats. Multi-claim/mixed-source bullets: :52 (default false + Security Hub DynamoDB.6), :54 (Security Hub + default 35 + AWS 1-35, mixed provider/AWS sources), :56 (customer-key use + AWS-managed-key behavior), :60 (ignore_changes + policy_type). :44 combines root `~>` and module `>=` and CLI. Fix: split or trim to one claim, add one URL each.

M5. U6 block names are tagged (unverified) but are very likely correct, and the tag text is misleading. always-do-indexes-capacity.md:128-135; unverified-and-risks.md:25. aws_appautoscaling_policy does use `target_tracking_scaling_policy_configuration { predefined_metric_specification { predefined_metric_type = ... } target_value = ... }` (from my knowledge of the provider; not live-fetched). The research example (line 104) already shows predefined_metric_type and target_value from that page's example, which implies the nesting; the author never recorded it. HCL is not wrong, but the comment "not recorded in the research" leaks provenance and teaches users to distrust correct HCL. Fix: read the policy page, record the nesting, drop U6 and its mapping row (or keep as (medium confidence) if it cannot be fetched). While there, resolve U1: the write metric is `DynamoDBWriteCapacityUtilization` in the AWS/provider docs.

M6. Orphan register row and process item. unverified-and-risks.md:33 (M2 "WebFetch paraphrases"), :60 mapping row "Medium-Confidence Items above - warning wording | M2". No shipped skill text uses the tag for M2; the mapping row points at the register itself. M2 is a research-process note, not a skill claim. Fix: delete M2 and its mapping row.

M7. Example values not marked. always-do-replication-satellites.md:68 `aws_kinesis_stream.orders.arn` (undefined resource, no "example" or "defined elsewhere" marker); :104-110 terraform test assertion/error_message (no example marker; `aws_dynamodb_table.orders` also undefined in that file). Fix: add "# example" / "# stream defined elsewhere" comments.

M8. Source misattribution (statement cites a page that does not state it). SKILL.md:18 constraint `~> 6.69` (root) / `>=` (modules) cited to the provider releases page (the root/module rule is from the version-constraints page, and 6.69 is a choice); :100 Quick Reference `~> 6.69` cited to version-constraints (page does not mention 6.69); :103 PITR row mixes provider default 35 with AWS page only; always-do-foundation.md:97 "PITR may take about 10 minutes" and "restore creates a new table" carry no source line directly (second one is AWS page [20]). Fix: one claim per source, or add both URLs.

### LOW

L1. Provenance leakage in shipped text: always-do-foundation.md:74 ("not stated in the research"), always-do-replication-satellites.md:14, always-do-indexes-capacity.md:128, unverified-and-risks.md:25-26 ("the research records only"), M2 wording ("WebFetch"). Replace with "the cited page does not state ...".

L2. "family rows verified 2026-10-14/22" at always-do-foundation.md:3 and never-do-replication-provider.md:3 refers to internal orchestration, not a source. Remove.

L3. Always Do bullet count is 12 (SKILL.md:44-66), not 13 as stated by the author. Confirm which bullet is missing or correct the claim.

L4. Policy choices in Always Do: deletion_protection_enabled = true (:52) and PITR enable (:54) are grounded only in Security Hub controls (cost/destroy behavior tradeoffs); consider Ask First. "CI-safe" (:66) is inference.

L5. Always bullet :62 "the documented way for V2" vs Never row 6 alternative that allows aws_dynamodb_table_replica alone, and Ask First row listing replica blocks only. Make wording consistent ("one mechanism per table").

L6. "deprecated in 6.x" (SKILL.md:58, :86, never-do-table-indexes.md:77-88): the page states deprecation; the introducing 6.x version is not recorded (same gap as U5). Say "marked deprecated on the table page".

L7. Ask First row 1 (SKILL.md:73) "satisfied by either" is the research's lever mapping (inference); the Security Hub page names the control, not these Terraform levers. Tag (medium confidence) or phrase as "passes the control when ...", cite Config rule.

L8. Register: mapping table header is "Tag text | Where | Register id" instead of the policy's "Tag text used in the skill"; evaluation-scenarios.md:44 and :114 use tags with no mapping rows; U-table has no stated count header (acceptable).

L9. Formatting: always-do-foundation.md:97-98 no blank line before "## 5." heading; never-do-table-indexes.md:11 label "reported diffs" fine, but alternative "set values above the minimum" (SKILL.md:87) is not in any recorded page claim (research says only "omit instead").

## Check (7) U6 judgement

Likely correct HCL, wrongly flagged. See M5. Severity MEDIUM (misleading tag and provenance leak), not HIGH.

## HIGH list

None.
