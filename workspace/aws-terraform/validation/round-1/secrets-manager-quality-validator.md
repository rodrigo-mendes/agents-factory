# Quality validation, round 1: provisioning-aws-secrets-manager-v6

Target: packages/aws-terraform/.apm/skills/provisioning-aws-secrets-manager-v6/. Date: 2026-10-23.
Method: full read of SKILL.md and 8 blueprints, checked against research_AWS_SecretsManager_tf-aws-v6.md, _family_facts_v6.md and the 3 policy files. About 40 claims sampled (Always Do, Never Do, Ask First, Quick Reference, HCL comments, migration section). WebFetch was not used. Grounding was checked against the research file only.
Counts: HIGH 1, MEDIUM 9, LOW 6.

## Checks that pass
- Line counts: SKILL.md 163. Blueprints: always-do-patterns 13, always-do-secrets 95, always-do-rotation-policy 65, never-do-patterns 19, never-do-secrets 109, never-do-rotation-policy 118, unverified-and-risks 66, evaluation-scenarios 98. All are at most 160 lines. Counted from the Read tool output.
- Frontmatter: only `name` and `description`; the description is quoted, under 300 characters, and contains "Use when"; the name matches the folder; the `-v6` suffix is approved.
- (b) Terraform versions are not conflated. Write-only arguments need 1.11 (SKILL.md:19, always-do-secrets:49, never-do-secrets:27). Identity import needs 1.12 (always-do-secrets:45). Ephemeral resources need 1.10.
- (c) `duration` is given in hours as "3h" (SKILL.md:77, :112). `force_delete_without_recovery` is called not an argument. No resource is claimed removed in v6; row 3 says "no such resource appears in the docs".
- (g) No F#/M# internal ids, bold or bracket tags appear in shipped text. The only register ids are U1, U2, M1, M2, M3, L1 to L3, and these are legitimate. Every tag instance has a mapping row, and no mapping row is orphaned. Research legacy claims 4 and 6 are not reproduced as fact.
- Sampled claims that match the research: recovery window 7-30, default 30, and 0 means no recovery; the `kms_key_id` ARN rule; the `replica` block fields; `AWSCURRENT` perpetual diff; `rotate_immediately` default true; `rotation_enabled` since 6.62.0; the `"{}"` policy behaviour; `block_public_policy` default not stated; `type` immutable; 6.57.0 withdrawn; the 6.45/6.47/6.50/6.56/6.57.1/6.62/6.70 migration facts; the SecretsManager.4 and .5 mappings.

## HIGH

### H1. Never Do row 3 (`aws_secretsmanager_secret_replica`) is not High-confidence
- Location: SKILL.md:111; never-do-secrets.md:76-90; never-do-patterns.md:12; evaluation-scenarios.md:65.
- Research §8 item 3 says "no such resource appears in any doc fetched ... (claim unsupported)". That is absence of evidence, which caps at (medium confidence, absence of evidence) under evidence-rule.md. Never Do allows High rows only.
- The cited source is the secret resource page, which never mentions a replica resource. It cannot ground the claim.
- Fix: move the row out of Never Do into Ask First or a blueprint, tagged (medium confidence, absence of evidence), and add an M-id to the register. Alternatively fetch an upstream resource listing that confirms the resource does not exist, then record it as High. Reword scenario 3 so it does not require the rejection as a fact.

## MEDIUM

