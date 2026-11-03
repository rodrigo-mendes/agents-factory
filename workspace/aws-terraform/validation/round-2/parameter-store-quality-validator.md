# Quality validation, round 2: provisioning-aws-parameter-store-v6

Scope: SKILL.md plus 9 blueprints, read from packages/aws-terraform/.apm/skills/provisioning-aws-parameter-store-v6/. Checked against the research file, the family facts, the four policy files and the round-1 report.
Not done: WebFetch is not available in this run. Claims were checked against the research and family-facts files, not live pages. `verify_skill.py` was not run.
Known decisions not reported: the `-v6` suffix, and page-from-`main` confidence (G3).

## Counts

HIGH 0, MEDIUM 4, LOW 6.

Claims sampled (new, not in round 1): 36. Pass 33. Findings 3 (all MEDIUM or LOW, see below). Other findings come from structural checks.

## Part 1. Round-1 items

| Item | Status | Evidence |
|---|---|---|
| H1 Never row 3 alternative depends on medium content | FIXED, residual R2-M1 | SKILL.md:82 Instead is now "Avoid reading the value through the data source..." and no longer says "use the ephemeral resource". It still carries "(see Ask First: Ephemeral read)", a pointer into a medium section. |
| H2 Never row 3 text differs, wrong page cited | FIXED | SKILL.md:82 and never-do-secrets.md:50-65 match. The by-path claim is its own row (SKILL.md:83, never-do-secrets.md:67-81) and cites the `d/ssm_parameters_by_path` page. |
| M-1 Always Do bullets without URL, bundled claims, key_id caveat | FIXED, residual L-4 | Each bullet in SKILL.md:48-60 has one inline URL. The `key_id` condition moved to Ask First (SKILL.md:70). Scenario 1 still says "or asks whether", which is consistent. Bullets 1 and 2 still hold two facts each. |
| M-2 Import `id` form "Terraform >= 1.5" mis-attributed | FIXED | always-do-foundation.md:42-44 no longer states 1.5. |
| M-3 `(unverified)` inside always-do HCL | FIXED | always-do-secrets.md:17 uses `var.db_password_wo`, marked placeholder. The ephemeral/random_password line is gone. See R2-M3 for the leftover U2 row. |
| M-4 Vague `ephemeral-capable` variable comment | FIXED | never-do-secrets.md:22 and :45 now say "placeholder: declared elsewhere". |
| M-5 Ask First rows with one trailing citation group | FIXED | SKILL.md:67 and :68-73 attach the citation to each clause. |
| M-6 "Fixes need at least that line" | FIXED | SKILL.md:48 and always-do-foundation.md:7-8 now say `~> 6.69` includes the 6.58.0/6.59.0 fixes. |
| M-7 Ephemeral HCL placement and always-do naming | FIXED | New blueprints/ask-first-ephemeral.md (29 lines). Hub intro always-do-patterns.md:4-5 links it. Quick Navigation SKILL.md:37 links it. Mapping rows unverified-and-risks.md:50-51 point to it. |
| L-1 `region` cited to the guide only | NOT FIXED | SKILL.md:98 unchanged. The data-source and ephemeral pages are not cited for "data sources and ephemeral resource". |
| L-2 Tag orphans in the mapping | FIXED | The "(Ask First, medium confidence)" and never-do-secrets comment tags no longer exist. Every tag in text has a mapping row. |
| L-3 Placeholders not marked | FIXED | `# example` / `placeholder` markers on all HCL values (foundation :32,:34; secrets :14,:16,:17,:18). Exception: R2-L5. |
| L-4 "ephemeral resource only reads" unsourced | FIXED in blueprints, residual in evaluation-scenarios.md:87 (R2-M4). |
| L-5 Trap scenarios reproduce legacy claims | Accepted | Framed as rejections (scenarios 2, 4, 5). No change needed. |
| L-6 Security Hub negative claim | Accepted | SKILL.md:107 is narrowed to the seven controls and dated. |
| L-7 Sibling names unconfirmed | FIXED | `provisioning-aws-secrets-manager-v6`, `-kms-v6` and `-iam-v6` all exist under packages/aws-terraform/.apm/skills/ (glob). |
| L-8 Identity import source differs | NOT FIXED | SKILL.md:21 cites the ssm page. SKILL.md:60 and foundation :58 cite the vpc page (F11). The research cites both. Record it or cite one page. See R2-L2. |

