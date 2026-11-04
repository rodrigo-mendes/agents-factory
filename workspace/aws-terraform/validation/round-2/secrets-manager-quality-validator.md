# Quality validation, round 2: provisioning-aws-secrets-manager-v6

Target: packages/aws-terraform/.apm/skills/provisioning-aws-secrets-manager-v6/. Date: 2026-10-23.
Method: full read of SKILL.md and 8 blueprints; grounding against research_AWS_SecretsManager_tf-aws-v6.md and _family_facts_v6.md; 4 policy files. WebFetch and shell are not available in this run, so grounding is against the research file only, and verify_skill.py / normalize_tags.py were not executed. Line counts come from the Read tool output.
Counts: HIGH 0, MEDIUM 4, LOW 10 (3 of the LOW items are round-1 leftovers). Policy note: 1 (not counted).

## Round-1 findings status

| Id | Status | Evidence |
|---|---|---|
| H1 replica Never row | FIXED | Never table (SKILL.md:104-113) has no replica row. It is now an Ask First row tagged (medium confidence, absence of evidence), SKILL.md:98, register M4 (unverified-and-risks.md:32, mapping :51). Gone from never-do-secrets.md and never-do-patterns.md. |
| M-1 block_public_policy in Always Do | FIXED | Always Do bullets SKILL.md:47-85 contain no tag. The default caveat is in Ask First :96 (U2). |
| M-2 "one place" policy in Always Do | FIXED in SKILL.md | Only in Ask First :96 (M1). The tag remains in always-do-rotation-policy.md:54, which is a blueprint (allowed). See LOW N11. |
| M-3 M1 entry in Never blueprint | FIXED | never-do-rotation-policy.md has no M1 text; never-do-patterns.md:7 states only sourced rows are listed. |
| M-4 inline rotation_* Never row | FIXED | Now an Ask First row, SKILL.md:97, tagged M5. |
| M-5 90-day rule | FIXED (see N10) | SKILL.md:80 and always-do-rotation-policy.md:10-11 now say SecretsManager.4 checks rotation within 90 days (default). HCL comment :20 reads "example value". |
| M-6 Upgrade path sentence | FIXED | Removed; grep for "Upgrade path" finds nothing. |
| M-7 migration attribution | FIXED | SKILL.md:136 cites the upgrade guide only; :138-143 cite CHANGELOG. |
| M-8 "fails init" | FIXED | Removed; SKILL.md:28 and unverified-and-risks.md:11 now say only "withdrawn ... never pin". |
| M-9 source blending | FIXED | SKILL.md:50-51 provider page, :53-54 Terraform docs, :56-57 provider page. Matches research lines 98-106. |
| L-1 example markers | NOT FIXED (partial) | Marked: always-do-secrets.md:34, always-do-rotation-policy.md:20, never-do-rotation-policy.md:12. Unmarked: `tags = { Environment = "prod" }` always-do-secrets.md:38; `automatically_after_days = 30` always-do-rotation-policy.md:39, never-do-rotation-policy.md:19,34,40. |
| L-2 Never row 1 note | FIXED (moot) | The absence-based row is gone. The remaining Never row 1 (ISO-8601 duration) rests on the positive spec "hours, e.g. 3h" (research :129). |
| L-3 register shape | NOT FIXED (partial) | Mapping columns now read "Tag text used in the skill / Where / Register id" (:45). "No I items" line present (:23). Still no header counts for the U/M/L sections (policy: header counts equal the items). Script not run. |
| L-4 undefined policy document | FIXED | always-do-rotation-policy.md:60 says "placeholder: define this data source elsewhere"; never-do-rotation-policy.md:57 has a placeholder note. |
| L-5 KMS source | FIXED | SKILL.md:91 cites the provider secret page. |
| L-6 combined ephemeral HCL | NOT FIXED | always-do-secrets.md §3 (:59-64) feeds `var.db_password`; §4 (:80-82) shows the ephemeral separately. No example wires the ephemeral into `secret_string_wo`. |

No regressions.

