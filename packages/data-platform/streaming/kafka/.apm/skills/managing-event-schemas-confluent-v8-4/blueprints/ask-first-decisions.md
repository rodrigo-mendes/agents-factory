# Ask-first decisions, Confluent Schema Registry 8.4.0

Back to [SKILL.md](../SKILL.md). Provenance: official pages read 2026-11-04. Items here rest on a single source, a source with a conflict, or a partly read page. Ids refer to [unverified and risks](./unverified-and-risks.md).

## Decisions that need the user

| Decision | Options and tradeoff | Ask | Register |
|---|---|---|---|
| Which registry? | The request names no registry and no file is open: Confluent (`managing-event-schemas-confluent-v8-4`) or Apicurio (`managing-event-schemas-apicurio-v3-3`) | "Do you run Confluent Schema Registry 8.4 or Apicurio Registry 3.3?" | none |
| Kafka 3.9 brokers | Compatibility of Schema Registry 8.4.0 with 3.9 brokers was not researched (unverified) | "Which broker version runs? Check the Confluent interoperability page for it" | U22 |
| Compatibility type | BACKWARD (default, checks X-1), BACKWARD_TRANSITIVE, FORWARD(_TRANSITIVE), FULL(_TRANSITIVE), NONE. See [compatibility](./compatibility-and-evolution.md) | "How many versions must stay readable, which side upgrades first, do Kafka Streams or Flink consume the topic?" | M2, U3 |
| Subject name strategy | `TopicNameStrategy`, `RecordNameStrategy`, `TopicRecordNameStrategy`, `AssociatedNameStrategy`. Docs say TopicNameStrategy is the default, the 8.4.0 source defaults to AssociatedNameStrategy with TopicNameStrategy fallback (unverified) | "Do topic-subject associations exist? Set `key/value.subject.name.strategy` explicitly" | U1 |
| Schema ID location | Payload prefix (default) vs header GUID from CP 8.1.1. Non-Confluent consumers expecting the 5-byte prefix may break (unverified) | "Any consumer on serdes older than 8.1.1 or a non-Confluent deserializer?" | U12 |
| Pre-registration | CI registration (Maven plugin `register`, REST) with `auto.register.schemas=false` vs runtime registration (medium confidence) | "May producers create schemas at runtime, or only CI?" | M1 |
| Authentication and authorization | HTTPS plus Basic, mTLS, OAuth, or RBAC and ACL authorizers through the Security Plugins (Enterprise license, medium confidence) | "Do you hold a Confluent Enterprise license?" | M16 |
| Multi-cluster sharing | Replicator of `_schemas` plus `leader.eligibility=false` on secondary-DC nodes (medium confidence) vs Schema Linking (Enterprise, medium confidence) | "Which topology and license do you have?" | M8, M16 |
| Schema contexts alone | Independent scopes, qualified subject `:.mycontext:mysubject`. License when used without Schema Linking (unverified) | "Do you need contexts without Schema Linking?" | U13, M13 |
| `LOGICAL` policy | Conflicts with FORWARD types. Request body not captured (unverified) | "Which subjects inherit FORWARD?" | U10 |
| Credentials source | Docs default `STATIC_TOKEN`, source default `URL` (unverified). Always set it explicitly | "Which Basic-auth source do your clients use?" | U2 |
| Release age | 8.4.0 was released 2026-10-27 (medium confidence). 8.4.1 CI build tags exist | "Ship 8.4.0 now, or wait for an 8.4.1 release?" | M17 |
| Header IDs vs old clients | Header mode needs serdes 8.1.1 or later on every consumer | "Can all consumers be upgraded first?" | U12 |

## Single-source practices (medium confidence)

Each is a recommendation from one official page, or a page older than 12 months. Offer them, do not auto-apply.