No REGRESSED items.

### Never rows, counted

| Place | Rows | Evidence |
|---|---|---|
| SKILL.md Never table | 7 | lines 80-86 |
| never-do-patterns.md hub | 7 | lines 8-14 |
| `## ` WRONG entries in blueprints | 7 | never-do-secrets.md 5, never-do-names-version.md 2 (grep count) |

One-to-one by topic and order: insecure_value, value, data source, by-path, ephemeral name, leading slash, 6.57.0. Hub anchors resolve by slug (checked all 7, plus foundation, secrets and register anchors). Blueprint WRONG headings match the rows.

DON'T texts are documented facts (resource page, data-source pages, ephemeral page, CHANGELOG/F4). Instead column: rows 1, 2, 5, 6, 7 are documented. Rows 3 and 4 are advice, not a documented fact (R2-M1).

`value_wo` needs Terraform >= 1.11: stated at SKILL.md:20, :50, :81 and always-do-secrets.md:7. Pass. ask-first-ephemeral.md does not restate it, which is acceptable.

Ephemeral move consistency: hub intro, Quick Navigation, never-do-secrets.md:64 and :80, SKILL.md:72, and register rows all agree. The ephemeral blueprint is correctly in the Ask First tier and carries U1 and M1 tags with mapping rows.

## HIGH

None.

## MEDIUM

- R2-M1: Never rows 3 and 4 Instead are advice, not documented facts, and row 3 and 4 point into a medium section.
  - Location: SKILL.md:82-83, never-do-secrets.md:63-64 and :79-80.
  - Evidence rule: the Never alternative must be High. "Avoid reading... when you need a clean state" is a recommendation derived from the documented plaintext-state fact. It adds "(see Ask First: Ephemeral read)", which links to content tagged medium and unverified.
  - Fix: either state the documented fact only ("the data source stores the decrypted value in raw state as plain text") in the Instead column, or move rows 3 and 4 to Ask First. If the rows are removed, the Never count becomes 5 and hub plus blueprints must follow.
- R2-M2: Untagged inference in Ask First and the ephemeral blueprint.
  - SKILL.md:72: "It is the option when a data source's state exposure is not acceptable." Follows a medium tag but is not itself tagged and has no page.
  - ask-first-ephemeral.md:29: "`value_wo = ephemeral...` is the safe write". It depends on M1 semantics and is not tagged.
  - Fix: tag both `(medium confidence)` or cut them. Rate: MEDIUM (unsourced and untagged).
- R2-M3: Orphan register row U2.
  - Location: unverified-and-risks.md:21. "not used in any shipped example", status "not shipped". `U2` appears nowhere else (grep).
  - Fix: delete the row. The `random_password` item is not shipped. Renumbering U3 and U4 then needs mapping updates (rows :47-48).
- R2-M4: Evaluation scenario 4 requires a statement the skill does not make.
  - Location: evaluation-scenarios.md:87 ("States that the ephemeral resource only reads") and :88 (relies on M1 semantics).
  - The skill removed the "only reads" claim after round 1 (L-4), so a judge cannot confirm it from the skill. The research has it only as a legacy-claim correction (W4).
  - Fix: change to "States that writing with `value` stores the plaintext in state; recommends `value_wo`" and mark the ephemeral-source part as medium confidence.

## LOW

