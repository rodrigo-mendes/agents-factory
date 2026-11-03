# Quality validation, round 2: provisioning-aws-cognito-v6

Validated 2026-10-23. Skill read from packages/aws-terraform/.apm/skills/provisioning-aws-cognito-v6/ (SKILL.md 169 lines, 8 blueprints).
Method note: WebFetch was NOT available. The live provider pages were not re-fetched. The orchestrator's verification of the cognito_user_pool page (M-5, deletion_protection, schema) is taken as given. All other claims were compared with the research file and family facts.

Counts: HIGH 0, MEDIUM 0, LOW 4 (all new or residual). Round-1 items: 1 HIGH fixed, 6 MEDIUM fixed, 8 LOW (6 fixed, 2 not fully fixed), 4 evaluator items fixed.

## Round-1 findings

| Item | Status | Evidence |
|---|---|---|
| H1 | FIXED | never-do-client-oauth.md CORRECT blocks: §1 :20-25 (flag + flows), §2 :41-49 (flag, flows ["code"], scopes ["openid"]), §3 :66-70 (no OAuth args), §4 :89-95 (flag), §5 :112-119 (flag, flows, scopes). Every CORRECT block in never-do-pool-domain.md (§1-§5) uses no client OAuth args; §2 CORRECT is a comment only. No CORRECT block has the defect. |
| M-1 | FIXED | never-do-pool-domain.md:28, :41-42 and SKILL.md:108 say only "the page says to use taint"; the invented command line is gone and the comment states "exact command line not stated on the page". |
| M-2 | NOT FIXED (LOW) | SKILL.md:46-48 still holds two claims (`~> 1.16`, `~> 6.69`) with one URL that supports only the `~>` convention. Values are sourced in the Version Context table (:16-17). |
| M-3 | FIXED | SKILL.md:67-69 now states only the page facts (ACTIVE/INACTIVE, default INACTIVE, deactivate before deleting). The Cognito.6 recommendation moved to Ask First :94 with the Security Hub URL. |
| M-4 | FIXED | Ask First rows :90-100 each carry a provider, AWS or Security Hub URL, including token revocation :98. Only the API Gateway row :101 has none, and it is tagged (unverified). |
| M-5 | FIXED | always-do-pool.md:28-31 quotes "requires at least 2 `account_recovery_setting` entries", flags the difference from the page example, tags (medium confidence), and the HCL :51-60 follows the example (one block, two `recovery_mechanism`). SKILL.md:58 (hub bullet) no longer repeats the "two entries" wording. Ask First :93 carries the same flag. deletion_protection ACTIVE/INACTIVE default INACTIVE (SKILL.md:67, pool §3 :84) and schema add-only quote (SKILL.md:64, pool §3 :77) match the verified page text. |
| M-6 | FIXED | always-do-client-domain.md:39-40 tags both the provider alias and `region` routes (medium confidence). Register M5 maps it (unverified-and-risks.md:63). |
| L-1 | FIXED (one residual) | "Superseded claims" and "read across a read boundary" are gone. M1 still says "was not read (coverage limit)" (unverified-and-risks.md:34); acceptable neutral phrasing. See new L-C. |
| L-2 | FIXED | SKILL.md:113 "either the legacy values or the ALLOW_* values in one client, not both". |
| L-3 | FIXED | SKILL.md:116 Instead cell is `~> 6.69` only. |
| L-4 | FIXED | SKILL.md:24-27 now has inline URLs on both version-lifetime bullets. |
| L-5 | FIXED | SKILL.md:96 reads "(unverified)". |
| L-6 | FIXED | M3 is a "provider default not stated" claim tagged (medium confidence), SKILL.md:98. The absence-of-evidence form is used where it applies (SKILL.md:154, M1). |
| L-7 | NOT FIXED (LOW) | Heading is now "Tag to register mapping" (unverified-and-risks.md:50). Column header is still "Tag text" (:52); policy tag-notation-and-registers.md:19 says "Tag text used in the skill". |
| L-8 | FIXED | Bullet 2 now cites the cognito_user_pool page, which documents `region` (SKILL.md:49-51). |
| Family-facts note (1.16.7 date) | FIXED | F1 now says 1.16.7 released 2026-10-22; skill matches (SKILL.md:16, unverified-and-risks.md:10). |
| Evaluator 1 (adaptive auth in SKILL.md) | FIXED | SKILL.md:90 "threat protection (including adaptive authentication) is a Plus-plan feature". |
| Evaluator 2 (hubs unlinked) | FIXED | SKILL.md:37 links both hubs. |
| Evaluator 3 (U/M ids in must_not) | FIXED | evaluation-scenarios.md:98 now says the skill's own U#/M# register ids are allowed. |
| Evaluator 4 (scenario 2 criterion 4) | FIXED | evaluation-scenarios.md:45 "Does not state as fact whether the provider forces replacement". |

