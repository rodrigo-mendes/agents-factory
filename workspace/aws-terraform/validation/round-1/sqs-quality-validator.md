# Quality validation, round 1: provisioning-aws-sqs-v6

Target: `packages/aws-terraform/.apm/skills/provisioning-aws-sqs-v6/` (SKILL.md 137 lines, 9 blueprints, max 129 lines).
Method: full read of skill, research and family facts, and the policy files. No WebFetch tool was available in this run, so every claim was checked against the research file's recorded reading of the pages, not a fresh fetch. The Principal "*" finding rests on the research paraphrase plus the skill's own SQS.3 text, and should be confirmed on the live page.
Structural checks passed:
- Frontmatter has only `name` and `description`; the description is quoted, under 300 characters, and contains "Use when"; the name equals the folder.
- All internal links and anchors resolve.
- No F#, M#, workspace or absolute paths in shipped text. U/M/L ids appear only in the register.
- Plain tag notation, with no bold or brackets.
- 5 evaluation scenarios.

Totals: HIGH 1, MEDIUM 9, LOW 8.

## HIGH

H1. Never row `Principal "*"` overstates its sources (SKILL.md:92; never-do-policies-access.md:41-77; never-do-patterns.md:10; evaluation-scenarios.md:92-101).
- The evidence cited is only "avoid public queues" (best-practices page) and "SQS.3 covers public access".
- The skill itself says (always-do-policies.md:39-41) that SQS.3 evaluates fixed-value conditions, and that wildcards or variables in conditions are not evaluated as PASSED. That means a `*` principal restricted by a fixed condition is a case the source treats as evaluable, not as an absolute ban.
- The unconditional Never rule is therefore a derived rule, not a documented fact. The WRONG example is also unconditioned, so the nuance is lost.
- Fix: reword to "Principal `*` (or `{AWS:"*"}`) without a restricting fixed condition", or move it to Ask First with the quoted page text. Re-read the best-practices page and SQS.3 and cite the exact sentence. The research (section 8) already words the SQS.3 lever as "without `*` principal; fixed-value conditions only", which is inconsistent with the Never wording.

## MEDIUM

M1. Absence claim stated as High fact in an Always Do bullet. "Inline `policy` is not deprecated" appears at SKILL.md:57, always-do-policies.md:11 and evaluation-scenarios.md:69.
- The evidence is only that the provider page does not say "deprecated". That is absence of evidence.
- Per the evidence rule it needs `(medium confidence, absence of evidence)` and must not sit in an Always Do bullet (High-only, no tags). Move it to Ask First or the register.

M2. Always Do bullets break the "one High claim, one inline URL, no caveats" rule (SKILL.md:47-67).
- There are 11 bullets, not 12 (lines 47, 49, 51, 53, 55, 57, 59, 61, 63, 65, 67).
- None carries an inline URL; they only link blueprint anchors.
- Bullet 2 carries a Security Hub severity claim, and bullet 7 carries a parenthetical caveat ("use aws:SourceAccount for multiple topics").
- Bullets 6 and 9 bundle several claims.
- No tags were found in any bullet. That part passes.

M3. Never row 2 cites the wrong page for its HCL (SKILL.md:87; never-do-queue-config.md:6-19).
- The "integer, not string" note is on the `aws_sqs_queue` page, about the inline `redrive_policy`.
- The WRONG and CORRECT HCL use `aws_sqs_queue_redrive_policy`, whose page has no such note (research section 5).
- Show the inline `redrive_policy` on `aws_sqs_queue` in the example, or cite the redrive_policy page and drop the claim for that resource.

M4. never-do-queue-config.md:76-94 (entry 7): the CORRECT block attaches `aws_sqs_queue_redrive_policy.good` to `aws_sqs_queue.src_bad`, which still carries an inline `redrive_policy`.
- That mixes inline and dedicated policy, which the skill's own Ask First (M3 register item) says is unresolved.
- The resource is also named `src_bad`, which is a copy-paste hazard.
- Fix: define a separate good source queue without the inline policy.

M5. Register has orphan rows and unmapped tags (unverified-and-risks.md:15-48).
- U2, U4, L2 and L3 have no tag anywhere in the skill text. U2 and U4 even say "not stated anywhere in this skill". L1 is visible as an untagged sentence at SKILL.md:122.
- `(medium confidence)` at evaluation-scenarios.md:70 and `(unverified)` at evaluation-scenarios.md:121 are not in the mapping table.
- M1's content appears untagged at SKILL.md:105 and always-do-queues.md:23 ("docs disagree on default").
- Fix: remove orphans or add a tagged mention, and add the missing mapping rows or tags.

M6. Import row cites one page for four resources (SKILL.md:109; always-do-dlq.md:56-69).
- The identity attribute `queue_url` for `aws_sqs_queue_redrive_policy` and `aws_sqs_queue_redrive_allow_policy` comes from pages 4 and 5.
- Those pages are not cited in the Import section or Quick Reference, and they are missing from External Resources.
- The `url` versus `queue_url` split matches the research, so the content is correct but the sourcing is not.

M7. always-do-dlq.md:13-14 states that encryption is unchanged by the move and that DLQ consumers need `kms:Decrypt` on the source key.
- The research attributes this to the SSE and key-management pages.
- The block's Source lines (44-47) cite only the provider and DLQ pages, so the claim is uncited.

