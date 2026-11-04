# Quality validation, round 2: provisioning-aws-step-functions-v6

Target: packages/aws-terraform/.apm/skills/provisioning-aws-step-functions-v6/ (SKILL.md 152 lines, 10 blueprints).
Method: read all 11 files, research, facts, round-1 report, policy (evidence-rule, tag-notation-and-registers). WebFetch was NOT available, so the AWS and HashiCorp pages were not re-fetched. Verdicts on page content rest on the recorded research and facts, and on the orchestrator's quote for States.ALL given in the brief. `verify_skill.py` was not run.
Not reported, per brief: -v6 suffix, page-from-main confidence.

Counts: HIGH 1, MEDIUM 3, LOW 11.

## Count checks (done by reading and counting)
- Never rows: SKILL.md 97-106 = 10; never-do-patterns.md index = 10; blueprint sections 1-5 (never-do-configuration) + 6-10 (never-do-iam-asl) = 10. 10=10=10 confirmed.
- Always Do bullets: SKILL.md 52-78 = 14. Confirmed. No tags inside any Always Do bullet. Each has one URL.
- corrections-and-limits.md is linked from SKILL.md:43, SKILL.md:120, unverified-and-risks.md:19 and :43. Rows 1, 2 and 6 (absence) carry `(medium confidence, absence of evidence)`; rows 3-5 are sourced presence claims and correctly untagged.
- Tag to register: every inline tag has a mapping row (M1-M6, U1-U4). M6 maps to SKILL.md Quick Reference "Versions"/"Definition substitution", the 5.x to 6.x section, and the corrections table. No orphan register id, no unmapped tag. Consistent.

## HIGH

H1. Per-source read dates are wrong. The skill states one blanket date, 2026-10-23, for sources read on 2026-10-14 and 2026-10-22.
- Files: SKILL.md:9 ("Pages read 2026-10-23"), SKILL.md:110; always-do-foundation.md:3; never-do-configuration.md:3; always-do-encryption-testing.md:3; never-do-patterns.md:5; unverified-and-risks.md:3 and :62 ("All read 2026-10-23" over the bibliography).
- Pages that were read earlier, per _family_facts_v6.md: Terraform releases and CHANGELOG, S3 backend, version-constraints, dependency-lock, tests/mocking, plan/validate, the enhanced-region guide and the vpc page = 2026-10-14. Provider releases page = 2026-10-22. Only the unit pages (sfn_* docs, AWS Step Functions pages) are 2026-10-23.
- The blanket date is false for the foundation, version-context and testing material. Version Context rows (SKILL.md:18-22) carry no per-source date at all.
- Fix: put the date on each source (inline or in the bibliography). Use 2026-10-14 for the Terraform and S3 backend pages and the enhanced-region guide, 2026-10-22 for the provider releases page, and 2026-10-23 for the unit pages. Replace the file-header "Pages read 2026-10-23" with "see the per-source dates".

## MEDIUM

M1. SKILL.md:135 says the 6.0 upgrade guide "uses `~> 6.0`". Neither the research nor the facts record this. It is unsourced and untagged. Fix: drop the parenthetical or tag it `(unverified)` and register it.

M2. Unit-test claim "`mock_provider` with `command = plan` avoids real AWS calls". Files: SKILL.md:86; always-do-encryption-testing.md:88. The facts (F10) record only that `.tftest.hcl` lives in `tests/`, `run` takes `command = plan|apply`, and `mock_provider` exists. "Avoids real AWS calls" is not in the recorded evidence. It is untagged. Fix: tag `(medium confidence)`, or restrict the text to what F10 records.

M3. Wrong page for state-machine tagging. always-do-state-machine.md:115-116 says "AWS best practices say to tag state machines and activities" and cites the Security Hub page, which covers activities only (StepFunctions.2). The state-machine claim comes from sfn-best-practices (research line 98). This was round-1 M4; only the Always Do bullet was fixed (it now reads "Tag activities", SKILL.md:74). Fix: cite the best-practices page for the state-machine half.

## LOW

