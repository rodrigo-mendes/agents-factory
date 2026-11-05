# Observability and operations, Kafka Connect 4.4.0

Back to [SKILL.md](../SKILL.md). Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [administration](https://kafka.apache.org/44/kafka-connect/administration/), [monitoring](https://kafka.apache.org/44/operations/monitoring/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/). All read 2026-11-04 (monitoring page 157611 of 157611 characters). Representative commands; adapt to your environment.

## Connector and task states

States from the administration page: `UNASSIGNED`, `RUNNING`, `PAUSED`, `STOPPED` (connector only), `FAILED`, `RESTARTING`. `GET /connectors/{name}/status` returns connector and task states and the `worker_id`.

## REST operations

| Call | Effect |
|---|---|
| `GET /` | version, commit, Kafka cluster ID |
| `GET /connector-plugins` | plugins visible to the worker |
| `PUT /connector-plugins/{type}/config/validate` | validate a config before creating |
| `POST /connectors/{name}/restart?includeTasks=true&onlyFailed=true` | both flags default `false`. A restart during a rebalance returns HTTP 409 |
| `PUT /connectors/{name}/pause` | state kept across cluster restarts |
| `PUT /connectors/{name}/stop` | shuts tasks down and releases resources |
| `PATCH /connectors/{name}/config` | a `null` value removes a key |
| `GET`, `DELETE`, `PATCH /connectors/{name}/offsets` | KIP-875. `DELETE` and `PATCH` need a stopped connector |
| `GET`, `PUT /admin/loggers/{name}` | change log levels (KIP-495) |
| `GET /connectors/{name}/topics`, `PUT .../topics/reset` | topic tracking. Disable with `topic.tracking.enable=false`, block resets with `topic.tracking.allow.reset=false` |
| `DELETE /connectors/{name}` | removes the connector. Whether stored offsets are removed is (unverified) |

Resuming a stopped connector with `PUT /connectors/{name}/resume` is implied by the administration page, not stated (medium confidence).

```bash
curl -X PUT    http://localhost:8083/connectors/orders-src/stop
curl -X DELETE http://localhost:8083/connectors/orders-src/offsets
curl -X PUT    http://localhost:8083/connectors/orders-src/resume
```

## Metrics (JMX)

| MBean | Attributes |
|---|---|
| `kafka.connect:type=connect-worker-metrics` | `connector-count`, `task-count`, `connector-startup-failure-total`, `task-startup-failure-total`, per connector `connector-failed-task-count`, `connector-unassigned-task-count` |
| `kafka.connect:type=connect-worker-rebalance-metrics` | `rebalancing`, `completed-rebalances-total`, `rebalance-max-time-ms`, `time-since-last-rebalance-ms` |
| `kafka.connect:type=connector-metrics,connector=...` | `status` |
| `kafka.connect:type=connector-task-metrics,...` | `status`, `offset-commit-failure-percentage`, `batch-size-avg` |
| `kafka.connect:type=sink-task-metrics,...` | `sink-record-lag-max`, `put-batch-max-time-ms`, `offset-commit-skip-total` |
| `kafka.connect:type=source-task-metrics,...` | `source-record-poll-rate`, `source-record-write-rate`, `source-record-active-count`, `transaction-size-avg` |
| `kafka.connect:type=task-error-metrics,...` | `total-record-errors`, `total-record-failures`, `total-records-skipped`, `deadletterqueue-produce-requests`, `deadletterqueue-produce-failures`, `last-error-timestamp` |

A worker also exposes all producer and consumer metrics. `metric.reporters` defaults to JmxReporter. Remote JMX is off by default and is enabled with `JMX_PORT`. JMX authentication is off by default, so production should set security through `KAFKA_JMX_OPTS`.

## Alert thresholds

The docs give no thresholds (unverified). A common choice, not from the docs, is to alert when the failed task count is above 0, when `deadletterqueue-produce-failures` is above 0, or when `rebalancing` stays true (unverified).

## Performance knobs

`tasks.max` is the parallelism ceiling (default 1); a connector may create fewer tasks. `offset.flush.interval.ms` defaults to 60000 (the sample file uses 10000 for testing). `offset.flush.timeout.ms` defaults to 5000. `task.shutdown.graceful.timeout.ms` defaults to 5000. The incremental cooperative rebalance (default since 2.3.0) moves only affected tasks. `scheduled.rebalance.max.delay.ms` (default 300000) gives a departed worker 5 minutes to return before its tasks are reassigned.

## Verification commands

```bash
curl -s http://localhost:8083/
# Expected: JSON with the version 4.4.0, a commit and a Kafka cluster ID (field names unverified)

curl -s http://localhost:8083/connector-plugins
# Expected: list containing the FileStreamSink connector class (class name unverified)

curl -s -X PUT -H 'Content-Type: application/json' \
  http://localhost:8083/connector-plugins/FileStreamSink/config/validate \
  -d '{"connector.class":"FileStreamSink","topics":"orders","tasks.max":"1"}'
# Expected: an error count of 0 (response field names unverified)

curl -s http://localhost:8083/connectors/orders-file-sink/status
# Expected: connector and task state RUNNING

bin/connect-plugin-path.sh list --plugin-path /opt/connect-plugins
# Expected: plugins listed. Under hybrid_warn look for WARN lines in the worker log
```

No official test harness for connectors or SMTs appears in the 4.4 pages read (unverified). Unit-testing an SMT by calling `configure()` and `apply()` on a `SinkRecord`, and integration tests against a disposable Compose broker plus worker, are representative approaches that are not official (unverified).
