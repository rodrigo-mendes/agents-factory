# Performance tuning, Kafka 3.9.2

Back to [SKILL.md](../SKILL.md). Sources read 2026-11-04: [Java](https://kafka.apache.org/39/operations/java-version/), [hardware](https://kafka.apache.org/39/operations/hardware-and-os/), [broker configs](https://kafka.apache.org/39/configuration/broker-configs/), [producer configs](https://kafka.apache.org/39/configuration/producer-configs/), [consumer configs](https://kafka.apache.org/39/configuration/consumer-configs/), [monitoring](https://kafka.apache.org/39/operations/monitoring/), [basic operations](https://kafka.apache.org/39/operations/basic-kafka-operations/). Values from a single page are tagged (medium confidence, M10).

## JVM

Typical arguments from the Java page: `-Xmx6g -Xms6g -XX:MetaspaceSize=96m -XX:+UseG1GC -XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=35 -XX:G1HeapRegionSize=16M -XX:MinMetaspaceFreeRatio=50 -XX:MaxMetaspaceFreeRatio=80 -XX:+ExplicitGCInvokesConcurrent`. In Compose, pass them through `KAFKA_HEAP_OPTS` and `KAFKA_JVM_PERFORMANCE_OPTS`. That the start scripts read these variables is (medium confidence, M7). Java 17 or 21 ([always-do](./always-do-patterns.md#10-java-17-or-21)).

## Operating system (hardware page, medium confidence, M10)

- At least 100000 file descriptors (`ulimits: nofile`). Each log segment uses 2 map areas, so check `vm.max_map_count` (often about 65535 by default).
- Use multiple drives and do not share them with OS or application logs. XFS gave better latency than ext4 (160 ms against 250 ms or more). `noatime` is safe. RAID costs write throughput and rebuilds can effectively disable a server.
- Keep the flush defaults: application fsync is disabled (`log.flush.interval.messages` is the maximum long).

## Broker threads

| Setting | Default | Guidance |
|---|---|---|
| `num.network.threads` | 3 | Tune against `NetworkProcessorAvgIdlePercent`, keep above 0.3 |
| `num.io.threads` | 8 | Tune against `RequestHandlerAvgIdlePercent`, keep above 0.3 |
| `num.replica.fetchers` | 1 | Raise when follower lag grows. The threshold is (unverified, U31) |
| `zookeeper.session.timeout.ms` | 18000 | Keep. Tuning guidance is (unverified, U31) |
| `log.segment.bytes` | 1073741824 | Keep |
| `message.max.bytes` | 1048588 | Keep unless records are large |

## Producer and consumer

- Producer defaults in 3.9: `linger.ms` 0 (4.0 changed it to 5, see `operating-kafka-v4-4`), `batch.size` 16384, `compression.type` none, `acks=all`, `enable.idempotence=true`, `delivery.timeout.ms` 120000. Raise `linger.ms` and `batch.size` for throughput at the cost of latency (guidance not stated as a number on the page, unverified, U31).
- Consumer: `enable.auto.commit` defaults to `true` every 5000 ms, `isolation.level` to `read_uncommitted`.
- Idempotence requires `acks=all`, `retries` above 0 and `max.in.flight.requests.per.connection` at most 5. With conflicting settings it is silently disabled if it was not set explicitly and throws `ConfigException` if it was.
- Transactions need at least 3 brokers by default (`transaction.state.log.replication.factor`), and `transaction.timeout.ms` is 60000.

## Delivery guarantees

| Guarantee | Producer | Consumer |
|---|---|---|
| At-most-once | `acks=0`, or commit before processing | commit offset before processing |
| At-least-once (default) | `acks=all`, idempotence on, retries bounded by `delivery.timeout.ms` | `enable.auto.commit=false`, commit after processing |
| Exactly-once | `transactional.id` set (implies idempotence) | `isolation.level=read_committed`, `enable.auto.commit=false` |

Sources: producer configs, consumer configs, design (three pages).

## Quotas

By default clients have unlimited quota. Set `producer_byte_rate`, `consumer_byte_rate` and `request_percentage` per user and/or client-id with `kafka-configs.sh` ([basic operations](https://kafka.apache.org/39/operations/basic-kafka-operations/), [design](https://kafka.apache.org/39/design/design/)).

## ZooKeeper tuning

Heap, `initLimit` for large snapshots, and the dedicated `dataLogDir` are in [zookeeper-ensemble](./zookeeper-ensemble.md). `maxClientCnxns` value is (unverified, U31).

Sizing numbers: [capacity-sizing](./capacity-sizing.md).
