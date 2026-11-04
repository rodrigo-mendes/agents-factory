# Quality validation, provisioning-aws-sns-v6 (round 1)

Date: 2026-10-23. Skill: packages/aws-terraform/.apm/skills/provisioning-aws-sns-v6/.
Method: read all 9 files in full, compared against the research, the family facts and the policy files.
WebFetch was not available in this run, so no claim was re-fetched. Findings marked "general knowledge" rest on my own AWS/Terraform knowledge and are not confirmed.
Known family-level decisions were not reported: the `-v6` suffix and page-from-`main` confidence.

Counts: HIGH 1, MEDIUM 8, LOW 9.

## Structure checks (pass)
- Frontmatter: only `name` and `description`; the name equals the folder; the description is quoted, about 262 characters, and contains "Use when".
- Lengths: SKILL.md has 146 lines. Blueprints have 93 to 126 lines, all at or under 160.
- Anchors: all links and anchors in SKILL.md, never-do-patterns.md and always-do-patterns.md resolve (checked by hand against the headings).
- Residues: grep found no F#/G#/M# ids, `workspace`, `research_`, `_family`, absolute paths or relative dates in shipped text. The U/M ids are the allowed register ids.
- Evaluation scenarios: 5, covering canonical, edge, rejection and trap. They encode the research's legacy-claim corrections: FIFO accepts SQS standard, `MessageGroup` is the high-throughput mode, and a customer managed key is required.
- Always Do bullets contain no tags.

## Rule 1: Never rows vs blueprint WRONG entries
- SKILL.md has 8 rows (lines 95-102). never-do-patterns.md lists 8 entries. The blueprints have 4 in never-do-access-kms.md and 4 in never-do-subscriptions.md. Row order and wording match one-to-one, and all 8 anchors resolve, including the one the orchestrator fixed.
- The `aws.topic_account` and `aws.queue_account` aliases are used without being defined (see LOW-3).

## Findings

### HIGH
H1. Never row 4 has an alternative that is not High, and it destroys data.
- Where: SKILL.md:98; never-do-access-kms.md:78 and 90-92.
- The row tells the reader to "Apply `archive_policy = jsonencode({})` first (disables and deletes the archive), then destroy".
- AWS states that `{}` disables the policy and deletes the archive. How the Terraform provider handles `jsonencode({})` for `archive_policy` is not documented in the research (the author flagged this). The provider page was read with no archive-removal guidance.
- Evidence rule: the alternative of a Never row must be High, and the alternative here is an unconfirmed Terraform behavior.
- The alternative also deletes the archive. That makes it an Ask First decision, not a mechanical "instead".
- Fix:
  - Keep the Never row as "destroy with active archive fails".
  - Move the `{}` alternative to Ask First, tagged (unverified) with a register row, or make it a generic "deactivate the archive policy per AWS, confirm the plan, then destroy".
  - Warn that the archive is deleted.

### MEDIUM
M1. Always Do bullet 4 and topic §2 contain an untagged inference.
- Where: SKILL.md:52; always-do-topic.md:23.
- "SNS.1 passes with any KMS key" is not stated by the controls page. The research derives it from the control description wording ("keys managed in AWS KMS").
- By the evidence rule this is (unverified), and Always Do must be High-only with no embedded caveats.
- Fix: cite only the page's title wording, or drop the "passes with any key" clause.

M2. Never row 5 cites the wrong page for part of the row.
- Where: SKILL.md:99.
- "SQS (FIFO or standard)" and "reach Lambda through an SQS queue" are stated by the AWS fifo-message-delivery page. The row cites only the provider topic page.
- The blueprint at never-do-subscriptions.md:18-19 cites both pages. SKILL.md:99 should too.

M3. Quick Reference miscites the version constraints.
- Where: SKILL.md:110.
- The row "Provider / CLI constraint `~> 6.69` / `~> 1.16`" cites the Terraform version-constraints page. That page states the `~>` operator and root-module practice. It does not state 6.69 or 1.16, which come from the releases pages.
- always-do-topic.md:14 has the same issue.
- Always Do bullet 1 (SKILL.md:46) has no inline URL at all.

