# Never-do patterns, Kafka 3.9.2

Back to [SKILL.md](../SKILL.md). Every row rests on at least two versioned official pages read in full and has a High-confidence alternative; the ZooKeeper rows cite the 4.4 KRaft page and the 4.0.0 announcement, both read in full on 2026-11-04. All sources read 2026-11-04. Single-page warnings (for example SCRAM credentials in ZooKeeper only where ZooKeeper is secure and private, SASL/PLAIN without TLS, the unsecured default OAUTHBEARER, finalizing a migration early, stretching one cluster across datacenters) are not here: see [ask-first-decisions](./ask-first-decisions.md#single-page-guidance-kept-out-of-always-do-and-never-do).

## min.insync.replicas=1 with RF 1 (risk: critical)

Why: with `acks=all` an acknowledgement means only that the current ISR members have the write. With min ISR 1, an ISR of one replica still accepts writes, so losing that node loses data. The topic page describes RF 3 with min ISR 2 as the typical setup. Sources: [design](https://kafka.apache.org/39/design/design/), [topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/), [production example](https://kafka.apache.org/39/operations/kafka-configuration/).

```properties
# 🚫 WRONG
default.replication.factor=1
min.insync.replicas=1
# ✅ CORRECT
default.replication.factor=3
min.insync.replicas=2
```

Detection: `kafka-topics.sh --bootstrap-server kafka-1:19092 --describe | grep -E "ReplicationFactor: 1|min.insync.replicas=1"`.

## Official Compose example settings in a persistent cluster (risk: high)

Why: the 3.9 isolated example sets the offsets and transaction-state replication factor and min ISR to 1, uses `KAFKA_LOG_DIRS: '/tmp/kraft-combined-logs'`, no volumes and a fixed `CLUSTER_ID`. The README says the single-replica offsets setting suits only a single node. The broker config page shows the defaults 3, 3 and 2. Sources for the risk and the defaults: [design](https://kafka.apache.org/39/design/design/), [topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/), [broker configs](https://kafka.apache.org/39/configuration/broker-configs/). Sources for the example contents (branch head, supporting): [examples README](https://raw.githubusercontent.com/apache/kafka/3.9/docker/examples/README.md), [isolated example](https://raw.githubusercontent.com/apache/kafka/3.9/docker/examples/docker-compose-files/cluster/isolated/plaintext/docker-compose.yml).

```yaml
# 🚫 WRONG
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
KAFKA_LOG_DIRS: '/tmp/kraft-combined-logs'   # no volume
# ✅ CORRECT
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 3
KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 2
KAFKA_LOG_DIRS: '/var/lib/kafka/data'        # named volume mounted here (medium confidence, M20)
```

Detection: `grep -nE "REPLICATION_FACTOR: 1|MIN_ISR: 1|/tmp/" docker-compose.yml`. See [deploy-compose-zookeeper](./deploy-compose-zookeeper.md).

## Unclean leader election on durable topics (risk: high)

Why: it lets an out-of-sync replica become leader "as a last resort, which may cause data loss". The default has been `false` since 0.11.0.0. Sources: [topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/), [design](https://kafka.apache.org/39/design/design/).

```properties
# 🚫 WRONG
unclean.leader.election.enable=true
# ✅ CORRECT (the default)
unclean.leader.election.enable=false
```

Detection: `kafka-configs.sh --bootstrap-server kafka-1:19092 --entity-type topics --describe --all | grep unclean.leader.election.enable=true`.

## Direct ZooKeeper-to-4.x upgrade (risk: high)

Why: 3.9 is the last bridge release and 4.x runs entirely without ZooKeeper. Sources: [4.4 KRaft page](https://kafka.apache.org/44/operations/kraft/), [4.0.0 announcement](https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/).

```text
# 🚫 WRONG: roadmap "ZooKeeper cluster -> 4.x"
# ✅ CORRECT: ZooKeeper cluster -> KRaft migration on the 3.9 bridge release (this skill) -> 4.x (operating-kafka-v4-4)
```

Detection: `grep -l "zookeeper.connect" /path/to/broker-*.properties`. Runbook: [zk-to-kraft-migration](./zk-to-kraft-migration.md).

## Keeping ZooKeeper mode as the destination (risk: high)

Why: ZooKeeper mode is deprecated since 3.5 and removed in 4.0. Sources: [ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/), [4.0.0 announcement](https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/). The archived status of 3.9.x is an Ask First item (support window).

```text
# 🚫 WRONG: roadmap "keep ZooKeeper indefinitely"
# ✅ CORRECT: plan the KRaft migration on the 3.9 bridge release, then follow operating-kafka-v4-4
```

Detection: `grep -l "zookeeper.connect" /path/to/broker-*.properties`.

## ZooKeeper reachable by clients or published (risk: high)

Why: ZooKeeper metadata is world-readable and manipulating it can disrupt the cluster, so only brokers and admin tools should reach it. The Admin Guide expects a trusted computing environment. Sources: [ZooKeeper auth](https://kafka.apache.org/39/security/zookeeper-authentication/), [Admin Guide](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html).

```yaml
# 🚫 WRONG
zk-1:
  ports:
    - "2181:2181"   # published on all host interfaces
# ✅ CORRECT: no ports on zk-*, networks: [kafka-internal] with internal: true
```

Detection: `docker compose config | grep -A3 "zk-" | grep -E "published|2181:2181"`. Hardening: [zookeeper-security](./zookeeper-security.md).
