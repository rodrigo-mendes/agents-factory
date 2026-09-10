# Kafka 3.7 Reference Card

Pinned facts for **Apache Kafka 3.7.x**. Every entry must be verifiable at the cited source URL and dated. This card is imported by `researching-streaming-broker` when `PLATFORM_SOFTWARE=Apache Kafka` and `TARGET_VERSION` in `[3.7.0, 3.7.x]`.

**Version snapshot**: 3.7.0 released 2024-02-27 (source: [kafka.apache.org/downloads](https://kafka.apache.org/downloads))

---

## Metadata Store

- **Default in 3.7**: KRaft mode is the recommended and default deployment for new clusters (source: kafka.apache.org/documentation, §KRaft)
- **ZooKeeper mode**: still supported for migration; deprecated for new installs — removed in Kafka 4.0 per KIP-833
- **Minimum controller quorum**: 3 controllers (odd number for majority quorum)

## Critical Configuration (top-20 for OLTP-style workload)

| Parameter | Scope | Default (3.7) | Recommended | Source |
|---|---|---|---|---|
| `replication.factor` | topic | 1 | 3 for production | Broker/Topic configs |
| `min.insync.replicas` | topic/broker | 1 | `replication.factor - 1` (i.e., 2 for RF=3) | KIP-101 |
| `unclean.leader.election.enable` | broker | false | false — data-loss risk if true | Broker configs |
| `default.replication.factor` | broker | 1 | 3 | Broker configs |
| `num.partitions` | broker | 1 | Target-throughput ÷ per-partition-throughput | Broker configs |
| `log.retention.hours` | topic/broker | 168 (7 days) | Match SLA | Log configs |
| `log.segment.bytes` | topic/broker | 1073741824 (1GB) | Keep default | Log configs |
| `log.retention.check.interval.ms` | broker | 300000 (5min) | Keep default | Log configs |
| `message.max.bytes` | broker | 1048588 (~1MB) | Match producer max.request.size | Broker configs |
| `replica.fetch.max.bytes` | broker | 1048576 (~1MB) | Match message.max.bytes | Broker configs |
| `num.network.threads` | broker | 3 | nCPUs / 2 | Broker configs |
| `num.io.threads` | broker | 8 | nCPUs | Broker configs |
| `socket.send.buffer.bytes` | broker | 102400 (100KB) | 1048576 (1MB) for high-throughput | Broker configs |
| `socket.receive.buffer.bytes` | broker | 102400 (100KB) | 1048576 (1MB) for high-throughput | Broker configs |
| `compression.type` | topic | producer | zstd for storage efficiency; lz4 for CPU efficiency | Topic configs |
| `acks` (producer) | client | all (since 3.0) | all for durability; 1 for lower latency | Producer configs |
| `enable.idempotence` (producer) | client | true (since 3.0) | true — prevents duplicates on retry | Producer configs |
| `linger.ms` (producer) | client | 0 | 5-100 for batching throughput | Producer configs |
| `batch.size` (producer) | client | 16384 (16KB) | 65536 (64KB) or higher for throughput | Producer configs |
| `max.poll.records` (consumer) | client | 500 | Tune for processing time per batch | Consumer configs |

Sources: [kafka.apache.org/documentation/#configuration](https://kafka.apache.org/documentation/#configuration) (2024-02-27)

## HA Topology — KRaft Mode

```
Minimum production cluster:
  - 3 controllers (metadata quorum via Raft)
  - 3 brokers (data plane)
  - Combined mode allowed for small clusters: 3 nodes where each is both controller and broker
  - Separated mode for large clusters: 3-5 dedicated controllers + N brokers

Replication:
  - ISR (In-Sync Replicas): replicas caught up with leader within replica.lag.time.max.ms (default 30s)
  - Leader election: only from ISR by default (unclean.leader.election.enable=false)
  - Failover: automatic; controller elects new leader on broker unavailability
```

## Backup & Restore

- **Native tools**: `kafka-dump-log.sh`, `kafka-console-consumer.sh` (partition-by-partition extraction)
- **Recommended tools**:
  - **MirrorMaker 2** (bundled) — cross-cluster mirroring for DR
  - **Kafka Connect** with JDBC/S3 sink connectors — sink to durable storage
  - **Cruise Control** — for cluster rebalancing during recovery
- **PITR**: not native; achieved via consumer offset replay from a specific timestamp
- **Snapshot backup**: broker log directory copy is possible but requires broker to be stopped for consistency

## Upgrade Path to 3.7

- **From 3.6**: rolling upgrade supported; no protocol version change required
- **From 3.5**: rolling upgrade supported; verify KRaft mode compatibility
- **From 3.4 or older**: two-hop upgrade (via 3.5 or 3.6); ZooKeeper-to-KRaft migration is separate procedure (KIP-866)
- **Rollback**: possible until first message written with new inter-broker protocol; set `inter.broker.protocol.version` explicitly during upgrade

## Observability — Prometheus Metrics (via JMX Exporter)

| Metric | Type | Alert |
|---|---|---|
| `kafka_server_replicafetchermanager_maxlag` | gauge | > 1000 messages |
| `kafka_server_replicamanager_underreplicatedpartitions` | gauge | > 0 sustained |
| `kafka_controller_activecontrollercount` | gauge | ≠ 1 |
| `kafka_network_requestmetrics_requestspersec` (by request_type) | counter | trend baseline |
| `kafka_log_size_bytes` (by topic, partition) | gauge | approach retention limit |
| `kafka_consumer_group_lag` | gauge (exporter-derived) | > threshold per group |
| `kafka_server_brokertopicmetrics_bytesin_total` | counter | trend baseline |
| `kafka_server_brokertopicmetrics_bytesout_total` | counter | trend baseline |

## Security Hardening

- **Authentication**: SASL/PLAIN, SASL/SCRAM-SHA-256/512, SASL/GSSAPI (Kerberos), SASL/OAUTHBEARER, mTLS
- **Authorization**: ACLs via `kafka-acls.sh`; StandardAuthorizer built-in
- **Encryption in transit**: TLS on client-broker AND broker-broker (inter.broker.security.protocol)
- **Encryption at rest**: OS-level (LUKS/dm-crypt); Kafka does not encrypt on-disk natively in 3.7 open-source
- Source: [kafka.apache.org/documentation/#security](https://kafka.apache.org/documentation/#security) (2024-02-27)

## Kubernetes Operator: Strimzi

- **Compatible operator version**: Strimzi 0.40.x for Kafka 3.7 (verify at strimzi.io/downloads)
- **CRDs**: `Kafka`, `KafkaTopic`, `KafkaUser`, `KafkaConnect`, `KafkaConnector`, `KafkaMirrorMaker2`, `KafkaBridge`
- **Helm chart**: `strimzi/strimzi-kafka-operator` on strimzi.io/charts
- **KRaft support**: since Strimzi 0.36
- **Minimum CR for a 3-broker KRaft cluster**:

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: my-cluster
spec:
  kafka:
    version: 3.7.0
    replicas: 3
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2
      inter.broker.protocol.version: "3.7"
    storage:
      type: jbod
      volumes:
        - id: 0
          type: persistent-claim
          size: 100Gi
          deleteClaim: false
  zookeeper:                    # remove entirely for KRaft-only in Strimzi 0.40+
    replicas: 3
    storage:
      type: persistent-claim
      size: 10Gi
      deleteClaim: false
```

Source: [strimzi.io/docs/operators/0.40.0/deploying](https://strimzi.io/docs/operators/0.40.0/deploying)

## Ecosystem (Kafka 3.7-compatible)

| Tool | Purpose | Compatibility |
|---|---|---|
| Confluent Schema Registry / Apicurio Registry | Message schema management (Avro/Protobuf/JSON Schema) | Compatible |
| Kafka Connect | Source/sink connectors to databases, cloud storage, other systems | Bundled with Kafka 3.7 |
| MirrorMaker 2 | Cross-cluster active-active or DR replication | Bundled with Kafka 3.7 |
| Cruise Control | Automated partition rebalancing, cluster health | v2.5.130+ for Kafka 3.7 |
| AKHQ / Kafka UI / Redpanda Console | Web UI for topic browsing, consumer lag monitoring | All compatible |
| ksqlDB | SQL-based stream processing | Requires KRaft-compatible version |

## Known Issues in 3.7

- Check [issues.apache.org/jira/browse/KAFKA](https://issues.apache.org/jira/browse/KAFKA) for `fixVersion=3.7.1` and later — always verify no open blocker for `TARGET_VERSION` before recommending
