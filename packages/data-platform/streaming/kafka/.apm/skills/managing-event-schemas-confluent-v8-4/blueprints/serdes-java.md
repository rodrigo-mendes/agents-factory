# Java serdes, Confluent Schema Registry 8.4.0

Back to [SKILL.md](../SKILL.md). Provenance: official pages read 2026-11-04. Sources: [serdes overview](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/index.html), [client configs](https://docs.confluent.io/platform/8.4/schema-registry/sr-client-configs.html), [serializer config source at v8.4.0](https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/schema-serializer/src/main/java/io/confluent/kafka/serializers/AbstractKafkaSchemaSerDeConfig.java).

## Wire format

Java serdes write a 5-byte prefix: magic byte 0 and a big-endian 4-byte schema ID, followed by Protobuf message indexes when the format is Protobuf. Opt-in header mode (CP 8.1.1 and later) writes a 16-byte GUID to the headers `__key_schema_id` and `__value_schema_id` instead. Set `key.schema.id.serializer` or `value.schema.id.serializer` to `io.confluent.kafka.serializers.schema.id.HeaderSchemaIdSerializer`. The default serializer is `PrefixSchemaIdSerializer`, the default deserializer `DualSchemaIdDeserializer` (header first, then payload). Every consumer needs serdes 8.1.1 or later. Interop with non-Confluent consumers is (unverified), U12.

## Dependencies

```xml
<repositories>
  <repository>
    <id>confluent</id>
    <url>https://packages.confluent.io/maven/</url>
  </repository>
</repositories>
<dependency>
  <groupId>io.confluent</groupId>
  <artifactId>kafka-avro-serializer</artifactId>
  <version>8.4.0</version>
</dependency>
```

`kafka-protobuf-serializer` and `kafka-json-schema-serializer` 8.4.0 are listed in the repository metadata. The `kafka-clients` version to pair with serdes 8.4.0 is (unverified), U9. That CP 8.4 bundles Kafka 4.4.x is (unverified), U21. Sources: Maven metadata for [avro](https://packages.confluent.io/maven/io/confluent/kafka-avro-serializer/maven-metadata.xml), [protobuf](https://packages.confluent.io/maven/io/confluent/kafka-protobuf-serializer/maven-metadata.xml), [JSON Schema](https://packages.confluent.io/maven/io/confluent/kafka-json-schema-serializer/maven-metadata.xml).

## Avro producer and consumer

```java
// Confluent serdes 8.4.0, Avro producer
Properties props = new Properties();
props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "broker:9092");
props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, io.confluent.kafka.serializers.KafkaAvroSerializer.class);
props.put("schema.registry.url", "https://schema-registry:8081");
props.put("basic.auth.credentials.source", "USER_INFO");
props.put("basic.auth.user.info", System.getenv("SR_USER") + ":" + System.getenv("SR_PASSWORD"));
props.put("normalize.schemas", true);
```

```java
// Consumer, specific records (specific.avro.reader defaults to false, medium confidence M13)
props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, io.confluent.kafka.serializers.KafkaAvroDeserializer.class);
props.put("specific.avro.reader", true);
```

`normalize.schemas` and the credentials keys are the Always Do items A8 and A9 in [always-do-patterns](./always-do-patterns.md).

## Registration behavior

Defaults in the 8.4.0 source: `auto.register.schemas=true`, `use.latest.version=false`, `normalize.schemas=false`. Pre-registering from CI with `auto.register.schemas=false` is a single-source practice (medium confidence, M1), see [ask-first-decisions](./ask-first-decisions.md). If you choose it, `use.latest.version=true` is only read when `auto.register.schemas=false`.

```java
props.put("auto.register.schemas", false);   // medium confidence, M1
props.put("use.latest.version", true);       // only read when auto.register.schemas=false
```

## Subject name strategy

Keys: `key.subject.name.strategy`, `value.subject.name.strategy`. Docs name `TopicNameStrategy` (`<topic>-key`, `<topic>-value`) as default. The 8.4.0 source defaults to `AssociatedNameStrategy`, which falls back to `TopicNameStrategy` when the topic has no association, unless `subject.name.strategy.fallback.type` is `RECORD`, `TOPIC_RECORD` or `NONE` (unverified, U1). Behavior is the same unless associations exist. Not resolved here: set the strategy explicitly.

## Protobuf and JSON Schema

- Protobuf: `io.confluent.kafka.serializers.protobuf.KafkaProtobufSerializer` and `KafkaProtobufDeserializer` ([Protobuf serdes](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/serdes-protobuf.html)).
- JSON Schema: `KafkaJsonSchemaSerializer` and `KafkaJsonSchemaDeserializer`. The package name is (unverified), U8. Keep `json.type.allowed.packages` empty unless javaType resolution is needed (medium confidence, M11).

## Tests: mock registry (medium confidence)

```java
// Tests only, source-only evidence (medium confidence, M12)
String scope = "orders-test";
props.put("schema.registry.url", "mock://" + scope);
SchemaRegistryClient client = MockSchemaRegistry.getClientForScope(scope);
// produce and consume with KafkaAvroSerializer/Deserializer sharing the same URL
MockSchemaRegistry.dropScope(scope);   // fresh registry next time
```

Source: [MockSchemaRegistry at v8.4.0](https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/client/src/main/java/io/confluent/kafka/schemaregistry/testutil/MockSchemaRegistry.java). No documentation page was found.

## Client version floor

Every producer and consumer must use `kafka-schema-registry-client` 6.2 or later before Schema Registry moves to 8.x (medium confidence, M18; see [ask-first-decisions](./ask-first-decisions.md#single-source-anti-patterns)).
