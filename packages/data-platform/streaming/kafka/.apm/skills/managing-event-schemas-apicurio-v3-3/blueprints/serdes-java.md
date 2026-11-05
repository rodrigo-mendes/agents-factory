# Java SerDes and Confluent compatibility, Apicurio Registry 3.3.4

Back to [SKILL.md](../SKILL.md). Pages read 2026-11-04: [SerDes usage](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-using-kafka-client-serdes.html) and [SerDes configuration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-kafka-client-serdes.html). Constants live in `SerdeConfig` (usage page).

## Dependency

```xml
<!-- Avro artifact opened at 3.3.4. Protobuf: apicurio-registry-protobuf-serde-kafka; JSON Schema: apicurio-registry-jsonschema-serde-kafka (unverified, U9: names and 3.3.4 versions not opened) -->
<dependency>
  <groupId>io.apicurio</groupId>
  <artifactId>apicurio-registry-avro-serde-kafka</artifactId>
  <version>3.3.4</version>
</dependency>
```

Use the version of the server. That the SerDes version should equal the server version is not stated on the pages read (unverified, U9). The 3.3.4 release was confirmed for the Avro artifact only.

## Producer and consumer (Avro)

```java
// Representative: class and property names from the usage and configuration pages.
Properties p = new Properties();
p.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka:9092");
p.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
p.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG,
      io.apicurio.registry.serde.avro.AvroKafkaSerializer.class.getName());
p.put("apicurio.registry.url", "https://registry.example.com/apis/registry/v3");
p.put("apicurio.registry.find-latest", "true");     // use the pre-registered schema
p.put("apicurio.registry.auto-register", "false");  // default value; production policy is Ask First (medium confidence, M2)
p.put("apicurio.registry.auth.service.token.endpoint",
      "https://idp.example.com/realms/registry/protocol/openid-connect/token");
p.put("apicurio.registry.auth.client.id", System.getenv("REGISTRY_CLIENT_ID"));
p.put("apicurio.registry.auth.client.secret", System.getenv("REGISTRY_CLIENT_SECRET"));
p.put("apicurio.registry.fault-tolerant-refresh", "true");

Properties c = new Properties();
c.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG,
      io.apicurio.registry.serde.avro.AvroKafkaDeserializer.class.getName());
c.put("apicurio.registry.url", "https://registry.example.com/apis/registry/v3");
c.put("apicurio.registry.use-specific-avro-reader", "true");   // generated classes
```

Keep client id and secret out of source code. The `fault-tolerant-refresh` line is recommended by the [best-practices page](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html).

- Protobuf: `io.apicurio.registry.serde.protobuf.ProtobufKafkaSerializer` and `ProtobufKafkaDeserializer`. The deserialized type is `DynamicMessage` unless `apicurio.registry.deserializer.value.return-class` is set.
- JSON Schema: `io.apicurio.registry.serde.jsonschema.JsonSchemaKafkaSerializer` and `JsonSchemaKafkaDeserializer`. `apicurio.registry.serde.validation-enabled` defaults to `true`. Auto-registration support conflicts between the two pages (unverified, U4).
- Resilience defaults: `check-period-ms` 30000, retry count 3, retry backoff 300 ms. `apicurio.registry.background-refresh-enabled` defaults to `false`.
- `apicurio.registry.tls.trust-all` stays `false`: the configuration page marks it not for production.

## Wire format and ID defaults in 3.3.x

| Setting | Default | Alternative |
|---|---|---|
| `apicurio.registry.use-id` | `contentId` | `globalId` |
| `apicurio.registry.headers.enabled` | `false` (magic byte + ID + data in the payload) | `true` |
| `apicurio.registry.id-handler` | `io.apicurio.registry.serde.Default4ByteIdHandler` | `Legacy8ByteIdHandler` |

Producers and consumers must agree on these three settings. That requirement is inferred from the wire-format description (unverified, U11). Mixed 2.x/3.x setups: Ask First.

## Artifact resolver strategy

Default `TopicIdStrategy`: artifact IDs `<topic>-key` and `<topic>-value`. Alternatives: `RecordIdStrategy` (Avro full name), `TopicRecordIdStrategy` (topic + full name), `SimpleTopicIdStrategy` (topic name only). Set `apicurio.registry.artifact-resolver-strategy` on the serializer only. The usage page says a record-ID strategy suits several topics that share one Avro type.

## Confluent-compatible API

Source: [ccompat](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-confluent-schema-registry-compatibility.html). Existing Confluent clients set `schema.registry.url=http://<host>:8080/apis/ccompat/v7` (v8 also fully supported). Limits:

- Exporters and Schema Linking unsupported (`GET /exporters` returns an empty list).
- KEK/DEK endpoints absent (404). Cluster Metadata API absent.
- Data Contract `metadata` and `ruleSet` are accepted but neither stored nor enforced.
- Avro responses are normalized to canonical compact JSON.
- `apicurio.ccompat.max-subjects` defaults to 1000.
- ID mode: by default (`apicurio.ccompat.legacy-id-mode.enabled=false`) the Confluent ID is the `contentId`, so identical content returns the same ID across subjects. The page recommends this mode. `true` maps IDs to `globalId`.
- Subjects map to the default group unless `apicurio.ccompat.group-concat.enabled=true` (separator `:`). The exact default subject-to-artifact mapping is not described (unverified, U12).
- Registration does not enforce the `BACKWARD` default unless a rule is set.

For Confluent Schema Registry itself, use `managing-event-schemas-confluent-v8-4`.

## Testing

No official mocking guidance exists in the 3.3.x pages read (unverified, U16). Two inferred options: run `apicurio/apicurio-registry:3.3.4` with default in-memory H2 as a throwaway test container (the Docker page says H2 is for development and testing), or unit-test producers with a Kafka `MockProducer` and keep the Apicurio SerDes for an integration test.
