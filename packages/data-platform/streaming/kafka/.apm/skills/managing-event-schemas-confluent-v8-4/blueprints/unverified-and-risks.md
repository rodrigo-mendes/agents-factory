# Unverified and risks register, Confluent Schema Registry 8.4.0

Back to [SKILL.md](../SKILL.md). Provenance: the official pages in the [Source Bibliography](#source-bibliography) (read 2026-11-04). Conflicts (U1, U2, U3) and irresolvable items (I1, I2, I3) are not resolved here: a human must verify them.

## Version-lifetime risk

- Confluent Schema Registry 8.4.0 (Confluent Platform 8.4.0) was released 2026-10-27 per the Confluent Platform support table; the research date is 2026-11-04 (medium confidence, M17). The changelog says "Released October 2026". The Docker Hub tag 8.4.0 was pushed 2026-10-26 and the Maven metadata shows release 8.4.0.
- GitHub shows build tags v8.4.1-29 and v8.5.0-4xx dated 2026-11-04. They are CI build tags, not releases: no 8.4.1 image or Maven artifact was seen. **Check for an 8.4.1 release before shipping.**
- Support: Community end of support 2027-10-27, Enterprise 2028-10-27, Platinum 2029-10-27 (medium confidence, M17).
- No CVE lookup was done for 8.4.0 (unverified, U17).
- Do not apply this skill to 7.x or to 8.5 builds.

## Unverified (U1..U23): 23 items

| ID | Item | Tag | Note |
|---|---|---|---|
| U1 | Default `key/value.subject.name.strategy`: the docs name `TopicNameStrategy`, the 8.4.0 source defaults to `AssociatedNameStrategy` with `TopicNameStrategy` fallback | (unverified) | Conflict between official sources. Same behavior unless associations exist. Set the strategy explicitly |
| U2 | Default of `basic.auth.credentials.source`: client-config page says `STATIC_TOKEN`, serializer source says `URL` | (unverified) | Conflict. Set it explicitly |
| U3 | Kafka Streams supported compatibility types: "only BACKWARD" vs FULL, FULL_TRANSITIVE, BACKWARD_TRANSITIVE on the same page | (unverified) | Conflict in wording. Not resolved |
| U4 | Environment variable form of `schema.registry.group.id` under the Docker naming rule | (unverified) | Rule applied, result not tested |
| U5 | Whether the image honors `SCHEMA_REGISTRY_OPTS` for the JAAS file | (unverified) | Documented for `schema-registry-start` |
| U6 | The `kafkastore` SASL JAAS config key | (unverified) | Not captured from the config page |
| U7 | `GET /config` response field name, and the register response shape beyond `id` | (unverified) | Check against your server |
| U8 | Package name of the JSON Schema serializer classes | (unverified) | Page gives class names only |
| U9 | `kafka-clients` version paired with serdes 8.4.0 | (unverified) | Compare with U21 (bundled Kafka version) |
| U10 | Request body that sets the `LOGICAL` compatibility policy | (unverified) | Not captured from the API page |
| U11 | Whether `mode.mutability` defaults to false | (unverified) | API page says `PUT /mode` needs it true |
| U12 | Header-ID interop with non-Confluent consumers | (unverified) | Inference from the 5-byte prefix format |
| U13 | Licensing of schema contexts used without Schema Linking | (unverified) | Contexts page read in part |
| U14 | Both Compose files (development stack and hardened node) as tested wholes | (unverified) | Researcher's assembly. The official file sets more `KAFKA_*` keys that were not captured |
| U15 | Container upgrade path (change image tag, restart one node at a time) | (unverified) | Upgrade page documents the package path |
| U16 | Impact of "Reject if/then/else and not schemas" on existing JSON Schemas | (unverified) | One changelog line only |
| U17 | CVE status of 8.4.0 | (unverified) | No lookup done |
| U18 | Exact `kafka-configs` call for `unclean.leader.election.enable` on `_schemas` | (unverified) | Setting name is from the deployment page |
| U19 | Maven plugin XML element names beyond `schemaRegistryUrls`, `subjects`, `schemaTypes`, `references` | (unverified) | Goals are named, XML not captured |
| U20 | Alerting on zero or two nodes reporting `master-slave-role=1` | (unverified) | Inference from the metric definition |
| U21 | That Confluent Platform 8.4 bundles Apache Kafka 4.4.x | (unverified) | Not confirmed on a page read at `/platform/8.4/`. Check the release notes of your CP build |
| U22 | Compatibility of Schema Registry 8.4.0 with Kafka 3.9 brokers | (unverified) | Not researched. No page read states it. Check the interoperability page for your broker version |
| U23 | Practical reading of the Community License (own use allowed, hosting a competing service is the Excluded Purpose) | (unverified) | Inference from the license text, not legal advice. Ask a lawyer |

## Irresolvable (I1..I3): 3 items

| ID | Item | Tag | Note |
|---|---|---|---|
| I1 | No official health-check endpoint for 8.4.0 | (unverified) | Docs search and the source were checked. Community files probe `GET /subjects`, not official. With auth on the probe needs credentials |
| I2 | License of the `confluentinc/cp-schema-registry` Docker image | (unverified) | Repo and docs license facts only. Redistribution of the image is not covered by the LICENSE files read |
| I3 | Release date of tag v8.4.0 on GitHub, and an official 8.4.0 date line in the release notes | (unverified) | Tag exists, date not shown. The support table gives 2026-10-27, Docker push 2026-10-26 |

## Medium confidence (M1..M20): 20 items

| ID | Claim | Tag |
|---|---|---|
| M1 | Pre-register schemas from CI and set `auto.register.schemas=false` in production. 8.4 Maven plugin page and 8.4 serdes and upgrade pages | (medium confidence) |
| M2 | Upgrade consumers first under BACKWARD types, producers first under FORWARD. Schema evolution page only | (medium confidence) |
| M3 | Use HTTPS whenever Basic auth is enabled. Security page only | (medium confidence) |
| M4 | Kafka ACLs for the Schema Registry principal on `_schemas`, `__consumer_offsets`, the cluster, the group and `_schemas_acl`. Security page only | (medium confidence) |
| M5 | `min.insync.replicas` above 1 for `_schemas`. Deployment page only | (medium confidence) |
| M6 | Back up `_schemas` with Replicator, S3 sink or console tools, restore to `_schemas_restore`. Deployment page only | (medium confidence) |
| M7 | Upgrade Schema Registry only after all Kafka brokers. Upgrade page only | (medium confidence) |
| M8 | Multi-DC: `leader.eligibility=false` on secondary nodes, one-way Replicator. Multi-DC page only | (medium confidence) |
| M9 | JVM flags and the 1 GB heap per about 10,000 schemas. Deployment page only | (medium confidence) |
| M10 | Pin the image to `8.4.0`, avoid `latest`. No official page says it | (medium confidence) |
| M11 | Keep `json.type.allowed.packages` empty. JSON Schema page read in part | (medium confidence) |
| M12 | `mock://` and `MockSchemaRegistry` are for tests only. Source file only, no docs page | (medium confidence) |
| M13 | Claims resting on partly read pages: JSON Schema drafts and defaults, `specific.avro.reader` default, monitoring metrics, Schema Linking keys, schema contexts | (medium confidence) |
| M14 | Use a new topic and migration instead of `NONE` for breaking changes. Schema evolution page only | (medium confidence) |
| M15 | Protobuf null fields cause NPE, use optional or wrapper types. Protobuf serdes page only | (medium confidence) |
| M16 | License split: Community License server, Apache 2.0 modules, Enterprise license for RBAC, Schema Linking and Schema ID Validation. Held at (medium confidence): the license pages were not re-read in full | (medium confidence) |
| M17 | Release and support dates, Java support, bundled Avro 1.12.1, changelog entries, JMX exporter and license-topic notes. Pages read at `/platform/current/`, not at `/platform/8.4/` | (medium confidence) |
| M18 | Do not upgrade to Schema Registry 8.x while a client is older than `kafka-schema-registry-client` 6.2. One 8.4 upgrade page plus the `/platform/current/` versions page | (medium confidence) |
| M19 | The `LOGICAL` compatibility policy conflicts with FORWARD and FORWARD_TRANSITIVE. Release-notes page at `/platform/current/` only | (medium confidence) |
| M20 | The client key `schema.registry.basic.auth.user.info` is deprecated. One client source file (a file at tag v8.4.0) plus the client configs page does not name it | (medium confidence) |

## Coverage limits (L1..L5): 5 items

| ID | Limit |
|---|---|
| L1 | Every page was read through WebFetch, which returns a model-written extract, not verbatim text. Docs pages are 128k to 295k characters, mostly navigation after the article body. Pages cited in Always Do or Never Do were read in all chunks |
| L2 | Pages read in part (first 100000 characters): Avro serdes (183307), SR overview (143024), schema contexts (128214), Schema Linking (203603), installation overview (130041, no Maven section), JSON Schema serdes (196027), monitoring (134544). The body ended in view for each except the installation overview |
| L3 | Release notes, changelog and versions pages were read at `/platform/current/`, which said Confluent Platform 8.4 at read time. Their `/platform/8.4/` equivalents were not fetched |
| L4 | Several `/platform/8.4/` pages show "Last updated" lines older than 12 months (SR overview and Avro serdes 2023-04-11, Maven plugin 2023-03-30). They are served in the 8.4 tree |
| L5 | Only the first GitHub tags page was read. Web search results (community pages) were not used as evidence |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Version Context and Ask First | U9, U21, U22, I1, U1, U12, U10, U3, U2 |
| (medium confidence) | SKILL.md Version Context, Ask First, Quick Reference | M17, M16, M1, M2, M8, M18, M19, M20 |
| (unverified) | always-do-patterns.md | U18, U4, U2, U7 |
| (medium confidence) | always-do-patterns.md | M20 |
| (unverified) | ask-first-decisions.md | U1, U12, U13, U10, U2, U15, U22 |
| (medium confidence) | ask-first-decisions.md | M1 to M20 as listed in its Register column and sections |
| (unverified) | deploy-compose.md | U14, U4, U5, U6, I1, I2 |
| (medium confidence) | deploy-compose.md | M3, M10 |
| (unverified) | compatibility-and-evolution.md | U3, U10, U19, U7, U11, U16 |
| (medium confidence) | compatibility-and-evolution.md | M14, M2, M13, M15, M17, M19 |
| (unverified) | serdes-java.md | U12, U9, U21, U1, U8 |
| (medium confidence) | serdes-java.md | M13, M1, M11, M12, M18 |
| (unverified) | security-and-ha.md | U6, U11, U20, I1 |
| (medium confidence) | security-and-ha.md Security checklist | M3, M4, M16, M11 |
| (medium confidence) | security-and-ha.md | M16, M3, M8, M6, M5, M9, M13, M17, M20 |
| (unverified) | licensing.md | I2, U13, U23 |
| (medium confidence) | licensing.md | M16 |
| (unverified), (medium confidence) | evaluation-scenarios.md | U1, I2, I1, U17, M16 |
| (unverified), (medium confidence) | this file | U1 to U23, I1 to I3, M1 to M20 |

## Source Bibliography

All pages read 2026-11-04. Docs base: `https://docs.confluent.io/platform/8.4/`.

| ID | Title | URL |
|---|---|---|
| P1 | Release notes CP 8.4 (read at /current/) | https://docs.confluent.io/platform/current/release-notes/index.html |
| P2 | Component changelog 8.4.0 (read at /current/) | https://docs.confluent.io/platform/current/release-notes/changelog.html |
| P3 | Versions and interoperability (read at /current/) | https://docs.confluent.io/platform/current/installation/versions-interoperability.html |
| P4 | GitHub tags | https://github.com/confluentinc/schema-registry/tags |
| P5 | Docker Hub tags | https://hub.docker.com/v2/repositories/confluentinc/cp-schema-registry/tags?page_size=30&ordering=last_updated |
| P6 | Schema evolution and compatibility | https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/schema-evolution.html |
| P7 | Serdes overview and wire format | https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/index.html |
| P8 | Avro serdes (partly read) | https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/serdes-avro.html |
| P9 | Client configuration | https://docs.confluent.io/platform/8.4/schema-registry/sr-client-configs.html |
| P10 | Production deployment | https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html |
| P11 | Server configuration reference | https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html |
| P12 | Security overview | https://docs.confluent.io/platform/8.4/schema-registry/security/index.html |
| P13 | Repository at tag v8.4.0 | https://github.com/confluentinc/schema-registry/tree/v8.4.0 |
| P14 | License page | https://docs.confluent.io/platform/8.4/installation/license.html |
| P15 | LICENSE-ConfluentCommunity at v8.4.0 | https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/LICENSE-ConfluentCommunity |
| P16 | LICENSE at v8.4.0 | https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/LICENSE |
| P17 | README at v8.4.0 | https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/README.md |
| P18 | REST API reference | https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html |
| P19 | Docker configuration reference | https://docs.confluent.io/platform/8.4/installation/docker/config-reference.html |
| P20 | cp-all-in-one community Compose, 8.4.0-post | https://github.com/confluentinc/cp-all-in-one/blob/8.4.0-post/cp-all-in-one-community/docker-compose.yml |
| P21 | Schema Registry overview (partly read) | https://docs.confluent.io/platform/8.4/schema-registry/index.html |
| P22 | Multi-datacenter | https://docs.confluent.io/platform/8.4/schema-registry/multidc.html |
| P23 | Fundamentals | https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/index.html |
| P24 | Schema contexts (partly read) | https://docs.confluent.io/platform/8.4/schema-registry/schema-contexts-cp.html |
| P25 | Schema Linking (partly read) | https://docs.confluent.io/platform/8.4/schema-registry/schema-linking-cp.html |
| P26 | Schema deletion guidelines | https://docs.confluent.io/platform/8.4/schema-registry/schema-deletion-guidelines.html |
| P28 | AbstractKafkaSchemaSerDeConfig.java at v8.4.0 | https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/schema-serializer/src/main/java/io/confluent/kafka/serializers/AbstractKafkaSchemaSerDeConfig.java |
| P29 | AssociatedNameStrategy.java at v8.4.0 | https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/schema-serializer/src/main/java/io/confluent/kafka/serializers/subject/AssociatedNameStrategy.java |
| P30 | SchemaRegistryClientConfig.java at v8.4.0 | https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/client/src/main/java/io/confluent/kafka/schemaregistry/client/SchemaRegistryClientConfig.java |
| P31 | MockSchemaRegistry.java at v8.4.0 | https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/client/src/main/java/io/confluent/kafka/schemaregistry/testutil/MockSchemaRegistry.java |
| P32 | Installation overview (partly read) | https://docs.confluent.io/platform/8.4/installation/overview.html |
| P33 | Maven plugin | https://docs.confluent.io/platform/8.4/schema-registry/develop/maven-plugin.html |
| P34 | Maven metadata, kafka-avro-serializer | https://packages.confluent.io/maven/io/confluent/kafka-avro-serializer/maven-metadata.xml |
| P35 | Maven metadata, kafka-protobuf-serializer | https://packages.confluent.io/maven/io/confluent/kafka-protobuf-serializer/maven-metadata.xml |
| P36 | Maven metadata, kafka-json-schema-serializer | https://packages.confluent.io/maven/io/confluent/kafka-json-schema-serializer/maven-metadata.xml |
| P37 | Upgrade guide | https://docs.confluent.io/platform/8.4/installation/upgrade.html |
| P38 | Protobuf serdes | https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/serdes-protobuf.html |
| P39 | JSON Schema serdes (partly read) | https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/serdes-json.html |
| P40 | Monitoring (partly read) | https://docs.confluent.io/platform/8.4/schema-registry/monitoring.html |
