---
name: managing-event-schemas-confluent-v8-4
description: "Manages Kafka schemas with Confluent Schema Registry 8.4.0: compatibility, _schemas topic, serdes, security, licensing. Use when running or reviewing Confluent Schema Registry 8.4. Not for Apicurio (managing-event-schemas-apicurio-v3-3) or Kubernetes (operating-kafka-confluent-kubernetes-v3-4)."
---

# Managing event schemas with Confluent Schema Registry 8.4.0

> Version lock: every claim applies to **Confluent Schema Registry 8.4.0 (Confluent Platform 8.4.0)** only. Research date **2026-11-04**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page.
> Provenance: the cited official pages (bibliography in [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)).

## Version Context

| Item | Value | Source (fetched 2026-11-04) |
|---|---|---|
| Schema Registry | 8.4.0, released 2026-10-27, research date 2026-11-04 (medium confidence). Docker Hub tag pushed 2026-10-26 | https://docs.confluent.io/platform/current/installation/versions-interoperability.html and https://hub.docker.com/v2/repositories/confluentinc/cp-schema-registry/tags?page_size=30&ordering=last_updated |
| Support | Community end of support 2027-10-27, Enterprise 2028-10-27, Platinum 2029-10-27 (medium confidence) | https://docs.confluent.io/platform/current/installation/versions-interoperability.html |
| Kafka bundled | CP 8.4 bundles Apache Kafka 4.4.x (unverified, U21). Kafka 4.4.0 itself was released 2026-10-22 | https://docs.confluent.io/platform/current/release-notes/index.html |
| Java (server) | Supported 25, 21, 17; 21 recommended (medium confidence) | https://docs.confluent.io/platform/current/installation/versions-interoperability.html |
| Container image | `confluentinc/cp-schema-registry:8.4.0` | https://hub.docker.com/v2/repositories/confluentinc/cp-schema-registry/tags?page_size=30&ordering=last_updated |
| Java serdes | `io.confluent:kafka-{avro,protobuf,json-schema}-serializer` 8.4.0, repository `https://packages.confluent.io/maven/`. Paired `kafka-clients` version not recorded (unverified) | https://packages.confluent.io/maven/io/confluent/kafka-avro-serializer/maven-metadata.xml |
| License | Confluent Community License v1.0 for the server, Apache 2.0 for listed client and serde modules (medium confidence). See [licensing](./blueprints/licensing.md) | https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/README.md and https://docs.confluent.io/platform/8.4/installation/license.html |
| Compatibility with 3.9 brokers | Not researched (unverified, U22) | page not recorded |
| Health endpoint | No official health-check endpoint found (unverified) | page not recorded |

