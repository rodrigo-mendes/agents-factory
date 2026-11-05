---
name: managing-event-schemas-apicurio-v3-3
description: "Manages Kafka event schemas with Apicurio Registry 3.3.x (pinned 3.3.4): storage, rules, SerDes, security, upgrades. Use when running or reviewing Apicurio Registry 3.3. Not for Confluent Schema Registry (managing-event-schemas-confluent-v8-4), Registry 2.x or running a registry on Kubernetes."
---

# Managing event schemas with Apicurio Registry 3.3.4

> Version lock: every claim applies to **Apicurio Registry 3.3.x, pinned to 3.3.4** only. Research date **2026-11-04**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page.
> Provenance: the cited official pages (bibliography in [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)).

## Version Context

| Item | Value | Source (fetched 2026-11-04) |
|---|---|---|
| Apicurio Registry | 3.3.4, released 2026-11-03. Minor line 3.3.x since 3.3.0 (2026-06-08). Active | https://github.com/Apicurio/apicurio-registry/releases/tag/3.3.4 and https://github.com/Apicurio/apicurio-registry/releases/tag/3.3.0 |
| Support policy | The two most recent minor lines get security patches: 3.3.x and 3.2.x as of 2026-11-04. No dated end-of-life is published | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-versioning-support-policy.html |
| Container images | `apicurio/apicurio-registry:3.3.4` and `apicurio/apicurio-registry-ui:3.3.4` | https://hub.docker.com/v2/repositories/apicurio/apicurio-registry/tags?page_size=25&name=3.3 |
| Java SerDes | `io.apicurio:apicurio-registry-avro-serde-kafka` 3.3.4 confirmed on Maven Central. Protobuf and JSON Schema artifacts exist, their 3.3.4 version was not opened (unverified) | https://repo1.maven.org/maven2/io/apicurio/apicurio-registry-avro-serde-kafka/maven-metadata.xml |
| Registry Java runtime | page not recorded (unverified) | page not recorded |
| Kafka (including 3.9 brokers) and PostgreSQL versions supported | no support matrix found, so compatibility with 3.9 brokers is not stated (unverified, U2). The official sample compose uses `postgres:15` | https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/in-memory-with-auth/docker-compose.yml |
| License | Apache License, Version 2.0, read on branch main, not on the 3.3.4 tag (medium confidence) | https://raw.githubusercontent.com/Apicurio/apicurio-registry/main/LICENSE |

