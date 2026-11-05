# Always-do patterns, Confluent Schema Registry 8.4.0

Back to [SKILL.md](../SKILL.md). Provenance: official pages read 2026-11-04. Only the nine triangulated items A1 to A9 are here. Single-source items are in [ask-first-decisions](./ask-first-decisions.md). CLI and REST commands are representative: adapt them to your environment.

## A1 Set the compatibility level explicitly

Why: the implicit default is non-transitive `BACKWARD`, not `BACKWARD_TRANSITIVE`. BACKWARD checks only against the previous version.

```bash
# Representative, Schema Registry 8.4.0
curl -s -X PUT -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data '{"compatibility": "BACKWARD_TRANSITIVE"}' \
  https://schema-registry:8081/config/orders-value
# Expected: {"compatibility":"BACKWARD_TRANSITIVE"}
# 422 with error code 42203 = invalid compatibility level
```

```properties
# schema-registry.properties: none, backward, backward_transitive, forward,
# forward_transitive, full, full_transitive
schema.compatibility.level=backward_transitive
```

Sources: [config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html), [schema evolution](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/schema-evolution.html), [API](https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html).

## A2 Use BACKWARD_TRANSITIVE for Protobuf subjects

Why: adding new message types is not forward compatible, so the Protobuf page recommends `BACKWARD_TRANSITIVE`. Use the same `PUT /config/{subject}` call as A1 with `{"compatibility":"BACKWARD_TRANSITIVE"}`.

Sources: [Protobuf serdes](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/serdes-protobuf.html), [schema evolution](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/schema-evolution.html).

## A3 Keep the `_schemas` replication factor at 3

The effective value is the lesser of the setting and the live broker count. With one broker, `_schemas` gets RF 1: acceptable for development only.

```properties
kafkastore.topic=_schemas
kafkastore.topic.replication.factor=3
```

Sources: [deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html).

## A4 Disable unclean leader election for `_schemas`

Why: a replica outside the ISR must not become leader, or committed schema records are lost. The multi-DC page repeats the requirement for the secondary DC Kafka cluster.

```bash
# Representative: the exact CLI call is (unverified), the setting name comes from the deployment page
kafka-configs --bootstrap-server broker:9092 --alter --entity-type topics \
  --entity-name _schemas --add-config unclean.leader.election.enable=false
```

Sources: [deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [multi-DC](https://docs.confluent.io/platform/8.4/schema-registry/multidc.html).

## A5 Use Kafka-based primary election

ZooKeeper-based election and `kafkastore.connection.url` were removed in Confluent Platform 7.0.0. The multi-DC page says "Use Kafka based primary election in all cases."

```properties
kafkastore.bootstrap.servers=SASL_SSL://broker-1:9093,SASL_SSL://broker-2:9093,SASL_SSL://broker-3:9093
```

Sources: [deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [multi-DC](https://docs.confluent.io/platform/8.4/schema-registry/multidc.html), [config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html).

## A6 Set a resolvable `host.name` on every node

Why: secondaries forward writes to the primary. The Docker default is the Java canonical hostname, "which may not always be resolvable in a Docker environment".

```yaml
environment:
  SCHEMA_REGISTRY_HOST_NAME: schema-registry-1
  SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: "broker:29092"
  SCHEMA_REGISTRY_LISTENERS: "http://0.0.0.0:8081"
```

Sources: [config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html), [deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [Docker config reference](https://docs.confluent.io/platform/8.4/installation/docker/config-reference.html), [API](https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html).

## A7 One `schema.registry.group.id` per cluster

All nodes of one cluster share one value. Each separate cluster on a shared Kafka cluster gets its own. The default is `schema-registry`, and the cluster ID takes its name from the group ID.

```properties
schema.registry.group.id=schema-registry-prod
```

Whether the Docker environment variable form of this key works as the Docker naming rule suggests is (unverified), see [unverified and risks](./unverified-and-risks.md) U4.

Sources: [multi-DC](https://docs.confluent.io/platform/8.4/schema-registry/multidc.html), [config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html).

## A8 Enable normalization

Why: semantically identical schemas written differently then map to one schema and one ID. Without it they are registered as separate schemas. The default is `false` for the serializers and for the `normalize` query parameter on register.

```java
props.put("normalize.schemas", true);   // AbstractKafkaSchemaSerDeConfig.NORMALIZE_SCHEMAS, default false
```

```bash
# Per registry: "normalize": true in PUT /config, or per call
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" --data @schema.json \
  "https://schema-registry:8081/subjects/orders-value/versions?normalize=true"
```

Sources: [serdes overview](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/index.html), [serializer config source at v8.4.0](https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/schema-serializer/src/main/java/io/confluent/kafka/serializers/AbstractKafkaSchemaSerDeConfig.java), [API](https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html).

## A9 Basic-auth credentials on clients

Use `basic.auth.credentials.source=USER_INFO` and `basic.auth.user.info`. The key `schema.registry.basic.auth.user.info` is marked `@Deprecated` in the client source (one source file, medium confidence, M20). The documented default of the credentials source conflicts with the source default (unverified, U2), so the value is set explicitly.

```java
props.put("schema.registry.url", "https://schema-registry:8081");
props.put("basic.auth.credentials.source", "USER_INFO");
props.put("basic.auth.user.info", System.getenv("SR_USER") + ":" + System.getenv("SR_PASSWORD"));
```

Sources: [client configs](https://docs.confluent.io/platform/8.4/schema-registry/sr-client-configs.html), [client config source at v8.4.0](https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/client/src/main/java/io/confluent/kafka/schemaregistry/client/SchemaRegistryClientConfig.java).

## Verification

```bash
# Representative, Schema Registry 8.4.0
curl -s http://localhost:8081/subjects
# Expected: [] on a fresh registry (the repository README quickstart uses GET /subjects)
kafka-topics --bootstrap-server localhost:9092 --describe --topic _schemas
# Expected: PartitionCount: 1, cleanup.policy=compact
```

The `GET /config` response field name is (unverified), U7.
