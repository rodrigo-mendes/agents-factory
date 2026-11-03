# Quality validation, provisioning-aws-sns-v6 (round 2)

Date: 2026-10-23. Skill: packages/aws-terraform/.apm/skills/provisioning-aws-sns-v6/ (9 files read in full).
WebFetch was not available in this run. Grounding was done against the research file and the family facts file. No page was re-fetched.
Not reported (known decisions): the `-v6` suffix and page-from-`main` confidence.

Counts: HIGH 0, MEDIUM 1, LOW 8.

## Round-1 findings (SKILL = SKILL.md, line numbers from this run)

| Id | Status | Evidence |
|---|---|---|
| H1 | FIXED | SKILL:110 Never row: "Destroy a topic whose `archive_policy` is active, it cannot be deleted" with Instead "Deactivate the archive policy first, as AWS instructs". The research (section 3, archive) states both facts: an active policy blocks deletion and `{}` disables it. The `jsonencode({})` step is now Ask First (SKILL:97), tagged (unverified), mapped to U6 (unverified-and-risks:23, 48), and warns "deletes the archive". The AWS part of that row (`{}` deletes the archive) is documented; only Terraform's handling is untagged-free (it carries the tag). never-do-access-kms:76-91 WRONG/CORRECT match the row and are documented facts. See L-g for a small residue. |
| M1 | FIXED | SKILL:56 and always-do-topic:23 now quote only the control title. The "passes with any key" clause is gone. |
| M2 | FIXED | SKILL:111 cites both the topic page and fifo-message-delivery, as the blueprint does. |
| M3 | FIXED | SKILL:122-124 and always-do-topic:14-15 cite the releases pages for 6.69/1.16 and the constraints page for `~>`. Bullet 1 (SKILL:46-49) now has URLs. |
| M4 | FIXED | always-do-topic:75-76, 94 and 99-100 mark the key policy as a fragment and say not to attach it alone. It is not misleading. One unsourced clause remains, see N1. |
| M5 | FIXED | always-do-access-delivery:58-59, 77 and 86 mark the SQS/DLQ and cross-account HCL as fragments with pointers to provisioning-aws-sqs-v6. Not misleading. |
| M6 | FIXED | SKILL:139-149 now says only what the guide states, plus "this skill adds no SNS-specific migration step". The unsourced 5.x steps were removed. |
| M7 | FIXED | Text tags: the inline-policy row is (unverified) = U4; the SourceArn row is (unverified) = U5; AuthenticateOnUnsubscribe is (medium confidence, absence of evidence) = M1. The classes now match the evidence table. |
| M8 | FIXED | Old U4 (SNS.2) and old M3 are deleted. SNS.2 grep across the skill returns nothing. |
| L1 | NOT FIXED | See L-a. |
| L2 | PARTIAL | The IAM-role caveat is in the bullet (SKILL:60-62) but that is a caveat inside an Always Do bullet. The `*` principal in the Deny example is still unexplained (L-b). |
| L3 | PARTIAL | The aliases now use `queue_account_topic_region`, and the Firehose/IAM resources are marked placeholder. SQS and topic resources in never-do-subscriptions are still undefined (L-d). |
| L4 | FIXED | SKILL:128 and 130 cite the topic page. |
| L5 | NOT FIXED | See L-c. |
| L6 | FIXED | always-do-topic:57 has `# example`. |
| L7 | FIXED | always-do-access-delivery:51-52 says "for the DLQ". |
| L8 | FIXED | always-do-topic:43-44 has a full URL. |
| L9 | NOT FIXED | See L-e. It is cosmetic. |

### Register consistency (M7 detail)
- Register ids: U1-U6, M1, L1-L3 (unverified-and-risks:16-37). Mapping rows U1-U6 and M1 (lines 43-49).
- Every tag in SKILL.md and the blueprints has a mapping row, and every mapping row has a tag in the shipped text: U1 SKILL:95, U2 SKILL:94, U3 access-delivery:108, U4 SKILL:93, U5 SKILL:98, U6 SKILL:97, M1 SKILL:99. No orphan rows. L1-L3 are untagged coverage limits (allowed).
- Section headers carry no counts, so there is nothing to drift.
- Tags use plain notation. No F#, G# or M# internal ids, no `workspace`, no `research_`, no absolute paths (grep: no matches).

### Never row count
SKILL.md Never table: 8 rows (lines 107-114). never-do-patterns.md: 8 entries. Blueprints: 4 sections in never-do-access-kms plus 4 in never-do-subscriptions, which is 8. Count: 8 = 8 = 8, in the same order. Anchors resolve. The alternative on each row is High.

## Findings

### HIGH
None.

### MEDIUM
N1. Unsourced, untagged claim in the key-policy fragment.
- Where: always-do-topic:75-76. The comment says the full key policy must keep the key-administration statements "otherwise it replaces them".
- It is plausible KMS behavior, but no fetched page states it, and it carries no tag.
- Fix: delete "otherwise it replaces them" and keep "do not attach this fragment alone". Or tag it (unverified) and add a register row.