- R2-L1: `region` row cites the guide and the resource page only (SKILL.md:98). Add the data-source and ephemeral pages or narrow the claim.
- R2-L2: Identity-import sources differ (SKILL.md:21 ssm page; SKILL.md:60 and always-do-foundation.md:58 vpc page). Use one consistent page, or cite both everywhere.
- R2-L3: `always-do-patterns.md` and `never-do-patterns.md` are not linked from SKILL.md Quick Navigation or any file (grep). The hubs are unreachable. Add one link each.
- R2-L4: Always Do bullets 1 and 2 hold two facts each (SKILL.md:48 "includes the fixes" plus "needs >= 6.59.0"; SKILL.md:50 "never in state" plus "Terraform >= 1.11"). Both facts are on one page each, so tolerable. Split if strict.
- R2-L5: SKILL.md:84 `arn = aws_ssm_parameter.x.arn` has no `# example` marker.
- R2-L6: Register mapping table columns are `Tag text | Where | Register id`. The policy names the first column `Tag text used in the skill`. Rename.

## Checklist

| Check | Result |
|---|---|
| Frontmatter only name + description, quoted, "Use when", name = folder | pass (about 262 chars) |
| SKILL.md length 100-200 | pass (132 lines) |
| Blueprint length <= 160 | pass (all under 85) |
| Evaluation scenarios >= 4 | pass (5) |
| Plain tag notation (no bold, no brackets) | pass (grep 0) |
| F#/M#/W# ids and workspace paths in shipped text | none; only register ids M1, M2 |
| Tags and register consistent | pass, except orphan row U2 (R2-M3) |
| Header counts in register | not stated, cannot compare |
| Example and placeholder markers | pass, one gap (R2-L5) |
| Anchors resolve | pass by slug check |

## Claims sampled (36)

All pass unless a finding is listed.

1. `data_type` values `text`, `aws:ssm:integration`, `aws:ec2:image`.
2. Attributes `arn`, `version`, `has_value_wo`, `tags_all`.
3. `type` values.
4. Exactly one of `value`, `value_wo`, `insecure_value`; `value` always sensitive.
5. Data source `name:version` selects a version.
6. Data source `with_decryption` default `true`.
7. Data source returns strings; `split()` for `StringList`.
8. By-path `path` starts with `/`, max 15 levels.
9. By-path `recursive` default `false`.
10. A full parameter name as `path` returns nothing unless it is a hierarchy prefix.
11. Parameter ARN shape without an extra `/`.
12. `/parameter-name` and `parameter-name` both root parameters.
13. Encryption context `PARAMETER_ARN` and its IAM condition key.
14. KMS permissions per tier and for decrypt.
15. 100 versions retained.
16. Tier limits 10,000/4 KB and 100,000/8 KB.
17. Intelligent-Tiering creates Standard unless Advanced is needed, then upgrades one-way.
18. Parameter policies and cross-account sharing are Advanced features.
19. Standard free, Advanced charged.
20. Default tier is per account/Region and does not affect existing parameters.
21. `tier` defaults to the account/Region default tier.
22. Secrets Manager recommendation wording.
23. Parameter Store rotation None.
24. PutParameter default 3 TPS (10 higher).
25. `overwrite` defaults, no deprecation marker, lifecycle pointer.
26. 6.58.0 ARN import and specific-version fixes.
27. 6.59.0 leading-slash fix and new list resource.
28. 6.0.0 guide has no entries; `aws_ssm_association` adjacent.
29. Terraform 1.17.0 stable since 2026-10-21, no breaking changes (F2).
30. 6.70.0 latest, no 7.x, v7 planned (F3).
31. 6.57.0 withdrawn from GitHub and the Registry (F4).
32. Ephemeral resource: `arn` required, `with_decryption` default `true`.
33. Ephemeral page says "new feature, usage may change"; no minimum version (U1).
34. Ephemeral page directs metadata reads to the data source.
35. Parameter policies: no Terraform argument documented (L3).
36. `aws/ssm` cannot have access-control policies; only symmetric keys. Pass. The "needed for key-policy control" wording is a logical reading of the AWS statement, accepted.

Weak points among the 36 are captured in R2-M1, R2-M2, R2-L1 and R2-L2.

## Verdict

Round-1 HIGH items are fixed. No HIGH remains. Fix R2-M1 to R2-M4 (all small edits) before marking VERIFIED. Re-run `verify_skill.py` after the edits.