## Structure and counts (verified by reading)

- Never Do rows: SKILL.md:105-116 = 10; never-do-patterns.md:8-17 = 10; blueprint sections 5 (never-do-pool-domain.md) + 5 (never-do-client-oauth.md) = 10. Order and wording match one to one.
- Always Do bullets: SKILL.md:46-84 = 13. Each has one claim (bullet 1 excepted, see L-A) and one URL, no tags.
- Hub always-do-patterns.md: 6 rows mapping to blueprint sections 1-6.
- Register: U1-U9, M1-M6, L1-L4. Every tag in the skill maps (unverified-and-risks.md:52-64), including new M6 (SKILL.md:93; always-do-pool.md:31). No orphans: U2, U3, U6, U7 and L1-L4 are registered-only (stated limits, not used as tags).
- Tags are plain parenthetical text. Grep for F#/workspace/round ids in shipped text found none; the 26 U/M/L hits in unverified-and-risks.md are the register's own ids, and one in evaluation-scenarios.md is the allowed mention.
- Dates: shared-fact sources 2026-10-23; Terraform 1.17.0 CHANGELOG 2026-10-22 (SKILL.md:25, unverified-and-risks.md:3); 1.16.7 2026-10-22.
- Frontmatter: name + quoted description with "Use when", name matches folder.

## Fresh grounding sample (34 claims not checked in round 1; all grounded)

Checked against the research file (and F-facts): 6.70.0 date 2026-10-21 (F3); Terraform 1.17.0 stable 2026-10-21 (F2); identity-based import needs Terraform >= 1.12 (F11); user_pool_tier LITE/ESSENTIALS/PLUS; advanced_security_mode OFF/AUDIT/ENFORCED; audit mode >= 2 weeks; MFA OFF default; Cognito.5 password-only; Cognito.6 deletion protection; Cognito.1-6 all Medium and their titles; Cognito.3 (min 8, four classes, 7 days); Cognito.1/4 levers (tagged inference); Cognito.2 identity pools; email sender values; DEVELOPER/source_arn rule; `{####}` in email MFA message; password_history_size 0-24 and its advanced-security requirement; schema max 50 and data types; AWS "custom attributes are permanent"; `user_attribute_update_settings` rule; software token disable rule (OFF + remove block); explicit_auth_flows value list; `prevent_user_existence_errors` LEGACY/ENABLED; token validity ranges; managed_login_version 1/2; custom domain exports and `evaluate_target_health = false`; A record / public hosted zone prerequisites; propagation 60 s / up to 1 h; domain import = domain value; ui_customization needs a domain; managed_user_pool_client "does not create or delete"; resource_server, user_group, identity_provider, identity_pool, roles_attachment import IDs and required args; `mapping_rule` max 25; `ambiguous_role_resolution` required for Token/Rules; 6.0 guide only changes `aws_cognito_user_in_group` id; absence claim 6.48-6.70 (tagged); upgrade path wording (F17); v7 note (F18).
Result: 0 wrong, 0 unsourced-and-untagged.

## LOW findings

- L-A (residual M-2). SKILL.md:46-48, Always Do bullet 1 carries two claims (the `~>` convention and the `~> 1.16` / `~> 6.69` targets) with one URL that supports the convention only. Fix: keep the convention in the bullet and leave the target values to the Version Context table.
- L-B (residual L-7). unverified-and-risks.md:52. Rename the column "Tag text" to "Tag text used in the skill".
- L-C. evaluation-scenarios.md:58 heading says "claims from the legacy checklist" and unverified-and-risks.md:34 says "was not read". Both are mild research-process wording. Use "unsupported claims" and "not covered".
- L-D. never-do-client-oauth.md:31-37 (§2 WRONG) and :103-108 (§5 WRONG) omit `allowed_oauth_flows_user_pool_client = true`, so each shows a second defect beyond the labeled one. Optional: add the flag so each WRONG block isolates one defect. Register ordering M1, M6, M2 (unverified-and-risks.md:34-36) is also out of sequence; cosmetic.

## Verdict

Ready: no HIGH or MEDIUM findings. The 4 LOW items are optional polish. Limit: live provider pages were not re-fetched in this round.
