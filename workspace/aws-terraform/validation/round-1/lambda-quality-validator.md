# Quality validation, round 1: provisioning-aws-lambda-v6

Date: 2026-10-23. Target: `packages/aws-terraform/.apm/skills/provisioning-aws-lambda-v6/` (SKILL.md + 11 blueprints).
Method: full read of all 12 files, compared with the research file, the family facts, 3 policy blueprints, and the frontmatter rule.
LIMITATION: WebFetch is not available in this run, so the two requested live spot-checks (lambda_function, lambda_event_source_mapping) were NOT done. Every "matches the page" verdict below is "matches the research file", not "matches the live page". Items that need a live check are marked VERIFY-LIVE.

Counts: HIGH 1, MEDIUM 13, LOW 8. About 55 claims sampled (13 Never rows, 12 Always bullets, 12 Ask First rows, 14 Quick Reference rows, HCL comments, register).

## Structure checks (pass)

- Frontmatter has only `name` and `description`. The description is quoted, about 265 characters, contains "Use when", and the name equals the folder.
- SKILL.md is 155 lines. The longest blueprint is 117 lines. All are within limits.
- Never rows: 13 in SKILL.md, 13 in the hub (`never-do-patterns.md`), 5+5+3 = 13 WRONG entries across the 3 never-do blueprints. This is one-to-one. All anchors resolve.
- Always Do: 12 bullets, one URL each, no tags. Pass, with the caveats in M3 and M4.
- No F#/M#/U# ids in SKILL.md or in the always/never blueprints. The only ids are in the register itself, which is allowed. Tag notation is plain parentheses.
- Every tag used in SKILL.md and the blueprints has a mapping row, except the issue in M10. No bold or bracket tags.

## HIGH

H1. `blueprints/always-do-invocation.md:18` says "references aws_lambda_function.orders (publish = true is set on it)". The only `orders` function in the skill (`always-do-function.md:80-99`) has no `publish`, and the default is `false` (stated at `always-do-invocation.md:32`).
- The statement is false as shipped.
- The composed example gives `function_version = aws_lambda_function.orders.version`, which is `$LATEST` without publish.
- A provisioned concurrency config on an alias that points to `$LATEST` is not allowed by Lambda. This is not in the research (the research says "no $LATEST statement on the page", research line 100), so it is (unverified) in the skill.
- A reader copying §3 + §8 gets a failing apply, and the skill claims otherwise.
- Fix: add `publish = true` to the §3 function, or write "requires `publish = true` on the function" and tag the `$LATEST` limitation (unverified) or source it.

## MEDIUM

M1. `SKILL.md:20`, Version Context, identity-import row. The row cites the `vpc` page for "documented for function, event source mapping, permission, alias, layer version". The vpc page can only support the "Terraform >= 1.12" half (family fact F11). The per-resource claim comes from the 5 Lambda pages (research lines 17, 76, 85, 126). Split the row or cite the Lambda pages for the second half.

M2. `SKILL.md:62` (Always bullet) and the Lambda.1 Never row (`SKILL.md:104`, `never-do-access-provider.md:29-34`).
- The Always bullet "Set `source_account` with `source_arn` ... for S3" cites only the permission page. The requirement comes from the Security Hub page (Lambda.1).
- The research says the permission page describes `source_account` only as an optional argument ("cross-account, S3, SES"), and says there is no confused-deputy text on the page (research line 90).
- The mapping `source_account` -> condition `AWS:SourceAccount` is the author's inference, untagged.
- The Never row is a compliance-control outcome, not a documented error. The row and the ✅ cell are sourced, but the ✅ link between the argument and the control is not stated by either cited page.
- Fix: cite the lambda-controls page in the Always bullet. Either move the `source_account` -> `AWS:SourceAccount` link to Ask First as (medium confidence), or fetch the permission page and confirm.

M3. `SKILL.md:56` and `SKILL.md:58` (Always bullets for tracing and multi-AZ). Both rest on Security Hub controls (Low, Medium), which are preferences, not Terraform requirements.
- The bullet carries an inline rationale ("— Security Hub Lambda.7 checks it"), which the evidence rule says to avoid.
- Active tracing depends on X-Ray IAM permissions that the skill itself lists as (unverified) (Ask First row, U4). An unconditional Always rule has an unverified dependency.
- Multi-AZ applies only when a VPC is attached, and VPC attachment is an Ask First choice (`SKILL.md:77`).
- Fix: move tracing to Ask First, or keep it only if U4 is resolved. Make the multi-AZ bullet conditional ("when `vpc_config` is set").

M4. `SKILL.md:46`. The Always bullet makes two claims in one ("`required_version = ~> 1.16` and `version = ~> 6.69`"), both cited to the provider releases page.
- That page can only support the provider version. The Terraform CLI version comes from the Terraform releases page.
- The pins are choices, not documented facts. The evidence rule requires one High claim per bullet.
- Fix: split into two bullets with the proper URLs, or move the choice to Ask First.

