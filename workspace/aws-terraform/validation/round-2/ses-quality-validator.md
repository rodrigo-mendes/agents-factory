# Quality validation round 2 — provisioning-aws-ses-v6

Skill: packages/aws-terraform/.apm/skills/provisioning-aws-ses-v6/. No WebFetch was available, so claims were checked against the research file and `_family_facts_v6.md` (F1–F19), not re-read from the live pages.
Counts: HIGH 0 · MEDIUM 1 · LOW 6. About 50 claims sampled, none of them re-checked from round 1; 0 wrong, 1 unsourced and untagged (MEDIUM), 5 imprecise or weakly grounded (LOW). Verdict: pass, with one MEDIUM residual.

## Structure
- SKILL.md has 161 lines. Frontmatter is name and description only, the description is under 300 characters and contains "Use when". Blueprints are at most 137 lines.
- All hub, Quick Navigation and Never-row anchors resolve. This covers `#4-custom-event-bus-in-event_bridge_destination`, `#5x--6x-migration-ses`, `#1-pinning-version-6570` and `#version-lifetime-risk`.
- No F/U/M/L/I ids leak outside `unverified-and-risks.md` (grep with that file excluded returned no matches).
- The sibling skills provisioning-aws-{sns,eventbridge,route53,iam}-v6 all exist.
- `aws_sesv2_account_vdm_options` appears only as a wrong name: evaluation-scenarios.md:62/65/70 and unverified-and-risks.md:43.
- No VDM or dedicated-IP-pool Always bullet remains. VDM and the pool are Ask First rows (SKILL.md:82, 84) plus blueprint sections that are labelled Ask First.

## Never rows (H1 re-count)
Never rows: SKILL.md:93–98 has 6, never-do-patterns.md:8–13 has 6, and the blueprints have 6 (never-do-ses-config §1–4, never-do-provider-migration §1–2). The counts are consistent and every row has a WRONG and a CORRECT block.

| # | Row | Grounding | Verdict |
|---|---|---|---|
| 1 | REJECT_MESSAGE without mail_from_domain | provider page [2], High | ✅ cell sourced |
| 2 | Several MX records on the MAIL FROM domain | AWS mail-from page quote [17] | ✅ cell "exactly one MX record" matches the AWS quote |
| 3 | Underscore-prefixed DKIM CNAME name | AWS creating-identities, correct/incorrect example [16] | ✅ |
| 4 | Custom bus in event_bridge_destination | provider page quote "Only the default bus is supported." | ✅ |
| 5 | Pin 6.57.0 | F4, High | ✅ cell `~> 6.69` or a non-withdrawn patch |
| 6 | dynamodb_table | F7, High | ✅ cell `use_lockfile = true` |

## Round-1 findings

| ID | Status | Evidence |
|---|---|---|
| H1 | FIXED | The key-length Never row is gone. SKILL.md:77 is now an Ask First row. It quotes the AWS sentence including "(unless it's the first downgrade to 1024 in that period)", cites the provider page and the AWS page, and the ask text carries the exception. never-do-ses-config.md has no key-length section; never-do-patterns.md has no key-length row; evaluation-scenarios.md Scenario 4 no longer mentions it. |
| M1 | FIXED | The list-vs-set indexing carries one (unverified) tag at each file's header: always-do-identity-dns.md:4 and never-do-ses-config.md:4. always-do-sending-config.md:9 covers `delivery_options[0]` at §4 (see N4), and the mapping row is U9. |
| M2 | FIXED | The "10,000 per Region" figure is gone. SKILL.md:109 now quotes only the separate-identity sentence. |
| M3 | PARTIALLY FIXED | The Always bullet at SKILL.md:61 now makes one claim. The `tls_policy = "REQUIRE"` mapping moved to Quick Reference SKILL.md:119, where it still shares one URL (the Security Hub page) with the severity claim. See N1. |
| M4 | FIXED | No VDM Always bullet. SKILL.md:84 is Ask First with U6, and the sending §7 text says Ask First. |
| M5 | FIXED | SKILL.md:141–142 are tagged (medium confidence, absence of evidence), M2. SKILL.md:143–144 are tagged (medium confidence) with a URL, M4. |
| M6 | FIXED | SKILL.md:17 gives 1.16.7 as 2026-10-22, matching F1. unverified-and-risks.md:7 gives the same date. |
| M7 | FIXED | Ask First rows 76–87 all have source links. The "whole account in a Region" wording is gone from row 84. |
| M8 | FIXED | always-do-identity-dns.md:82 states only the key format, with a source at :100. The "do not combine" claim is removed. |
| M9 | FIXED | always-do-sending-config.md:7–8 say only "checks that … tagged". The residual parameter claim is N2. |
| M10 | FIXED | No research-process wording remains in SKILL.md or the register. SKILL.md:86 "pages cited here" (U8) is evidence scope, not process, so it is acceptable. |
| M11 | FIXED | always-do-sending-config.md:117–119 now correctly says `domain` and `event_topic_arn` have example defaults and `dkim_private_key` and `sending_policy_json` do not. |
| L1 | FIXED | SKILL.md:22 and :145 cite the 6.0 guide and the provider releases page. |
| L2 | FIXED | There is no dedicated-IP-pool Always bullet. |
| L3 | FIXED | The Always bullets (SKILL.md:49–69) are clean one-claim lines. |
| L4 | FIXED | Quick Navigation SKILL.md:35 links the migration section. |
| L5 | FIXED | The mapping columns are Tag text used in the skill / Where / Register id, as the policy requires. |
| L6 | NOT FIXED | M1 (CHANGELOG 6.55.0) is still a register row with no tag in any skill text. The mapping row says "Registered only", which is an acknowledged orphan. Fix: delete M1, since M2 already covers the absence claim. |
| L7 | FIXED | "PENDING / creation return" is tagged (medium confidence), M5, at SKILL.md:79 and always-do-identity-dns.md:78. See N4 for the class concern. |
| L8 | FIXED | The sibling skills exist (see Structure). |
| L9 | FIXED | Scenario 3 now says "is not documented". |