M4. The key-policy example would fail or lock out the key as shown.
- Where: always-do-topic.md:74-94.
- The policy document contains only the CloudWatch statement. A "key administrators (not shown)" comment stands in for the rest.
- Attaching it as written (`policy = ...json`) replaces the default key policy. KMS rejects policies that would leave the key unmanageable unless a lockout bypass is set (general knowledge, not verified).
- Fix: show a minimal admin statement, for example the account root with `kms:*`, or the `aws_kms_key` example with the default policy merged in.

M5. The SQS examples omit the queue policies and may be misleading (general knowledge).
- Where: always-do-access-delivery.md:57-74 and 93-98.
- Neither the main queue nor the DLQ has a policy that allows SNS to send. The DLQ would not receive messages and the subscription would not deliver.
- `aws_sqs_queue.orders` is not defined in the example.
- The research did not record this requirement, so I cannot confirm it from the sources. Either mark the examples as incomplete (with a pointer to provisioning-aws-sqs-v6) or add the policies from a fetched AWS page.
- The §8 cross-account example also lacks the topic-policy Subscribe permission for the queue account.

M6. The 5.x to 6.x upgrade path is unsourced and untagged.
- Where: SKILL.md:132.
- "move to latest 5.x, get a clean plan, set `~> 6.69`, run `terraform init -upgrade`" appears in no part of the research. The cited upgrade guide is only stated to say nothing about SNS.
- Fix: source it or remove it.

M7. Tag classes do not match the evidence table.
- Where: SKILL.md:82, 86, 87; unverified-and-risks.md:27, 28, 30.
- M1 ("both write the same policy so they would conflict") is an inference. The notation rule makes that (unverified).
- M2 depends on a page that was not fetched. That is also (unverified).
- M4 is an absence claim. The notation rule asks for "(medium confidence, absence of evidence)".
- Using bare (medium confidence) for all three blurs the evidence classes.
- The rows are sensibly placed in Ask First.

M8. Orphan register rows, and a shipped mention of SNS.2.
- Where: unverified-and-risks.md:21 and 29; the mapping at lines 42-49.
- U4 (SNS.2) and M3 have no tag anywhere in the shipped text, so they are orphan register rows. L2 and L3 are untagged coverage limits, which is acceptable.
- U4 names "SNS.2" in shipped text. The instruction was that SNS.2 must not be cited as a control. It is not cited as a control, but it appears by name and the row is an orphan. Delete U4.
- M3 ships an inference ("an AWS-managed key cannot satisfy the requirement because its policy cannot be edited"). It states it is unused, which makes it dead weight. Delete M3.
- Check the register headers and counts after the deletions.

### LOW
L1. Always Do bullets are not "one claim, one URL".
- Bullet 1 has no URL. Bullet 2 combines two claims and two URLs. Bullet 4 combines SNS.1 and key support with two URLs. Bullet 5 and bullet 7 combine claims, and bullet 8 packs four claims plus a caveat.
- Where: SKILL.md:46-76.
- Bullet 12 (SNS.3) does not itself say why tagging is needed beyond the Low control.

L2. Bullet 5 overgeneralizes.
- Where: SKILL.md:55-57.
- "grant the service principal" is not right for the sources that need an IAM role in the key policy (EC2 Auto Scaling, CodePipeline and others). The blueprint (always-do-topic.md:68-69) says so, but the bullet does not.
- Bullet 7 says to "avoid a `*` principal". The example Deny statement at always-do-access-delivery.md:28-31 uses principal `*`. This is standard for a Deny, but the page does not say so.

L3. Undefined aliases and resources in HCL.
- `aws.topic_account`, `aws.queue_account` (never-do-subscriptions.md:55 and 62) and `aws.topic_region` (never-do-subscriptions.md:44) have no `provider` blocks.
- The §8 example in always-do-access-delivery.md fully defines its own alias, `queue_account_topic_region`.
- Judgment: the never-do HCL is not materially misleading, because the aliases appear only in WRONG/CORRECT comments. Using `queue_account_topic_region` in all three places would be more consistent.
- `aws_iam_role.sns_feedback`, `aws_iam_role.sns_to_firehose` and `aws_kinesis_firehose_delivery_stream.orders` are undefined. always-do-topic.md:119 says the role is defined elsewhere, but the Firehose resources have no such note.

