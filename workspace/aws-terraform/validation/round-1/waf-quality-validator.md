# Quality validation, round 1: provisioning-aws-waf-v6

Date: 2026-10-22. Target: `packages/aws-terraform/.apm/skills/provisioning-aws-waf-v6/` (SKILL.md plus 10 blueprints).
Rubric: hybrid-format-checklist, tag-notation-and-registers, evidence-rule, skill-frontmatter. Grounding: `research_AWS_WAF_tf-aws-v6.md` and `_family_facts_v6.md`.

## Counts

| Severity | Count |
|---|---|
| HIGH | 0 |
| MEDIUM | 6 |
| LOW | 10 |

Grade: PASS with conditions. No wrong fact was found against the research or F-facts. One required check could not be executed (see OPEN-1 / M6).

## OPEN-1: raw-doc HCL verification NOT performed

This run had no web-fetch tool, only Read/Grep/Glob/Write. The raw pages for `wafv2_web_acl`, `wafv2_rule_group` and `wafv2_ip_set` were therefore NOT fetched.
- Checked only against the research summaries, where `ip_set_reference_statement { arn }`, `action { block {} }`, `override_action { count {} }` and web ACL `capacity` (attribute) are consistent (research 3.2, 3.3, 3).
- The rule_group `capacity` argument is required and forces new (research 8).
- Those HCL shapes also match the validator's general knowledge of the provider. That is memory only, and counts as (unverified) under the evidence rule.
- The caller must fetch the three raw pages and confirm the argument names and shapes below before marking VERIFIED. If any is wrong it is HIGH.

HCL shapes to confirm:
- `always-do-resources.md:23-54`: rule_group `rule { action { block {} } statement { ip_set_reference_statement { arn } } visibility_config }`, top-level `visibility_config`, `capacity`.
- `always-do-resources.md:15-20`: ip_set `addresses`, `ip_address_version`.
- `always-do-foundation.md:47-82`: web ACL `rule.override_action.count {}` and `managed_rule_group_statement { name vendor_name }`.

## Explicit checks requested

| Check | Result | Evidence |
|---|---|---|
| WCU max 5000 (not 1500) | ✅ | SKILL.md:54,87; never-do-limits:7-30; research 8, 11.1 [16] |
| Rate-limit minimum 10 | ✅ | SKILL.md:56,88,105; always-do-resources:61-71; never-do-limits:32-55 |
| `aws_wafv2_web_acl_rule` uses `web_acl_arn` (no `scope`, no `web_acl_id`) | ✅ | SKILL.md:60,83; attach:32-35; never-do-attachment:5-27; research 4 |
| Association REST-only, HTTP unsupported | ✅ | SKILL.md:85; never-do-attachment:50-67; research 5 |
| CloudFront ACL via `web_acl_id` (ARN), not association | ✅ | SKILL.md:52,84,108; foundation:112-115; research 5, [13] |
| Legacy wrong claims not reproduced | ✅ | All 8 items in research 12 appear only as labelled WRONG blocks, or as unverified/not quoted (error names U2). Item 8, `region`, is covered. |
| F16 (`aws_wafv2_*` regional, accept `region`) | ✅ | Version Context row (SKILL.md:20); alias-vs-`region` tagged (medium confidence) M1 |
| Tag/register consistency | ⚠️ | See L1-L3 below. Every real tag has a mapping row, and every mapping row points to a real file and section (no orphan rows). Notation variants exist. |
| Anchors and links | ✅ | All 18 intra-skill anchors resolve (slug check done by hand). |

## Mechanical checklist

