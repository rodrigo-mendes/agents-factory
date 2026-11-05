# Always-do patterns, Kafka 3.9.2

Back to [SKILL.md](../SKILL.md). All code is representative: adapt names and ports to your environment. Container paths under `/opt/kafka` come from the image Dockerfile at the 3.9 branch head, not the 3.9.2 tag (medium confidence, U13). Caveats and options live in [ask-first-decisions](./ask-first-decisions.md). All sources read 2026-11-04.

## 1. RF 3 with min.insync.replicas=2

Sources: [topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/) (the typical scenario), [production example](https://kafka.apache.org/39/operations/kafka-configuration/) (`default.replication.factor=3`, `min.insync.replicas=2`).

```bash
docker exec kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:19092 \
  --create --topic orders --replication-factor 3 --partitions 6 --config min.insync.replicas=2
docker exec kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:19092 --describe --topic orders
# Expected: ReplicationFactor: 3 and Configs containing min.insync.replicas=2
```

## 2. Producer acks=all

Sources: [producer configs](https://kafka.apache.org/39/configuration/producer-configs/) (default `all`), [topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/). `min.insync.replicas` has no effect with `acks=0` or `acks=1`.

```properties
acks=all
delivery.timeout.ms=120000
```

## 3. Producer idempotence

Sources: [producer configs](https://kafka.apache.org/39/configuration/producer-configs/) (default `true`), [design](https://kafka.apache.org/39/design/design/).

```properties
enable.idempotence=true
```

## 4. Unclean leader election off

Sources: [topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/), [design](https://kafka.apache.org/39/design/design/), [broker configs](https://kafka.apache.org/39/configuration/broker-configs/). Default `false` since 0.11.0.0.

```bash
docker exec kafka-1 /opt/kafka/bin/kafka-configs.sh --bootstrap-server kafka-1:19092 \
  --entity-type topics --describe --all | grep unclean.leader.election.enable=true
# Expected: no output
```

## 5. Odd ZooKeeper ensemble, at least 3

Sources: [ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/) (5 or 7 typical; tolerates 2 and 3), [Admin Guide](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html) ("Three ZooKeeper servers is the minimum recommended size", odd count best).

```bash
docker exec zk-1 bash -c 'exec 3<>/dev/tcp/127.0.0.1/2181; echo srvr >&3; cat <&3'
# Expected: "Mode: leader" on one server, "Mode: follower" on the others
```

The `/dev/tcp` redirection and the `srvr` command inside the image are (unverified, U12). `srvr` is the only four-letter command whitelisted by default (see [zookeeper-ensemble](./zookeeper-ensemble.md)).

## 6. Dedicated device for the ZooKeeper transaction log

Sources: [Admin Guide](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html) ("must be on a dedicated device. (A dedicated partition is not enough.)"), [ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/) (`dataLogDir`).

```properties
dataDir=/var/lib/kafka/data/zookeeper
dataLogDir=/var/lib/kafka/data/zookeeper-txlog   # bind-mount a separate disk here
```

Containers on one host share its disks unless you bind-mount separate devices, so under Compose this holds only with per-device mounts (medium confidence, M5).

## 7. Encrypted listeners

Sources: [SSL](https://kafka.apache.org/39/security/encryption-and-authentication-using-ssl/), [listeners](https://kafka.apache.org/39/security/listener-configuration/). Default is `listeners=PLAINTEXT://:9092`, so set the protocol explicitly.

```properties
listeners=CLIENT://:9092,INTERNAL://:19092
listener.security.protocol.map=CLIENT:SASL_SSL,INTERNAL:SSL
```

## 8. Encrypted inter-broker traffic

Sources: [SSL](https://kafka.apache.org/39/security/encryption-and-authentication-using-ssl/), [listeners](https://kafka.apache.org/39/security/listener-configuration/), [running cluster](https://kafka.apache.org/39/security/incorporating-security-features-in-a-running-cluster/). `security.inter.broker.protocol` defaults to PLAINTEXT. Setting `security.inter.broker.protocol=SSL` is the alternative when no named inter-broker listener is used.

```properties
inter.broker.listener.name=INTERNAL
# INTERNAL is mapped to SSL above
```

## 9. Hostname verification on

Sources: [SSL](https://kafka.apache.org/39/security/encryption-and-authentication-using-ssl/) (on by default since 2.0.0), [broker configs](https://kafka.apache.org/39/configuration/broker-configs/) (`ssl.endpoint.identification.algorithm=https`). Keystores carry a SAN: `keytool ... -ext SAN=DNS:{FQDN},IP:{IPADDRESS}`.

## 10. Java 17 or 21

Sources: [Java](https://kafka.apache.org/39/operations/java-version/) (8, 11, 17, 21 fully supported, 25 best effort; Java 11 deprecated since 3.7, removed in 4.0), [upgrade notes](https://kafka.apache.org/39/getting-started/upgrade/) (3.7.0 notes).

```bash
docker exec kafka-1 java -version
# Expected: version 17 or 21
```

## 11. Generate the cluster ID once

Sources: [KRaft](https://kafka.apache.org/39/operations/kraft/), [quickstart](https://kafka.apache.org/39/getting-started/quickstart/) (`random-uuid`). Formatting every KRaft node with that same ID is not in the main guardrail list: the multi-node rule rests on one official page ([KRaft](https://kafka.apache.org/39/operations/kraft/)), so it is an Ask First item (cluster ID, medium confidence, M14). For the ZooKeeper migration, use the existing ZooKeeper cluster ID instead (see [migration](./zk-to-kraft-migration.md)).

```bash
KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
bin/kafka-storage.sh format -t "$KAFKA_CLUSTER_ID" -c config/kraft/server.properties
```

## 12. IBP 3.9 before migration

Sources: [KRaft migration section](https://kafka.apache.org/39/operations/kraft/) (prerequisite), [upgrade notes](https://kafka.apache.org/39/getting-started/upgrade/) (IBP bump steps; no downgrade after the bump).

```bash
grep -h "inter.broker.protocol.version" /path/to/broker-*.properties
# Expected: inter.broker.protocol.version=3.9 on every broker
```

## 13. Rolling restart, one broker at a time

Sources: [upgrade notes](https://kafka.apache.org/39/getting-started/upgrade/), [running cluster](https://kafka.apache.org/39/security/incorporating-security-features-in-a-running-cluster/) (bounce one broker at a time). Waiting for the ISR to rejoin before the next restart is not in the main guardrail list: the running-cluster page is the one page that states it, so it is an Ask First item (rolling restart pacing, medium confidence, M15). The check below is that item's verification.

```bash
docker compose stop kafka-1 && docker compose up -d kafka-1
docker exec kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:19092 --describe --under-replicated-partitions
# Expected: empty before moving to kafka-2
```

## 14. MirrorMaker 2 for DR

Sources: [datacenters](https://kafka.apache.org/39/operations/datacenters/), [geo-replication](https://kafka.apache.org/39/operations/geo-replication-cross-cluster-data-mirroring/) (replicates consumer groups including offsets).

```properties
clusters = primary, secondary
primary.bootstrap.servers = kafka-1:19092,kafka-2:19092,kafka-3:19092
secondary.bootstrap.servers = dr-kafka-1:9092
primary->secondary.enabled = true
```

```bash
/opt/kafka/bin/connect-mirror-maker.sh connect-mirror-maker.properties
# Expected: kafka.connect.mirror metrics (record-count, replication-latency-ms) increase
```

More DR detail: [high-availability-dr](./high-availability-dr.md).
