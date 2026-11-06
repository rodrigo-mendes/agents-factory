# Deploy with Docker Compose, Kafka 4.4.0

Back to [SKILL.md](../SKILL.md). Scope: dev, CI and staging on one Docker host (medium confidence, single-host inference, register M12). Kubernetes is out of scope; use `operating-kafka-strimzi-v1-3` or `operating-kafka-confluent-kubernetes-v3-4`. S-ids resolve in the [Source Bibliography](./unverified-and-risks.md#source-bibliography).

## Images [S2]

- `apache/kafka` (JVM, since 3.7.0) and `apache/kafka-native` (GraalVM, since 3.8.0), both with tag `4.4.0`.
- The Docker page describes the native image as "intended for local development and testing purposes only" and "not recommended for production use".
- Use Docker 20.10.4 or later [S3] (medium confidence, M27: one release-branch file).

## Environment variable mapping [S3]

- Prefix every property with `KAFKA_`. `.` becomes `_`, `_` becomes `__`, `-` becomes `___`.
- Environment variables override properties from a file mounted at `/mnt/shared/config`.
- With no configuration the container runs a single combined-mode KRaft node (dev only).
- SSL secrets go in `/etc/kafka/secrets`, referenced by `KAFKA_SSL_KEYSTORE_FILENAME`, `KAFKA_SSL_KEYSTORE_CREDENTIALS`, `KAFKA_SSL_KEY_CREDENTIALS`, `KAFKA_SSL_TRUSTSTORE_FILENAME`, `KAFKA_SSL_TRUSTSTORE_CREDENTIALS`.

Official examples live under `docker/examples/docker-compose-files/` [S3]: `single-node/{plaintext,ssl,file-input,sasl_plaintext}`, `cluster/combined/{plaintext,ssl,sasl_plaintext}`, `cluster/isolated/{plaintext,ssl,sasl_plaintext}`.

## Hardened isolated cluster

Base: official isolated example [S5] (branch 4.4, read 2026-11-04). Changes: image pinned to 4.4.0 (the official file uses `${IMAGE}`), `ulimits: nofile` and `depends_on` on the controllers (part of the assembled file below, not compared line by line with the official file), RF 3 and min ISR 2, named volumes instead of `/tmp`, host ports bound to `127.0.0.1` (medium confidence, M28), auto topic creation off (medium confidence, U12). The path `/var/lib/kafka/data` is a factory choice (medium confidence). PLAINTEXT is kept for brevity: use SSL or SASL_SSL beyond a laptop ([tls-and-security](./tls-and-security.md)).

```yaml
# Representative — adapt to your environment
x-controller-env: &controller-env
  KAFKA_PROCESS_ROLES: 'controller'
  KAFKA_CONTROLLER_QUORUM_VOTERS: '1@controller-1:9093,2@controller-2:9093,3@controller-3:9093'
  KAFKA_CONTROLLER_LISTENER_NAMES: 'CONTROLLER'
  KAFKA_LISTENERS: 'CONTROLLER://:9093'
  CLUSTER_ID: '${KAFKA_CLUSTER_ID}'   # generate once: kafka-storage.sh random-uuid
  KAFKA_LOG_DIRS: '/var/lib/kafka/data'
x-broker-env: &broker-env
  KAFKA_PROCESS_ROLES: 'broker'
  KAFKA_CONTROLLER_QUORUM_VOTERS: '1@controller-1:9093,2@controller-2:9093,3@controller-3:9093'
  KAFKA_CONTROLLER_LISTENER_NAMES: 'CONTROLLER'
  KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: 'CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT'
  KAFKA_INTER_BROKER_LISTENER_NAME: 'PLAINTEXT'
  KAFKA_LISTENERS: 'PLAINTEXT://:19092,PLAINTEXT_HOST://:9092'
  CLUSTER_ID: '${KAFKA_CLUSTER_ID}'
  KAFKA_LOG_DIRS: '/var/lib/kafka/data'
  KAFKA_DEFAULT_REPLICATION_FACTOR: 3
  KAFKA_MIN_INSYNC_REPLICAS: 2
  KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
  KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 3
  KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 2
  KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'false'
services:
  controller-1: { image: 'apache/kafka:4.4.0', hostname: controller-1, environment: { <<: *controller-env, KAFKA_NODE_ID: 1 }, volumes: ['c1:/var/lib/kafka/data'] }
  controller-2: { image: 'apache/kafka:4.4.0', hostname: controller-2, environment: { <<: *controller-env, KAFKA_NODE_ID: 2 }, volumes: ['c2:/var/lib/kafka/data'] }
  controller-3: { image: 'apache/kafka:4.4.0', hostname: controller-3, environment: { <<: *controller-env, KAFKA_NODE_ID: 3 }, volumes: ['c3:/var/lib/kafka/data'] }
  kafka-1:
    image: apache/kafka:4.4.0
    hostname: kafka-1
    ports: ['127.0.0.1:29092:9092']   # (medium confidence, M28)
    environment: { <<: *broker-env, KAFKA_NODE_ID: 4, KAFKA_ADVERTISED_LISTENERS: 'PLAINTEXT://kafka-1:19092,PLAINTEXT_HOST://localhost:29092' }
    volumes: ['b1:/var/lib/kafka/data']
    depends_on: [controller-1, controller-2, controller-3]
    ulimits: { nofile: { soft: 100000, hard: 100000 } }   # [S16] (medium confidence, M19)
    healthcheck:
      test: ['CMD-SHELL', '/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:19092 --list >/dev/null']   # path (medium confidence)
      interval: 30s
      timeout: 10s
      retries: 5
  # kafka-2 (node 5, host port 39092) and kafka-3 (node 6, host port 49092) follow the same pattern [S5]
volumes: { c1: {}, c2: {}, c3: {}, b1: {}, b2: {}, b3: {} }
```

Advertised listeners: use the service hostname for in-network clients and `localhost:<mapped port>` for host clients [S4]. `advertised.listeners` is not dynamic in KRaft: changing it needs a restart [S20].

## Bring-up and verification

```bash
export KAFKA_CLUSTER_ID="$(docker run --rm apache/kafka:4.4.0 /opt/kafka/bin/kafka-storage.sh random-uuid)"   # path (medium confidence)
docker compose up -d
docker exec kafka-1 /opt/kafka/bin/kafka-metadata-quorum.sh --bootstrap-server kafka-1:19092 describe --status
# Expected: LeaderId set, 3 CurrentVoters
```

## Open points

- Volume ownership and UID inside `apache/kafka:4.4.0` are (unverified), U3. If the broker cannot write the data directory, fix permissions, or mount the volume at the official `/tmp` path.
- Bundled JRE version and heap environment variable names (`KAFKA_HEAP_OPTS`, `KAFKA_JVM_PERFORMANCE_OPTS`) are (unverified), U3.
- Dynamic quorum formatting by environment variables is (unverified), U5.
- Native image and SASL: conflicting official sources (unverified, U1). Use the JVM image for SASL.
