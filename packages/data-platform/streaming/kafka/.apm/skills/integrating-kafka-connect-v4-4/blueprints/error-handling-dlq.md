# Error handling and dead letter queue, Kafka Connect 4.4.0

Back to [SKILL.md](../SKILL.md). Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/), [monitoring](https://kafka.apache.org/44/operations/monitoring/). All read 2026-11-04. Representative code; adapt to your environment.

## Defaults are fail fast

| Key | Default |
|---|---|
| `errors.tolerance` | `none` |
| `errors.retry.timeout` | 0 (-1 retries forever) |
| `errors.retry.delay.max.ms` | 60000 |
| `errors.log.enable` | false |
| `errors.log.include.messages` | false |
| `errors.deadletterqueue.topic.name` | empty |
| `errors.deadletterqueue.topic.replication.factor` | 3 |
| `errors.deadletterqueue.context.headers.enable` | false (headers start with `__connect.errors.`) |

The DLQ keys exist in the sink connector section of the configs page only. The source section has no DLQ keys.

## Tradeoff

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `errors.tolerance=none` | No silent data loss, task fails visibly | One bad record stops the task | Strict correctness pipelines |
| `all` with DLQ | Pipeline keeps flowing, bad records kept | Needs a DLQ topic, Write ACL on it, DLQ monitoring | Sinks with occasional malformed records |
| `all` without DLQ | Throughput | Bad records are skipped and lost, counted in `total-records-skipped` | Rarely acceptable; ask the user |

Ask: "Are skipped records acceptable, and who drains the DLQ?"

## Sink connector with DLQ

```json
{
  "errors.tolerance": "all",
  "errors.retry.timeout": "300000",
  "errors.deadletterqueue.topic.name": "dlq.orders-sink",
  "errors.deadletterqueue.topic.replication.factor": "3",
  "errors.deadletterqueue.context.headers.enable": "true",
  "errors.log.enable": "true",
  "errors.log.include.messages": "false"
}
```

Keep `errors.log.include.messages` at `false`: `true` logs key, value and headers and may expose sensitive data.

## Secured cluster

The worker needs Write on the DLQ topic when one is set ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/)).

## Metrics to watch

From the `kafka.connect:type=task-error-metrics` group: `total-record-errors`, `total-record-failures`, `total-records-skipped`, `deadletterqueue-produce-requests`, `deadletterqueue-produce-failures`, `last-error-timestamp`. Alert thresholds are not given by the docs (unverified). See [observability](./observability.md).

## Verify

```bash
curl -s http://localhost:8083/connectors/orders-sink/status
# Expected: connector and task state RUNNING
```
