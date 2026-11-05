# Observability, Kafka Streams 4.4.0

Back to [SKILL.md](../SKILL.md). Source for the metric names: [Streams monitoring section](https://kafka.apache.org/44/operations/monitoring/) (read 2026-11-04, 157611 of 157611 characters, two reads). Recording level is set with `metrics.recording.level` (default INFO, [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/)).

## Documentation warnings

The 4.4 monitoring page lists some ratio metrics under the wrong MBean (documentation errors). Verify an MBean name against a running app (JMX) before building a dashboard on it. The memory-management page names the stale key `cache.max.bytes.buffering`; use `statestore.cache.max.bytes` (see [scaling and rebalancing](./scaling-and-rebalancing.md#memory)).

## Metrics by level

| Scope | MBean | Metrics (level) |
|---|---|---|
| Client | `kafka.streams:type=stream-metrics,client-id=...` | `state`, `client-state`, `alive-stream-threads`, `failed-stream-threads` (INFO) |
| Thread | `kafka.streams:type=stream-thread-metrics,thread-id=...` | `process-rate`, `process-latency-*`, `commit-latency-*`, `poll-ratio`, `process-ratio`, `blocked-time-ns-total` (INFO) |
| Task | task-level MBean | `dropped-records-rate`, `dropped-records-total`, `active-process-ratio` (INFO); `record-lateness-avg`, `record-lateness-max` (DEBUG) |
| Processor node | processor-node MBean | `record-e2e-latency-avg`, `-max`, `-min` (INFO) |
| State store | state-store MBean | put/get/range latency (DEBUG); `num-open-iterators`, `oldest-iterator-open-since-ms` |
| RocksDB | state-store MBean | `block-cache-usage`, `estimate-num-keys`, `estimate-pending-compaction-bytes`, `background-errors` (INFO) |
| Consumer lag | consumer client metrics | `records-lag-max` |

`number-open-files` always reports -1 since the RocksDB upgrade in 4.0 ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/)).

## Alert candidates

The monitoring page names no Streams metric to alert on. Thresholds are (unverified, U8). Candidates from factory practice, to set from your own baseline:

- `failed-stream-threads` above 0
- `dropped-records-rate` above 0
- client `state` not RUNNING
- rising `records-lag-max`
- `oldest-iterator-open-since-ms` growing (a leaked iterator, see [never-do-patterns](./never-do-patterns.md))

## Verification

```bash
# Representative. Adapt to your environment
bin/kafka-streams-groups.sh --bootstrap-server localhost:9092 --describe --group orders-agg --offsets
# Expected (streams protocol): group listed with committed offsets per input partition
# JMX: read kafka.streams:type=stream-metrics,client-id=<id> attribute state
# Expected: RUNNING after a rolling restart
```