- M-1. SKILL.md:83: an Always Do bullet carries "(unverified)" for the `block_public_policy` default (U2). Evidence-rule says Always Do has one High claim per bullet and no caveats. Move the default caveat to Ask First and keep only a High advisory in Always Do.
- M-2. SKILL.md:86: an Always Do bullet is tagged (medium confidence) for "manage policy in one place" (M1). It also appears in always-do-rotation-policy.md:54. Move it to Ask First.
- M-3. never-do-rotation-policy.md:90-107 and never-do-patterns.md:18: the Never Do blueprint carries a (medium confidence) entry (M1). It is correctly absent from the SKILL.md Never Do table, but the blueprint index presents it as a Never Do. Move it to Ask First or a medium-risk blueprint.
- M-4. SKILL.md:110 (Never Do, inline `rotation_*`): this rests on absence in the secret page, backed by the upgrade guide having no Secrets Manager entry. The documented positive is `aws_secretsmanager_secret_rotation`. Either tag the absence or ground it in the secret page's argument list. The page is main-branch, so it is arguably medium confidence under evidence-rule.md. The factory treats main-branch pages as High via F12, so this is a policy ambiguity to resolve.
- M-5. SKILL.md:80 and always-do-rotation-policy.md:10,20: the Always Do "Keep `rotation_rules` at 90 days or less" is stated as a rule. The research says only that the SecretsManager.4 parameter `maxDaysSinceRotation` is configurable from 1 to 180, with a default of 90. This is a compliance choice, not a provider requirement. Reword it as a Security Hub default or move it to Ask First. The HCL comment "keep at 90 or less" should say it is the SecretsManager.4 default.
- M-6. SKILL.md:150 ("Upgrade path: get a clean plan on the latest 5.x, set `~> 6.69`, run `terraform init -upgrade`"): the research does not contain this. It is untagged and unsourced.
- M-7. SKILL.md:142-148: the whole migration section cites the 6.0.0 upgrade guide as its source. Only line 144 comes from it. Lines 145-148 come from the CHANGELOG, so the source attribution is wrong.
- M-8. SKILL.md:28 and unverified-and-risks.md:11: "any constraint resolving to it fails init" is not in the research. The research says only "withdrawn" (F4). It is untagged and unsupported.
- M-9. Source blending (known risk e), SKILL.md:50-51 and :56-58. Line 50-51 attributes "write-only values are not persisted" to the provider page URL, but that comes from the Terraform docs [9]. The research says the provider page does not itself say this. Lines 56-58 attribute the quoted phrase "keeps them out of logs and console output" to the Terraform docs URL, but it is the provider page's wording. Always-do-secrets.md:65-66 cites both sources, which is acceptable. Correct the SKILL.md attribution so each statement points to the page that makes it.

## LOW

- L-1. The example values `eu-west-1` (always-do-secrets.md:34, never-do-secrets.md:87), `automatically_after_days = 30` (always-do-rotation-policy.md:20,39; never-do-rotation-policy.md:22,34,41,55) and `tags = { Environment = "prod" }` are not marked as examples. Add "example value" comments.
- L-2. SKILL.md:109 (Never Do row 1) is absence-based but consistent with research §8.1, where the doc states the argument is absent. Consider a note that the page was read in full.
- L-3. The register is missing an irresolvable (I..) section and the header counts the policy asks for. The mapping columns are named "Tag text / Where / Register id" instead of "Tag text used in the skill / Where / Register id". Run verify_skill.py.
- L-4. always-do-rotation-policy.md:60 references `data.aws_iam_policy_document.secret`, which is not defined. Similar undefined references are in never-do-rotation-policy.md:98,102. Add a stub or a comment.
- L-5. SKILL.md:97 (Ask First, KMS): it cites the AWS best-practices page for "created on first use" and "ARN for another account". Both come from the provider page [1]. Fix the source.
- L-6. The Always Do bullet "Feed write-only arguments from the ephemeral resource" (SKILL.md:53) has no HCL that wires the ephemeral value into `secret_string_wo`. always-do-secrets.md:80-95 shows the two separately. Add a combined example.

## Prioritized actions
1. H1: remove the replica row from Never Do and re-tag it.
2. M-1, M-2, M-3: move medium-confidence and unverified items out of the Always Do and Never Do tiers.
3. M-6, M-7, M-8: ground or drop the unsupported sentences and fix the migration sources.
4. M-4, M-5, M-9: fix wording and source attribution.
5. Fix the LOW items; run verify_skill.py and normalize_tags.py before re-validating.