M5. `SKILL.md:16-17, 22-23` and `unverified-and-risks.md:8`. `~> 1.16` means >= 1.16, < 2.0, so it DOES allow 1.17.0. The text "targets `~> 1.16`, so 1.17.0 is not covered / re-verify before moving" reads as if the constraint excludes 1.17.
- Likewise `~> 6.69` allows every 6.x >= 6.69, not only "6.70.x" (`SKILL.md:17` parenthetical).
- Fix: reword to "verified against 1.16.x; the constraint admits 1.17.x, which was not verified".

M6. `always-do-function.md:33-57`, `aws_iam_role` (`name`, `assume_role_policy = jsonencode(...)`) and `aws_iam_role_policy` (`name`, `role = ...id`, `policy = jsonencode(...)`). Untagged and not in the research, which only covers the trust principal and log actions from the Lambda execution-role page.
- Argument shapes are correct from general knowledge, but no IAM page was read.
- Both policy documents omit `Version = "2012-10-17"`. The Lambda page examples include it, and omitting it silently selects the legacy 2008-10-17 version.
- The `Resource` placeholder is marked.
- Fix: add `Version`. Add a one-line "argument shapes belong to provisioning-aws-iam-v6 (not read here)" with (unverified), or cite the IAM resource page.

M7. `event_source_arn` on `aws_lambda_event_source_mapping`, used in `always-do-events-layers.md:23` and `never-do-events.md:16,37,46,61,81` (and `never-do-events.md:16` for the starting_position WRONG block). The argument is not in the research (research lines 110-121 list no source-ARN argument) and is untagged. It is correct from general knowledge, and the value is a marked placeholder. The skill never states that the argument is required for SQS. Fix: add it to the research or fetch the page, then state "required for SQS" with its source.

M8. `always-do-function.md:95`, `log_group = aws_cloudwatch_log_group.orders.name`. Not in the research. The research only says `log_group` points to a DELIVERY-class group for S3/Firehose (research line 77). I cannot confirm name vs ARN without WebFetch (VERIFY-LIVE on the lambda_function page `logging_config.log_group`). The AWS LoggingConfig API takes the group name, so `.name` is very likely right, but it is untagged and unsourced. Fix: tag (unverified) or cite the page text. If the page says ARN, this becomes HIGH.

M9. `unverified-and-risks.md:49` (M4) and tag-mapping row `:72`.
- M4 says the verbatim wording of provider docs is "partly reconstructed". This is internal process wording (the research says "WebFetch paraphrases") shipped to users.
- It undermines every quoted phrase in the skill (`never-do-function.md:76-77` "Out-of-band changes ... will not be captured", `SKILL.md:96`, "intentional dangling resources" at `always-do-events-layers.md:41`).
- The mapping row points at itself, and no tag appears in shipped text: an orphan row.
- Fix: delete M4, and quote only text that was read. Otherwise paraphrase without quote marks.

M10. `SKILL.md:133-137`, the 5.x -> 6.x migration section.
- "no Lambda items" in the upgrade guide and "no BREAKING Lambda entries" in the changelog are absence claims. Register L1 says the 6.55.0 header sat at an unread chunk boundary. They need (medium confidence, absence of evidence), and they carry no tag.
- The "Upgrade path" bullet (`SKILL.md:137`) has no source and no tag.
- The section is also not in the hybrid-format schema (extra heading). That is acceptable, but it must obey the evidence rule.

M11. `SKILL.md:122,124` (Quick Reference). The severity words "Medium" and "Low" collide with the confidence tags. Policy: "Severity wording ... uses low|moderate|high, never the bare word 'medium'". Rows: Lambda.2 and Lambda.5 say "(Medium ...)". Use "moderate".

M12. `SKILL.md:94` (Never row: `vpc_config` with `capacity_provider_config`) and `never-do-function.md:31-48`.
- Register L2 and Ask First (`SKILL.md:87`) admit that the provider version that introduced `capacity_provider_config` is not pinned. The research marks `capacity_provider_config` as a "newer block present on main" (research line 72).
- A High Never row about a block whose existence in the pinned 6.69 line is unconfirmed conflicts with L2.
- The ✅ cell "Use only `vpc_config` for a VPC-attached function" implies that a managed-instances function cannot be VPC-attached. That is an inference.
- The WRONG HCL uses an empty `capacity_provider_config {}`, and the CORRECT block is only a comment.
- Fix: put the pairing in Ask First as (medium confidence) until the introducing version is read, or pin the version.

M13. VERIFY-LIVE, `SKILL.md:100` (Never row 9) and `never-do-events.md:53-70`. The claim is "`provisioned_poller_config` is MSK and self-managed Kafka only, not SQS". Per my recollection, AWS added SQS provisioned mode for event source mappings in late 2025, and the provider docs may have been updated. I could not fetch the page. If the live page lists SQS, the row and the ✅ are WRONG (HIGH). The row also carries a hard "(Never)" on a statement that is exposed to this kind of drift. Fix: fetch lambda_event_source_mapping and quote the exact sentence into the research.

## LOW

