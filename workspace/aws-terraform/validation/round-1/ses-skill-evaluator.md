# Evaluation Report: provisioning-aws-ses-v6 (round 1)

Method: self-simulated responses using only SKILL.md and its blueprints (no sub-agents, per instruction). Skill read from packages/aws-terraform/.apm/skills/provisioning-aws-ses-v6/. 5 scenarios in blueprints/evaluation-scenarios.md (the C1 minimum of 3 is met).

## Summary

| Scenario | must_pass | must_not OK | Verdict |
|---|---|---|---|
| 1 Canonical (domain identity, config set, SNS events) | 6/6 | 3/3 | PASS |
| 2 Edge (multi-Region, sandbox) | 4/4 | 2/2 | PASS |
| 3 Misuse (vdm_options, sandbox exit) | 3/3 | 3/3 | PASS |
| 4 Anti-pattern trap (5 items) | 5/5 | 2/2 | PASS |
| 5 Family mixing | 2/2 | 2/2 | PASS |

Overall: 5/5 scenarios PASS. must_pass 20/20, must_not 12/12.

Family separation: held in every answer. v2 uses `aws_sesv2_*` with `USE_DEFAULT_VALUE` / `REJECT_MESSAGE`. Classic `aws_ses_*` is confined to the Classic section, where `UseDefaultValue` belongs to `aws_ses_domain_mail_from`.

## Scenario 1 - PASS

Response, built from identity-dns §1-3 and sending §4-5:
- Terraform block with `required_version = "~> 1.16"`, `aws ~> 6.69`, S3 backend with `use_lockfile = true`.
- Resources: `aws_sesv2_email_identity` (Easy DKIM `RSA_2048_BIT`), `aws_sesv2_email_identity_mail_from_attributes` (`mail_from_domain = "mail.${var.domain}"`, `USE_DEFAULT_VALUE`), `aws_sesv2_configuration_set` (`delivery_options { tls_policy = "REQUIRE" }`, `tags`), `aws_sesv2_configuration_set_event_destination` (`enabled = true`, `matching_event_types = ["BOUNCE","COMPLAINT"]`, `sns_destination`).
- Output `"${t}._domainkey.${var.domain}"`, with a note that the CNAME value suffix is "(unverified)" and that I'd ask how it is produced.
- Example values are marked `# example`.

must_pass evidence:
1. PASS. SKILL.md Always Do and identity-dns §1 give the exact strings.
2. PASS. All four resources are in identity-dns §2-3 and sending §5.
3. PASS. sending §4 shows `tls_policy = "REQUIRE"` and `tags`.
4. PASS. sending §5 shows `enabled = true`.
5. PASS. identity-dns §2: "AWS form: <token>._domainkey.<domain>".
6. PASS. Identity-dns §2 comment: "how to obtain that suffix in HCL is (unverified)". Ask First has a DKIM CNAME row.

must_not: all OK.
- No `aws_ses_*` arguments appear in the v2 resources.
- The backend uses `use_lockfile`; `dynamodb_table` is not used.
- No `dkim.amazonses.com` suffix is stated as fact. Ask First rates it "likely outdated (medium confidence)".

Note: the sending §4 example sets `sending_pool_name` to a dedicated pool. A faithful answer must either drop that line or include the pool resource. The canonical snippet therefore isn't copy-pasteable as a fragment without the §6 pool. This is a minor skill ergonomics point, not a failure.

## Scenario 2 - PASS

Response:
- Create and verify a separate identity per Region (eu-west-1, us-east-1). Use the optional `region` argument (default = provider Region; changing it forces replacement) or one provider configuration per Region.
- The sandbox "is unique per each AWS Region".
- AWS documents the console and `aws sesv2 put-account-details` for production access.
- Whether a Terraform resource for production access exists is (unverified). I'd ask: "Is production access already granted in each target Region?"

must_pass:
1. PASS. Always Do ("separate identity in every Region"), identity-dns §2, and the Version Context row on `region`.
2. PASS. Ask First, "Sandbox and production access" row.
3. PASS. Same row.
4. PASS. Same row, plus register U7.

must_not: OK. I did not say Terraform cannot request production access. I did not say one identity covers all Regions.