L1 (carried). Always Do bullets are not strictly one claim each. SKILL.md:52 (lockfile + deprecated), :56 (conditions + "AWS recommends"), :58, :60, :66, :68, :70 and :76 carry a second clause after the em dash or a parenthetical. The evidence rule says "no caveats inside the bullet". Bullet :76 now holds a caveat ("Sync Express: `kms:Decrypt` only"). Fix: one claim per bullet, move the exception to Ask First or a blueprint.
L2 (carried). The bare word "medium" is used as a severity at SKILL.md:60 and :126, which collides with the confidence tag. Policy: low|moderate|high.
L3 (carried). SKILL.md:12 cites the generic enhanced-region guide for "these resources take `region`"; the research bases it on the four resource and data-source pages. The import `<arn>@<region>` claim (:133-134) is now sourced (fixed).
L4 (carried from round-1 L5). Quick Reference line 117 "Encryption type" does not say it is the state-machine setting or which enum applies. The activity enum differs (see Ask First row :90).
L5 (carried from round-1 L8). Heading "Tag to Register Mapping" (unverified-and-risks.md:45) differs in casing from the policy's "Tag to register mapping". "Coverage Limits" is in the register as a pointer only.
L6 (new). The U4 text says "condition operators are omitted from the examples" (unverified-and-risks.md:28), but always-do-foundation.md:61-62 uses `StringEquals` and `ArnLike`. The foundation header (:5) does say operators are not quoted, so the claim is tagged. Fix: reword U4 to "except the trust-policy example".
L7 (carried from round-1 M3). SKILL.md:121 and corrections-and-limits.md:10 still attribute "build the string with `templatefile()` or `jsonencode()`" to the sfn_state_machine page. That page does not say it. The tag in that row covers the absence claim, not this advice.
L8 (new). Research-process wording is in shipped prose: SKILL.md:85 "the `templatefile` function page was not re-read"; unverified-and-risks.md:35, :80 "cited, not re-read". No F#/G#/"round"/"orchestrator"/"WebFetch" was found (grep). Fix: "(medium confidence)" alone.
L9 (new). The SKILL.md Never row for States.ALL (:104) states both halves, but omits the sourced exclusion (`States.DataLimitExceeded`/`States.Runtime` are not caught). It is present only in never-do-iam-asl.md:40-41. Round 1 asked to keep it. Optional: add to the Instead cell.
L10 (new). The register has no L rows. Coverage limits L1-L3 live in corrections-and-limits.md (policy lists them as a register section). SKILL.md and the register link correctly, so the effect is small.
L11 (new). The Import row (SKILL.md:122) puts "Terraform >= 1.12.0" on the sfn_state_machine page. The fact was recorded from the vpc page (F11). Cite the vpc page or tag it.

## Round-1 item status

| Item | Status | Where |
|---|---|---|
| H1 States.ALL | FIXED | SKILL.md:104 Never row states both halves ("alone in `ErrorEquals` and in the last retrier/catcher"); Instead cell correct; never-do-iam-asl.md:36-55 quotes the page, WRONG block has States.ALL mixed and in a non-last retrier, CORRECT has it alone and last; the DataLimitExceeded/Runtime exclusion is in the prose (:40). Eval scenario 4 (evaluation-scenarios.md:87,92) covers both halves. See L9 for the hub omission. |
| M1 absence tags | FIXED | SKILL.md:120, :121, :130-132; corrections table; 404 URL cited at corrections-and-limits.md:9; eval scenario 3 (:69-70) says "absence of evidence" |
| M2 upgrade path | FIXED, with regression | The unsourced "5.x then 6.69" path is gone (SKILL.md:135-137), but the new "(it uses `~> 6.0`)" is unsourced: new M1 above |
| M3 citations | PARTIALLY FIXED | Workflow Studio claim removed; templatefile advice tagged (SKILL.md:85); the Quick Reference attribution remains (L7) |
| M4 tagging cite | PARTIALLY FIXED | Always Do bullet fixed (SKILL.md:74); always-do-state-machine.md:115-116 still wrong (new M3) |
| M5 CMK example | FIXED | always-do-encryption-testing.md:49-62: operators removed, condition shown as key and value in comments; "an `arn:aws:logs:...` ARN" matches the research; no `StringEquals` or `:*` |
| M6 canary alias | FIXED | always-do-state-machine.md:95-110: unused data block removed, `var.other_version_arn` named a placeholder, the 10% leg labelled "version published at creation" |
| M7 orphan M5 | FIXED | SKILL.md:90 tagged; mapping row present; header column correct |
| M8 corrections table | FIXED | moved to corrections-and-limits.md, linked, absence rows tagged |
| M9 plan-only bullet | FIXED, with a residue | the bullet is now an Ask First row (SKILL.md:86); the "avoids real AWS calls" wording is unsourced (new M2) |
| L1 bullets one claim | NOT FIXED | see L1 |
| L2 "medium" severity | NOT FIXED | see L2 |
| L3 region source | NOT FIXED (half fixed) | see L3 |
| L4 citation placement | FIXED | foundation :43-44 cites the enhanced-region page; :112-114 cites connect-lambda and the IAM page |
| L5 | PARTIAL | patch pair fixed (single 6.70.0, SKILL.md:8); encryption row not fixed (L4) |
| L6 scaffolding tags | FIXED | one header note per blueprint, U4 registered; residue L6 (U4 wording) |
| L7 | FIXED | never-do-configuration.md:64-69 adds the unpublished case; `kms:ViaService` value removed (never-do-iam-asl.md:11-18) |
| L8 mapping heading | NOT FIXED | see L5 |
| No regressions of the HIGH/MEDIUM class beyond new M1 and M2 | | |

