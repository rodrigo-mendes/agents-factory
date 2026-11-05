# Ask-first decisions, Apicurio Registry 3.3.4

Back to [SKILL.md](../SKILL.md). Stop and ask before choosing. Pages read 2026-11-04. Doc base: `https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/`.

## 1. Storage: PostgreSQL vs KafkaSQL

Sources: [Docker install](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-docker.html), [storage](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-storage-openshift.html), [config reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html), [high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html). The selection guidance is this skill's assembly of those pages (medium confidence).

| Option | Optimizes | Sacrifices |
|---|---|---|
| PostgreSQL (`sql` + `postgresql`) | Standard database backup (`pg_dump`, WAL archiving), no extra Kafka topics | Needs an HA Postgres with replication and automatic failover |
| KafkaSQL (`kafkasql`) | No separate database, reuses the Kafka cluster | Each replica replays the full journal into embedded H2 at startup, topic config must be exact, backup through MirrorMaker 2 |

Other kinds named in the config reference (`gitops`, `kubernetesops`, MySQL on the HA page) are out of scope. Ask: "Which stateful platform do you operate and back up today?"

## 2. Compatibility level

Sources: [compatibility modes](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-compatibility-modes.html), [best practices](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html). Only the best-practices page recommends `BACKWARD_TRANSITIVE` for production, especially when consumers may lag more than one version, and says to avoid `NONE` in production (medium confidence, M1).

| Option | Optimizes | Sacrifices |
|---|---|---|
| `BACKWARD` | Fewer rejections | Compared only against the latest version |
| `BACKWARD_TRANSITIVE` | Old data replayed by new consumers | Restricts more changes |
| `FULL` / `FULL_TRANSITIVE` | Both directions | Most restrictive (`FULL_TRANSITIVE` is the strictest mode) |

Which side must upgrade first per mode is not stated (unverified, U1). Ask: "How long is topic retention and how far can consumers lag?"

## 3. Pre-register schemas vs auto-registration

Sources: [best practices](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html), [SerDes configuration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-kafka-client-serdes.html), [SerDes usage](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-using-kafka-client-serdes.html).

- The default `apicurio.registry.auto-register=false` and `apicurio.registry.auto-register.if-exists=FIND_OR_CREATE_VERSION` (other values `FAIL`, `CREATE_VERSION`) come from the configuration page.
- Only the best-practices page recommends pre-registering in CI (Maven plugin `io.apicurio:apicurio-registry-maven-plugin`, goal `register`, or REST) and keeping `auto-register=false` in production (medium confidence, M2). If auto-registration cannot be avoided, restrict writes with authentication and roles.
- The usage page says the JSON Schema serializer does not support auto-registration, the configuration page does not repeat it (unverified, U4). Pre-register JSON Schemas in CI.
- The Maven plugin XML was not read (unverified, U15).

Ask: "May producers create schemas at runtime, or only CI?"

## 4. Native SerDes vs Confluent clients

Source: [ccompat](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-confluent-schema-registry-compatibility.html). The choice itself is guidance (medium confidence, M8); the limits are documented. Details in [serdes-java](./serdes-java.md). Ask: "Must existing Confluent clients work unchanged, and do they use KEK/DEK, exporters or Data Contract rules?" If the user wants Confluent Schema Registry itself, route to `managing-event-schemas-confluent-v8-4`.

## 5. Schema ID location and width

Sources: [SerDes usage](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-using-kafka-client-serdes.html), [SerDes configuration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-kafka-client-serdes.html), [migration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html). The 3.x defaults moved from `globalId` and the 8-byte handler to `contentId` and `Default4ByteIdHandler`. The migration page says mixed 2.x/3.x environments work "With proper configuration", but the matching settings per pair are not spelled out, and that producers and consumers must agree is an inference (unverified, U11). Ask: "Does any producer or consumer still run 2.x SerDes?"

## 6. Authentication mechanism mix

Sources: [security](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-registry-security.html), [config reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html). OIDC is the default choice. HTTP basic client credentials (`APICURIO_AUTHN_BASIC_CLIENT_CREDENTIALS_ENABLED=true`) need OIDC enabled. Proxy-header authentication only behind a proxy that strips client identity headers (otherwise "clients can impersonate any user"). Kubernetes authentication is experimental and exclusive with OIDC. Priority order: `apicurio.authn.mechanism.priority`, default `basic,proxy-header,oidc`. Ask: "Which IdP exists, and do non-OIDC tools such as Kafka Connect converters need basic credentials?"

## 7. Kafka connection security for KafkaSQL

Sources: [secured Kafka](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-deploying-registry-secured-kafka.html), [storage](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-storage-openshift.html), [config reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html). The secured-Kafka page is operator-oriented, and the variables appear inside operator `env` lists (medium confidence, M6).

- SCRAM: `APICURIO_KAFKA_COMMON_SECURITY_PROTOCOL=SASL_SSL`, `APICURIO_KAFKA_COMMON_SASL_MECHANISM=SCRAM-SHA-512`, `APICURIO_KAFKA_COMMON_SASL_JAAS_CONFIG` (single line, no `KafkaClient {}` wrapper).
- OAuth: `APICURIO_KAFKASQL_SECURITY_SASL_ENABLED=true` plus client id, client secret and token endpoint.
- TLS stores: `apicurio.kafkasql.security.ssl.*`.
- Interaction when both families are set is not documented (unverified, U13).

Ask: "Which Kafka listener security does the cluster use?"

## 8. Downgrade or rollback

Source: [support policy](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-versioning-support-policy.html). Only this page says database schema migrations are forward-only and irreversible, that an older version fails against a newer schema, and that recovery means restoring the pre-upgrade backup (medium confidence, M3). So never roll the image back in place:

1. Stop the registry.
2. Restore the pre-upgrade backup.
3. Deploy the previous version.

Ask: "Is a restorable pre-upgrade backup in place?"

## 9. Journal topic partitions

Sources: [migration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html) (1 partition), [storage](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-storage-openshift.html) and [high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html) (3 partitions in examples). No required count is stated (unverified, U3). Do not claim one. Ask the user and verify with a human.

## 10. Patch released 2026-11-03

3.3.4 was released 2026-11-03, research date 2026-11-04 ([release](https://github.com/Apicurio/apicurio-registry/releases/tag/3.3.4)). The notes list bug fixes (CLI, GitOps status, web console) and one CLI enhancement, no breaking changes or CVEs. The support page says patches carry no bug fixes, a conflict not resolved here (unverified, U5). Ask: "Pin 3.3.4 now, or wait?"

## 11. Which registry?

Applies when the request names no registry and no file is open. This skill covers Apicurio Registry 3.3 only; Confluent Schema Registry is covered by `managing-event-schemas-confluent-v8-4`. Ask: "Do you run Apicurio Registry 3.3 or Confluent Schema Registry 8.4?" and route accordingly.

## 12. Protobuf or JSON Schema SerDes

The Protobuf and JSON Schema Java artifact names and their 3.3.4 versions were not opened (unverified, U9). The Avro artifact is covered in [serdes-java](./serdes-java.md), which also lists what is unconfirmed for the other formats. Ask: "Which schema format do the clients use?" and verify the artifact version on Maven Central before pinning.