| Item | Result |
|---|---|
| Frontmatter: only `name` and `description`; name equals folder; quoted; has "Use when" | ✅ (description about 250 chars, under 300) |
| SKILL.md 100-200 lines | ✅ 136 lines |
| Blueprints at most 160 lines | ✅ largest is 118 |
| Required sections (Version Context with Source column, Quick Navigation, Always / Ask First / Never, Quick Reference) | ✅ |
| Required blueprints (always-do-patterns, never-do-patterns, unverified-and-risks, evaluation-scenarios; 4 scenarios: canonical, edge, rejection, trap) | ✅ |
| No absolute paths, `.github`, relative dates | ✅ (grep: only URL hits for `X:\` pattern, no real matches) |
| `-v6` suffix | not flagged (approved) |
| Line counts (grep `.*` count): SKILL 136, foundation 118, attach-logging 111, resources 84, never-do-web-acl 105, never-do-attachment 91, never-do-limits 85, unverified 76, eval 104, always-do-patterns 15, never-do-patterns 17 | verified |

## Claims sampled (36). Result: 33 grounded and correct, 3 flagged

| # | Claim (location) | Basis | Result |
|---|---|---|---|
| 1 | `~> 6.69`, `~> 1.16` (SKILL:46) | F1, F3 | ✅ |
| 2 | `use_lockfile`, `dynamodb_table` deprecated (SKILL:46) | F7 | ✅ |
| 3 | scope/default_action/visibility_config required; scope forces new (SKILL:48) | research 3 | ✅ |
| 4 | Count mode first, then `none` (SKILL:50) | research 11.1 | ✅ |
| 5 | CLOUDFRONT needs us-east-1 (SKILL:52) | research 1.1 | ✅ |
| 6 | capacity forces replacement; 5,000 max (SKILL:54) | research 8 | ✅ |
| 7 | limit at least 10 (SKILL:56) | research 3.3 [16] | ✅ |
| 8 | `ignore_changes = [rule]` (SKILL:58) | research 3.1, 4, 10 | ✅ |
| 9 | association targets list (SKILL:61; attach:61-65) | research 5 | ✅ |
| 10 | `aws-waf-logs-` prefix (SKILL:63) | research 9 | ✅ |
| 11 | `cloudwatch_metrics_enabled` in the logging bullet (SKILL:63) | WAF.12 (research 11.2), not a logging-resource fact | ⚠️ see L5 |
| 12 | Ask First: `AWSWAF-LOGS` policy (SKILL:73) | research 9 | ✅ |
| 13 | Ask First: Amplify (SKILL:74) | research 5, U3 | ✅ (tagged) |
| 14 | Ask First: Bot Control ML default `false` (SKILL:75) | research 2 | ✅ |
| 15 | Ask First: Shield rule name pattern (SKILL:76) | research 3.1 | ✅ |
| 16 | Never: inline rule plus separate rules needs `ignore_changes` (SKILL:82) | research 3.1 | ✅ |
| 17 | Never: `override_action` for rule-group statements (SKILL:89) | research 3.2 | ✅ |
| 18 | Never: `rule_json` vs `rules_json` (SKILL:90) | research 3.1, 8 | ✅ |
| 19 | QR: nesting 3 levels (SKILL:102) | research 3.1 | ✅ |
| 20 | QR: window 60/120/300/600, default 300, key default IP (SKILL:105) | research 3.3 | ✅ (source misattributed, L4) |
| 21 | QR: IP set no `/0`, max 10,000 (SKILL:106) | research 6 | ✅ (source misattributed, L4) |
| 22 | QR: create timeout 5m, 1 call per 2 s (SKILL:107) | research 5 | ✅ (source misattributed, L4) |
| 23 | QR: Security Hub WAF.10/11/12 (SKILL:110) | research 11.2 | ✅ |
| 24 | Migration: Bot Control ML only 6.0.0 item (SKILL:117-119) | research 2 | ✅ |
| 25 | Changelog additions 6.59.0/6.65.0/6.69.0 (SKILL:121-123) | research 2 | ✅ |
| 26 | HCL: 4 rate-based rules per rule group, 10 per web ACL (resources:63) | research 11.1 | ✅ |
| 27 | HCL: window means "how far back" (resources:63) | research 3.3 | ✅ |
| 28 | HCL: `single_header.name` lowercase (attach:90) | research 9 | ✅ |
| 29 | HCL: `logging_filter` structure (attach:94-106) | research 9 | ✅ |
| 30 | HCL: "lower numbers are evaluated first" (foundation:57) | research 11.1 [11]; L2 says the AWS page was not fetched | ⚠️ L6 |
| 31 | HCL: importing with `rules_json` set causes a one-time in-place update (never-do-web-acl:81) | research 8 | ✅ |
| 32 | HCL/text: "Satisfies Security Hub WAF.11" (attach:81) | research TF mapping (inferred) | ⚠️ L6 |
| 33 | `terraform {}` S3 backend `bucket`/`key`/`region`, `source = "hashicorp/aws"`, `var.region` (foundation:11-36) | NOT in research (author admits) | ⚠️ M2 |
| 34 | `aws_wafv2_web_acl_rule` with `action { count {} }` and `rate_based_statement` (attach:37-47) | research 4 lists no `action` for this resource | ⚠️ M3 |
| 35 | "Attaching a rule group ... is done with `aws_wafv2_web_acl_rule_group_association`" (resources:11-12) | research 10 says it exists; "is done with" is exclusive | ⚠️ M4 |
| 36 | "backend region is unrelated to the WAF scope" (never-do-limits:61) | research 12.6, no source | ⚠️ M5 |

## Findings

### HIGH
None.

### MEDIUM

- M2: `always-do-foundation.md:11-36`. Untagged boilerplate not in the research or F-facts: S3 `bucket`, `key`, `region`; `source = "hashicorp/aws"`; `provider "aws" { region = var.region }`. F7 and F6 cover only `use_lockfile` and `~>`.
  - Fix: tag it as boilerplate, for example a comment "# placeholder values; backend arguments beyond use_lockfile not in research (unverified)". Or add a row to the register as a coverage limit.
  - The same applies to the Source lines at foundation:26-27, which cite pages for a block that includes those arguments.
- M3: `always-do-attach-logging.md:37-47`. The `action { count {} }` block and the `rate_based_statement` inside `aws_wafv2_web_acl_rule` are not in research section 4. That section lists only the required arguments and `region`. The shape was inferred from the inline `rule` block.
  - Fix: confirm on the raw `wafv2_web_acl_rule` page (OPEN-1). If unconfirmed, tag it (medium confidence) and add a register row. If the action argument differs, it is HIGH.
- M4: `always-do-resources.md:11-12`. "Attaching a rule group to a web ACL is done with `aws_wafv2_web_acl_rule_group_association`" is stated as the only way and is untagged.
  - The research does not say this is exclusive, and the web ACL page has a rule-group reference statement path (inline). No HCL is given, which is declared as L4.
  - Fix: reword to "can be done with ...", or tag it (unverified) and map it to L4.
- M5: `never-do-limits-provider.md:60-61` (and eval scenario 2 `must_not`). "The backend region is unrelated to the WAF scope" is stated as fact. The research treats it only as an absence of a source (research 12.6). The evidence rule requires `(medium confidence, absence of evidence)`. Only the first clause carries `(unverified)`.
  - Fix: tag the second clause and map it in the register (U4 row), or soften it.
- M6: rule_group HCL. `always-do-resources.md:23-54`: `rule { action { block {} } statement { ip_set_reference_statement { arn } } }` is taken from web ACL summaries. Research section 8 has nothing on the rule-group `rule` shape. The author admits this. See OPEN-1: unverified until the raw `wafv2_rule_group` and `wafv2_ip_set` pages are read. Treat as MEDIUM now; escalate to HIGH if wrong.
- M7: Verification gap (process, not content). OPEN-1: the raw-doc fetch was not done in this round.

### LOW

- L1 `never-do-limits-provider.md:9`: non-standard tag `(not verified, Coverage Limit L1)`. Notation requires plain `(unverified)` or `(medium confidence)`. It is also not in the Tag to Register Mapping. Fix: rewrite as "(unverified, see L1)" and map it, or drop the tag.
- L2 `never-do-attachment-scope.md:90`: variant `(medium confidence, see Ask First)`. The mapping row exists, but the text does not match the "(medium confidence)" form. Align the wording.
- L3 `unverified-and-risks.md:40-51`: the mapping header is `Tag text` / `Where` / `Register id`. The rule requires `Tag text used in the skill`. Section headers carry no counts ("Header counts equal items" is not checkable). There are two non-research ids: U4 (from research 12.6) and L4 (new). That is acceptable but should be noted in the register.
- L4 Source misattribution in the SKILL.md Quick Reference. The claim is in the research but cited to the wrong page.
  - Line 105: window, default and key default come from the `wafv2_web_acl` page; the cited page is limits.html.
  - Line 106: 10,000 addresses comes from limits.html [16]; the cited page is `wafv2_ip_set`.
  - Line 107: the 2 s rate comes from limits.html [16]; the cited page is `wafv2_web_acl_association`.
  - Line 91: the 6.57.0 pin is sourced from the CHANGELOG, but the row cites only the S3 backend page.
- L5 SKILL.md:63. The bullet mixes the log-name prefix and `cloudwatch_metrics_enabled` (Security Hub WAF.12). The evidence rule wants one claim and one inline URL per bullet. The cited blueprint section (attach 8) does not cover metrics.
- L6 Untagged inferences stated as fact: foundation:57 ("lower numbers are evaluated first", L2 says the AWS priority page was not fetched) and attach:81 ("Satisfies WAF.11", the research's own TF mapping).
- L7 SKILL.md:46-64. Always-Do bullets carry no inline URL (evidence rule: one inline URL per bullet). The reference VPC skill has the same pattern, so this is probably accepted house style. Line 46 also bundles four claims.
- L8 Dangling cross-references: `provisioning-aws-api-gateway-v6` and `provisioning-aws-shield-v6` are referenced (SKILL.md:3, never-do-attachment:62, eval scenario 3) but do not exist in `packages/aws-terraform/.apm/skills/` (existing: vpc, kms, cloudwatch, iam, s3, waf, acm, route53, cloudfront). `cloudfront` exists. Confirm they are planned siblings.
- L9 Internal tension: Never Do row (SKILL.md:86) forbids CLOUDFRONT scope "with the provider on another region", while Ask First (line 70) offers per-resource `region = "us-east-1"` (medium confidence). Add a clause to row 86 ("without a us-east-1 provider alias or `region`"), or note the carve-out.
- L10 Minor: SKILL.md:8 "reference patch 6.69.0/6.70.0" versus line 18 "reference 6.69.0". Pick one. `attach:61-65` lists Amplify as supported without the `(unverified)` note that SKILL.md:74 attaches (U3). Systemic: the resource pages were read from `main`, not a release tag. Under the strict evidence table that is a max of medium, though F-facts rate them High. Left as the family's decision.

## Priority fix order

1. Run OPEN-1: fetch the raw `wafv2_web_acl`, `wafv2_rule_group`, `wafv2_ip_set` and `wafv2_web_acl_rule` pages. This resolves M3 and M6, and could produce HIGH.
2. M2: tag the boilerplate.
3. M4 and M5: reword or tag.
4. L1-L3: notation clean-up (`normalize_tags.py` plus manual mapping header).
5. L4-L10.