## Fresh grounding sample (34 claims not checked in round 1)
Legend: OK = in research/facts with matching source; NOTE = finding.

1. Retry defaults 1/3/2.0/NONE (SKILL.md:124) OK (research 79). 2. Logging policies 10 per Region/5,120 (:125) OK. 3. Alias timeouts 30m (:119) OK. 4. State machine timeouts 5m/1m/5m (:118) OK. 5. `type` default STANDARD (:115) OK. 6. Logging levels ALL/ERROR/FATAL/OFF (:116) OK. 7. Lambda `arn:aws:states:::lambda:invoke`, result under `Payload` (:123) OK. 8. Reuse period 60-900, default 300 (:117) OK. 9. Required arguments `definition`, `role_arn` (:114) OK. 10. 6.55.0 list resource (:22; risks :16 date 2026-07-15) OK. 11. 6.57.0 withdrawn (:20, :101) OK (F4). 12. No 7.x (:19) OK. 13. Trust principal `states.amazonaws.com` (:54) OK. 14. X-Ray four actions (:64) OK. 15. Lambda four transient exceptions (:72) OK. 16. Alias at most two versions, total 100 (:68) OK. 17. `/aws/vendedlogs/` prefix (:62) OK. 18. `TimeoutSeconds` has no default (:70) OK. 19. `kms:ViaService` can break executions (:102) OK. 20. Sync Express `kms:Decrypt` only (:76) OK. 21. `delivery.logs` only `kms:Decrypt` (:78) OK. 22. Deploying principal needs `kms:DescribeKey`/`kms:GenerateDataKey` (encryption-testing :81) OK. 23. `kms_key_id` accepts alias/ARN/ID; ARN needed cross-account (:19-20) OK. 24. Activity polls >= 100 (state-machine :127) OK. 25. No X-Ray for Distributed Map child executions (foundation :93) OK. 26. `.sync` needs events/describe permissions (foundation :115) OK. 27. Unqualified Lambda ARN gives Access Denied (never-do-iam-asl :59) OK. 28. Express supports only Request Response (:103) OK. 29. Standard/Express nesting (:87) OK. 30. In-flight Standard executions keep their revision (:88) OK. 31. `init -upgrade` and commit lock (foundation :35) OK (F8). 32. `plan -detailed-exitcode` 0/1/2 (encryption-testing :110) OK (F9). 33. `~> 6.0` in the upgrade guide (:135) NOTE: unsourced (M1). 34. mock_provider avoids real AWS calls (:86) NOTE: unsourced (M2). 35. Tag state machines (state-machine :115) NOTE: wrong page (M3). 36. Import TF >= 1.12.0 (:122) NOTE: citation (L11).

Unsourced+untagged: 2 (M1, M2). Wrong-page: 1 (M3). Wrong fact: 0. Wrong date: H1 (not a content claim).

## Other checks
- Always Do: High-only, no tags, one URL each, 14 bullets (multi-clause residue: L1).
- No invented `StringEquals`/`:*` in the CMK logging example (encryption-testing :49-62).
- No internal wording ids; L8 only.
- Legacy corrections stay corrections: no `aws_sfn_state_machine_version`, no `definition_substitutions`, trust principal `states.amazonaws.com`, `logs:CreateLogStream` included.