- **Pre-register from CI, `auto.register.schemas=false` in production** (M1). The 8.4 Maven plugin page says the `register` goal "can be used in a continuous deployment pipeline". The 8.4 serdes docs show `auto.register.schemas=false` with `use.latest.version=true` and `latest.compatibility.strict=false` only for multiple event types per topic and for code-generated classes that differ slightly from the registered schema. The default of `auto.register.schemas` is `true`. The upgrade page also advises `false` when old Avro clients cannot be upgraded at once (memory leak against 8.x).
- **Upgrade order** (M2): under BACKWARD or BACKWARD_TRANSITIVE upgrade consumers first, under FORWARD producers first (schema evolution page only).
- **HTTPS with Basic auth** (M3): Basic auth "passes credentials in plain text" (security page only).
- **Kafka ACLs for the Schema Registry principal** (M4): Read, Write, DescribeConfigs and Describe on `_schemas`, Describe on `__consumer_offsets`, Create on the cluster, access to the `schema-registry` group. Add Read, Write and DescribeConfigs on `_schemas_acl` when the ACL Authorizer is used.
- **`min.insync.replicas` above 1** for `_schemas`, for example RF 3 with 2 (M5).
- **Back up `_schemas`** with Replicator, an S3 sink with ByteArrayConverter, or the console consumer and producer, and restore to a new topic such as `_schemas_restore` (M6).
- **Upgrade Schema Registry only after all Kafka brokers** (M7). Steps: brokers then controllers one at a time, clients at 6.2 or later, each Schema Registry node in a rolling fashion (`schema-registry-stop`, back up config, install 8.4.0, `schema-registry-start`), clients last. The container path (change the image tag, restart one node at a time) is (unverified), U15. RBAC environments: add the ResourceOwner role for the REST Proxy user on the license topic, default `_confluent-command`.
- **Multi-DC**: `leader.eligibility=false` on secondary nodes and one-way Replicator of `_schemas` from the active DC (M8). If the primary DC is lost, secondaries keep serving requests that do not write to Kafka but new registrations fail.
- **JVM**: `-Xms1g -Xmx1g -XX:MetaspaceSize=96m -XX:+UseG1GC -XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=35 -XX:G1HeapRegionSize=16M -XX:MinMetaspaceFreeRatio=50 -XX:MaxMetaspaceFreeRatio=80`. A 1 GB heap covers about 10,000 unique schemas (M9).
- **Pin the image** to `confluentinc/cp-schema-registry:8.4.0`, not `latest`. The official examples pin 8.4.0 and `latest` moved with the 8.4.0 push. No official page says "do not use latest" (M10).
- **Keep `json.type.allowed.packages` empty** unless javaType resolution is needed. `*` "is not recommended" (M11, page partly read).

Sources: [serdes overview](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/index.html), [Maven plugin](https://docs.confluent.io/platform/8.4/schema-registry/develop/maven-plugin.html), [upgrade](https://docs.confluent.io/platform/8.4/installation/upgrade.html), [security](https://docs.confluent.io/platform/8.4/schema-registry/security/index.html), [deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [multi-DC](https://docs.confluent.io/platform/8.4/schema-registry/multidc.html), [schema evolution](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/schema-evolution.html), [JSON Schema serdes](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/serdes-json.html).

## Single-source anti-patterns

| ❌ Don't | ✅ Instead | Register |
|---|---|---|
| Point a non-test application at `mock://` or use `MockSchemaRegistry` outside tests: it is an in-memory registry (source file only, medium confidence) | `https://schema-registry:8081` in production, `mock://<test-scope>` in tests with `MockSchemaRegistry.dropScope(scope)` in teardown | M12 |
| Use `NONE` to push an incompatible change into an existing topic (medium confidence) | A new topic and a migration | M14 |
| Use Basic auth over plain HTTP (medium confidence) | HTTPS listeners | M3 |
| Set `leader.eligibility=true` on secondary-DC nodes (medium confidence) | `leader.eligibility=false` | M8 |
| Set Protobuf fields to null: this causes NPE (medium confidence) | `optional` or wrapper types | M15 |
| Upgrade Schema Registry to 8.x while any client uses `kafka-schema-registry-client` older than 6.2: 8.x adds JSON response fields (`guid`, `subject`, `ts`, `deleted`) that older clients fail on. One versioned page plus a page not versioned to 8.4 (medium confidence) | Upgrade every client to 6.2 or later first, preferably to 8.4.0 serdes. The Avro memory-leak fix is in 7.5.16, 7.6.14, 7.7.12, 7.8.11, 7.9.10, 8.0.8 and later. Otherwise keep Schema Registry on 7.x | M18 |
| Set the `LOGICAL` compatibility policy on subjects with FORWARD or FORWARD_TRANSITIVE, or globally without checking inherited policies: the release notes say it conflicts with those types, and forcing past it with `?force=true` risks data corruption (medium confidence) | List each subject's inherited `compatibilityPolicy`, move FORWARD subjects to a backward-family type, then set `LOGICAL` where needed. The request body is (unverified), U10 | M19 |
| Set the client key `schema.registry.basic.auth.user.info`: marked deprecated in one client source file (medium confidence) | `basic.auth.credentials.source=USER_INFO` with `basic.auth.user.info` | M20 |

Sources: [MockSchemaRegistry source at v8.4.0](https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/client/src/main/java/io/confluent/kafka/schemaregistry/testutil/MockSchemaRegistry.java), [schema evolution](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/schema-evolution.html), [security](https://docs.confluent.io/platform/8.4/schema-registry/security/index.html), [multi-DC](https://docs.confluent.io/platform/8.4/schema-registry/multidc.html), [Protobuf serdes](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/serdes-protobuf.html), [versions and interoperability](https://docs.confluent.io/platform/current/installation/versions-interoperability.html), [upgrade guide](https://docs.confluent.io/platform/8.4/installation/upgrade.html), [release notes](https://docs.confluent.io/platform/current/release-notes/index.html), [client config source at v8.4.0](https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/client/src/main/java/io/confluent/kafka/schemaregistry/client/SchemaRegistryClientConfig.java).