## Anchors and one-to-one checks

- Anchors: all resolve. never-do-patterns.md:9-16 -> never-do-secrets.md headings 1-4 and never-do-rotation-policy.md headings 1-4, including `#2-rotation_rules-with-rotation_enabled--false` and `#4-pinning-version-6570`. always-do-patterns.md:8-13 and SKILL.md "See" links -> always-do-secrets §1-4, always-do-rotation-policy §5-6. Also `#version-lifetime-risk`, `#source-bibliography`, `#blueprints--guardrails`, `#quick-reference`, `#external-resources`.
- Never rows: SKILL.md has 8 rows, never-do-patterns.md has 8 index rows, and the blueprints have 8 sections. The same 8 topics appear in the same set. They are NOT one-to-one at WRONG-entry level, see N3.
- Scenario 3 (evaluation-scenarios.md:56-76): judgeable (3 must_pass, 2 must_not) and consistent with Never rows 4 and 6. Scenarios 2 and 4 are consistent with Never rows 5, 2, 3 and 1.
- Line counts: SKILL.md 156; always-do-patterns 13; never-do-patterns 16; never-do-secrets 74; never-do-rotation-policy 81; always-do-secrets 95; always-do-rotation-policy 65; unverified-and-risks 74; evaluation-scenarios 99. All within limits. Frontmatter is valid (name, quoted description under 300 characters, "Use when").

## Strict checks requested

- No Never row rests on absence or a medium/unverified item: PASS. The 8 Never rows each cite a positive statement (ISO/hours, Terraform state docs, deprecated `arn`, exactly-one-source, `policy` warning, `rotation_rules` omission, `type` immutability, withdrawn 6.57.0). Caveat: the Never blueprint carries an (unverified) note (N3) and one alternative is not page-stated (N8).
- Always Do bullets High-only with no tags inside: PASS (SKILL.md:47-85).
- Terraform versions not conflated: PASS. `secret_string_wo` >= 1.11 cited to the provider page (SKILL.md:19, :50, :107); ephemeral >= 1.10 cited to Terraform docs (:20); identity import >= 1.12 appears only in always-do-secrets.md:45.
- Rotation `duration` is in hours ("3h"): PASS (SKILL.md:77, :106, :128).
- SecretsManager.4 wording is not a hard rule: PASS with caveat N10.
- Tags and register consistent: PASS. Tags in text are U1, U2, U3, M1, M2, M3, M4, M5, and each has a mapping row with no orphans. Plain notation. No F#/M# ids in skill text (grep clean). Only wording drift is N9.

## Fresh grounding sample

About 40 claims checked against the research, not covered in round 1. Examples: 1.16.6 current (F1); latest 6.70.0 dated 2026-10-21; 1.17.0 stable 2026-10-21 (F2); secret name charset and `name_prefix` conflict; exports `arn`/`id`/`replica`/`tags_all`; version exports; `replica` computed status fields; replica `kms_key_id` default; `tags` overriding `default_tags`; no required argument; `version_stages` and `AWSCURRENT`; "resource tracks only its own version"; ephemeral "same arguments as the data source"; data source `version_stage` default; "may evolve" quote; Aurora `depends_on`; mid-rotation `AWSPENDING`; destroy does not re-enable rotation; Zelkova wording; M1 "same underlying policy"; `type` values; `force_overwrite_replica_secret` description; migration entries 6.45, 6.47, 6.50, 6.56, 6.57.1, 6.62, 6.70; SecretsManager.1-5 titles. All match the research except the items below.

## MEDIUM

