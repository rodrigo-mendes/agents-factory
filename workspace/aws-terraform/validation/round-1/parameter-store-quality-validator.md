# Quality validation, round 1: provisioning-aws-parameter-store-v6

Scope: SKILL.md plus 8 blueprints, read from packages/. Checked against the research file, the family facts, the three policy files and skill-frontmatter.md.
Not done: WebFetch was not used. Claims were checked against the research and family-facts files, not against live pages.
Known family decisions not reported: the `-v6` suffix, and page-from-`main` confidence (G3).

## Counts

HIGH 2, MEDIUM 7, LOW 8.

Claims sampled: 34. Pass: 22. Findings: 12 (HIGH 2, MEDIUM 7, LOW 3). The other 5 LOW findings come from structural checks.

## HIGH

### H1: Never row 3 alternative depends on medium or unverified content
- Location: SKILL.md:78 and never-do-secrets.md:64-67.
- Rule 1 (Never rows) requires the alternative to be High-confidence.
- The alternative is "use the ephemeral resource". That pattern is labelled medium confidence (always-do-secrets §5, SKILL.md:68). Its minimum CLI version is unverified (U1) and its semantics are medium (M1).
- never-do-secrets.md:64 even says "see always-do-secrets §5, medium confidence". So a High-only tier points at a medium pattern.
- Fix: make the alternative the High statement only. For example, "Do not read a SecureString through a data source if plaintext in state is unacceptable; use `with_decryption = false`." Only use that if the data source page states it. Alternatively, move the Never row to Ask First.

### H2: Never row 3 alternative differs between SKILL.md and the blueprint, and one clause is unsourced
- Location: SKILL.md:78 and never-do-secrets.md §3.
- Rule 1 requires one-to-one equality across SKILL.md, never-do-patterns.md and the blueprints.
- SKILL.md adds "use the data source only for metadata". The blueprint does not.
- The "metadata" statement comes from the ephemeral page ("directs you to the data source"). The SKILL.md row cites only the data-source page.
- The row names `aws_ssm_parameters_by_path` but cites only `d/ssm_parameter`. Rule 5 requires the page that states the claim; that page is `d/ssm_parameters_by_path`.
- It is HIGH because it breaks the one-to-one equality rule on the Never tier.
- Fix: align both texts and cite both pages.

## MEDIUM

### M-1: Always Do bullets carry no inline URL
- Location: SKILL.md:47-58.
- Evidence rule: "one High claim per bullet, one inline URL, no caveats".
- All six bullets link only to blueprints.
- Several bullets bundle claims from different pages:
  - Bullet 5: `/` is required (TF resource page), 15 levels (AWS hierarchies page).
  - Bullet 2: `value_wo` never in state, version bump, and Terraform >= 1.11.
  - Bullet 4: the "when you need key-policy control" condition is a caveat in an Always Do bullet. The alternative reading is an Ask First decision.
- Fix: one claim per bullet, one source each. Move the conditional `key_id` wording to Ask First. The decision matches evaluation scenario 1 ("or asks whether"), so fix it consistently.

### M-2: Import `id` form "Terraform >= 1.5" is attributed to the provider page
- Location: always-do-foundation.md:42-43 and :57.
- The research lists "TF >= 1.5" with no source.
- F11 only supports >= 1.12 for `identity`, and its source is the vpc page. The provider ssm page is cited for the 1.5 claim.
- That is a Terraform-core fact. Cite the Terraform import docs, or tag it as unsourced.
- The identity form `identity = { name = ... }` with optional `account_id` and `region` matches the research, so it passes.

### M-3: always-do-secrets §4 contains an `(unverified)` tag inside an always-do pattern
- Location: always-do-secrets.md:17.
- The HCL uses `ephemeral.random_password.db.result  # (unverified)`.
- The SKILL.md Always Do bullet 2 is High, but its canonical HCL example carries an unverified dependency.
- Rule 2 says High only, no tags inside the Always Do material.
- Fix: use a variable example. The research suggests "var marked ephemeral". Show the declaration with `ephemeral = true`, only after sourcing it. Or drop the line to a comment-free `var.db_password_wo`. Then remove U2.

