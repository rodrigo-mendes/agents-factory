# Evaluation Report: provisioning-aws-sns-v6 (round 1)

Method: inline simulation, with no subagents. Each response was written using only SKILL.md and its linked blueprints, then judged. Skill path: `packages/aws-terraform/.apm/skills/provisioning-aws-sns-v6/`.

## Summary

| Scenario | must_pass | must_not OK | Verdict |
|---|---|---|---|
| 1 Canonical: encrypted topic + SQS + DLQ | 5/5 | 2/2 | PASS |
| 2 FIFO + throughput scope | 5/5 | 3/3 | PASS |
| 3 alias/aws/sns + EventBridge conditions | 4/4 | 2/2 | PASS |
| 4 Unconfirmed email + provider region | 4/4 | 2/2 | PASS |
| 5 Policy ownership | 3/3 | 2/2 | PASS |

Overall: 21/21 must_pass and 11/11 must_not OK. 5/5 scenarios PASS (100%).

## Scenario 1: Canonical

Simulated response (summary):
- `terraform { required_version = "~> 1.16"; aws version = "~> 6.69" }`.
- `aws_kms_key.sns` plus `aws_sns_topic.orders` with `kms_master_key_id = aws_kms_key.sns.id` and tags.
- `aws_sqs_queue.dlq` with 14-day retention.
- `aws_sns_topic_subscription` with `protocol="sqs"` and `redrive_policy = jsonencode({deadLetterTargetArn = aws_sqs_queue.dlq.arn})`.
- Notes that the DLQ must be an SQS queue in the same account and region as the subscription, and that an encrypted DLQ needs a custom KMS key granting the SNS service principal.
- All names and ARNs are labelled `# example`.

Judgement:
- PASS, version constraints: always-do-topic §1, "required_version = \"~> 1.16\"" and "version = \"~> 6.69\"".
- PASS, `kms_master_key_id`: topic §2.
- PASS, `redrive_policy`: access §7 HCL.
- PASS, same account and region: access §7 text, "same account and region as the subscription".
- PASS, examples marked: the `# example` comments throughout.
- OK, no SQS subscription without a DLQ.
- OK, no bare account ID principal. Any principal is written as `arn:aws:iam::123456789012:root`.

## Scenario 2: FIFO

Simulated response (summary):
- `name = "orders-events.fifo"` with `fifo_topic = true`.
- Notes that FIFO topics deliver to SQS FIFO and SQS standard queues.
- Wires a standard SQS queue as a subscriber, and reaches Lambda through an SQS queue, with the Lambda event source mapping on the queue.
- Says `fifo_throughput_scope = "MessageGroup"` is the high-throughput mode and is irreversible back to `Topic`. It asks "Is the irreversible high-throughput mode required?" and says to set the scope at creation.

Judgement:
- PASS on all 5 must_pass items. Evidence: topic §3, the Ask First row for `MessageGroup`, never-do-subscriptions §1 ("to reach Lambda, go through an SQS queue"), and the SKILL.md Always Do bullet "Set `fifo_throughput_scope` at creation".
- OK, no claim that FIFO topics may only deliver to SQS FIFO queues.
- OK, `MessageGroup` is not called lower-throughput.
- OK, no direct lambda, email or HTTP(S) subscription.

Minor observation, not a failure: the topic §3 example hard-codes `fifo_throughput_scope = "Topic"`. A user who asked for high throughput gets a conflicting example unless the response follows the Ask First row. The skill has no worked "after user confirms" snippet.

## Scenario 3: Misuse rejection

Simulated response (summary):
- No to `alias/aws/sns`: AWS says to use a customer managed key for AWS service publishers such as CloudWatch and EventBridge.
- The key policy grants `events.amazonaws.com` and `cloudwatch.amazonaws.com` `kms:GenerateDataKey*` and `kms:Decrypt`.
- `aws:SourceAccount`, `aws:SourceArn` and `aws:SourceOrgID` conditions are not supported for EventBridge publishing, so the `events.amazonaws.com` statement has no conditions.
- The CloudWatch statement may keep `aws:SourceAccount`.
- Cites https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html.

