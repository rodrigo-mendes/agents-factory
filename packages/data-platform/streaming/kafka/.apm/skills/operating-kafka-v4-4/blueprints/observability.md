# Observability, KPIs and runbooks, Kafka 4.4.0

Back to [SKILL.md](../SKILL.md). S-ids resolve in the [Source Bibliography](./unverified-and-risks.md#source-bibliography). The monitoring page was read 100000 of 157611 characters (register L2).

## Exposure

- Metrics are exposed over JMX: Yammer for the server, Kafka Metrics for clients. Remote JMX is off by default and enabled with `JMX_PORT` or `KAFKA_JMX_OPTS` [S14].
- Secure remote JMX through `KAFKA_JMX_OPTS` (authentication and TLS) before publishing the port [S14]. The exact JVM flags are standard JDK flags (medium confidence).
- The 4.4 monitoring page names no Prometheus exporter. Any JMX-to-Prometheus bridge is third-party and its 4.4 compatibility is (unverified, U16).
- KIP-1291 adds Linux I/O metrics over JMX in 4.4 [S23]. Exact names are (unverified), U10.

## KPI table

| Metric | Scope | Normal | Alert |
|---|---|---|---|
| `kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions` | broker | 0 [S14] | above 0 sustained (medium confidence) |
| `kafka.server:type=ReplicaManager,name=UnderMinIsrPartitionCount` | broker | 0 [S14] | above 0: acks=all producers fail |
| `kafka.controller:type=KafkaController,name=OfflinePartitionsCount` | controller | 0 (medium confidence) | above 0 |
| `kafka.controller:type=KafkaController,name=ActiveControllerCount` | controller | exactly one node reports 1 [S14] | cluster sum not 1 |
| `kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec` | controller | 0 [S14] | above 0 |
| `kafka.controller:type=KafkaController,name=FencedBrokerCount` | controller | 0 (medium confidence) | above 0 |
| `kafka.server:type=raft-metrics` (current-state, high-watermark, commit-latency-avg/max) | broker, controller | leader, follower or observer; -1 is unknown [S14] | state unknown or rising latency (unverified threshold) |
| `kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent` | broker | above 0.3 [S14] | below 0.3 |
| `kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent` | broker | above 0.3 [S14] | below 0.3 |
| `IsrShrinksPerSec` / `IsrExpandsPerSec` | broker | 0 except around restarts [S14] | sustained above 0 |
| `kafka.server:type=ReplicaFetcherManager,name=MaxLag,clientId=Replica` | broker | proportional to max produce batch [S14] | growing |
| `BytesInPerSec`, `BytesOutPerSec`, `MessagesInPerSec` | broker, topic | baseline [S14] | deviation from baseline |
| `kafka.network:type=RequestMetrics,name=TotalTimeMs,request=Produce` or `FetchConsumer` | broker | baseline [S14] | p99 above your SLO (unverified threshold) |
| Consumer lag: `kafka-consumer-groups.sh --describe` LAG, client `records-lag-max` | group | near 0, bounded [S12][S14] | above the per-group SLO |
| MM2 `replication-latency-ms`, `record-age-ms` | MM2 | baseline [S13] | above your RPO |

Alert thresholds beyond the value 0 are (unverified), U9: set them from your own baseline. The RPO link to `replication-latency-ms` is an inference (medium confidence).

## Lag commands

```bash
bin/kafka-consumer-groups.sh --bootstrap-server kafka-1:19092 --describe --group my-group
# LAG = log-end offset minus committed offset [S12]. Client records-lag-max uses the current position, not the committed offset [S14].
```

## Runbook: disk full on a broker volume

- Detect: `df -h` inside the container on the log dir; rising `BytesInPerSec` against capacity [S14].
- Respond: lower retention on the largest topics: `kafka-configs.sh --bootstrap-server kafka-1:19092 --entity-type topics --entity-name <t> --alter --add-config retention.ms=<lower>` [S12].
- Recover: expand the volume, or move partitions with `kafka-reassign-partitions.sh --execute --throttle <bytes/s>`, then `--verify` to remove the throttle [S12].
- Prevent: set `retention.bytes` [S27]; size disks by the heuristic in [capacity-sizing](./capacity-sizing.md).

## Runbook: consumer lag spike or poison pill

- Detect: the LAG column grows [S12]; client `records-lag-max` [S14].
- Respond: scale consumers up to the partition count. For share groups configure a dead-letter queue (`errors.deadletterqueue.topic.name`, needs `share.version` 2 or higher) [S12].
- Recover: for consumer groups skip a bad offset with `--reset-offsets --shift-by 1 --execute` while the group is inactive [S12].
- Prevent: lag alerts per group, plus an application-level DLQ for classic consumer groups (a pattern, not a broker feature).

## Runbook: startup failure after the 4.4 upgrade (OAUTHBEARER JWKS)

- Trigger: a JWKS URL is set without `sasl.oauthbearer.expected.audience` and `sasl.oauthbearer.expected.issuer`, or one of the allow-unverified flags [S1][S10].
- Detect: the broker exits at startup; read the container logs. The exact message is (unverified, U17).
- Recover: set both properties and restart. Prevent: read the 4.4 upgrade notes before rolling.

## Runbook: older broker refuses a directory (KIP-1170)

- Trigger: a directory formatted with the 4.4 `kafka-storage` tool is started by an older broker [S1].
- Detect: the older broker refuses the directory. The exact message is (unverified, U17).
- Recover: run a broker equal to or newer than the formatting tool.
