# Quality validation round 1 — provisioning-aws-ses-v6

Written by the orchestrator from the validator's returned report (validator could not write files and had no WebFetch). Counts: HIGH 1 · MEDIUM 11 · LOW 9. 44 claims sampled. Verdict: pass with fixes.

Structure passes: frontmatter, 160-line SKILL.md, blueprints <= ~133 lines, all anchors resolve, no leaked F#/U# ids, classic family in its own section/blueprint, `aws_sesv2_account_vdm_options` appears only as a wrong name, upgrade path = F17, v7 = F18, Security Hub severities correct.

## HIGH
- H1 key-length Never row (SKILL.md:95, never-do-ses-config.md:67-87, never-do-patterns.md:11): AWS says changing the DKIM key length more than once in 24 h is not allowed "unless it's the first downgrade to 1024 in that period". The WRONG block (RSA_1024_BIT then RSA_2048_BIT) is exactly the exempted downgrade; Instead "at most once per day" drops the exception; CORRECT block is a static config; SKILL.md cites only the AWS page while "at most once per day" is from the provider page.

## MEDIUM
1 untagged list indexing `dkim_signing_attributes[0].tokens` (always-do-identity-dns.md:70, never-do-ses-config.md:52/:61), `delivery_options[0].tls_policy` (always-do-sending-config.md:126). 2 SKILL.md:109 "10,000 per Region (AWS page)" unconfirmed. 3 SKILL.md:58 SES.3 bullet two claims on one URL (tls_policy→SES.3 mapping). 4 SKILL.md:68 VDM Always bullet conflicts with U6/Ask First row. 5 CHANGELOG absence claims via summaries: tags too strong; 6.51.0/6.62.0 entries (SKILL.md:143) untagged. 6 1.16.7 date (F1 fixed). 7 Ask First rows without source links (SKILL.md:79,81,82,83,85); row 83 "whole account in a Region" unsourced. 8 BYODKIM "separate identity; do not combine with Easy DKIM block" (always-do-identity-dns.md:80) unsourced. 9 "tags satisfy SES.2" overclaim (always-do-sending-config.md:7). 10 research-process wording in register (lines 29, 38, 41). 11 "variables have example defaults" false (always-do-sending-config.md:115-116).

## LOW
1 v7 row/bullet citations; 2 "Attach a dedicated IP pool" is situational; 3 SKILL.md:48 parenthetical constraints unsourced; 4 Quick Navigation omits migration section; 5 mapping column names; 6 M1 orphan in register; 7 "creation can return with PENDING" untagged; 8 sibling skills sns/eventbridge existence (they exist); 9 Scenario 3 "does not exist" is stronger than the evidence ("not in the pages read").
