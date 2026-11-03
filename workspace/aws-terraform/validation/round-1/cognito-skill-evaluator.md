# Evaluation Report: provisioning-aws-cognito-v6 (round 1)

Method: no sub-agents. Each scenario was answered by me using only SKILL.md and its blueprints (always-do-pool, always-do-client-domain, never-do-pool-domain, never-do-client-oauth, unverified-and-risks), then judged. Evidence below is quoted from the skill content that the answer relies on.
Note: always-do-patterns.md and never-do-patterns.md exist in the folder but SKILL.md does not link them. They were not used.

## Scenario 1: Canonical (pool + web client + custom domain) - PASS (7/7, 3/3 OK)

Response summary: terraform block with `required_version = "~> 1.16"` and `version = "~> 6.69"`. Pool with `username_attributes = ["email"]`, `mfa_configuration = "OPTIONAL"` and `software_token_mfa_configuration { enabled = true }`. Client with the flag `true`, `allowed_oauth_flows = ["code"]` and https callback URLs. Domain `auth.example.org` with `certificate_arn = aws_acm_certificate_validation.cognito.certificate_arn`, created through a us-east-1 provider alias. Values marked `# example`.

must_pass:
- Version pins: PASS. always-do-pool §1 has `required_version = "~> 1.16"` and `version = "~> 6.69"`.
- username_attributes only: PASS. `username_attributes = ["email"]`, no alias_attributes.
- MFA method block: PASS. `software_token_mfa_configuration { enabled = true }`.
- OAuth flag plus code flow: PASS. always-do-client-domain §4 sets the flag `true` and `allowed_oauth_flows = ["code"]`.
- default_redirect_uri inside callback_urls, https: PASS. Both are `https://app.example.org/callback`.
- ISSUED ACM cert in us-east-1: PASS. always-do-client-domain §5: "ISSUED ACM certificate in us-east-1".
- Marks examples: PASS. The `# example` comments and the header "All names, ARNs and URLs are examples".

must_not: no other-Region cert OK; no 6.57.0 OK; no username_attributes plus alias_attributes OK.

## Scenario 2: Edge (drop SMS, change sign-in) - PASS (5/5, 2/2 OK)

Response summary: No, not in place. Quote the provider page: "the SMS configuration cannot be removed without recreating the Cognito User Pool." The page says to use `taint` to force recreation. For sign-in, quote AWS: "After you create a user pool, you can't change this setting." Whether the provider forces replacement is not stated on its page (unverified), so I do not claim it either way. Then ask: "Email, phone, or alias sign-in - confirmed final for this pool?", and confirm recreation is acceptable before proceeding.

must_pass:
- SMS warning: PASS (SKILL Never Do row 2; never-do-pool-domain §2).
- taint: PASS ("Plan to recreate the pool; the page says to use `taint`").
- AWS sign-in quote: PASS (Ask First, Sign-in identifiers).
- Does not claim provider replacement behaviour, or tags it (unverified): PASS (SKILL Ask First; register U1).
- Asks before proceeding: PASS (Ask First row).

must_not: no in-place promise OK; no "documented" replacement claim OK.

Observations (not failures):
- The skill gives no guidance on how to migrate users when changing sign-in. It only says to recreate the pool. That is acceptable under the criteria.
- `terraform taint` is the page's wording. The skill does not mention `-replace`. I did not add it, because it is outside the skill's sources.

## Scenario 3: Misuse rejection (legacy checklist claims) - PASS (4/4, 3/3 OK)

Response summary: all three claims are false. (1) Both `user_pool_tier` and `user_pool_add_ons.advanced_security_mode` are documented on the provider page; do not remove `user_pool_add_ons`. (2) Threat protection, including adaptive authentication, is a Plus-plan feature, not ESSENTIALS. (3) Cognito resources document the optional `region` argument (regional); changing it forces replacement.

must_pass:
- Both arguments documented: PASS. Ask First: "`advanced_security_mode` ... is still documented"; user_pool_tier is `LITE`, `ESSENTIALS` or `PLUS`. unverified-and-risks: "`user_pool_tier` does not replace `user_pool_add_ons.advanced_security_mode` (both documented)".
- Threat protection is Plus-only: PASS. Ask First: "threat protection is a Plus-plan feature". unverified-and-risks: "threat protection including adaptive authentication is Plus-only".
- Region argument: PASS (SKILL Version Context; always-do-pool §1).
- Does not reproduce the claims: PASS.

must_not: all OK.

Criterion note (low): the phrase "including adaptive authentication" appears only in unverified-and-risks.md "Superseded claims". SKILL.md itself says only "threat protection is a Plus-plan feature". The answer is still derivable, but the SKILL.md body does not explicitly name adaptive authentication. Optional fix: add three words to the Ask First tier row.

## Scenario 4: Anti-pattern trap (broken client) - PASS (5/5, 2/2 OK)

Response summary: not fine. Four problems:
1. `client_credentials` must be the only flow. It is mixed with `code` (AWS CreateUserPoolClient).
2. Legacy `USER_PASSWORD_AUTH` cannot be combined with `ALLOW_*` (AWS CreateUserPoolClient). Use `ALLOW_*` only.
3. `http://app.example.org/cb` is not localhost. HTTPS is required (AWS CreateUserPoolClient). Use an https URL.
4. `allowed_oauth_flows_user_pool_client = true` must be set before `allowed_oauth_flows` (provider cognito_user_pool_client page).
Also noted: `client_credentials` needs `generate_secret = true`. The answer cites provider and AWS URLs only.

must_pass: all 5 PASS. Sources are in never-do-client-oauth §1, §3, §4 and §5, and in the SKILL Never Do table.
must_not: no problem accepted; no research ids or workspace paths cited. OK.

Risk (low): the register ids U1..U9 and M1..M5 exist in unverified-and-risks.md. A response could leak them, which would violate the second must_not. Those ids are internal to the skill, not workspace paths, but the criterion is a little ambiguous. This run did not leak them.

## Pass rates

| Scenario | must_pass | must_not OK | Verdict |
|---|---|---|---|
| 1 Canonical | 7/7 | 3/3 | PASS |
| 2 Edge | 5/5 | 2/2 | PASS |
| 3 Misuse rejection | 4/4 | 3/3 | PASS |
| 4 Anti-pattern | 5/5 | 2/2 | PASS |

Overall: 4/4 scenarios PASS. 21/21 must_pass and 10/10 must_not.
Caveat: I authored and judged the answers myself, so the run is self-graded. There was no independent execution.

## Fixes needed (all minor, none blocking)

1. SKILL.md Ask First "Plan tier and threat protection" row: add "including adaptive authentication" to the Plus-plan statement. Scenario 3 criterion 2 currently relies on unverified-and-risks.md.
2. Folder hygiene: always-do-patterns.md and never-do-patterns.md are not linked from SKILL.md. Link them or delete them. If they are stale, they may contradict the linked blueprints.
3. Scenario 4 must_not "Cite research ids or workspace paths": clarify that the U/M register ids count as research ids. Optionally rephrase the unverified-and-risks.md ids so they are clearly internal.
4. Optional: scenario 2 criterion 4 could be worded "does not state as fact whether the provider forces replacement". Its current "or tags that point (unverified)" wording is ambiguous.