## Tag-to-register consistency
- Every in-text tag has a mapping row: U1–U9, M2–M5. The mapping lists all of U1–U9. M1 is registered but never used (see L6).
- The U9 tags are at the blueprint headers (identity-dns, never-do-ses-config) and at sending §4. There is no uncovered `[0]` indexing, because the only other occurrence is the sending §8 test, which sending §4 line 9 names.
- M4: the 6.51.0 and 6.62.0 text at SKILL.md:143–144, the dates in L2/L3 (2026-06-17, 2026-08-26) and the research all agree.
- M5: the SKILL.md:79 and identity-dns:78 wording match the register, but the register describes something "not documented" (see N4).
- Register sections are Version-lifetime risk, Unverified, Medium, Coverage Limits, Tag to register mapping and Source Bibliography. No header counts are stated, so there is nothing to mismatch. The M rows are listed out of order (M1, M4, M5, M2, M3), which is cosmetic.

## New findings
- **N1 MEDIUM** (M3 residual). SKILL.md:119 puts "`tls_policy = "REQUIRE"`" in the SES.3 row with the Security Hub URL as its only source. The research gives this as a "Terraform lever" and the facts file does not cover it. It is neither sourced to the provider page nor tagged. Fix: cite the configuration set provider page for the `tls_policy` argument and keep only the Security Hub claim on the Security Hub URL.
- **N2 LOW.** always-do-sending-config.md:8 says the SES.2 control "has a required-tag-keys parameter". The research lists the parameter only for SES.1 (SES.1 row, `requiredTagKeys`). The same claim for SES.2 is unsupported. Fix: drop it or limit it to SES.1.
- **N3 LOW.** SKILL.md:78 says the identity page "exports `tokens` only". The page also exports `current_signing_key_length`, `status`, `signing_attributes_origin` and others. Fix: "exports no hosted-zone attribute".
- **N4 LOW.** M5 and U9 classification: the M5 register entry says whether creation returns before verification completes is "not documented". That reads as a U-class item, and U1 already covers part of it, so the policy's "no parallel class" rule is at risk. The U9 register text says "tagged once per blueprint header", but the sending-config tag is at §4, not the header. Fix: merge M5 into U1 or reword, and correct the U9 note.
- **N5 LOW.** always-do-sending-config.md:117 claims `mock_provider` with `command = plan` "runs without AWS credentials". Neither the research nor F10 states this. The cited mocking page was not re-read. Fix: tag it (medium confidence) or drop it.
- **N6 LOW.** SKILL.md:63 and :65 put an instruction and the Security Hub control claim in one bullet. SKILL.md:61 is a fact, not an instruction. This is acceptable for a single URL but is weaker than strict one-claim bullets.

## Grounding sample (about 50 claims, all supported unless listed above)
Version Context rows 17–23 (F1/F2/F3/F4/F5/F6/F18); Ask First rows 76–87 (AWS default 2048, BYODKIM quote, SigningHostedZone, 72 h, PENDING value, event destination types, scaling_mode values, required `default_subscription_status`, sandbox quote, `put-account-details`, USE_DEFAULT_VALUE / MailFromDomainNotVerified); Always bullets 49–69; Quick Reference 108–120 (key length values, MX 10 feedback-smtp, TXT SPF, `max_delivery_seconds` 300–50400, import IDs, SES.1/2 low, DMARC name and rollout); classic lines 127–129 (identity policy args, `UseDefaultValue`, 45 minute timeout); upgrade path 133–145 (F17/F18); identity-dns §1–3 (three CNAMEs, parent-domain rule, BYODKIM key format); sending §4–§7 (arguments, `matching_event_types`, import IDs); classic blueprint §9; register L2/L3 dates.

## Always Do bullets and v2/classic separation
- All 11 Always bullets are High-only and carry no tags. Each has one URL.
- v2 and classic are never mixed. SKILL.md:125 and classic blueprint :26 only contrast casing as a warning, and the families sit in separate sections and blueprints.

## Dates
- Shared-fact sources are dated 2026-10-23 (F19).
- The Terraform 1.17.0 CHANGELOG is 2026-10-22 at SKILL.md:9, :18 and in the register.
- 1.16.7 is 2026-10-22.
- 6.70.0 is 2026-10-21. 1.17.0 stable since 2026-10-21 matches F2. All consistent.