**Version-lifetime risk** (as of 2026-11-04; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- 3.3.4 was released 2026-11-03 and the research date is 2026-11-04. The 3.3 minor line has been out since 2026-06-08.
- 3.4.x docs are published but no 3.4.0 release appears on GitHub as of 2026-11-04. Do not mix 3.4.x docs into this skill.
- The release notes of 3.3.4 list bug fixes while the support policy says patches carry none (unverified, U5).

## Scope

In scope: Apicurio Registry 3.3.x as the schema registry for Kafka (Avro, Protobuf, JSON Schema), with PostgreSQL or KafkaSQL storage, on Docker Compose, with Java Kafka SerDes. Out of scope: Confluent Schema Registry (use `managing-event-schemas-confluent-v8-4`), Registry 2.x, Kubernetes operator content (Strimzi and Confluent for Kubernetes skills), Debezium, the Kafka broker itself (use `operating-kafka-v4-4`). The Strimzi and Confluent for Kubernetes skills cover Kafka itself and not a registry.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Ask-first decisions](./blueprints/ask-first-decisions.md)
- [Deploy with Docker Compose](./blueprints/deploy-compose.md)
- [Compatibility rules and schema evolution](./blueprints/compatibility-and-evolution.md)
- [Java SerDes and Confluent compatibility](./blueprints/serdes-java.md)
- [Security and high availability](./blueprints/security-and-ha.md)
- [Migration guide 2.x to 3.x](./blueprints/migration-guide.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

Code and verification commands for each item are in [always-do-patterns](./blueprints/always-do-patterns.md).

- **Use PostgreSQL (`sql`) or KafkaSQL (`kafkasql`) storage outside development** — the default embedded H2 is for development and testing only ([Docker install](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-docker.html), [high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html)).
- **Create every KafkaSQL topic with `cleanup.policy=delete`, `retention.ms=-1` and `retention.bytes=-1`** — the registry refuses to start with other settings ([high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html), [secured Kafka](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-deploying-registry-secured-kafka.html), [migration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html), [storage](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-storage-openshift.html)).
- **Set a `COMPATIBILITY` rule explicitly** — with no rule configured, no rule is applied ([rules](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-intro-to-registry-rules.html), [ccompat](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-confluent-schema-registry-compatibility.html)).
- **Enable OIDC authentication on any shared registry** — every authentication and authorization option is off by default ([security](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-registry-security.html), [config reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html)).
- **Enable role-based authorization together with authentication** — authentication alone gives every identity the same access ([security](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-registry-security.html), [config reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html)).
- **Supply datasource credentials through `_FILE` variables** — file-based secrets instead of plain environment values ([Docker install](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-docker.html), [official pg-secrets compose](https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/pg-secrets/docker-compose.yml)).
- **Pin the image to the exact release tag `apicurio/apicurio-registry:3.3.4`** ([support policy](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-versioning-support-policy.html), [Docker Hub tags](https://hub.docker.com/v2/repositories/apicurio/apicurio-registry/tags?page_size=25&name=3.3)).
- **Take a storage backup and test the restore before any minor upgrade** ([support policy](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-versioning-support-policy.html), [high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html)).
- **Use the 3.x Avro SerDes artifact `io.apicurio:apicurio-registry-avro-serde-kafka` 3.3.4** — the 2.x `apicurio-registry-serdes-*` names were replaced ([migration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html), [Maven metadata](https://repo1.maven.org/maven2/io/apicurio/apicurio-registry-avro-serde-kafka/maven-metadata.xml)).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Which registry? | The request names no registry and no file is open: Apicurio (`managing-event-schemas-apicurio-v3-3`) or Confluent (`managing-event-schemas-confluent-v8-4`) | "Do you run Apicurio Registry 3.3 or Confluent Schema Registry 8.4?" |
| Storage backend | PostgreSQL (standard DB backup, needs HA Postgres) vs KafkaSQL (reuses Kafka, every replica replays the journal) (medium confidence) | "Which stateful platform do you operate and back up today, PostgreSQL or Kafka only?" |
| Compatibility level | `BACKWARD_TRANSITIVE` recommended for production by one official page (medium confidence) vs `BACKWARD` vs `FULL(_TRANSITIVE)` | "How long is topic retention, and how far can consumers lag?" |
| Upgrade order | Which side upgrades first per mode is not stated (unverified) | "Do you control both producers and consumers? Verify with a human before asserting an order" |
| Auto-registration | CI pre-registration with `auto-register=false` recommended by one page (medium confidence) vs runtime registration | "May producers create schemas at runtime, or only CI?" |
| Confluent clients | Native Apicurio SerDes vs Confluent clients on `/apis/ccompat/v7` (gaps: no KEK/DEK, no exporters) | "Must existing Confluent clients work unchanged, and do they use KEK/DEK, exporters or Data Contract rules?" |
| Schema ID and width | Defaults `contentId` + 4-byte handler differ from 2.x. Mixed 2.x/3.x settings not fully spelled out (unverified) | "Does any producer or consumer still run 2.x SerDes?" |
| Authentication mix | OIDC vs HTTP basic client credentials vs proxy-header vs Kubernetes auth (experimental) | "Which IdP exists, and do non-OIDC tools need basic credentials?" |
| Kafka connection security (KafkaSQL) | SCRAM over `SASL_SSL` vs OAuth vs TLS stores; interaction when both families are set is not documented (unverified, U13) | "Which Kafka listener security does the cluster use?" |
| Downgrade or rollback | Single page says migrations are forward-only (medium confidence); recovery is restore of a backup | "Is a restorable pre-upgrade backup in place?" |
| Journal topic partitions | Official docs show 1 and 3 partitions, no required count (unverified) | "Which partition count do you want? Verify with a human" |
| Patch released 2026-11-03 | 3.3.4 was released 2026-11-03, research date 2026-11-04 | "Pin 3.3.4 now, or wait for field reports on it?" |
| Protobuf or JSON Schema SerDes | Artifact names and 3.3.4 versions were not opened (unverified, U9); see [serdes-java](./blueprints/serdes-java.md) and ask-first section 12 | "Which schema format do the clients use? Verify the artifact version on Maven Central" |

Details: [ask-first-decisions](./blueprints/ask-first-decisions.md).

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Put log compaction (`compact` or `compact,delete`) on KafkaSQL topics ([high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html), [storage](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-storage-openshift.html)) | `cleanup.policy=delete`, `retention.ms=-1`, `retention.bytes=-1` |
| Run more than one replica on the default embedded H2 ([high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html), [Docker install](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-docker.html)) | `APICURIO_STORAGE_KIND=sql` with PostgreSQL, or `kafkasql` |
| Set a fixed KafkaSQL consumer group ID such as `REGISTRY_KAFKASQL_CONSUMER_GROUP_ID` ([high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html), [migration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html)) | `APICURIO_KAFKASQL_CONSUMER_GROUP_PREFIX` (default `apicurio-`) |
| Use 2.x variable names (`REGISTRY_DATASOURCE_URL`, `AUTH_ENABLED`) on a 3.3 server ([migration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html), [config reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html)) | `APICURIO_DATASOURCE_URL`, `QUARKUS_OIDC_TENANT_ENABLED`, and the required `APICURIO_STORAGE_KIND` |
| Add an Avro field without a default under a BACKWARD-family rule ([compatibility modes](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-compatibility-modes.html), [best practices](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html)) | `{"name":"f","type":["null","string"],"default":null}` |
| Remove a Protobuf field without reserving its number and name ([compatibility modes](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-compatibility-modes.html), [best practices](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html)) | `reserved 2; reserved "coupon";` |
| Run `latest-snapshot` images in production ([support policy](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-versioning-support-policy.html), [Docker Hub tags](https://hub.docker.com/v2/repositories/apicurio/apicurio-registry/tags?page_size=25&name=3.3)) | `apicurio/apicurio-registry:3.3.4` |
| Reuse the official sample compose files in production: they use `latest-snapshot` and CORS `*` ([in-memory-with-auth](https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/in-memory-with-auth/docker-compose.yml), [pg-secrets](https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/pg-secrets/docker-compose.yml), [security](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-registry-security.html)) | Pinned 3.3.4 image, explicit CORS origins, `_FILE` secrets |

Details: [never-do-patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| REST API base | `/apis/registry/v3` (v2 stays at `/apis/registry/v2`) | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html |
| Ports | 8080 API, 9000 management (health, metrics) | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html |
| Confluent-compatible API | `/apis/ccompat/v7` and `/apis/ccompat/v8` | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-confluent-schema-registry-compatibility.html |
| Artifact types for Kafka | `AVRO`, `PROTOBUF`, `JSON` | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-artifact-reference.html |
| Rule types, precedence | `VALIDITY`, `COMPATIBILITY`, `INTEGRITY`; artifact over group over global | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-intro-to-registry-rules.html |
| SerDes defaults | `use-id=contentId`, `headers.enabled=false`, `Default4ByteIdHandler`, `auto-register=false` | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-kafka-client-serdes.html |
| Artifact resolver default | `TopicIdStrategy` (`<topic>-key`, `<topic>-value`) | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-using-kafka-client-serdes.html |
| KafkaSQL journal topic default | `kafkasql-journal`; consumer group prefix `apicurio-` | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html |
| ccompat subject cap | `apicurio.ccompat.max-subjects` = 1000 | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-confluent-schema-registry-compatibility.html |
| Schema cache refresh | `apicurio.registry.check-period-ms` = 30000 | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-kafka-client-serdes.html |

## External Resources

All fetched 2026-11-04.

- [Apicurio Registry 3.3.x documentation](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/index.html)
- [Release 3.3.4 (2026-11-03)](https://github.com/Apicurio/apicurio-registry/releases/tag/3.3.4)
- [Versioning and support policy](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-versioning-support-policy.html)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
