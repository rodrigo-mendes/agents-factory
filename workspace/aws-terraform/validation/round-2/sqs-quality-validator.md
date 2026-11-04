# Quality validation, round 2: provisioning-aws-sqs-v6

Target: `packages/aws-terraform/.apm/skills/provisioning-aws-sqs-v6/` (SKILL.md 141 lines, 9 blueprints).
Method: full read of skill, research, facts, round-1 report and the tag policy. WebFetch is not available in this run, so claims were checked against the research file's recorded page reading, not a fresh fetch.

Totals: HIGH 0, MEDIUM 3, LOW 6.

## Round-1 items

| Id | Status | Evidence |
|---|---|---|
| H1 | FIXED (residual LOW-1) | SKILL.md:90 now reads "without a restricting condition" and cites best-practices page plus SQS.3. The page text ("avoid public queues", `Principal` `*`) and SQS.3 (public access, fixed-value conditions only; always-do-policies.md:39-41) are documented, so the row is a documented fact, not a free derived rule. Only the phrase "restricting condition" is the skill's own bridge. never-do-policies-access.md:43-45 states the WRONG example has no condition. |
| M1 | FIXED | "Not deprecated" is gone from Always Do (SKILL.md:57 now cites the page's recommendation). Residual: evaluation-scenarios.md:69 still asserts "does not mark the inline argument deprecated" untagged (LOW-5). |
| M2 | FIXED (residual LOW-2) | 12 bullets (SKILL.md:47-69), each with one inline URL, no tags, no parenthetical caveats. |
| M3 | FIXED | never-do-queue-config.md:11-19 uses inline `redrive_policy` on `aws_sqs_queue`, matching the cited queue page. |
| M4 | FIXED | never-do-queue-config.md:91-98 defines a separate `src_good` without inline policy. |
| M5 | NOT FIXED (partly) | U2 and U4 are still rows with no tag in the skill (unverified-and-risks.md:20,22,42). The register itself says "not stated anywhere in this skill". That is an orphan row by the stated criterion. Other tags map cleanly (rows 46-54); L2 header fixed. See MED-1. |
| M6 | NOT FIXED (partly) | Quick Reference Import row now cites four pages (SKILL.md:112). But Always Do bullet 12 (SKILL.md:69, "all four resources") cites only the queue page, and always-do-dlq.md:70-71 cites only the queue and queue_policy pages for the redrive identity attributes. See MED-2. |
| M7 | FIXED | always-do-dlq.md:13-14 cites the SSE and key-management pages inline. |
| M8 | NOT FIXED (partly) | "fails init" is removed (SKILL.md:25 now only says never pin). The upgrade path sentence (SKILL.md:127) is now attached to the upgrade-guide URL, but the research says the guide has no SQS content and records no sentence about "latest 5.x first". See MED-3. |
| M9 | FIXED | SKILL.md:61 and always-do-policies.md:76 scope to SSE-KMS. |
| L1 | FIXED | "medium severity" lowercase with "severity" (SKILL.md:49, 114); no bare "Medium". |
| L2 | FIXED | Header is `Tag text used in the skill` (unverified-and-risks.md:44). |
| L3 | FIXED | SKILL.md:104 cites the version-constraints page (supported by family fact F6). |
| L4 | PARTLY FIXED | max_message_size row now cites the AWS API page (SKILL.md:78). The DLQ row (SKILL.md:82) still cites only the DLQ page for "API default 10" and "console range 1-1,000" (research sources: SetQueueAttributes and configure-DLQ page). See LOW-3. |
| L5 | FIXED | always-do-queues.md:61 cites the SSE page. |
| L6 | FIXED | SKILL.md:55 and 89 say "without explicit Version"; no "another value". |
| L7 | FIXED | SKILL.md:26 cites the upgrade guide ("removed in v7.0.0"). |
| L8 | FIXED | Never table order equals hub order (see below). |

## Explicit checks

1. Never rows equal blueprint WRONG entries one-to-one: SKILL.md rows 89-96 = 8; never-do-patterns.md index lines 9-16 = 8; blueprint sections 1-8 (policies-access 1-3, queue-config 4-8) = 8. 8=8=8, same order, each anchor resolves. H1 row: High (documented).
2. `redrivePermission`: the HCL (always-do-dlq.md:41-44) uses only `byQueue` and `sourceQueueArns`, sourced to the provider page (line 48). `allowAll` and `denyAll` appear only in SKILL.md:82, 115 and always-do-dlq.md:53-55, all cited to the AWS DLQ page. PASS. No other value is attributed to the provider page.
3. Always Do: 12 bullets, one claim each (minor bundles in LOW-2), inline URL each. Tags and register consistent except U2/U4 orphans. No F#, M#, workspace or absolute paths in shipped text (grep: only "Version-lifetime" and the eval prompt word "deprecated" matched). Plain notation. Example markers present on ARNs, names, URLs, variable defaults and sizes.

## MEDIUM

MED-1. Orphan register rows U2 and U4 (unverified-and-risks.md:20,22,42). Remove them, or add a tagged mention in the skill (for example a `fifo_queue` replacement note) and a mapping row.

MED-2. Import "all four resources" is sourced to one page (SKILL.md:69; always-do-dlq.md:59-61,70-71). Add the redrive_policy and redrive_allow_policy page URLs to the bullet or the §8 Source lines. The two pages are also absent from SKILL.md External Resources (bibliography has them).

MED-3. Upgrade path (SKILL.md:127) has no research basis. The research records only that the guide lacks SQS entries. Either tag it (unverified) with a register row, or delete it, or add the exact guide sentence.

## LOW

LOW-1. H1 residual: "restricting condition" is the skill's wording; the pages say avoid public queues. Consider quoting the page sentence in never-do-policies-access.md:43.
LOW-2. Bullets 2 and 3 pair the control with a severity (two claims); bullet 8 gives two claims (CMK plus the two KMS actions); bullet 9 gives DLQ placement and no-auto-create. Bullet 1 cites the version-constraints page for specific values `~> 1.16` and `~> 6.69`, which are family decisions (F1, F3), not page text; that page was fetched 2026-10-14, not 2026-10-23 as the skill states.
LOW-3. SKILL.md:82 DLQ row citation mismatch (see L4).
LOW-4. SKILL.md:123 (6.42.0 list resource) sits under a heading citing the upgrade guide, but the fact comes from the CHANGELOG.
LOW-5. evaluation-scenarios.md:69 absence claim ("does not mark deprecated") untagged.
LOW-6. SKILL.md:125 states the 6.55.0 coverage gap (L1) with no tag or pointer to the register row.

## Fresh grounding sample (28 claims, not in round 1)

Pass (24): SSE encrypts body only; default_tags override and tags_all; standard queue back-of-queue rule (maxReceiveCount > 3); FIFO resets timestamp; "no DLQ with FIFO if order must hold"; SNS auto-confirm same account; AWS managed key and cross-account Lambda, HTTPS plus SigV4; aws:SourceArn or SourceAccount in key policies; best-practices TLS, least privilege, VPC endpoints; SQS.3 critical; SQS.2 requiredTagKeys; queue_policy required args and no exports; `id` is the queue URL; import block needs 1.5; S3 example on queue_policy page; kms_master_key_id options; KMS reuse cost; producer and consumer KMS actions; 6.0 guide silent on SQS; 6.53.0 regression fix; Terraform 1.16.6 (2026-10-14) and 1.17.0 (2026-10-21); 6.57.0 withdrawn; region replacement and `id@region`; 6.70.0 date.
Flagged (4): upgrade path (MED-3); import four-resource sourcing (MED-2); DLQ row citation (LOW-3); 6.42.0 citation (LOW-4).
Wrong claims: none.
