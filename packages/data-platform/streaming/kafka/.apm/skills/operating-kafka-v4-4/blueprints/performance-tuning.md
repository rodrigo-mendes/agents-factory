# Performance tuning, Kafka 4.4.0

Back to [SKILL.md](../SKILL.md). S-ids resolve in the [Source Bibliography](./unverified-and-risks.md#source-bibliography). All defaults are for 4.4.0: re-check before applying to other versions. Broker defaults come from the broker config page (read 200000 of 201536 characters, register L1).

## Configuration reference

| Parameter | Scope | Default (4.4.0) | Recommended | Source |
|---|---|---|---|---|
| `num.network.threads` | broker | 3 | raise if NetworkProcessorAvgIdlePercent is below 0.3 | [S7][S14] |
| `num.io.threads` | broker | 8 | raise if RequestHandlerAvgIdlePercent is below 0.3 | [S7][S14] |
| `num.replica.fetchers` | broker | 1 | raise if follower lag grows (medium confidence) | [S7] |
| `num.recovery.threads.per.data.dir` | broker | 2 (was 1 before 4.0) | default | [S7][S1] |
| `socket.send.buffer.bytes`, `socket.receive.buffer.bytes` | broker | 102400 | larger for high-latency links | [S7][S19] |
| `log.flush.interval.messages`, `log.flush.interval.ms` | broker | Long.MAX, null | keep defaults (no application fsync) | [S7][S16] |
| `compression.type` | broker, topic | producer | producer | [S7][S27] |
| `message.max.bytes`, `max.message.bytes` | broker, topic | 1048588 | match producer `max.request.size` (1048576) | [S7][S27][S28] |
| `replica.fetch.max.bytes` | broker | 1048576 | at least `message.max.bytes` (medium confidence) | [S7] |
| `log.segment.bytes`, `segment.bytes` | broker, topic | 1073741824 | default | [S7][S27] |
| `log.retention.hours`, `retention.ms` | broker, topic | 168, 604800000 | per SLA | [S7][S27] |
| `log.retention.bytes`, `retention.bytes` | broker, topic | -1 | per disk budget | [S7][S27] |
| `cleanup.policy` | topic | delete | `compact` for keyed state topics | [S27] |
| `message.timestamp.after.max.ms` | topic | 3600000 (1 hour) | default; broker-page conflict is (medium confidence), U6 | [S27][S1] |
| Producer `linger.ms` | client | 5 | 5 to 100 for throughput (medium confidence) | [S28] |
| Producer `batch.size` | client | 16384 | larger trades latency for throughput (medium confidence) | [S28] |
| Producer `delivery.timeout.ms` | client | 120000 | at least `request.timeout.ms` + `linger.ms` | [S28] |
| Consumer `enable.auto.commit` | client | true | false for at-least-once with manual commit | [S29] |
| Consumer `isolation.level` | client | read_uncommitted | read_committed for exactly-once | [S29][S15] |
| Consumer `group.protocol` | client | classic | `consumer` when all clients support it (medium confidence) | [S29][S1] |

## Procedure

1. Read the idle-percent metrics ([observability](./observability.md)). Raise `num.network.threads` or `num.io.threads` only when the matching idle ratio stays below 0.3 [S14].
2. Change one parameter at a time and compare produce and fetch `TotalTimeMs` p99 with the baseline.
3. For producers, raise `linger.ms` and `batch.size` together, and keep `compression.type` consistent (producer-side compression is the default path).
4. Keep flush defaults. Durability comes from replication, not fsync [S16][S15].

## JVM

Typical arguments from the Java page [S17]: `-Xmx6g -Xms6g -XX:MetaspaceSize=96m -XX:+UseG1GC -XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=35 -XX:G1HeapRegionSize=16M -XX:MinMetaspaceFreeRatio=50 -XX:MaxMetaspaceFreeRatio=80 -XX:+ExplicitGCInvokesConcurrent`.

In Compose, pass them through `KAFKA_HEAP_OPTS` and `KAFKA_JVM_PERFORMANCE_OPTS`. These variable names are (unverified) on the pages read, U3. Java 17, 21 and 25 are fully supported; 25 is recommended on the Java page as of 2026-11-04 [S17]. The image's bundled JRE is (unverified), U3.

## OS and disks

- Kafka uses free memory as page cache; size it to about 30 seconds of writes [S16]. See [capacity-sizing](./capacity-sizing.md).
- Use multiple drives; disk throughput is usually the bottleneck. XFS is preferred over ext4, `noatime` is safe. RAID costs write throughput, and rebuilds can effectively disable a server [S16].
- A Compose host shares disks across all brokers, which limits throughput (medium confidence, M12).
- At least 100000 file descriptors (medium confidence, M19). Each partition needs at least 2 memory map areas, so check `vm.max_map_count` (about 65535 default) on hosts with many partitions [S16].

## Quotas

```bash
kafka-configs.sh --bootstrap-server kafka-1:19092 --alter \
  --add-config 'producer_byte_rate=1048576,consumer_byte_rate=2097152,request_percentage=50' \
  --entity-type users --entity-name alice --entity-type clients --entity-name app-1
```

Source: [S12][S15]. The numeric values are placeholders, not recommendations.

## Verification

```bash
kafka-topics.sh --bootstrap-server kafka-1:19092 --describe --topic orders
# Expected: partition leaders spread across brokers; no partition with Isr smaller than min.insync.replicas
```