**Version-lifetime risk** (as of 2026-11-04; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- 8.4.0 was released 2026-10-27. GitHub already shows unreleased 8.4.1 build tags (CI tags, not releases). **Check for an 8.4.1 release before shipping.**
- 8.5.0 build tags exist. Do not apply this skill to 8.5 or to 7.x (ZooKeeper election options, no header IDs).

## Scope

In scope: Confluent Schema Registry 8.4.0 as the schema registry for Kafka (Avro, Protobuf, JSON Schema), the `_schemas` topic, Docker Compose, Java serdes, REST API, security options and the license split. Out of scope: Apicurio Registry (use `managing-event-schemas-apicurio-v3-3`), Kubernetes deployment (use `operating-kafka-confluent-kubernetes-v3-4`), the Kafka broker (use `operating-kafka-v4-4`), Debezium.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Ask-first decisions](./blueprints/ask-first-decisions.md)
- [Deploy with Docker Compose](./blueprints/deploy-compose.md)
- [Compatibility rules and schema evolution](./blueprints/compatibility-and-evolution.md)
- [Java serdes](./blueprints/serdes-java.md)
- [Security and high availability](./blueprints/security-and-ha.md)
- [Licensing](./blueprints/licensing.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

Code and verification commands for each item are in [always-do-patterns](./blueprints/always-do-patterns.md).

- **Set the compatibility level explicitly** with `schema.compatibility.level` or `PUT /config` and `PUT /config/{subject}` ([config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html), [schema evolution](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/schema-evolution.html), [API](https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html)).
- **Use `BACKWARD_TRANSITIVE` for Protobuf subjects** ([Protobuf serdes](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/serdes-protobuf.html), [schema evolution](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/schema-evolution.html)).
- **Keep `kafkastore.topic.replication.factor=3` on a cluster with at least 3 live brokers** ([config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html), [deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html)).
- **Set `unclean.leader.election.enable=false` on the Kafka cluster that holds `_schemas`** ([deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [multi-DC](https://docs.confluent.io/platform/8.4/schema-registry/multidc.html)).
- **Use Kafka-based primary election by setting `kafkastore.bootstrap.servers` on every node** ([deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [multi-DC](https://docs.confluent.io/platform/8.4/schema-registry/multidc.html), [config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html)).
- **Set `host.name` (`SCHEMA_REGISTRY_HOST_NAME` in Docker) on every node of a multi-node cluster to a name the other nodes resolve** ([config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html), [deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [Docker config](https://docs.confluent.io/platform/8.4/installation/docker/config-reference.html)).
- **Give all nodes of one cluster the same `schema.registry.group.id`** ([multi-DC](https://docs.confluent.io/platform/8.4/schema-registry/multidc.html), [config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html)).
- **Give each separate Schema Registry cluster on a shared Kafka cluster its own `schema.registry.group.id`** ([multi-DC](https://docs.confluent.io/platform/8.4/schema-registry/multidc.html), [config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html)).
- **Enable schema normalization with `normalize.schemas=true` or `"normalize": true` in `/config`** ([serdes overview](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/index.html), [serializer config source](https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/schema-serializer/src/main/java/io/confluent/kafka/serializers/AbstractKafkaSchemaSerDeConfig.java), [API](https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html)).
- **Configure client Basic auth with `basic.auth.credentials.source=USER_INFO` and `basic.auth.user.info`** ([client configs](https://docs.confluent.io/platform/8.4/schema-registry/sr-client-configs.html), [client config source](https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/client/src/main/java/io/confluent/kafka/schemaregistry/client/SchemaRegistryClientConfig.java)).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Which registry? | The request names no registry and no file is open: Confluent (`managing-event-schemas-confluent-v8-4`) or Apicurio (`managing-event-schemas-apicurio-v3-3`) | "Do you run Confluent Schema Registry 8.4 or Apicurio Registry 3.3?" |
| Compatibility type per subject | BACKWARD (default), BACKWARD_TRANSITIVE, FORWARD, FULL, NONE. Upgrade order per type rests on one page (medium confidence) | "How many schema versions must stay readable, and which side upgrades first?" |
| Subject name strategy | Docs name `TopicNameStrategy` as default, the 8.4.0 source defaults to `AssociatedNameStrategy` with fallback (unverified) | "Do topic-subject associations exist? Verify the strategy explicitly" |
| Schema ID location | Payload prefix (default) vs header GUID since 8.1.1. Interop with non-Confluent consumers (unverified) | "Does any consumer use serdes older than 8.1.1 or a non-Confluent deserializer?" |
| Pre-registration | CI registration with `auto.register.schemas=false` vs runtime registration (medium confidence) | "May producers create schemas at runtime, or only CI?" |
| Authentication and authorization | HTTPS plus Basic, mTLS, or RBAC and ACL authorizers that need an Enterprise license (medium confidence) | "Do you hold a Confluent Enterprise license?" |
| Multi-cluster sharing | Replicator of `_schemas` with `leader.eligibility=false` (medium confidence) vs Schema Linking (Enterprise, medium confidence) | "Which topology and license do you have?" |
| `LOGICAL` compatibility policy | One release-notes page says it conflicts with FORWARD types (medium confidence, M19). Request body not captured (unverified) | "Which subjects inherit FORWARD?" Move FORWARD subjects to a backward-family type before setting `LOGICAL` |
| Clients older than 6.2 | Schema Registry 8.x adds JSON response fields that older clients may fail on (medium confidence, M18) | "Does any client use `kafka-schema-registry-client` older than 6.2? Upgrade clients first" |
| Deprecated Basic-auth key | The client source marks `schema.registry.basic.auth.user.info` deprecated (medium confidence, M20) | "Do clients still set the old key?" |
| Kafka Streams consumers | Official wording on supported types is inconsistent (unverified) | "Do Kafka Streams apps consume the topic?" |
| Basic-auth credentials source | Docs default `STATIC_TOKEN`, serializer source default `URL` (unverified) | "Set it explicitly: which source do you use?" |
| Release 8.4.0 of 2026-10-27 | 8.4.0 released 2026-10-27, 8.4.1 builds exist | "Ship 8.4.0 now, or wait for 8.4.1?" |

Details: [ask-first-decisions](./blueprints/ask-first-decisions.md).

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Create `_schemas` with more than one partition or a delete cleanup policy ([deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [fundamentals](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/index.html), [config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html)) | 1 partition, `cleanup.policy=compact`, replication factor 3 |
| Hard-delete (`?permanent=true`) without a soft delete first, or while the schema ID still occurs in topic data ([API](https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html), [deletion guidelines](https://docs.confluent.io/platform/8.4/schema-registry/schema-deletion-guidelines.html)) | Soft delete the version, hard delete only when no topic holds the ID |
| Configure ZooKeeper-based election with `kafkastore.connection.url` ([deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [multi-DC](https://docs.confluent.io/platform/8.4/schema-registry/multidc.html)) | `kafkastore.bootstrap.servers` |

Details: [never-do-patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Default compatibility | `backward`, non-transitive | https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html |
| State topic | `_schemas`, single partition, compacted, RF 3 default | https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html |
| Group ID default | `schema-registry` | https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html |
| Wire format | magic byte 0, 4-byte big-endian schema ID, Protobuf message indexes after | https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/index.html |
| REST content type | `application/vnd.schemaregistry.v1+json` | https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html |
| `normalize.schemas` default | `false` | https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/schema-serializer/src/main/java/io/confluent/kafka/serializers/AbstractKafkaSchemaSerDeConfig.java |
| `auto.register.schemas` default | `true` | https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/schema-serializer/src/main/java/io/confluent/kafka/serializers/AbstractKafkaSchemaSerDeConfig.java |
| Error codes | 40401 subject, 40402 version, 409 incompatible, 42201 schema, 42203 compatibility, 42204 mode | https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html |
| Bundled Avro | 1.12.1 (medium confidence) | https://docs.confluent.io/platform/current/release-notes/changelog.html |
| Official Compose | CP 8.4.0 KRaft combined mode, port 8081 | https://github.com/confluentinc/cp-all-in-one/blob/8.4.0-post/cp-all-in-one-community/docker-compose.yml |

## External Resources

All fetched 2026-11-04.

- [Schema Registry 8.4 documentation](https://docs.confluent.io/platform/8.4/schema-registry/index.html)
- [Release notes CP 8.4](https://docs.confluent.io/platform/current/release-notes/index.html)
- [Versions and interoperability](https://docs.confluent.io/platform/current/installation/versions-interoperability.html)
- [Source at tag v8.4.0](https://github.com/confluentinc/schema-registry/tree/v8.4.0)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