Criterion note (minor): "provider or region argument per Region" mentions a provider-alias route. The skill documents only the `region` argument (Version Context / enhanced-region-support). The alias route is general Terraform knowledge, not skill content. The criterion is satisfiable via `region` alone, so I rate it "slightly over-specified", not a bug.

## Scenario 3 - PASS

Response:
- Corrects the name. `aws_sesv2_account_vdm_options` does not exist; the resource is `aws_sesv2_account_vdm_attributes` with `vdm_enabled = "ENABLED"` (sending §7; the unverified-and-risks Coverage Limits row says the name does not exist).
- Production access: no resource or argument is invented. Point to the console or `aws sesv2 put-account-details` ([source](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html)). Whether the provider has a resource is (unverified).
- Ask: "Is this account-wide setting owned by this configuration, and what should destroy do?" Destroy behaviour is (unverified).

must_pass 3/3. must_not 3/3 OK. The `aws_sesv2_account_vdm_options` name is mentioned only as a rejected example, which is allowed. I did not say flatly that Terraform cannot do it.

Criterion note: must_pass #2 and must_not #3 are consistent with each other. Both rely on the single U7 source, SKILL.md Ask First. No criterion bug.

## Scenario 4 - PASS

Response, five rejections, each with its source:
1. `REJECT_MESSAGE` without `mail_from_domain`: the sesv2_email_identity_mail_from_attributes page requires it. Fix: set `mail_from_domain`.
2. Two MX records: mail-from.html says "the custom MAIL FROM setup with Amazon SES will fail". Fix: exactly one `MX 10 feedback-smtp.<region>.amazonses.com`.
3. `_<token>._domainkey`: creating-identities.html labels the leading underscore incorrect. Fix: `<token>._domainkey.<domain>`.
4. Custom event bus: "Only the default bus is supported" (event destination page). Fix: the default bus ARN.
5. Pin 6.57.0: withdrawn (provider CHANGELOG). Fix: `~> 6.69`.

All five come from SKILL.md Never Do and never-do-ses-config / never-do-provider-migration. must_pass 5/5. must_not OK: nothing accepted, and every rejection is cited.

Criterion note: must_not #1 ("Accept any of the five items") restates must_pass. It is redundant but harmless.

## Scenario 5 - PASS

Response:
- Use `behavior_on_mx_failure = "USE_DEFAULT_VALUE"` on the v2 resource. `UseDefaultValue` is the classic casing of `aws_ses_domain_mail_from`, so it is not copied (SKILL.md Classic section; classic blueprint §9).
- Managing the same identity with `aws_ses_domain_identity` and `aws_sesv2_*` together is (unverified): no provider page documents conflicts (U3). I'd ask first: "Is the identity already managed with `aws_ses_*`? Keep one family per identity?"
- I state neither "they conflict" nor "they are safe together".

must_pass 2/2. must_not 2/2 OK.

Criterion/skill tension to watch (not a failure): the register U3 and unverified-and-risks say "keep one family per identity unless confirmed". Phrased as a prudent default, it is not a factual claim of conflict. Its wording is close to the must_not line, so a judge could read it strictly. Suggest rewording to "unconfirmed; ask" if a stricter judge is used.

## Criteria flagged

No unsourced or unsatisfiable criteria found. Every criterion maps to explicit SKILL.md or blueprint text. Two soft points: the provider-alias mention in S2 must_pass #1, and the redundant must_not in S4.

## Fixes needed (short)

Nothing blocking. Optional:
1. always-do-sending-config.md §4: make the `sending_pool_name` line optional or comment it, so the canonical configuration set stands alone without the §6 pool.
2. evaluation-scenarios.md S2: drop "provider or" from the first must_pass, or add provider-alias guidance to the skill. The skill does not currently say it.
3. unverified-and-risks.md U3 and the SKILL.md Ask First row: soften "keep one family per identity" to "unconfirmed; ask", to avoid brushing against S5 must_not.
4. evaluation-scenarios.md S4: delete the redundant must_not "Accept any of the five items".

Limitation: responses were self-simulated by the evaluator, not produced by an independent sub-agent. They are therefore optimistic about the skill, and the pass rate should be confirmed with a fresh-context run.
