# Always-do patterns, Kafka 4.4.0

Back to [SKILL.md](../SKILL.md). All code is representative: adapt names and ports to your environment. Container paths under `/opt/kafka` are inferred from the image README (medium confidence); see register U3. Caveats and options live in [ask-first-decisions](./ask-first-decisions.md).

## Durable topic: RF 3, min ISR 2

Sources: [topic configs](https://kafka.apache.org/44/configuration/topic-configs/), [design](https://kafka.apache.org/44/design/design/) (read 2026-11-04). The topic config page calls RF 3 with min ISR 2 the typical scenario.

```bash
docker exec kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:19092 \
  --create --topic orders --replication-factor 3 --partitions 6 --config min.insync.replicas=2
docker exec kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:19092 --describe --topic orders
# Expected: ReplicationFactor: 3 and Configs containing min.insync.replicas=2
```

## Producer durability defaults

Sources: [producer configs](https://kafka.apache.org/44/configuration/producer-configs/), [design](https://kafka.apache.org/44/design/design/) (read 2026-11-04). `acks=all` and `enable.idempotence=true` are the defaults; do not override them.

```properties
acks=all
enable.idempotence=true
delivery.timeout.ms=120000
```

## Odd controller quorum (medium confidence, M16, M18)

Not in the main guardrail list: one official page ([KRaft](https://kafka.apache.org/44/operations/kraft/)), so it is an Ask First item (controller quorum size). 3 controllers tolerate 1 failure, 5 tolerate 2. The health check below rests on the same page.

```bash
docker exec kafka-1 /opt/kafka/bin/kafka-metadata-quorum.sh --bootstrap-server kafka-1:19092 describe --status
# Expected: LeaderId set, CurrentVoters lists 3 (or 5) ids, MaxFollowerLag small
```

## Dedicated roles in critical environments (medium confidence, M13)

Not in the main guardrail list: one official page ([KRaft](https://kafka.apache.org/44/operations/kraft/)), so it is an Ask First item (controller placement). Controllers get `process.roles=controller`, brokers get `process.roles=broker`.

```yaml
# controllers
KAFKA_PROCESS_ROLES: 'controller'
# brokers
KAFKA_PROCESS_ROLES: 'broker'
```

## Cluster ID generated once

Sources: [KRaft](https://kafka.apache.org/44/operations/kraft/), [quickstart](https://kafka.apache.org/44/getting-started/quickstart/) (`random-uuid`). Formatting every KRaft node with that same ID is not in the main guardrail list: the multi-node rule rests on one official page ([KRaft](https://kafka.apache.org/44/operations/kraft/)), so it is an Ask First item (cluster ID, medium confidence, M24). Auto-formatting was removed, so every node must be formatted explicitly.

```bash
KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
bin/kafka-storage.sh format --cluster-id "$KAFKA_CLUSTER_ID" --standalone --config config/controller.properties   # first controller
bin/kafka-storage.sh format --cluster-id "$KAFKA_CLUSTER_ID" --config config/server.properties                      # brokers
```

## Unique node.id (medium confidence, M17)

Not in the main guardrail list: [upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/) say `broker.id` is deprecated in 4.4, use `node.id`; the broker configs page was read 200000 of 201536 characters (L1). It is an Ask First item (node identity). In Compose set `KAFKA_NODE_ID` per service.

## Deny by default, with an authorizer (medium confidence, M14)

Source: [ACLs](https://kafka.apache.org/44/security/authorization-and-acls/). Keeping `allow.everyone.if.no.acl.found` at `false` and enabling `StandardAuthorizer` with `super.users` rest on this one page, so both are an Ask First item (authorizer). Set on every node (brokers, controllers, combined).

```properties
authorizer.class.name=org.apache.kafka.metadata.authorizer.StandardAuthorizer
super.users=User:admin
# allow.everyone.if.no.acl.found stays at its default false
```

```bash
kafka-acls.sh --bootstrap-server kafka-1:19092 --add --allow-principal User:Bob --producer --topic Test-topic
```

## Encrypted listeners

Sources: [SASL](https://kafka.apache.org/44/security/authentication-using-sasl/), [SSL](https://kafka.apache.org/44/security/encryption-and-authentication-using-ssl/), [listener configuration](https://kafka.apache.org/44/security/listener-configuration/). SCRAM-SHA-512 as the mechanism and SASL/PLAIN only with TLS are Ask First items (medium confidence, M21). Details in [tls-and-security](./tls-and-security.md).

```properties
listener.security.protocol.map=CONTROLLER:SSL,CLIENT:SASL_SSL
sasl.enabled.mechanisms=SCRAM-SHA-512
```

## Pinned image tag

Not in the main guardrail list: only [Docker](https://kafka.apache.org/44/getting-started/docker/) lists tag 4.4.0 (one page). Use `apache/kafka:4.4.0`. Avoiding floating tags such as `latest` is factory practice, an Ask First item (medium confidence, M15).

## Finalize features after the roll (unverified, U2)

Not in the main guardrail list: the 4.4 upgrade procedure has no body, so the steps come from the 4.3 and 4.2 notes (unverified, U2). Source: [upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/). See [migration-guide](./migration-guide.md).

```bash
/opt/kafka/bin/kafka-features.sh --bootstrap-server kafka-1:19092 upgrade --release-version 4.4
/opt/kafka/bin/kafka-features.sh --bootstrap-controller controller-1:9093 describe
```

## Alerts on the two safety metrics (medium confidence, L2)

Not in the main guardrail list: the monitoring page was only partly read (medium confidence, L2). Source: [monitoring](https://kafka.apache.org/44/operations/monitoring/). Alert when `kafka.server:type=ReplicaManager,name=UnderMinIsrPartitionCount` is above 0 (acks=all producers fail), and when the sum of `kafka.controller:type=KafkaController,name=ActiveControllerCount` across controllers is not 1. Full table in [observability](./observability.md).

## File descriptors (medium confidence, M19)

Not in the main guardrail list: one page, [hardware and OS](https://kafka.apache.org/44/operations/hardware-and-os/), says at least 100000. It is an Ask First item.

```yaml
ulimits:
  nofile: { soft: 100000, hard: 100000 }
```

## MirrorMaker 2 for DR

Sources: [geo-replication](https://kafka.apache.org/44/operations/geo-replication-cross-cluster-data-mirroring/), [datacenters](https://kafka.apache.org/44/operations/datacenters/). Full procedure in [high-availability-dr](./high-availability-dr.md).

```properties
clusters = primary, backup
primary->backup.enabled = true
primary->backup.topics = .*
tasks.max = 2
```

## Environment variable mapping in Compose

Source: [examples README](https://raw.githubusercontent.com/apache/kafka/4.4/docker/examples/README.md). Prefix `KAFKA_`; `.` becomes `_`, `_` becomes `__`, `-` becomes `___`. Example: `min.insync.replicas` becomes `KAFKA_MIN_INSYNC_REPLICAS`.