L1. `SKILL.md:66` (Always bullet "Use a `maximum_concurrency` of at least 2 on SQS mappings"). It duplicates the Never row and reads as "always set it". The value is only a constraint when the block is set. Reword as "When setting `maximum_concurrency`, use at least 2". Also, `never-do-events.md:29-31` states "which the provider rejects" for values below 2. The page says only "must be >= 2", so "provider rejects" is an unsourced inference. Say "invalid".

L2. `SKILL.md:64`. `function_response_types = ["ReportBatchItemFailures"]` as an Always rule depends on the function code returning `batchItemFailures` (a code contract the skill does not state). Consider Ask First.

L3. `SKILL.md:60, 103`, `never-do-access-provider.md:6-27`. The ✅ "keep the role ... until the function is destroyed" goes beyond the doc. The doc says deleting the role before the ENI is deleted prevents cleanup (up to 20 min after removing VPC config). Destroying the function does not itself guarantee the ENI is gone. The WRONG block is only a comment, not code, and the CORRECT block references `aws_iam_role_policy.vpc_access`, which is defined nowhere in the skill. `always-do-function-config.md:44-56` (§5) gives a VPC function with no VPC policy attachment and no `depends_on`.

L4. `SKILL.md:102`, `never-do-events.md:96-100`. The ✅ "at or below the visibility timeout" is the floor. The research notes the best-practices page; this is a weak alternative and omits any buffer guidance. Also, "CreateFunction fails or duplicates occur on update" is a compressed paraphrase.

L5. Runtime dates (`SKILL.md:75`, `unverified-and-risks.md:17-30`, `evaluation-scenarios.md:90-97`). No Always or Never row contains a runtime date, which is correct. Dates are duplicated in 3 places (Ask First row, register table, scenario 4 fixtures). If the register is refreshed and the Ask First row is not, they drift. Scenario 4 fixes "2029" and "2027-06-30" as pass criteria, and these will rot. "Supported to 2029" is vague (no date). Keep one copy in the register and link from Ask First.

L6. Legacy wording. `unverified-and-risks.md:27-29` rebuts the legacy file ("it is not 'approaching EOL'") and scenario 4 quotes "Our standards say ...". The substantive facts are right, but the framing is research-process wording rather than skill guidance. The dotnet8, java11 and `maximum_concurrency` >= 2 legacy corrections are all reproduced correctly: `maximum_concurrency` >= 2 appears in the Never row, the Always bullet and scenario 3, as expected. No registry.terraform.io page is cited as a source. The scenario 1 `must_not` line mentions registry pages, which is fine.

L7. Register column name. `unverified-and-risks.md:62`, "Tag text", vs. the policy column "Tag text used in the skill". Header counts are not stated, so the "counts equal" check is vacuous. Also, `SKILL.md:87` (Ask First "Newer function blocks ... not pinned") has no tag, although it corresponds to L2.

L8. `always-do-function.md:102-104`. The closing paragraph (`source_code_hash`, `code_sha256`, `default_tags` override) follows the HCL without its own inline URL. The page URL is given 30 lines above. Add it for per-statement citation.

## Item-by-item answers to the caller's checklist

1. Never rows (13). All 13 have a source and a ✅ cell. The ✅ cells for rows 2, 11, 12 and 10 rest on inference or weak sourcing (M12, L3, M2, L4). Row 8 (`maximum_concurrency` >= 2) is sourced and consistent across SKILL.md, hub and blueprint, with a minor "rejects" inference (L1). Row 12 (Lambda.1): sourced, High, but see M2. No Never or Always row contains a runtime date; runtime dates sit in Ask First, in the register with the read date 2026-10-23, and in the scenarios (L5). One-to-one mapping with the hub and the 3 blueprints: pass.
2. Always bullets (12): High-only, no tags, one URL each. Violations of "one claim, no caveats" are in M3 and M4. The `source_account` bullet cites the wrong page (M2).
3. No F#/M#/U# ids or internal wording in the shipped text, except register M4 wording "reconstructed" (M9). The register ids U1-U5, M1-M4, L1-L4 are consistent with the tag mapping, with one orphan row (M4/M9).
4. Untagged HCL: IAM role and policy (M6), `event_source_arn` (M7), `log_group .name` (M8, VERIFY-LIVE), `aws_cloudwatch_log_group` `name` and `retention_in_days` (PASS: the research at line 77 records the `/aws/lambda/<function_name>` name and `retention_in_days = 14` from the page examples; example values are marked). Example values are marked with `# example` or `# placeholder` throughout.
5. Per-statement citation. Failure: identity-import row cites the vpc page for a Lambda per-resource claim (M1). Also M2.
6. Legacy claims are not reproduced as facts (L6). The dotnet8 2026-11-10, java11 2027-06-30 and java11.al2023 2029 statements are consistent with the research, which says "supported to 2029" without a date.
7. §8 comment "publish = true is set on it": misleading and false, so HIGH (H1).

## Verdict

Not ready for VERIFIED. Fix H1. Resolve M13 and M8 with a live fetch, because either can escalate to HIGH. Then re-run after fixing M1-M12.