### M-4: never-do-secrets §1 CORRECT block teaches a vague pattern
- Location: never-do-secrets.md:22 and :45.
- `value_wo = var.db_password_wo  # example; ephemeral-capable input`
- The variable is not declared. The comment "ephemeral-capable" is an unsourced claim inside a High-only file.
- A plain `variable` is not wrong for `value_wo`, because the write-only argument is not stored in state.
- However, without `ephemeral = true` the example does not teach the point the comment makes. The claim that a non-ephemeral variable is safe for write-only arguments is not in the research.
- Fix: declare the variable (`ephemeral = true`) with a source, or label it plainly as "any value source" and drop "ephemeral-capable".

### M-5: Ask First rows cite several pages with a single trailing citation group
- Location: SKILL.md:64, 65 and 69.
- Rule 5 says each statement cites the page that states it.
- The Tier row mixes TF-page claims and AWS-page claims, then cites `([TF], [AWS])`.
- It is unclear which page states "Advanced: parameter policies, cross-account sharing, charged".
- Fix: attach the citation per clause.

### M-6: "Fixes need at least that line"
- Location: SKILL.md:47 and always-do-foundation.md:7-8.
- The 6.58 and 6.59 fixes need provider >= 6.59.0, not the `~> 6.69` line.
- "Need at least that line" overstates this. It is inference from the family constraint, not a documented requirement.
- Fix: say "6.58.0/6.59.0 fixes are included in ~> 6.69" (CHANGELOG), which is the documented fact.

### M-7: Ephemeral HCL placement, rule 7 judgement
- Location: always-do-secrets.md §5 and always-do-patterns.md.
- Verdict: placement is tolerable but not clean.
- The evidence rule allows medium items in blueprints when tagged. SKILL.md Always Do does not list the ephemeral pattern, and the Ask First row links it. That part passes.
- The problem is the file name `always-do-*` and the sentence in always-do-patterns.md:3-4 ("Each pattern has HCL and cites its official source"). Together they imply the ephemeral pattern is an always-do item.
- Only the first claim in §5 is High: the ephemeral resource requires `arn`, and `with_decryption` defaults to true.
- The medium and unverified sentences are tagged inline, so tags are consistent with the register (U1 and M1).
- The replica HCL (`value_wo = ephemeral...value`) depends on the medium M1 semantics, and the HCL itself is not marked as medium.
- Fix: move §5 to an ask-first blueprint (for example `ask-first-ephemeral-read.md`). Or add a medium-confidence comment line above the HCL. Update the links and mapping rows.

## LOW

- L-1: SKILL.md:93. `region` is cited only to the enhanced-region guide. The resource, data-source and ephemeral pages state it per argument. The guide does not necessarily list the ephemeral resource.
- L-2: Tag orphans in the register mapping.
  - "(Ask First, medium confidence)" in always-do-patterns.md:12, and the "medium confidence" in the comment at never-do-secrets.md:64, have no row in `Tag to Register Mapping`.
  - The `§5 heading (medium confidence)` row exists only partly: it is covered via M1.
- L-3: Placeholders `aws_kms_key.params`, `aws_db_instance.main` and `aws_ssm_parameter.db_password` in the HCL are not declared and not marked example (always-do-foundation.md:34, always-do-secrets.md:16, never-do-secrets.md:66). Mark them or add `# example` comments.
- L-4: always-do-secrets.md:24. "The ephemeral resource only reads" is inference (research W4 area). It is unsourced.
- L-5: Evaluation scenarios 2, 4 and 5 reproduce legacy claims W1, W2 and W4 as traps and in `must_not`. They are framed as rejections, which is acceptable. Confirm that the family treats trap queries as allowed.
- L-6: Security Hub row (SKILL.md:102). "None of SSM.1-SSM.7" is a negative claim. It is already narrowed to the seven controls and dated, which is fine. Consider adding "(absence of evidence)" if it is ever generalised beyond those seven controls.
- L-7: Sibling skill names (`provisioning-aws-secrets-manager-v6`, `-kms-v6`, `-iam-v6`, SKILL.md:10-11 and :66) could not be confirmed. The glob returned no sibling directories. Only the vpc sibling was confirmed to exist. Verify before the package ships, or treat them as planned.
- L-8: Version Context row for identity import (SKILL.md:21) cites the ssm page, but family fact F11 sources it from the vpc page. This is fine if the ssm page was read. Record it in the coverage notes.