M8. Unsourced and untagged statements.
- SKILL.md:124: "Upgrade path: move to the latest 5.x, get a clean plan, set `~> 6.69`, run `terraform init -upgrade`" has no research basis.
- SKILL.md:25: "a constraint that resolves to it fails init" is an inference. The family facts say only that 6.57.0 was withdrawn, and `~> 6.69` cannot resolve to it anyway.

M9. Always Do bullet 8 (SKILL.md:61; always-do-policies.md:76-81) says "customer managed KMS key for encrypted queues that AWS services send to".
- The source rule is about SSE-KMS (the AWS managed key policy cannot be edited), not SSE-SQS.
- Scope the bullet to SSE-KMS queues, or it wrongly implies that SSE-SQS queues cannot take service producers.

## LOW

L1. The bare word "Medium" is used as severity for SQS.1 (SKILL.md:49 and 111; always-do-queues.md:33). It collides with the confidence tag. Use "moderate".

L2. The mapping table header is `Tag text | Where | Register id`. The policy specifies `Tag text used in the skill`. There is also no I-section, which is acceptable if no irresolvable items exist.

L3. Quick Reference "Provider constraint (root) ~> 6.69" (SKILL.md:101) cites the CHANGELOG. A constraint is a decision. Cite the family decision or the version-constraints page.

L4. Ask First M1 row (SKILL.md:76) attributes "AWS API page says 1,048,576" but cites only the provider page. The Ask First DLQ row (SKILL.md:79) cites the DLQ page for the "API default 10", which the research sources to SetQueueAttributes.

L5. always-do-queues.md:61-62: "backlog not encrypted retroactively" is cited to the key-management page. The research sources it to the SSE page.

L6. SKILL.md:86: "(or use another value)" extends the provider warning, which says "not explicitly 2012-10-17". Reword to "without an explicit Version".

L7. SKILL.md:26-27: "aws v7 is planned (not released)" has no inline source. The family facts' F3 supports it; cite the releases page.

L8. The Never table order differs from the never-do-patterns index. It is still one-to-one, with no functional impact.

## Explicit checks requested

1. Never rows one-to-one.
   - SKILL.md has 8 rows, never-do-patterns.md has 8 entries, and there are 8 blueprint sections. 8=8 is confirmed.
   - The AWS managed key `alias/aws/sqs` row is a documented fact (the key policy cannot be modified) and is High-sourced. It passes.
   - Rows 1, 3, 4, 5, 6 and 8 pass on tier (High, sourced, alternative also High).
   - Row `Principal "*"`: see H1.
   - Row 2: see M3.
2. Always Do bullets: 11 bullets, not 12. No tags inside the bullets. Bullet 6 breaks the High-only rule (M1), and structure breaks the evidence-rule format (M2, M9).
3. No F#, M# or workspace paths, and plain notation: pass. Orphans: M5.
4. Example values: pass. ARNs, names, URLs, tags and variable defaults are marked `# example`. Only the WRONG-block names are unmarked, and the file headers cover them.
5. Each statement cites the page that states it: partial. See M3, M6, M7, L3, L4, L5.
6. The 7 legacy claims are not reproduced.
   - Inline policy: the skill says "not deprecated". That is correct in substance but badly tiered (M1).
   - Max message: no 262,144 "default maximum" claim. The range is 1,024 to 1,048,576 and the default dispute is flagged.
   - Default SSE: not claimed, tagged unverified.
   - Provider error: not claimed. The skill says the provider page is silent (medium confidence).
   - `aws:SourceArn` or `aws:SourceAccount`: the skill phrases it correctly.
   - The 70,000 msg/s figure is absent. Only per-partition numbers are given.
   - The legacy `>= 1.7` and `~> 6.0` values are absent.
7. `redrive_allow_policy`: pass.
   - The HCL uses `redrivePermission = "byQueue"` and `sourceQueueArns`, which matches the provider page.
   - `allowAll` and `denyAll` are cited to the AWS DLQ page (always-do-dlq.md:50-52, SKILL.md:79 and 112), not to the provider page.
   - The skill does not claim that the provider page documents those values (low risk).
   - Import ID is the queue URL. The identity attribute is `url` on `aws_sqs_queue` and `queue_url` on the other three, which is correct.

## Claims sampled (36)
- Pass (25): version rows (Terraform 1.16 and 1.17, aws 6.70, 6.57.0 withdrawn); region; identity import at 1.12 or later; the Version hang warning; `.fifo` suffix; throughput and scope pairing; DLQ type, account and Region; visibility, retention, delay and wait-time defaults and ranges; dedup defaults; name rules; timeouts; SQS.1, SQS.2 and SQS.3 severities; the 15-minute retention change; high-throughput per-partition numbers; the SNS producer shape; the CMK rule; producer and consumer KMS permissions; `byQueue` with up to 10 ARNs; the standard-queue timestamp rule; 6.42.0 list resource; 6.53.0 fix; 6.0 guide silent on SQS.
- Flagged (11): the Principal `*` rule (H1); inline "not deprecated" (M1); the maxReceiveCount page mismatch (M3); the entry-7 mixing (M4); import sourcing (M6); KMS-on-move (M7); upgrade path and "fails init" (M8); bullet 8 scope (M9); and the L-items above.