### LOW
- L-a. Always Do bullets are not strictly one claim with one URL (carry-over of round-1 L1).
  - Bullet 1 (SKILL:46-49) has three URLs and two claims.
  - The CMK bullet (SKILL:60-62) has several claims and a caveat ("some event sources need an IAM role instead"). The policy says to move that caveat to Ask First.
  - The non-public bullet (SKILL:66-68) has two URLs.
  - The DLQ bullet (SKILL:71-73) has two claims.
- L-b. The Deny example uses `principals { type = "*" ... }` (access-delivery:28-31), while the bullet and section say to avoid a `*` principal. The research gives no page statement about a Deny with a `*` principal. Add a one-line note, or mark it `# example`.
- L-c. The register mapping columns are "Tag text, Where, Register id". The policy wants "Tag text used in the skill". The section is named "Tag to Register Mapping" where the policy has "Tag to register mapping".
- L-d. Never-do-subscriptions HCL uses `aws_sns_topic.orders_fifo`, `aws_sqs_queue.orders_fifo` and `aws_sqs_queue.orders` with no placeholder marker. never-do-access-kms:43 uses `aws_kms_key.sns` the same way. Add `# placeholder: defined elsewhere`.
- L-e. The heading "Medium-Confidence Items" and the text "SNS.1 (severity Medium)" use "medium" for both confidence and severity. The notation rule restricts only headings, and the policy names the section "medium", so this is cosmetic.
- L-f. The SKILL.md:8 version lock says "reference patch 6.69.0/6.70.0". Two patches are ambiguous. The facts file says latest 6.70.0, with 6.69.0 as the earlier reference. Pick one wording.
- L-g. The Never row 4 alternative (SKILL:110) points to the Ask First row, and the "archive is deleted" warning is only there. The blueprint (never-do-access-kms:90) hedges with "may be deleted", while AWS says `{}` deletes the archive. State it plainly in the blueprint.
- L-h. The "Tag topics" bullet (SKILL:86-87) cites SNS.3, which says only that a `requiredTagKeys` parameter exists with no default. It does not say tagging is required. Reword it as a claim the control supports.

## Fresh grounding sample (28 claims not in the round-1 sample; all pass unless marked)
1. Terraform 1.17.0 stable since 2026-10-21, not the target: facts F2.
2. Terraform 1.16.6 reference patch: facts F1.
3. aws latest 6.70.0, no 7.x, v7 planned: facts F3.
4. 6.57.0 withdrawn from GitHub and the Registry: facts F4 (unverified-and-risks:11).
5. `identity` import needs Terraform >= 1.12: facts F11. (F11's source page is the VPC docs. Research lists the SNS pages as well, so it is accepted.)
6. Provider `default_tags` overridden by matching resource `tags`: research section 3.
7. The `region` argument: change forces replacement, import `id@region`: research section 1.
8. Feedback arguments for the five protocol prefixes, sample rate 0-100, failure role logs all failures: research section 3.
9. `aws_sns_topic_policy` requires `arn` and `policy`: research section 4.
10. SNS.4: `*` principal with fixed-value conditions can pass; wildcard or variable conditions are not evaluated: research section 4.
11. The control config rule ids `sns-encrypted-kms`, `tagged-sns-topic`, `sns-topic-no-public-access`: research section 7.
12. SNS.3 `requiredTagKeys` has no default: research section 7.
13. AWS also says to add `aws:SourceAccount`/`aws:SourceArn` conditions for service publishers: research section 7.
14. CloudWatch principal `cloudwatch.amazonaws.com`: research section 7.
15. Events principal `events.amazonaws.com`: research section 7.
16. IAM-role sources (EC2 Auto Scaling, CodePipeline, AWS Config, and others): research section 7.
17. Encrypted archive needs SNS `kms:Decrypt` and `kms:GenerateDataKey`: research section 3.
18. Archive has additional charges: research section 3.
19. `aws:SourceOrgID` also unsupported for EventBridge to an encrypted topic: research section 7.
20. Subscription protocols full/partial lists: research section 5.
21. A subscription imported after confirmation can be deleted by Terraform; deleting a topic deletes its subscriptions: research section 5.
22. `pending_confirmation` shows the status: research section 5.
23. Cross-account and cross-region use the queue account provider with the topic region: research section 5.
24. Without a DLQ, a client-side error makes SNS discard the message: research section 5. (SKILL:71-72 names only the client-side case; the research adds the server-side case after retries. That is consistent, and the blueprint has both.)
25. AWS advises domain names over raw-IP HTTP endpoints: research section 7.
26. The 6.0.0 guide has no `aws_sns_*` entries; the only SNS-related change is `region`: research section 2.
27. CHANGELOG 6.48.0-6.70.0 has no SNS entries in the windows read; the 6.55.0 partial read is recorded as L1: research section 2.
28. Evaluation scenarios 1-5 must_pass criteria against the research: all supported (FIFO accepts SQS standard, MessageGroup is high throughput and irreversible, a CMK is required, inline policy vs topic policy tagged (unverified)).
Result: no wrong claims. One unsourced untagged clause (N1, MEDIUM).

## Always Do check
- Every bullet is High-sourced and has plain notation, with no tags inside. Exceptions on form: L-a and L-h.
- No F#/M# ids, no SNS.2, and example/placeholder markers are present in all HCL except the L-d cases.
