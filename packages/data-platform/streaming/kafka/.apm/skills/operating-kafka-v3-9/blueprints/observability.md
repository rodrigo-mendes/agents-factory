# Observability and KPIs, Kafka 3.9.2

Back to [SKILL.md](../SKILL.md). Source for metric names and normal values: [monitoring](https://kafka.apache.org/39/operations/monitoring/) (read in full 2026-11-04, 121233 characters). ZooKeeper metrics: [Admin Guide](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html). Alert thresholds without a source are (unverified, U11).

## Metrics

| Metric (JMX) | Scope | Normal | Alert |
|---|---|---|---|
| `kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions` | broker | 0 | above 0 sustained (duration unverified, U11) |
| `kafka.server:type=ReplicaManager,name=UnderMinIsrPartitionCount` | broker | 0 | above 0 (producers with `acks=all` fail) |
| `kafka.server:type=ReplicaManager,name=AtMinIsrPartitionCount` | broker | 0 | above 0 means one more failure blocks writes (inferred, unverified, U30) |
| `kafka.controller:type=KafkaController,name=ActiveControllerCount` | controller | exactly one node reports 1 | sum across the cluster not 1 |
| `kafka.controller:type=KafkaController,name=OfflinePartitionsCount` | controller | 0 (page states none, unverified, U11) | above 0 |
| `kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec` | controller | 0 | above 0 |
| `kafka.server:type=ReplicaManager,name=IsrShrinksPerSec` / `IsrExpandsPerSec` | broker | 0 except during a broker failure | sustained above 0 |
| `kafka.server:type=ReplicaFetcherManager,name=MaxLag,clientId=Replica` | broker | proportional to the max produce batch | growing |
| `kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent` | broker | above 0.3 ideal | below 0.3 |
| `kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent` | broker | above 0.3 ideal | below 0.3 |
| `kafka.server:type=SessionExpireListener,name=SessionState` | broker (ZooKeeper mode) | SyncConnected or SaslAuthenticated | Disconnected, Expired, AuthFailed |
| `kafka.server:type=ZooKeeperClientMetrics,name=ZooKeeperRequestLatencyMs` | broker (ZooKeeper mode) | no range on the page (unverified, U11) | rising, threshold unverified (U11) |
| `ZkMigrationState`, `MigratingZkBrokerCount`, `ZkWriteBehindLag` (`kafka.controller`) | active controller, migration only | per phase | stuck phase, growing lag (threshold unverified, U11) |
| `kafka.server:type=raft-metrics` (current-state, high-watermark, commit-latency-avg) | KRaft nodes | no thresholds on the page | (unverified, U11) |

`ZkMigrationState` values: 0 NONE, 4 ZK, 2 PRE_MIGRATION, 1 MIGRATION, 3 POST_MIGRATION.

## Exporters

- Kafka exposes JMX. Remote JMX is disabled by default, and when enabled its authentication is off by default. Enable security before using remote JMX in production.
- No official Prometheus exporter for the broker was found in the pages read (medium confidence, M8).
- ZooKeeper ships a Prometheus provider: `metricsProvider.className=org.apache.zookeeper.metrics.prometheus.PrometheusMetricsProvider`, endpoint on `metricsProvider.httpPort` (default 7000), path `/metrics`. ZooKeeper normal ranges and thresholds: (unverified, U11).
- Four-letter commands: only `srvr` is whitelisted by default. The Kafka ZooKeeper page prefers them over JMX where they overlap.

## Also monitor

- Broker GC time, CPU and I/O service time.
- Consumers: max lag and min fetch rate.
- ZooKeeper: leader count across the ensemble (exactly one "Mode: leader").
- During migration: the controller log line "Completed migration of metadata from Zookeeper to KRaft" ([zk-to-kraft-migration](./zk-to-kraft-migration.md)).

```bash
# Representative: exactly one broker reports ActiveControllerCount=1
# MBean kafka.controller:type=KafkaController,name=ActiveControllerCount (read it with your JMX client)
docker exec kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:19092 --describe --under-min-isr-partitions
# The --under-min-isr-partitions flag is (unverified, U12)
```

Runbooks that use these signals: [high-availability-dr](./high-availability-dr.md).
