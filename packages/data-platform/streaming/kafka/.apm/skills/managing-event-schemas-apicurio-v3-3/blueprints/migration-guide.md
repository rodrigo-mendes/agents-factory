# Migration guide, Apicurio Registry 2.x to 3.3.4

Back to [SKILL.md](../SKILL.md). Sources read 2026-11-04: [migration 2.x to 3.x](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html), [support policy](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-versioning-support-policy.html), release notes [3.3.4](https://github.com/Apicurio/apicurio-registry/releases/tag/3.3.4) and [3.3.0](https://github.com/Apicurio/apicurio-registry/releases/tag/3.3.0).

## Within 3.x

- Patch (3.3.x to 3.3.4): the support policy says patches carry security fixes and dependency upgrades, no new features or bug fixes. The 3.3.4 notes list bug fixes (CLI, GitOps status, web console) and one CLI enhancement. These two statements conflict and this skill does not resolve it (unverified, U5). Read the patch notes before upgrading.
- Minor (for example 3.2.x to 3.3.4): read the notes of every intermediate version, back up, replace the image, start, verify clients. Migrations run automatically at startup and are cumulative, so skipping minors is supported (support policy). Schema migrations are forward-only (medium confidence, M3), so the backup is the way back.
- 3.3.0 notes list no breaking changes. New: Data Contracts, a CLI, MCP tool artifacts, API lifecycle governance, operator HPA support.
- Management port 9000 for health and metrics is a breaking change for probes on deployments upgraded from earlier versions. It already appears in the 3.2.x docs. The introducing release is unknown (unverified, U17).

## From 2.x (2.6.x) to 3.3.4

No in-place upgrade. Export from 2.6.x, import into a new 3.x registry.

**Breaking changes** (migration page)

- The v3 SQL schema and the KafkaSQL journal format are incompatible with v2. Use a new journal topic.
- REST API v3 at `/apis/registry/v3`. v2 stays available at `/apis/registry/v2`.
- Artifact metadata is separate from version metadata. A `latest` branch is managed automatically. `dryRun` replaces the `/test` endpoints. The UI is a separate container.
- `APICURIO_STORAGE_KIND` is now required.

**Renamed configuration** (selection)

| 2.x | 3.x |
|---|---|
| `REGISTRY_DATASOURCE_URL` | `APICURIO_DATASOURCE_URL` |
| `KAFKA_BOOTSTRAP_SERVERS` | `APICURIO_KAFKASQL_BOOTSTRAP_SERVERS` |
| `AUTH_ENABLED` | `QUARKUS_OIDC_TENANT_ENABLED` |
| `KEYCLOAK_URL` + `KEYCLOAK_REALM` | `QUARKUS_OIDC_AUTH_SERVER_URL` |
| `ROLE_BASED_AUTHZ_ENABLED` | `APICURIO_AUTH_ROLE_BASED_AUTHORIZATION` (the migration page writes the hyphen form `APICURIO_AUTH_ROLE-BASED-AUTHORIZATION`; the config reference property is `apicurio.auth.role-based-authorization`; which env spelling the server reads is (unverified, U22)) |
| `REGISTRY_REST_ARTIFACT_DELETION_ENABLED` | `APICURIO_REST_DELETION_ARTIFACT_ENABLED` |
| `CORS_ALLOWED_ORIGINS` | `QUARKUS_HTTP_CORS_ORIGINS` |
| `REGISTRY_KAFKASQL_CONSUMER_GROUP_ID` | removed; use `APICURIO_KAFKASQL_CONSUMER_GROUP_PREFIX` |

**SerDes and client**

- Artifact `apicurio-registry-serdes-avro-serde` becomes `apicurio-registry-avro-serde-kafka`. Client `apicurio-registry-client` becomes `apicurio-registry-java-sdk`.
- Default ID handler 8-byte becomes 4-byte. Default `USE_ID` `globalId` becomes `contentId`. `ENABLE_CONFLUENT_ID_HANDLER` is removed.
- OAuth `AUTH_SERVICE_URL` + `AUTH_REALM` become `AUTH_TOKEN_ENDPOINT`. TLS uses `SerdeConfig.TLS_TRUSTSTORE_*`. Registry URL `/apis/registry/v2` becomes `/apis/registry/v3`.
- 2.x SerDes "continue to work" against a 3.x server through `/apis/registry/v2`. The exact 2.x patch floor is not stated (unverified, U18). Mixed v2/v3 clients work "With proper configuration", settings per pair not spelled out (unverified, U11).

## Upgrade steps (2.6.x to 3.3.4, maintenance-window path)

1. Stop clients.
2. Export with `curl` against `/apis/registry/v2/admin/export`, or the official `./apicurio-export-registry-data.sh`.
3. Shut down 2.6.x.
4. For KafkaSQL, create a new journal topic with `cleanup.policy=delete`, `retention.ms=-1`, `retention.bytes=-1` ([always-do-patterns](./always-do-patterns.md)). The migration page names it `kafkasql-journal-v3`, the default name is `kafkasql-journal`.
5. Deploy 3.3.4 with the `APICURIO_*` configuration ([deploy-compose](./deploy-compose.md)).
6. Import into an empty v3 registry: `POST /apis/registry/v3/admin/import` with `Content-Type: application/zip`. The import adds to existing data and does not replace it.
7. Validate with `./apicurio-verify-registry-version.sh` and `./apicurio-verify-v3-api-features.sh`, update client configuration, start clients.

The repository location of these scripts was not identified (unverified, U14). `apicurio-import-registry-data.sh` and `apicurio-capture-metrics.sh` are also named on the page.

## Compatibility matrix

| Dependency | Value | Note |
|---|---|---|
| Server minors with security patches | 3.2.x and 3.3.x | support policy |
| Avro / JSON Schema / Protobuf | 1.0 to 1.12 / draft-04 to 2020-12 / proto2 and proto3 | [artifact reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-artifact-reference.html) |
| ccompat API | v7 and v8 | [ccompat](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-confluent-schema-registry-compatibility.html) |
| Kafka broker and client versions | not stated (unverified, U2) | |
| PostgreSQL versions | not stated (unverified, U2) | official sample uses `postgres:15` |

## Downgrades

Not supported through an image rollback. Restore the pre-upgrade backup, then deploy the previous version (medium confidence, M3). Refuse in-place downgrade requests.
