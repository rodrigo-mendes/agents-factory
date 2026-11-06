# Unverified and risks register, Apicurio Registry 3.3.4

Back to [SKILL.md](../SKILL.md). Provenance: the official pages in the [Source Bibliography](#source-bibliography) (research date 2026-11-04). Conflicts and gaps (U1, U2, U3, U4, U5, U22, U23) are not resolved here: a human must verify them.

## Version-lifetime risk

- Apicurio Registry 3.3.4 was released 2026-11-03 (GitHub release, Maven Central and Docker Hub agree); the research date is 2026-11-04. The 3.3 minor line has been out since 2026-06-08.
- Support policy: the two most recent minor lines get security patches, 3.3.x and 3.2.x as of 2026-11-04. No dated end-of-life is published (support policy, read 2026-11-04).
- 3.4.x docs exist but no 3.4.0 release appears on GitHub as of 2026-11-04. They were not used. Re-check the releases page before relying on this skill after a 3.4.0 release.
- License: Apache License, Version 2.0, read on branch main, not on the 3.3.4 tag (medium confidence, M9).

## Unverified (U1..U23): 23 items

| ID | Item | Tag | Note |
|---|---|---|---|
| U1 | Which side (producer or consumer) must upgrade first per compatibility mode. Not stated in the compatibility or best-practices pages | (unverified) | Irresolvable gap. Do not assert an order |
| U2 | Supported Kafka broker, Kafka client and PostgreSQL versions for 3.3.4. No matrix in the pages read | (unverified) | Irresolvable gap. Official sample uses `postgres:15`. Test your versions |
| U3 | Journal topic partition count: the migration page creates it with 1 partition, the storage and high availability pages show 3 | (unverified) | Conflict between official pages. No required count stated |
| U4 | JSON Schema serializer and auto-registration: usage page says unsupported, configuration page is silent | (unverified) | Conflict. Pre-register JSON Schemas in CI |
| U5 | Support policy says patches carry no bug fixes or features, the 3.3.4 notes list bug fixes and one CLI enhancement | (unverified) | Conflict. Read patch notes before upgrading |
| U6 | Environment-variable form of the global compatibility rule (`APICURIO_RULES_GLOBAL_COMPATIBILITY`) | (unverified) | Rules page names the property form only |
| U7 | Exact `pg_dump` flags for the pre-upgrade backup | (unverified) | The support page names `pg_dump` in custom format |
| U8 | `curl` present inside the registry image and the body shape of `/health/ready` | (unverified) | Check the image before a Compose healthcheck |
| U9 | Maven Central 3.3.4 for the Protobuf and JSON Schema SerDes, and that the SerDes version should equal the server version | (unverified) | Only the Avro artifact was opened |
| U10 | A 3.3 server falling back silently to default storage when given 2.x variable names | (unverified) | Inference |
| U11 | Exact settings for mixed 2.x/3.x clients, and that producers and consumers must agree on `use-id`, `headers.enabled` and `id-handler` | (unverified) | Inferred from the wire-format description |
| U12 | Default subject-to-artifact mapping in the Confluent-compatible API | (unverified) | Page describes the group setting only |
| U13 | Interaction of `APICURIO_KAFKA_COMMON_*` and `apicurio.kafkasql.security.*` when both are set | (unverified) | Not documented in pages read |
| U14 | Repository location of the migration scripts named on the migration page | (unverified) | Scripts are named, location not identified |
| U15 | Maven plugin XML for the CI registration gate | (unverified) | Goal `register` is named, XML not read |
| U16 | Official mocking or testing guidance | (unverified) | None found. Two inferred options in serdes-java |
| U17 | Release that introduced management port 9000 | (unverified) | Present in 3.2.x docs, introducing release unknown |
| U18 | Exact 2.x patch floor for 2.x SerDes against a 3.3 server | (unverified) | Page says "continue to work" |
| U19 | Container data path for the PostgreSQL volume in the Compose file | (unverified) | Official sample uses a named volume |
| U20 | The assembled Compose file as a tested whole | (unverified) | Every line traces to an official page, nobody ran the whole |
| U21 | Registry Java runtime version and image heap settings | (unverified) | page not recorded |
| U22 | Environment-variable spelling of role-based authorization: the migration page writes `APICURIO_AUTH_ROLE-BASED-AUTHORIZATION`, the compose and security examples use `APICURIO_AUTH_ROLE_BASED_AUTHORIZATION` | (unverified) | Property is `apicurio.auth.role-based-authorization`. Check the server log or the config endpoint after setting it |
| U23 | Environment-variable spelling of KafkaSQL topic auto-creation: the high availability page gives `APICURIO_KAFKASQL_TOPIC_AUTO-CREATE` with a hyphen | (unverified) | Property form not recorded. Check how the server reads it, or pre-create the topic and leave the setting out |

## Irresolvable (I1..): 0 items

No separate irresolvable class is kept. Two gaps are irresolvable (producer-versus-consumer upgrade order, Kafka and PostgreSQL support ranges): they appear once above as U1 and U2 with a human-verify note.

## Medium confidence (M1..M11): 11 items

| ID | Claim | Tag |
|---|---|---|
| M1 | `BACKWARD_TRANSITIVE` as the production compatibility level, and avoid `NONE` in production. Single official source: the best-practices page | (medium confidence) |
| M2 | Pre-register schemas in CI and set `auto-register=false` in production, with `FIND_OR_CREATE_VERSION` if auto-registration is unavoidable. Single source: the best-practices page. The default `false` is confirmed by the configuration page | (medium confidence) |
| M3 | Migrations are forward-only, no image downgrade, recover by restoring the backup. Single source: the support policy page | (medium confidence) |
| M4 | REST body shapes and paths (`CreateRule` body, `ifExists` values, `dryRun`, `/admin/rules`) from the 3.3.4 OpenAPI file, partly read | (medium confidence) |
| M5 | Version states `DRAFT` and `SUNSET` appear in the OpenAPI file but not in the glossary or artifact reference | (medium confidence) |
| M6 | KafkaSQL Kafka-authentication variable families (SCRAM, OAuth, TLS) taken from an operator-oriented page | (medium confidence) |
| M7 | Storage selection guidance, PostgreSQL versus KafkaSQL | (medium confidence) |
| M8 | Selection guidance, native SerDes versus Confluent clients on the ccompat API | (medium confidence) |
| M9 | License page read on branch main, not on the 3.3.4 tag | (medium confidence) |
| M10 | Set `apicurio.registry.fault-tolerant-refresh=true` on clients. Single source: the best-practices page | (medium confidence) |
| M11 | Keep at least 2 registry replicas during updates. Single source: the high availability page | (medium confidence) |

## Coverage limits (L1..L8): 8 items

| ID | Limit |
|---|---|
| L1 | The 3.3.4 OpenAPI file was read for characters 0 to 100000 and 200000 to 300000 of 350477 |
| L2 | The 3.2.x high availability page was read as a targeted extract (port 9000 sentences) only |
| L3 | The official Compose directory listing was truncated. Three sample files were read: pg-no-auth, in-memory-with-auth, pg-secrets |
| L4 | The GitHub releases API was read for 100000 of 130971 characters (10 newest releases) |
| L5 | Every page was read through WebFetch, which returns a model-written extract, not verbatim text. Character counts are estimates. The tool reported each docs page as complete |
| L6 | The storage page is the OpenShift page: only storage-generic facts are used |
| L7 | The sizing guide, the Kubernetes operator pages and the Maven plugin page were not read |
| L8 | The assets list of the 3.3.0 release page failed to load |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Version Context, SerDes Protobuf and JSON Schema versions; Ask First SerDes row | U9 |
| (unverified) | SKILL.md Version Context, Java runtime | U21 |
| (unverified) | SKILL.md Version Context, Kafka (3.9 brokers) and PostgreSQL support | U2 |
| (medium confidence) | SKILL.md Version Context, license | M9 |
| (unverified) | SKILL.md Version-lifetime risk, patch notes conflict | U5 |
| (medium confidence) | SKILL.md Ask First, which registry, storage, compatibility, auto-registration, downgrade | M9, M7, M1, M2, M3 |
| (unverified) | SKILL.md Ask First, upgrade order, ID width, partitions, SerDes row, Kafka connection security row | U1, U11, U3, U9, U13 |
| (unverified) | always-do-patterns.md | U3, U6, U7, U8, U9, U22 |
| (medium confidence) | always-do-patterns.md | M4 |
| (unverified) | never-do-patterns.md | U10, U20 |
| (unverified) | migration-guide.md, always-do-patterns.md, security-and-ha.md, deploy-compose.md, role-based authorization variable | U22 |
| (unverified) | deploy-compose.md, KafkaSQL topic auto-creation variable | U23 |
| (medium confidence) | never-do-patterns.md | M3 |
| (unverified) | ask-first-decisions.md | U1, U3, U4, U5, U9, U11, U13, U15 |
| (medium confidence) | ask-first-decisions.md | M1, M2, M3, M6, M7, M8 |
| (unverified) | deploy-compose.md | U2, U8, U19, U20, U22, U23 |
| (medium confidence) | deploy-compose.md | M4 |
| (unverified) | compatibility-and-evolution.md | U1, U15 |
| (medium confidence) | compatibility-and-evolution.md | M1, M2, M4, M5 |
| (unverified) | serdes-java.md | U4, U9, U11, U12, U16 |
| (medium confidence) | serdes-java.md | M2, M10 |
| (unverified) | security-and-ha.md | U2, U7, U17, U22 |
| (medium confidence) | security-and-ha.md | M3, M11 |
| (unverified) | migration-guide.md | U2, U5, U11, U14, U17, U18 |
| (medium confidence) | migration-guide.md | M3 |
| (unverified), (medium confidence) | evaluation-scenarios.md | U1, U3, U5, U20, M1, M3 |

## Source Bibliography

All pages read 2026-11-04. Doc base: `https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/`.

| ID | Title | URL |
|---|---|---|
| P1 | Versioning and support policy | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-versioning-support-policy.html |
| P2 | Documentation index 3.3.x | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/index.html |
| P3 | Artifact reference | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-artifact-reference.html |
| P4 | Rules introduction | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-intro-to-registry-rules.html |
| P4r | Rule reference | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-rule-reference.html |
| P5 | Compatibility modes | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-compatibility-modes.html |
| P6 | Kafka SerDes usage | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-using-kafka-client-serdes.html |
| P7 | Confluent Schema Registry compatibility | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-confluent-schema-registry-compatibility.html |
| P8 | Installing with Docker | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-docker.html |
| P9 | Storage (OpenShift page, generic facts only) | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-storage-openshift.html |
| P10 | Configuration reference | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html |
| P11 | Security configuration | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-registry-security.html |
| P12 | High availability 3.3.x | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html |
| P12b | High availability 3.2.x (corroboration, extract only) | https://www.apicur.io/registry/docs/apicurio-registry/3.2.x/getting-started/assembly-registry-high-availability.html |
| P13 | Migrating 2.x to 3.x | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html |
| P14 | Kafka SerDes configuration | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-kafka-client-serdes.html |
| P15 | Schema lifecycle best practices | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html |
| P19 | Deploying with secured Kafka | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-deploying-registry-secured-kafka.html |
| P2a | Managing artifacts through the REST API | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-managing-registry-artifacts-api.html |
| P2g | Concepts glossary | https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-concepts-glossary.html |
| P21 | GitHub release 3.3.4 (2026-11-03) | https://github.com/Apicurio/apicurio-registry/releases/tag/3.3.4 |
| P21b | GitHub release 3.3.0 (2026-06-08) | https://github.com/Apicurio/apicurio-registry/releases/tag/3.3.0 |
| P22 | OpenAPI v3 at tag 3.3.4 (partly read) | https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/common/src/main/resources/META-INF/openapi.json |
| P23 | License, read on main | https://raw.githubusercontent.com/Apicurio/apicurio-registry/main/LICENSE |
| P16 | Maven Central io.apicurio directory | https://repo1.maven.org/maven2/io/apicurio/ |
| P16b | Maven metadata, Avro SerDes (release 3.3.4) | https://repo1.maven.org/maven2/io/apicurio/apicurio-registry-avro-serde-kafka/maven-metadata.xml |
| P20 | Docker Hub tags, registry | https://hub.docker.com/v2/repositories/apicurio/apicurio-registry/tags?page_size=25&name=3.3 |
| P20b | Docker Hub tags, UI | https://hub.docker.com/v2/repositories/apicurio/apicurio-registry-ui/tags?page_size=10&name=3.3 |
| P17 | Official sample compose in-memory-with-auth, file at tag 3.3.4 | https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/in-memory-with-auth/docker-compose.yml |
| P17a | Official sample compose pg-no-auth, file at tag 3.3.4 | https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/pg-no-auth/docker-compose.yml |
| P18 | Official sample compose pg-secrets, file at tag 3.3.4 | https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/pg-secrets/docker-compose.yml |