L4. Quick Reference rows cite only part of the source.
- `kms_master_key_id` (SKILL.md:114): "AWS-managed or customer managed key ID" comes from the topic page, but only the key-management page is cited.
- Topic `delivery_policy` (SKILL.md:115): the "wrapped in `http`" claim for the topic is cited to the subscription page. It belongs to the topic page.

L5. Register mapping format.
- The mapping columns are "Tag text, Where, Register id". The policy asks for "Tag text used in the skill".
- The section is named "Tag to Register Mapping" (policy: "Tag to register mapping").
- There is no irresolvable (I) section, which is acceptable if there are none.

L6. Unmarked example values.
- `content_based_deduplication = true` (always-do-topic.md:54) is not marked `# example`.
- `fifo_topic = true` is required for FIFO and so is not an example.

L7. DLQ wording could be misread against the rule "FIFO accepts SQS standard".
- always-do-access-delivery.md:51 says "FIFO topic subscriptions use FIFO queues". It is correct for DLQs per the DLQ page, but the sentence should say "DLQ".

L8. always-do-topic.md:41 states a `default_tags` behavior with the citation "(topic page)", not a URL.

L9. Severity words: the "Medium-Confidence Items" heading and the SKILL.md table ("SNS.1 (Medium)") use "medium" for both severity and confidence. The notation rule restricts only headings, so this is cosmetic.

## Claim sample (about 40; verified against the research and facts)
Pass:
- Version table rows (6.70.0, 1.16.6, withdrawn 6.57.0, region, identity)
- the `.fifo` suffix
- no FIFO to email/SMS/mobile/HTTP(S) delivery
- FIFO to SQS FIFO and standard
- throughput scope direction, irreversible `MessageGroup`, at-creation recommendation
- symmetric keys only
- CMK for AWS publishers, with `kms:GenerateDataKey*` and `kms:Decrypt`
- bare account ID converted to the root ARN
- Deny on `aws:SecureTransport=false`
- SNS.1 Medium, SNS.3 Low, SNS.4 Critical
- same-account same-region DLQ
- encrypted DLQ needs a custom key
- 14-day retention, alarm on `ApproximateNumberOfMessagesVisible`
- DLQ retries (100,015 over 23 days; 50 over 6 hours)
- `subscription_role_arn` only for firehose
- up to five Firehose streams
- topic-region provider rule
- queue-account provider for same-region cross-account
- unconfirmed subscription destroy behavior
- `confirmation_timeout_in_minutes` default 1
- `endpoint_auto_confirms` default false
- `maximum_message_size` limits
- `delivery_policy` wrapped in `http` on the topic only
- archive 1-365 days, FIFO-only, delete-blocking
- SMS preferences not importable
- data protection import
- the 6.0 guide with no SNS entries
- EventBridge `aws:Source*` unsupported
- the `alias/aws/sns` rejection for service publishers

Defects are those listed above (M1, M2, M3, M5, M6; H1).

## Rule-by-rule answers
1. Never rows: 8 = 8 = 8, one-to-one, anchors good. The alternative of row 4 is the problem (H1). Row 5 miscites a page (M2).
2. Always Do: no tags inside bullets. They are not strictly High-only (M1) and are not strictly one claim each (L1).
3. Shipped text has no residues. Tags and register mostly agree. Orphans: U4 and M3 (M8). The untagged `fifo_throughput_scope = "MessageGroup"` Ask First row is High under the family convention: the AWS fifo-high-throughput page states the behavior, and the only non-High item in it (numeric quotas) carries (unverified), mapped to U2. The untagged `archive_policy` row is also High: every statement in it is on the AWS archiving page, and it contains no Terraform-behavior claim. Both pass.
4. Example values: marked, except L6.
5. Page citation: M2, M3, L4.
6. Legacy wrong claims: none reproduced. FIFO accepts SQS standard; the throughput direction is correct; cross-region SNS to SQS is stated correctly; a CMK is required for CloudWatch/EventBridge publishers. The unverified legacy claims (`AmazonSNSRole`, raw message delivery, 30,000 msg/s) are absent.
7. Author flags:
   - `jsonencode({})` is H1.
   - Undefined IAM roles are L3.
   - `aws.topic_region` is only a comment alias, not materially misleading (L3).
   - SNS.2 is not cited as a control but appears in U4 (M8).
