# Quality validation, round 1: provisioning-aws-cognito-v6

Validated 2026-10-23 against the research file, family facts (F1-F19), the three policy files and the frontmatter rule.
Method note: WebFetch was NOT available in this environment. The requested spot-check of the live `cognito_user_pool` and `cognito_user_pool_client` pages was NOT done. Every provider-page claim below was compared with the research file's record of those pages, not with the live pages.
Sample: 41 claims (13 Always Do, 10 Never Do rows, 10 Ask First rows, Quick Reference rows, HCL comments).

Counts: HIGH 1, MEDIUM 6, LOW 8.

## Structure checks (pass)

- Frontmatter has only name and description. The description is quoted, 280 characters or fewer, and contains "Use when". The name matches the folder.
- SKILL.md is 163 lines. All blueprints are under 160 lines.
- Never Do has 10 rows in SKILL.md. The index has 10 rows and the two blueprints have 5+5 sections. They match one to one, in the same order and wording.
- Always Do has 13 bullets. None has a tag. Each has one inline URL.
- No F#/M#/U# ids appear in shipped text, except the register's own ids. No workspace paths appear.
- Tag text is plain parenthetical notation. Register ids are consistent: U1, U4, U5, U8 and U9 are in Ask First; U2, U3, U6 and U7 are registered only; M1-M5 are all mapped, including M5 (`always-do-client-domain.md:40`) and no orphans.
- Dates: shared-fact sources are dated 2026-10-23. The Terraform 1.17.0 CHANGELOG is dated 2026-10-22 (`unverified-and-risks.md:3`). The skill says 1.16.7 is 2026-10-22 (`SKILL.md:16`, `unverified-and-risks.md:10`).
- Legacy claims are not reproduced. `user_pool_tier` does not replace `advanced_security_mode`. Threat protection is Plus only. Cognito is regional. Token revocation is on by default for new clients. Custom domain propagation is about 60 s with Route 53 and up to 1 h for a certificate change. No stale version pins.
- U1: the AWS sentence is attributed to the AWS page (`SKILL.md:88`). The provider's silence on forced replacement is tagged (unverified).
- Upgrade path matches F17 (`SKILL.md:150-152`). The v7 note matches F18 (`SKILL.md:153`). The 6.0 change is only the `aws_cognito_user_in_group` import ID (`SKILL.md:148`).

## HIGH

H1. `blueprints/never-do-client-oauth.md:36-46` (§2) and `:101-113` (§5). CORRECT and WRONG blocks set `callback_urls` and `default_redirect_uri` without `allowed_oauth_flows_user_pool_client = true`.
- The skill's own Always Do bullet (`SKILL.md:67`) and the provider page require the flag before `callback_urls`/`logout_urls`.
- The labeled CORRECT examples in §2 and §5 therefore break a documented requirement. Agents will copy them.
- The same blueprint's §1, §3 and §4 and `always-do-client-domain.md` §4 do set the flag.
- Fix: add `allowed_oauth_flows_user_pool_client = true` to the CORRECT blocks (and ideally the WRONG blocks, so each shows only its one defect).

## MEDIUM

M-1. `never-do-pool-domain.md:41-42`. The CORRECT block gives an exact command line, `terraform taint aws_cognito_user_pool.main   # then remove the block and apply`.
- The provider page only says to use `taint` (research §3). The command line and the "then remove the block and apply" sequence are not sourced or tagged.
- Terraform's own docs deprecate `taint` in favor of `apply -replace`, so this is also an overstatement where another official source offers an alternative.
- Fix: state only "the page says to use `taint` to force recreation", or cite the Terraform CLI page for the exact command. Likewise reword the `# WRONG to remove later` comment at line 34.

M-2. `SKILL.md:43-45`, Always Do bullet 1. It states two claims (`~> 1.16` and `~> 6.69`).
- The cited version-constraints page supports only the root-module `~>` convention.
- The values 1.16 and 6.69 come from the releases pages and a user decision, and the bullet does not cite them.
- Fix: cite the releases pages for the values, or limit the bullet to the one-claim `~>` rule. Same pattern at `SKILL.md:8`.