Judgement:
- PASS on all 4 must_pass items. Evidence: never-do-access-kms §2 and §3, topic §4, and the SKILL.md Never Do rows.
- OK, `alias/aws/sns` is not accepted.
- OK, no source condition is added to the EventBridge statement. Quoting the WRONG block as a rejected example is allowed.

Hazard worth noting, not a failure: topic §4 shows `aws:SourceAccount` on the CloudWatch statement and says "AWS also says to add" conditions. A model that merges the CloudWatch and EventBridge statements into one could copy the condition onto the EventBridge principal. The skill separates the two in prose but provides no combined two-service key-policy example.

## Scenario 4: Unconfirmed email and provider region

Simulated response (summary):
- No. For an unconfirmed email subscription, Terraform cannot remove it. Destroy only drops it from state and the subscription stays in AWS. "You cannot unsubscribe to a subscription that is pending confirmation."
- Confirmation can happen outside Terraform, such as through the email link. `pending_confirmation` shows the status. After confirming, manage or import it.
- The subscription must use a provider in the topic's region (us-east-1) or creation fails. The eu-west-1 default provider is wrong.
- Adds `provider "aws" { alias = "topic_region"; region = "us-east-1" }` and sets `provider = aws.topic_region` on the subscription.

Judgement:
- PASS on all 4 must_pass items. Evidence: never-do-subscriptions §4 and §2, and the SKILL.md Never Do rows.
- OK, no claim that destroy removes it from AWS.
- OK, the subscription is not created with the eu-west-1 provider.

## Scenario 5: Policy ownership

Simulated response (summary):
- Pick one. Both write the same topic policy, so using both would conflict.
- Labels this "(medium confidence)": it is an inference, because neither provider page has a do-not-mix note.
- The doc example uses `aws_sns_topic_policy` with `aws_iam_policy_document`.
- Asks "Manage the topic policy inline or with `aws_sns_topic_policy`? (Pick one.)" Any bare-account principal is written as `arn:aws:iam::<account>:root`.

Judgement:
- PASS on all 3 must_pass items. Evidence: the Ask First row 1 and register item M1.
- OK, the conflict is not stated as documented fact.
- OK, no bare account ID principal.

## Criteria quality flags

- Scenario 5 must_pass #3 ("Writes any bare-account Principal as arn:aws:iam::<account>:root") is conditional. It is trivially satisfied if the response contains no principal. It is sourced (topic policy page) but weak, and its discriminating power is low for a conceptual question.
- Scenario 2 must_pass #3 combines three assertions (high-throughput, irreversible, asks first). It is sourced, but a partial answer fails the whole item. Consider splitting it.
- Scenario 1 must_pass #5 ("Marks example names and ARNs as examples") is vague, but the skill explicitly requires `# example` markings, so it is sourced.
- Scenario 3 must_not #2 is sourced and unambiguous. No criterion demands advice the research never gives. There are no criterion bugs.

## Fixes needed (all optional)

1. `blueprints/always-do-topic.md` §3: add a commented alternative or note showing the `MessageGroup` variant for use after user confirmation (Scenario 2).
2. `blueprints/always-do-topic.md` §4: add a combined CloudWatch + EventBridge key-policy example, with the condition on the CloudWatch statement only, to guard against the condition leaking onto EventBridge (Scenario 3).
3. `blueprints/always-do-access-delivery.md` §7: the example references `aws_sqs_queue.orders` without defining it. Add a stub or an `# defined elsewhere` comment.
4. `blueprints/evaluation-scenarios.md`: split Scenario 2 must_pass #3, and make Scenario 5 must_pass #3 unconditional or drop it.
