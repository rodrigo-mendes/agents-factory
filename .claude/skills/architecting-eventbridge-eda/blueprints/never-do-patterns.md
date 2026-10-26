# Never-Do Patterns — AWS EventBridge EDA (2026)

Six anti-patterns summarised in SKILL.md, each with wrong / correct / detection.
Source research: `workspace/docs/research_cloud_AWS_EventBridge_EDA_2026.md` (research date 2026-08-28).

---

## A1 — No DLQ on production targets (CRITICAL)

Exhausted retries drop the event; permanent errors skip retry. Without a DLQ the loss is silent.

- ❌ Rule targeting Lambda with no `DeadLetterConfig` and default retry; throttling beyond `MaximumEventAgeInSeconds` or a permissions error makes events vanish.
- ✅ Standard SQS DLQ on the target, explicit `MaximumRetryAttempts` / `MaximumEventAgeInSeconds`, alarms on `InvocationsSentToDlq` and `InvocationsFailedToBeSentToDlq`.
- Detection: `aws events list-targets-by-rule` shows targets missing `DeadLetterConfig`.

Source: [eb-rule-dlq](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html) (accessed 2026-08-28)

---

## A2 — Recursive / infinite-loop rules (HIGH)

A rule whose target re-emits an event matching the same rule fires again, causing runaway cost and throttling.

- ❌ Rule on S3 object-created events whose target rewrites the object ACL, producing another object event that re-matches.
- ✅ Narrow the pattern to exclude the self-generated event (marker attribute or different `detail-type`), or route the corrective action to a separate bus/rule that cannot re-match. Monitor `DeadLetterInvocations` (counts loop-suppressed invocations).
- Detection: abnormal growth of `Invocations` / `TriggeredRules`; Cost Anomaly Detection on EventBridge.

Source: [eb-event-patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html) (accessed 2026-08-28)

---

## A3 — Third-hop forwarding across accounts / buses / Regions (HIGH)

Events received from a sender and forwarded by a rule to a third account or bus are not delivered.

- ❌ Account A bus to Account B bus (rule forwards) to Account C bus. A-origin events never reach C; DLQ shows `THIRD_ACCOUNT_HOP_DETECTED` / `THIRD_REGION_HOP_DETECTED`.
- ✅ Account A publishes directly to the B and C buses (one hop each), or consumers read from a single hub bus.
- Detection: inspect DLQ messages for the hop codes; audit rules whose source and target are both cross-account/cross-bus.

Source: [eb-cross-account](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cross-account.html) (accessed 2026-08-28)

---

## A4 — `"account": ["*"]` or an over-broad bus policy (HIGH)

`*` in a rule's `account` field matches nothing, and a broad `events:PutEvents` grant allows event injection.

- ❌ Bus policy with Principal `"*"` and no `aws:SourceArn`/account condition; rules with `"account": ["*"]`.

```json
{ "account": ["*"] }
```

- ✅ Scope the policy to specific account IDs or an Org ID with `aws:SourceArn`; pin explicit IDs in every rule; require IAM roles for cross-account targets (since 2023-03-02).

```json
{ "account": ["111122223333"] }
```

- Detection: `aws events describe-event-bus --name <bus>` and review the policy for wildcard principals; scan patterns for a missing or `*` account field.

Sources: [eb-cross-account](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cross-account.html), [eb-use-resource-based](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html) (accessed 2026-08-28)

---

## A5 — FIFO SQS queue as a DLQ (MEDIUM)

Rules, Pipes stream-source DLQs and Scheduler DLQs support standard SQS queues only; a FIFO DLQ silently fails to capture.

- ❌ `DeadLetterConfig.Arn` pointing at `orders-dlq.fifo`.
- ✅ Standard SQS queue in the same Region; encode ordering metadata in the consumer if reprocessing order matters.
- Detection: audit `DeadLetterConfig` ARNs for a `.fifo` suffix; force a failure and confirm the message arrives.

Source: [eb-rule-dlq](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html) (accessed 2026-08-28)

---

## A6 — CMK bus that still depends on Schema Discovery (MEDIUM)

Schema Discovery does not support CMK-encrypted buses (requires an AWS-owned key). Events larger than 1000 KiB are silently not discovered.

- ❌ Enabling a CMK on a bus with a discoverer enabled and expecting the Discovered registry to keep updating.
- ✅ Bootstrap schemas on an AWS-owned-key bus first (or maintain custom schemas), then apply the CMK; attach a DLQ for encryption/decryption failures.
- Detection: bus `KmsKeyIdentifier` set while a discoverer is enabled; stale versions in the Discovered registry.

Sources: [eb-schemas-infer](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schemas-infer.html), [eb-encryption-event-bus-cmkey](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-encryption-event-bus-cmkey.html) (accessed 2026-08-28)
