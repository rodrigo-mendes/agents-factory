# Pillar: alarms

Back to [SKILL.md](../SKILL.md). Scripts: `scripts/check-alarms.py` (read-only) and `scripts/trigger-alarm-test.py` (mutating, approval flag). AWS CLI 2.39.0 reference and CloudWatch and SNS docs read 2026-10-28. The manual `bash` forms below use `jq`; the Python scripts do not.

## Contents

- [Assertion chain](#assertion-chain)
- [Commands and JSON paths](#commands-and-json-paths)
- [State rules](#state-rules)
- [SNS subscriptions](#sns-subscriptions)
- [The approval-gated trigger test](#the-approval-gated-trigger-test)
- [Script behaviour](#script-behaviour)

## Assertion chain

1. `describe-alarms` with explicit `--alarm-types MetricAlarm CompositeAlarm` returns every alarm of the selection.
2. Per alarm: `ActionsEnabled` is true and `AlarmActions` is not empty.
3. State is `OK`; `INSUFFICIENT_DATA` is inconclusive; `ALARM` fails.
4. Each SNS topic in `AlarmActions` has at least one subscription and none pending.
5. Optional, approval-gated: the alarm action actually runs ([trigger test](#the-approval-gated-trigger-test)).

## Commands and JSON paths

| Step | Command | Read |
|---|---|---|
| describe | `cloudwatch describe-alarms --alarm-name-prefix P` or `--alarm-names A B` (max 100) `--alarm-types MetricAlarm CompositeAlarm` | `.MetricAlarms[]`, `.CompositeAlarms[]` |
| fields | | `AlarmName`, `StateValue` (`OK`, `ALARM`, `INSUFFICIENT_DATA`), `ActionsEnabled`, `AlarmActions[]`, `OKActions[]`, `InsufficientDataActions[]`, `StateReason`, `StateUpdatedTimestamp`, `TreatMissingData` (`breaching`, `notBreaching`, `ignore`, `missing`), `EvaluationState` |
| subscriptions | `sns list-subscriptions-by-topic --topic-arn ARN` | `.Subscriptions[].SubscriptionArn`, `.Protocol`, `.Endpoint` |
| history | `cloudwatch describe-alarm-history --alarm-name A --history-item-type Action --start-date T0` | `.AlarmHistoryItems[]`, `.HistoryItemType`, `.HistorySummary`, `.HistoryData` (JSON string) |

- `--alarm-name-prefix` cannot be combined with `--alarm-names`; without `--alarm-types` only metric alarms are returned ([describe-alarms](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/describe-alarms.html)).
- Composite alarms carrying the same `ActionsEnabled` and `AlarmActions` fields is (medium confidence).
- Alarm history retention is (unverified).

```bash
aws --output json cloudwatch describe-alarms --alarm-name-prefix "$P" --alarm-types MetricAlarm CompositeAlarm \
    | jq -c '.MetricAlarms[] | {n:.AlarmName, s:.StateValue, e:.ActionsEnabled, a:(.AlarmActions|length)}'
aws --output json sns list-subscriptions-by-topic --topic-arn "$TOPIC_ARN" | jq -c '[.Subscriptions[] | {p:.Protocol, arn:.SubscriptionArn}]'
```

## State rules

`INSUFFICIENT_DATA` means the alarm has just started, the metric is not available, or there is not enough data; alarms with a period of 1 minute or more are evaluated every minute ([alarm evaluation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarm-evaluation.html)). The scripts report it as WARN by default and as FAIL with `--fail-on-insufficient-data` (repo choice). Never print subscriber endpoints.

## SNS subscriptions

`list-subscriptions-by-topic` returns 100 subscriptions per call, paginated ([API](https://docs.aws.amazon.com/sns/latest/api/API_ListSubscriptionsByTopic.md)). An unconfirmed subscription shows as `PendingConfirmation` ([confirming a subscription](https://docs.aws.amazon.com/sns/latest/dg/SendMessageToHttp.confirm.html)); that page states it for the console, so the same value in CLI output is (medium confidence). The script fails on a pending subscription and on a topic without subscriptions. The topic Region is the fourth field of the ARN and is used for the call.

## The approval-gated trigger test

`cloudwatch set-alarm-state --alarm-name A --state-value ALARM --state-reason R` temporarily sets the state; when the state differs, the configured action runs, and `ALARM` sends an SNS message to real subscribers. The output is `None` ([reference](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/set-alarm-state.html)). Metric alarms return to their actual state quickly, often within seconds, visible in the History tab or `describe-alarm-history`; a composite alarm is not guaranteed to return until a child alarm changes state. `CloudWatchReadOnlyAccess` does not grant `SetAlarmState`.

Protocol (decision [K1](./ask-first-decisions.md#k1-set-alarm-state-notification-test)):

1. Ask the user, through the orchestrator, per run, naming the alarm and the audience.
2. Only with the relayed approval run `python3 scripts/trigger-alarm-test.py --alarm-name A --i-have-user-approval`.
3. The script refuses without the flag (exit 2, no AWS call), refuses composite alarms without `--allow-composite`, refuses an alarm already in `ALARM` (the state would not change, so no action runs; exit 2, nothing sent), and sends nothing if `ActionsEnabled` is false or `AlarmActions` is empty.
4. It records `T0` (epoch seconds), sends the state, then polls `describe-alarm-history --alarm-types MetricAlarm|CompositeAlarm --history-item-type Action --start-date T0` until an Action item appears or `--wait-seconds` (default 60) passes; no item is FAIL. The `--alarm-types` flag on this command is (unverified) (register U9): on CLI exit 252 the script warns and repeats the call without it, which covers metric alarms only. If a CLI error (exit 3) follows `set-alarm-state`, the script prints a RECOVERY line: read the state with `check-alarms.py`; a metric alarm returns by itself; forcing it back needs its own user approval.
5. Afterwards run `check-alarms.py` to confirm the alarm is back in its actual state.

## Script behaviour

`check-alarms.py (--alarm-prefix P | --alarm-names A,B)` prints `alarm.<name>.actions`, `alarm.<name>.state`, `sns.<topic>`. No alarm matching a prefix, a named alarm not found, a disabled or empty action list, `ALARM` state, a topic without subscriptions or with a pending one: FAIL. `INSUFFICIENT_DATA`: WARN. Alarm references that come from a dashboard are checked by [pillar dashboards](./pillar-dashboards.md).