M-3. `SKILL.md:64-66`, Always Do bullet 8. "Set `deletion_protection = "ACTIVE"` on user pools" is a posture recommendation, not a statement on the cited provider page.
- Provider-page facts are only that the values are ACTIVE|INACTIVE and that the pool must be deactivated before deletion.
- The ACTIVE recommendation comes from Security Hub Cognito.6, which is not cited.
- There are two claims in one bullet.
- Fix: split the claim, or cite the Security Hub page for the recommendation.

M-4. `SKILL.md:87-96` Ask First rows with no inline URL for factual claims. Affected rows:
- MFA mode: `OFF` default, Cognito.5 scope.
- Email sender: `COGNITO_DEFAULT`/`DEVELOPER`.
- Lambda triggers: `lambda_config`.
- Token revocation: "AWS activates revocation by default on new clients". This one is the AWS claim, with no URL. Only the provider default carries the tag.
- Identity pool guests: Cognito.2.
- Fix: add the provider, AWS or Security Hub URL to each row.

M-5. `always-do-pool.md:28` versus the example at `:48-57`.
- The text says "`email_mfa_configuration` needs at least two `account_recovery_setting` entries". The example has one `account_recovery_setting` block containing two `recovery_mechanism` blocks.
- The wording and the example disagree. I could not check which matches the live page because WebFetch was unavailable. Hub bullet 5 (`SKILL.md:55`) repeats the same wording.
- Fix: verify against the live page and make the wording and example agree, naming `recovery_mechanism` if that is what the page means.

M-6. `always-do-client-domain.md:39`. "Provision the certificate through a `us-east-1` provider alias" is untagged and sourced only to ACM/other-skill text.
- Only the `region =` alternative carries a tag (M5). The alias route is itself the research's unconfirmed route for CloudFront-scoped resources (F16 text).
- Fix: cite the provider page, or tag it.

## LOW

- L-1. `SKILL.md:87`, "Pricing not researched", `unverified-and-risks.md:34` (M1, "read across a read boundary") and `:49` ("Superseded claims deliberately not reproduced") are research-process wording in shipped text. Use neutral coverage-limit phrasing.
- L-2. `SKILL.md:108`, Never Do row 7. "Use `ALLOW_*` values only" is narrower than the AWS source, which only forbids mixing. An all-legacy set is also valid. State it as the recommended choice.
- L-3. `SKILL.md:111`, Never Do row 10. "or any non-withdrawn patch" is not sourced. The `~> 6.69` part is sound.
- L-4. `SKILL.md:24` (Terraform 1.17.0 stable) and `:153` ("no 7.x release exists") have no inline URL in the bullet. The sources are on the releases page and in the risks file.
- L-5. `SKILL.md:96` uses the variant tag "(unverified here)". Normalize to the registered tag text "(unverified)".
- L-6. `SKILL.md:93` (M3). The provider default is "unknown" but tagged `(medium confidence)`. Policy says an absence-based claim should be `(medium confidence, absence of evidence)`.
- L-7. `unverified-and-risks.md:54-56`. The heading is "Tag to Register Mapping" where policy says "Tag to register mapping". The column header is "Tag text" where policy says "Tag text used in the skill". Verify against `verify_skill.py`.
- L-8. `SKILL.md:46-48`, Always Do bullet 2. It cites the enhanced-region guide for "Cognito resources are regional". The resource pages document the `region` argument. The "nearest section" link (pool §1) is not misleading. Bullet 13's link (domain §5) is accurate.

Note outside this unit: `_family_facts_v6.md` F1 gives the 1.16.7 release as 2026-10-23, and gives 1.16.6 as 2026-10-23 too. The skill and the caller use 2026-10-22 for 1.16.7. The family facts should reconcile this.

## Never Do rows, per-row verdict

1. `username_attributes` with `alias_attributes`: pass.
2. Removing `sms_configuration`: the quote is faithful. The `terraform taint ...` line is an invention (M-1).
3. ON/OPTIONAL MFA with no method block: pass.
4. Certificate outside us-east-1: pass. The AWS page is cited. The Instead cell is backed by the provider page.
5. `allowed_oauth_flows` without the flag: row pass. Blueprint examples fail (H1).
6. `default_redirect_uri` missing from `callback_urls`: row pass. The CORRECT block fails (H1).
7. Legacy auth-flow values mixed with `ALLOW_*`: pass (L-2 on the Instead wording).
8. `client_credentials` mixed with other flows: pass.
9. Non-localhost `http://` callbacks: row pass. The CORRECT block fails (H1).
10. Pinning 6.57.0: pass (L-3).
