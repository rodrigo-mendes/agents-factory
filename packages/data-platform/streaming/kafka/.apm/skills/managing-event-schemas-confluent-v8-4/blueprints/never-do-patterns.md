# Never-do patterns, Confluent Schema Registry 8.4.0

Back to [SKILL.md](../SKILL.md). Provenance: official pages read 2026-11-04. Only N1 to N3 are here. The single-source anti-patterns are in [ask-first-decisions](./ask-first-decisions.md#single-source-anti-patterns). Commands are representative: adapt them to your environment.

## N1 Wrong `_schemas` topic (severity high)

Why: `_schemas` is the commit log and the source of truth. It "must be compacted to avoid data loss", it is a "durable single partition topic", and compaction keeps the latest value per key. Impact: schema, ID and config records are lost or misordered, which breaks deserialization of existing data.

```bash
# 🚫 WRONG
kafka-topics --bootstrap-server broker:9092 --create --topic _schemas \
  --partitions 6 --replication-factor 1 --config cleanup.policy=delete
```

```bash
# ✅ CORRECT: let Schema Registry create it, or create it exactly like this
kafka-topics --bootstrap-server broker:9092 --create --topic _schemas \
  --partitions 1 --replication-factor 3 --config cleanup.policy=compact
```

Sources: [deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [fundamentals](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/index.html), [config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html).

## N2 Hard delete without a soft delete, or with IDs still in use (severity high)

Why: a soft delete keeps the schema and its ID "so that the data can still be deserialized". A hard delete "removes all metadata, including schema IDs", and IDs are not reusable. The API page: "You must perform a soft delete first, then the hard delete." The deletion APIs are "primarily intended to be used" in development.

```bash
# 🚫 WRONG: no soft delete first, ID still in the topic
curl -X DELETE "https://sr:8081/subjects/orders-value?permanent=true"
```

```bash
# ✅ CORRECT
curl -X DELETE "https://sr:8081/subjects/orders-value/versions/3"               # 1. soft delete
curl -X DELETE "https://sr:8081/subjects/orders-value/versions/3?permanent=true" # 2. only when no topic holds the ID
```

`versions/latest` with `permanent=true` gives only a soft delete. A hard delete needs a version number.

Sources: [API](https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html), [deletion guidelines](https://docs.confluent.io/platform/8.4/schema-registry/schema-deletion-guidelines.html).

## N3 ZooKeeper-based election (severity high)

Why: removed in Confluent Platform 7.0.0. Kafka-based election is the only mode.

```properties
# 🚫 WRONG
kafkastore.connection.url=zookeeper:2181
```

```properties
# ✅ CORRECT
kafkastore.bootstrap.servers=PLAINTEXT://broker:29092
```

Sources: [deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [multi-DC](https://docs.confluent.io/platform/8.4/schema-registry/multidc.html).