## Checklist results

| Check | Result |
|---|---|
| Frontmatter: only `name` and `description`, quoted | pass. Description is about 276 characters, under 300, and contains "Use when". The name matches the folder. |
| SKILL.md line count 100-200 | pass (127 lines) |
| Blueprint files at most 160 lines | pass (all under 85 lines) |
| Required blueprints, at least 4 scenarios | pass (5 scenarios) |
| Links and anchors | pass. I checked the blueprint and section anchors by slug. I did not run `verify_skill.py`, so it should still be run. |
| No F#/M# ids or workspace paths in shipped text | pass. The grep hits are only the register ids M1 and M2. |
| Plain tag notation | pass |
| Register IDs and header sections | pass. U1-U4, M1-M2 and L1-L4 are present. Counts are not stated in headings, so they cannot be compared. |
| Orphan register rows | none. Orphan tags are listed in L-2. |
| Never rows one-to-one across SKILL.md, never-do-patterns.md and blueprints | 6 = 6 = 6 by count. Row 3 differs in content (H2). |
| `value_wo` needs Terraform >= 1.11 | pass |
| Ephemeral resource requires `arn` | pass |
| Import HCL forms vs research | pass for `identity = { name = ... }`; `id = ...` is fine (see M-2 for the 1.5 citation) |
| Legacy claims W1-W6 | not reproduced as facts (W1, W2 and W4 appear only as traps, L-5) |

## Claims sampled (34)

Pass unless a finding is listed.

1. `insecure_value` is never marked sensitive. Pass.
2. `insecure_value` cannot be used with SecureString. Pass.
3. `value` is stored in state as plain text. Pass.
4. `value_wo` is never stored in state. Pass.
5. `value_wo` needs Terraform >= 1.11. Pass.
6. `value_wo_version` is the only way to push a new value. Pass.
7. Data source: decrypted value stored in raw state. Pass.
8. `aws_ssm_parameters_by_path` with decryption stores plaintext. Pass, but cited to the wrong page in SKILL.md (H2).
9. Ephemeral resource requires `arn`. Pass.
10. Ephemeral `with_decryption` defaults to true. Pass.
11. Ephemeral minimum CLI version is unstated. Pass, tagged unverified (U1).
12. Ephemeral semantics. Pass, tagged medium (M1).
13. Names with a path must start with `/`. Pass.
14. Hierarchy maximum is 15 levels. Pass (AWS page).
15. 6.57.0 withdrawn. Pass.
16. 6.58.0 and 6.59.0 fixes. Pass.
17. The fixes "need at least ~> 6.69". Fail (M-6).
18. Identity import needs Terraform >= 1.12. Pass.
19. `id` import needs Terraform >= 1.5. Citation gap (M-2).
20. Tier limits (10,000/4 KB and 100,000/8 KB). Pass.
21. Advanced to Standard recreates the resource. Pass.
22. AWS says downgrade is not possible. Pass.
23. Intelligent-Tiering is a default-tier setting, one-way. Pass.
24. Changing the default tier does not affect existing parameters. Pass.
25. `overwrite` defaults (false on create, true afterward). Pass.
26. Parameter Store rotation is None. Pass.
27. PutParameter default is 3 TPS. Pass.
28. Throttling in `for_each` is inferred. Pass, tagged medium (M2).
29. KMS permissions per tier. Pass.
30. Only symmetric keys are supported. Pass.
31. `aws/ssm` cannot have access-control policies. Pass.
32. Encryption context `PARAMETER_ARN`. Pass.
33. 100 versions retained. Pass.
34. Security Hub SSM.1-SSM.7 do not cover parameters. Pass (L-6).

Plus 3 HCL comments checked (`# example` markers) and the 6 Never rows. Findings from those are covered in H1, H2, M-4 and L-3.

## Summary verdict

NOT YET VERIFIED. Fix H1 and H2 (Never row 3). Then address M-1, M-3 and M-7, which are the rule-2 and rule-7 items.
