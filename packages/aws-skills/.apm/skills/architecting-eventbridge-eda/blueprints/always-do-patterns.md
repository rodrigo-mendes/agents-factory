# Always-Do Patterns — AWS EventBridge EDA (2026)

Full detail for the 6 mandatory patterns summarised in SKILL.md.
Source research: `workspace/docs/research_cloud_AWS_EventBridge_EDA_2026.md` (research date 2026-08-28).

---

## M1 — DLQ + explicit retry policy on every production target

**Pillar**: Reliability

- EventBridge retries retriable failures for up to 24 h / 185 attempts with exponential backoff and jitter; after that the event is dropped.
- Permanent errors (missing permissions, deleted target, DNS failure) get no retry and go straight to the DLQ, or are lost if none exists.
- DLQ must be a **standard** SQS queue in the same Region. FIFO is not supported.
- Set `MaximumRetryAttempts` (0-185) and `MaximumEventAgeInSeconds` (60-86400) per target SLA; do not accept defaults.
- With `PutTargets` or a cross-account DLQ, attach the SQS policy manually: principal `events.amazonaws.com`, action `sqs:SendMessage`, condition `aws:SourceArn` = rule ARN (the console does this automatically).

```bash
aws events list-targets-by-rule --rule <rule-name> --event-bus-name <bus-name> \
  --query 'Targets[*].{Id:Id,DLQ:DeadLetterConfig.Arn,Retry:RetryPolicy}'
# Expected: every target has a non-null DLQ Arn and RetryPolicy
```

Alarm on `InvocationsFailedToBeSentToDlq` (any datapoint = event lost even with a DLQ).
Trade-off: one queue per target to operate and drain; minor cost.

Sources: [eb-rule-dlq](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html) (accessed 2026-08-28); [eb-rule-retry-policy](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html) (accessed 2026-08-28)

---

## M2 — Idempotent consumers (at-least-once, unordered)

**Pillar**: Reliability

- EventBridge and Scheduler are at-least-once with no fleet-wide ordering; archive replay processes in one-minute buckets, out of order.
- Derive an idempotency key from the event id or a stable business key.
- Record it in DynamoDB with a conditional write (`attribute_not_exists`) and a TTL; skip keys already seen.
- For ordering-sensitive flows use Pipes with an ordered source (Kinesis / DynamoDB Streams), which preserves source order end-to-end. Alternative: carry a sequence/version attribute and discard stale updates.

Verification: send deliberate duplicate `PutEvents`; confirm single-effect processing and one dedupe row per business key.
Trade-off: extra DynamoDB read/write per event; key design effort; TTL tuning.

Sources: [what-is-scheduler](https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html) (accessed 2026-08-28); [eb-archive](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html) (accessed 2026-08-28)

---

## M3 — Scope cross-account ingestion

**Pillar**: Security

- Pin explicit account IDs in the `account` field of every rule that consumes cross-account events. `"*"` matches nothing; it is not a wildcard.
- On the receiver bus grant `events:PutEvents` only to specific account IDs or an Organization ID, guarded with `aws:SourceArn`.
- Senders attach an IAM role trusted by `events.amazonaws.com`. Cross-account targets created after 2023-03-02 require an IAM role.

```json
{ "account": ["111122223333", "444455556666"], "source": ["com.example.orders"] }
```

```bash
aws events describe-event-bus --name <bus-name> --query 'Policy'
# Expected: scoped principals + conditions; no Principal "*"
```

Trade-off: policy maintenance grows with the account count.

Sources: [eb-cross-account](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cross-account.html) (accessed 2026-08-28); [eb-use-resource-based](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html) (accessed 2026-08-28)

---

## M4 — Server-side filtering in rule patterns / Pipe FilterCriteria

**Pillar**: Cost Optimization, Performance Efficiency

- Patterns (prefix, suffix, numeric, cidr, wildcard, anything-but, `$or`, exists) are evaluated at no extra cost; unmatched events never invoke or bill a target.
- In Pipes you pay only for events that match the filter, and filtering happens before enrichment.
- Limits: pattern <= 2,048 characters; max 30 wildcard rules per bus (hard); `$or` combinations < 1,000 (else `InvalidEventPatternException`). Wildcard matching is bus-rule-only, not Pipes.

```bash
aws events test-event-pattern --event-pattern file://pattern.json --event file://sample-event.json
# Expected: {"Result": true}
```

Monitor `MatchedEvents` vs `Invocations` to confirm the filter ratio.

Sources: [eb-create-pattern-operators](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-pattern-operators.html) (accessed 2026-08-28); [eb-pipes-event-filtering](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes-event-filtering.html) (accessed 2026-08-28)

---

## M5 — EventBridge Scheduler (not scheduled rules) for time-based work

**Pillar**: Operational Excellence

- AWS labels scheduled event-bus rules a "legacy feature".
- Scheduler adds one-time schedules, per-schedule IANA time zones with automatic DST, flexible windows, per-schedule retry + DLQ, 270+ targets, 10,000,000 schedules per Region.
- Set `ActionAfterCompletion=DELETE` on one-time schedules; completed ones keep consuming quota until deleted.
- Target input is capped at 256 KB. Schedule groups default to 500 per Region.
- Universal target ARN pattern: `arn:aws:scheduler:::aws-sdk:{service}:{apiAction}`.

```bash
aws scheduler get-schedule --name <schedule-name> --group-name <group-name> \
  --query '{Retry:RetryPolicy,DLQ:DeadLetterConfig.Arn,After:ActionAfterCompletion}'
```

Sources: [eb-rules](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rules.html) (accessed 2026-08-28); [what-is-scheduler](https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html) (accessed 2026-08-28)

---

## M6 — CMK encryption for sensitive buses, paired with a DLQ

**Pillar**: Security

- CMK coverage: buses (GA 2024-05-14), archives/replay (2025-04), filter patterns and input transformers (2025-09-17).
- AWS strongly recommends a DLQ on encrypted buses: encryption/decryption failures route to the DLQ instead of being dropped.
- Key policy: allow `events.amazonaws.com` `kms:DescribeKey`, `kms:GenerateDataKey`, `kms:Decrypt`, constrained by encryption context `kms:EncryptionContext:aws:events:event-bus:arn` = bus ARN and `aws:SourceArn`.
- Schema Discovery is unsupported on CMK buses (needs an AWS-owned key).

```bash
aws events describe-event-bus --name <bus-name> --query 'KmsKeyIdentifier'
# Expected: CMK ARN when encryption is required
```

Monitor `EventBusEncryptionFailed` (emitted only when non-zero) and CloudTrail KMS events.
Trade-off: KMS request cost, key governance, loss of Schema Discovery on that bus.

Sources: [eb-encryption-event-bus-cmkey](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-encryption-event-bus-cmkey.html) (accessed 2026-08-28); [What's New 2024-05](https://aws.amazon.com/about-aws/whats-new/2024/05/amazon-eventbridge-cmk-event-buses/) (accessed 2026-08-28; source dated 2024-05, verify currency)