- N1. SKILL.md:83 and always-do-secrets.md:38: "without PII" is cited to the Security Hub controls page. In the research the phrase appears only in the researcher's "Terraform lever" column (research :171), not as page text. `default_tags` is likewise a lever, not a page statement. Unsourced and untagged inside an Always Do bullet. Fix: cite the page that states it, or drop "without PII" and keep only "SecretsManager.5 checks required tag keys".
- N2. SKILL.md:29 and unverified-and-risks.md:13: "v7 is planned" has no source and no tag. The only supporting statement is orchestrator fact F3, whose listed sources are release listings that do not obviously say "planned". Fix: cite the page, tag it (unverified), or drop it.
- N3. Never rows versus blueprint WRONG entries are not one-to-one. never-do-rotation-policy.md §3 (:51-63) contains two WRONG entries (`policy = null` and `"{}"` on the policy resource), while SKILL.md:110 has one row (the `"{}"` rejection appears only in its Instead column). The same §3 prose (:47-49) carries (unverified) U3 text, which puts an unverified item inside a Never blueprint. Fix: split the "{}" case into its own row (it is documented as rejected by the policy page) or remove the second WRONG block; move the U3 note out of the Never blueprint to Ask First.
- N4. evaluation-scenarios.md:21: Scenario 1 must_pass "Does not put rotation arguments on aws_secretsmanager_secret" enforces claim M5 (medium confidence, absence of evidence) as a hard pass criterion, although the skill demoted it to Ask First. Fix: drop the criterion or make it advisory (not in must_pass).

## LOW

- L-1 (round-1 leftover): unmarked example values, see table above.
- L-3 (round-1 leftover): register has no header counts.
- L-6 (round-1 leftover): no combined ephemeral to `secret_string_wo` HCL.
- N5. SKILL.md:37-38 Quick Navigation labels are stale after the restructure: "removed args" and "policy conflicts" do not exist in the blueprints. They should read "secrets in state, value sources, deprecated `arn`, `type`" and "rotation duration, rotation_rules, policy removal, withdrawn 6.57.0".
- N6. SKILL.md:59 and :108 claim `arn` is deprecated on the version resource and the data source but cite only the resource page. The data source page (d/secretsmanager_secret_version) states the data source part; cite both.
- N7. Same claim, two pages: SKILL.md:111 cites the rotation page for "omit rotation_rules when rotation_enabled = false", never-do-rotation-policy.md:36 cites CHANGELOG 6.62.0. Research lines 44 and 126-127 place "must be omitted" in the CHANGELOG entry. Align both citations to the page that states it.
- N8. never-do-secrets.md §4 (:61-67): the WRONG block is a valid standalone resource ("WRONG if changed later"), so it is not demonstrable; and the Instead "create a new secret with the desired `type`" (SKILL.md:112) is a reasonable consequence but not page-stated. Rephrase the Instead or tag it.
- N9. Register M4 and M5 status cells read "(medium confidence)" (unverified-and-risks.md:32-33) while the text tag is "(medium confidence, absence of evidence)". The same claim should carry the same tag text.
- N10. SKILL.md:80: "Set rotation_rules with Security Hub SecretsManager.4 in mind" is advisory wording in the Always Do tier, with a parenthetical "(default)". It is acceptable as not a rule, but it is not an actionable High claim. Suggest moving it to Ask First (rotation frequency decision) or to a note.
- N11. always-do-patterns.md:13 lists pattern 6 (resource policy with `block_public_policy`) as Always Do, but SKILL.md has no matching Always Do bullet (it moved to Ask First), and always-do-rotation-policy.md:52-55 carries (unverified) and (medium confidence) text. Allowed in blueprints, but the index implies an Always Do rule that no longer exists. Rename or move the pattern to an "ask first" blueprint index.

## Policy note (not counted)

All provider-doc citations are main-branch raw markdown. evidence-rule.md:10 caps unversioned or "latest" pages and main-branch examples at medium confidence, but _family_facts_v6.md F12 designates these pages as the authority. This is a policy ambiguity (also noted in round 1 as M-4); the skill follows F12. Resolve in the policy file, not in this skill.

## Prioritized actions
1. N3 and N4: align Never rows, blueprint WRONG entries and scenarios with High-only evidence.
2. N1 and N2: source or drop "without PII" and "v7 is planned".
3. Close round-1 leftovers L-1, L-3, L-6; fix N5-N11.
4. Run verify_skill.py and normalize_tags.py (not run in this validation).
