# Evaluation Report: provisioning-aws-sqs-v6 (round 1)

Method: no sub-agents were spawned. I read SKILL.md and all linked blueprints, answered each scenario using only skill content, then judged my own answers. This is self-simulated, so a PASS means the skill content supports the criterion. It does not show that a separate model would respond correctly.

Skill: packages/aws-terraform/.apm/skills/provisioning-aws-sqs-v6/

## Summary

| Scenario | must_pass | must_not OK | Verdict |
|---|---|---|---|
| 1 Canonical (encrypted queue + DLQ + SNS) | 7/7 | 4/4 | PASS |
| 2 FIFO high throughput + FIFO DLQ | 5/5 | 3/3 | PASS |
| 3 Misuse rejection (inline policy, double SSE) | 4/4 | 3/3 | PASS |
| 4 Faulty snippet review | 4/4 | 4/4 | PASS |
| 5 Service producers on encrypted queue | 4/4 | 2/2 | PASS |

Overall: 24/24 must_pass and 16/16 must_not OK. All 5 scenarios PASS (100%).

## Scenario 1: PASS

Answer built from queues §1-2, policies §4-5 and dlq §7.

- Version constraints: `required_version = "~> 1.16"` and `version = "~> 6.69"` (queues §1). PASS.
- DLQ and redrive: separate `aws_sqs_queue.orders_dlq`, attached with `aws_sqs_queue_redrive_policy` and `maxReceiveCount = 5` (dlq §7). PASS.
- Encryption: `sqs_managed_sse_enabled = true` on both queues, with no `kms_master_key_id`. PASS.
- Policy resource: `aws_sqs_queue_policy` with `Version = "2012-10-17"` (policies §5). PASS.
- Policy shape: `Principal = { Service = "sns.amazonaws.com" }`, `sqs:SendMessage` and `ArnEquals` on `aws:SourceArn` (policies §5). PASS.
- Tags: queues §2 shows `tags`, but the dlq §7 example has none. The answer adds tags, citing SKILL.md Always Do (SQS.2). PASS.
- Retention: DLQ 1209600 against the source default of 345600 (dlq §7). PASS.
- must_not: Version is present, no `Principal "*"`, the count is an integer, and only one SSE option is set. All OK.

## Scenario 2: PASS

- FIFO naming: `payments-ht.fifo` and `payments-dlq.fifo`, both with `fifo_queue = true` (queues §3, never-do-queue-config §7). PASS.
- Throughput settings: `deduplication_scope = "messageGroup"` with `fifo_throughput_limit = "perMessageGroupId"` (queues §3). PASS.
- Message groups: "use many distinct message group IDs" (queues §3, Ask First). PASS.
- Deduplication: "`content_based_deduplication` ... hashes the message body with SHA-256; an explicit `MessageDeduplicationId` overrides it" (queues §3). PASS.
- Same account and Region: dlq §7 and never-do-queue-config §8. PASS.
- must_not: the DLQ is FIFO, the scope is not `queue` with `perMessageGroupId`, and no regional msg/s quota is stated as confirmed. The answer gives only the per-partition figures (3,000/s with batching, 300/s per operation), and U4 marks regional quotas unverified. All OK.

## Scenario 3: PASS

- Inline policy: "inline `policy` is not deprecated"; the provider page only recommends the dedicated resource (SKILL.md Always Do, policies §4). PASS.
- Double encryption: AWS allows one SSE option per queue, and the provider page is silent (medium confidence). The answer asks "Which single encryption option should this queue use?" (Ask First, M2). PASS.
- No provider-error claim: the answer says provider behaviour is undocumented. PASS.
- Dedicated resources and drift: "drift is detected only when the inline argument is set" (policies §4, Ask First). PASS.
- must_not: no deprecation claim, no provider-error claim, and no default-true claim (U1 says unverified, set it explicitly). All OK.

## Scenario 4: PASS

- Version: reject the missing `Version`, fix with `Version = "2012-10-17"`, cite the `timeout while waiting` hang (never-do-policies-access §1). PASS.
- Principal: reject `"*"`, use a service principal with an `aws:SourceArn` condition, cite SQS.3 (Critical) and the best-practices page (never-do-policies-access §2). PASS.
- Count: `"5"` becomes `5` (never-do-queue-config §4). PASS.
- FIFO name: `orders` becomes `orders.fifo` (never-do-queue-config §5). PASS.
- must_not: nothing was accepted, and only documented values were cited. All OK.

## Scenario 5: PASS

- Key choice: a customer managed key, because the AWS managed key policy cannot be modified (never-do-policies-access §3, policies §6). PASS.
- Key policy grants: the service principal needs `kms:Decrypt` and `kms:GenerateDataKey` (policies §6). PASS.
- Pointer: `provisioning-aws-kms-v6` is named in policies §6 and never-do-policies-access §3. PASS.
- Unverified conditions: the S3/EventBridge condition keys are unverified (U3, Ask First); take them from the S3 and EventBridge docs. PASS.
- must_not: `alias/aws/sqs` is shown only as the WRONG example, and no S3/EventBridge condition keys are given. Both OK.

## Criteria and skill issues (non-blocking)

1. evaluation-scenarios.md says "Four scenarios" in its header, but it has five. Fix the header.
2. S1 "Sets tags on the queues": the skill's own DLQ example (dlq §7) has no tags, which sits oddly beside the Always Do tag rule. Suggest adding `tags` to the dlq §7 snippet.
3. S2: no criterion or skill text says whether the FIFO DLQ itself needs the high-throughput settings. The skill is silent, so the answer cannot assert either way. This is a possible gap, not a failure.
4. S2 must_pass "Notes that content_based_deduplication..." is sourced (queues §3), but SKILL.md does not mention it. Only the blueprint does. This is fine, but the SKILL.md index could mention it.
5. S4 sample snippet: it also lacks `Effect` and `Resource`. The skill has no guidance on this, and the criteria do not require it.

## Fixes needed

- Correct the "Four scenarios" header in blueprints/evaluation-scenarios.md.
- Optional: add `tags` to the dlq §7 example.
- No behavioural fixes needed.
