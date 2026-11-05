# Deploy ZooKeeper-mode Kafka 3.9.2 with Docker Compose

Back to [SKILL.md](../SKILL.md). Container paths come from the 3.9 branch head Dockerfile, not the 3.9.2 tag (medium confidence, U13). All sources read 2026-11-04.

## Status of this layout

The whole ZooKeeper-ensemble Compose file below is (unverified, U28). It assembles official config keys ([broker configs](https://kafka.apache.org/39/configuration/broker-configs/), [Admin Guide](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html), [production example](https://kafka.apache.org/39/operations/kafka-configuration/)) into a layout that no official example shows, and it was not run. Named-volume write access for `appuser` is (unverified, U2). Compose is single-host, so use it for dev, CI and staging (medium confidence, M5).

## Why the command is overridden

- The image's launch script always runs the Kafka storage formatter at startup, through `KafkaDockerWrapper setup` (sources: [launch script](https://raw.githubusercontent.com/apache/kafka/3.9/docker/jvm/launch), [wrapper](https://raw.githubusercontent.com/apache/kafka/3.9/core/src/main/scala/kafka/docker/KafkaDockerWrapper.scala)).
- The 3.9 `StorageTool` rejects a config with no `process.roles`: "Formatting is only supported for clusters in KRaft mode" ([StorageTool](https://raw.githubusercontent.com/apache/kafka/3.9/core/src/main/scala/kafka/tools/StorageTool.scala)). The launch script tolerates only an "already formatted" error.
- So the default `CMD ["/etc/kafka/docker/run"]` exits for a ZooKeeper-mode config. The Dockerfile has no `ENTRYPOINT` ([Dockerfile](https://raw.githubusercontent.com/apache/kafka/3.9/docker/jvm/Dockerfile)), so a `command:` that calls `kafka-server-start.sh` bypasses the wrapper.
- This conclusion is inferred from source and was not run (medium confidence, U1). The image docs never mention ZooKeeper mode ([Docker](https://kafka.apache.org/39/getting-started/docker/)).
- Side effect: with the override, the image's `KAFKA_*` environment-to-property mapping does not run. Put every setting in the mounted properties files (medium confidence, U1).

## Compose: 3 ZooKeeper servers + 3 brokers

```yaml
# Representative, adapt to your environment. (unverified, U28)
name: kafka39-zk
x-kafka-image: &kafka_image apache/kafka:3.9.2
networks:
  kafka-internal: { internal: true }   # ZooKeeper and inter-broker traffic stay inside
  kafka-clients: {}
volumes: { zk-1-data: {}, zk-2-data: {}, zk-3-data: {}, kafka-1-data: {}, kafka-2-data: {}, kafka-3-data: {} }
services:
  zk-1:
    image: *kafka_image
    hostname: zk-1
    command: ["bash", "-c", "mkdir -p /var/lib/kafka/data/zookeeper && echo 1 > /var/lib/kafka/data/zookeeper/myid && exec /opt/kafka/bin/zookeeper-server-start.sh /mnt/zk/zookeeper.properties"]
    environment: { KAFKA_HEAP_OPTS: "-Xms1g -Xmx1g" }
    volumes: ["zk-1-data:/var/lib/kafka/data", "./config/zookeeper.properties:/mnt/zk/zookeeper.properties:ro"]
    networks: [kafka-internal]
    healthcheck:   # command inside the image is (unverified, U12)
      test: ["CMD", "/opt/kafka/bin/zookeeper-shell.sh", "localhost:2181", "ls", "/"]
      interval: 30s
      timeout: 10s
      retries: 5
  # zk-2, zk-3: same, with echo 2 / echo 3 and their own volumes
  kafka-1:
    image: *kafka_image
    hostname: kafka-1
    command: ["/opt/kafka/bin/kafka-server-start.sh", "/mnt/broker/server.properties"]
    environment: { KAFKA_HEAP_OPTS: "-Xms4g -Xmx4g" }
    ulimits: { nofile: { soft: 100000, hard: 100000 } }
    ports: ["127.0.0.1:29092:9092"]
    volumes: ["kafka-1-data:/var/lib/kafka/data", "./config/broker-1.properties:/mnt/broker/server.properties:ro"]
    networks: [kafka-internal, kafka-clients]
    depends_on:
      zk-1: { condition: service_healthy }
      zk-2: { condition: service_healthy }
      zk-3: { condition: service_healthy }
  # kafka-2, kafka-3: same, with broker-2/3.properties, host ports 39092 and 49092
```

`KAFKA_HEAP_OPTS` is read by the Kafka start scripts (medium confidence, M7). Size heaps to the host. The 100000 file-descriptor value comes from the [hardware page](https://kafka.apache.org/39/operations/hardware-and-os/) (single page, M10).

`config/zookeeper.properties` (keys from the Admin Guide; AdminServer disabled as in the bundled file):

```properties
tickTime=2000
initLimit=5
syncLimit=2
dataDir=/var/lib/kafka/data/zookeeper
dataLogDir=/var/lib/kafka/data/zookeeper-txlog
clientPort=2181
autopurge.snapRetainCount=3
autopurge.purgeInterval=1
admin.enableServer=false
4lw.commands.whitelist=srvr
server.1=zk-1:2888:3888
server.2=zk-2:2888:3888
server.3=zk-3:2888:3888
```

`config/broker-1.properties` (PLAINTEXT is for a single-host dev/CI layout only; for anything that leaves the host see [zookeeper-security](./zookeeper-security.md)):

```properties
broker.id=1
zookeeper.connect=zk-1:2181,zk-2:2181,zk-3:2181
listeners=INTERNAL://:19092,EXTERNAL://:9092
advertised.listeners=INTERNAL://kafka-1:19092,EXTERNAL://localhost:29092
listener.security.protocol.map=INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT
inter.broker.listener.name=INTERNAL
inter.broker.protocol.version=3.9
log.dirs=/var/lib/kafka/data/logs
default.replication.factor=3
min.insync.replicas=2
offsets.topic.replication.factor=3
transaction.state.log.replication.factor=3
transaction.state.log.min.isr=2
auto.create.topics.enable=false
unclean.leader.election.enable=false
```

`num.partitions=8` in the production example is an example value, not a sizing rule. Pinning `inter.broker.protocol.version=3.9` makes the migration prerequisite explicit.

## Image facts

- `apache/kafka` (JVM) exists since 3.7.0, `apache/kafka-native` since 3.8.0. The native image is "experimental and intended for local development and testing purposes only" ([Docker](https://kafka.apache.org/39/getting-started/docker/)). Tag `3.9.2` exists on Docker Hub, last updated 2026-02-21 ([registry API](https://hub.docker.com/v2/repositories/apache/kafka/tags/3.9.2)). Docs page shows tag `3.9.1`.
- Layout at the branch head: Kafka in `/opt/kafka`, `VOLUME` `/etc/kafka/secrets`, `/var/lib/kafka/data`, `/mnt/shared/config`, user `appuser`, base `eclipse-temurin:21-jre-alpine` (medium confidence, U13).
- Env mapping when the default `CMD` is used: `.` to `_`, `_` to `__`, `-` to `___`, prefix `KAFKA_`. Env vars override `/mnt/shared/config`, which overrides defaults ([README](https://raw.githubusercontent.com/apache/kafka/3.9/docker/examples/README.md)).
- Remote JMX: the monitoring page says authentication is off by default. The image launch script defaults `KAFKA_JMX_OPTS` to authenticate=false and ssl=false and opens remote access when `KAFKA_JMX_PORT` is set (medium confidence, U13). Do not publish JMX. Secure flag set: (medium confidence, U23).
- Unset `CLUSTER_ID` falls back to a hard-coded ID in `configureDefaults` (medium confidence, U13). Always set your own.

## KRaft on 3.9 (dedicated controllers)

Start from the official 3.9 isolated example ([example](https://raw.githubusercontent.com/apache/kafka/3.9/docker/examples/docker-compose-files/cluster/isolated/plaintext/docker-compose.yml)): 3 `controller` nodes (ids 1-3), 3 `broker` nodes (ids 4-6), static `KAFKA_CONTROLLER_QUORUM_VOTERS`. Then change:
- Pin `image: apache/kafka:3.9.2`, set one `CLUSTER_ID` from `random-uuid`, set RF 3 and min ISR 2.
- Set `KAFKA_LOG_DIRS: /var/lib/kafka/data` on named volumes, bind host ports to `127.0.0.1`.
- Do not set `KAFKA_ADVERTISED_LISTENERS` on controllers: the image's `configure` script exits with that message (medium confidence, U13).
- This is a static quorum, which 3.9 cannot convert to dynamic.

Kubernetes operators are out of scope: use `operating-kafka-strimzi-v1-3` or `operating-kafka-confluent-kubernetes-v3-4`.
