# Quality validation — provisioning-aws-sam-v6 (round 2)

Validator: quality-validator, 2026-10-23. Target: packages/aws-terraform/.apm/skills/provisioning-aws-sam-v6/ (SKILL.md 209 lines + 10 blueprints).
Not done: WebFetch spot-check (no WebFetch tool in this session). Grounding was checked against the research [P]/[A]/[I] tags and the facts file.

## Counts

HIGH 0 | MEDIUM 0 | LOW 3

## 1. Round-1 findings

| ID | Status | Evidence |
|---|---|---|
| H1 | FIXED | SKILL.md:107-109: the Always bullet states only AWS's sentence (macro template, including `AWS::Serverless`, created without first reviewing the changes in a change set) and cites API_CreateStack. SKILL.md:129 (Ask First) holds the provider-side conclusion, tagged (unverified, inference) and mapped to U4 (register line 64). always-do-cloudformation.md:53-58 repeats the AWS sentence and marks the provider behaviour (unverified). The HCL at always-do-cloudformation.md:70 is now a comment. never-do-cloudformation.md:70 has "capabilities omitted"; the other two WRONG/CORRECT blocks (lines 76-80, 91-100) have no `capabilities`. Scenario 4 (evaluation-scenarios.md:92) is aligned. A grep of CAPABILITY/capabilit across the skill shows no Always/Never row, HCL block or scenario that still depends on U4. |
| M1 | FIXED | SKILL.md:143 (Never row 2) now cites build, start-api and getting-started. |
| M2 | FIXED | SKILL.md:34 and :127 carry the same tag (medium confidence, absence of evidence). Both map to U2 (register line 62). A residual wording gap is LOW-1. |
| L1 | FIXED | SKILL.md:32-33 are tagged. The tag mismatch with Ask First :126 is LOW-1. |
| L2 | FIXED | SKILL.md:125 is now (unverified, inference). |
| L3 | FIXED | always-do-cloudformation.md:5 states (unverified) in the header. never-do-cloudformation.md:54 says "example attribute; see always-do-cloudformation.md header". always-do-cloudformation.md:104 has "# example attribute". |
| L4 | FIXED | SKILL.md:40-41 carries an inline URL for the v7 quote. |
| L5 | FIXED | SKILL.md:64 now says "this skill's targets are" for the values, with the page cited only for `~>`. |
| Evaluator items (Scenario 4) | FIXED | evaluation-scenarios.md:92 requires the AWS wording plus "provider reviews a change set is unverified". There are 5 scenarios with must_pass and must_not. |

No regressions found.

Never rows: 11 in SKILL.md (:142-152), 11 in the hub never-do-patterns.md (:8-18), and 5+4+2 = 11 in the blueprints, all one-to-one. Each is a [P]/[A] fact with a sourced Instead cell: the 6.57.0 withdrawal, the `dynamodb_table` deprecation, and the page-stated mitigations for rows 1, 4, 5 and 9. No Never row contains [I] text.
Always Do: 18 bullets (:64-118), High-only, no tags, one claim and one URL each.

## 2. Fresh grounding sample (about 42 claims not checked in round 1)

All matched the research or facts, with no HIGH or MEDIUM mismatch:
- Version Context rows: Terraform 1.16.7 (2026-10-22), 6.70.0 (2026-10-21), 6.57.0 withdrawn, SAM v1.170.0, v1.166.2 quote, `~>` for root modules and `>=` for reusable modules.
- Quick Reference rows: SAR stack timeouts 30m, `serverlessrepo-` prefix, `semantic_version` default; `template_body` 51,200 and `template_url` 460,800; stack set `permission_model` and import forms; CloudFormation.1-4 titles, severities and the April 2024 retirement.
- always-do-sam-cli.md: the five supported commands, Python 3.8 and GNU Make, resource-ID forms, `.aws-sam`, `hook_name` in the config file, `--build-image` container builds, the three limitations, the prepare hook text, and the metadata fields and `docker_file` default.
- always-do-cloudformation.md: data source purpose quote, import `name`/`name,DELEGATED_ADMIN`, import block 1.5.0, `administration_role_arn` and `execution_role_name` defaults, "SAM CLI expands at change-set creation", and the NOTE on parameters.
- never-do-sam-cli.md: the incompatible flags and the `--skip-prepare-infra` quote.
- Migration section: 6.0 guide mentions only `stack_set_instance`, the 6.52.0 entries, the "no entries 6.48.0-6.70.0" absence tag, and the upgrade-path wording (the phrases "Before upgrading", "without errors or unexpected" and "init -upgrade" are in the facts file, F17).
- v7 quote = F18. Read dates 2026-10-23 and Terraform 1.17.0 CHANGELOG 2026-10-22 are consistent with F19.

## 3. Rule checks

- Tags and register: U1-U12, M1-M3 and L1-L4 are all present, and the mapping covers every in-text tag with no orphans. The new rows are present: lines 65, 66, 75-77 (U4, U12, U7, U10) and the version-context row for U1/U2. Notation is plain.
- No internal ids, [I]/[P]/[A] tags or research wording appear in SKILL.md or the pattern blueprints (grep found no matches). U/M/L ids appear only in the register.
- Scope: SAM-is-not-a-provider-resource is at SKILL.md:12. Only `sam build` and `sam local invoke/start-api/start-lambda` are claimed. `sam deploy/sync/validate` are claimed only as absent from the reference pages (M3 tag). No SAM Terraform deploy claim appears.
- Upgrade path matches F17 wording. v7 matches F18. Read dates match F19.
- Legacy claims (`>= 1.7`, `~> 6.0`, `dynamodb_table` as correct, "nested", "cannot detect drift") do not appear.

## LOW

LOW-1. Tag mismatch for the same claim between the text and the register. SKILL.md:33 (minimum Terraform not stated) is tagged (medium confidence, absence of evidence), but Ask First :126 and register row U1 (unverified-and-risks.md:25, :61) say (unverified). SKILL.md:34 and :127 (hook status) use the absence tag, but the register U2 status (:26) says (unverified). Fix: align the U1 and U2 register status text and the Ask First tag, or note "absence of evidence" in the register.

LOW-2. always-do-patterns.md:13 lists `CAPABILITY_AUTO_EXPAND` as a component of the "always do" pattern 5 index entry, although the section now only states AWS's condition and leaves provider need as Ask First. Fix: reword to "capabilities (see Ask First)".

LOW-3. SKILL.md:74-76 (Always bullet 4) says to pass `--hook-name terraform` to `sam local invoke`, `start-api` and `start-lambda`, but cites the terraform-support page. The option text itself is on the command reference pages (start-api page, build page). The support page does list the commands, so the claim holds, but the URL is not the option's source. Fix: cite the start-api reference page, as bullet 5 cites the build page.

## Round-1 items NOT fixed

None.
