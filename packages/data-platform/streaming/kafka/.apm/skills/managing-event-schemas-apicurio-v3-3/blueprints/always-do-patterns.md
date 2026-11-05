# Always-do patterns, Apicurio Registry 3.3.4

Back to [SKILL.md](../SKILL.md). All code is representative: adapt names, hosts and credentials to your environment. Pages read 2026-11-04. Doc base: `https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/`. Caveats and options live in [ask-first-decisions](./ask-first-decisions.md).

## Storage: PostgreSQL or KafkaSQL

Sources: [Docker install](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-docker.html), [high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html). The H2 default loses data on container restart, and several replicas need a production-ready backend.

```bash
docker run -it -p 8080:8080 \
  -e "APICURIO_STORAGE_KIND=sql" \
  -e "APICURIO_STORAGE_SQL_KIND=postgresql" \
  -e "APICURIO_DATASOURCE_URL=jdbc:postgresql://postgres/apicurio-registry" \
  -e "APICURIO_DATASOURCE_USERNAME=apicurio-registry" \
  -e "APICURIO_DATASOURCE_PASSWORD=password" \
  apicurio/apicurio-registry:3.3.4
```

The inline password is for the docs example only. Use `_FILE` secrets (below).

## KafkaSQL topic settings

Sources: [storage](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-storage-openshift.html), [high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html), [migration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html), [secured Kafka](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-deploying-registry-secured-kafka.html). The registry checks the settings at startup. The 3.3.0 release fixed stale docs that still said `compact`.

```bash
kafka-topics.sh --bootstrap-server kafka:9092 --create \
  --topic kafkasql-journal --replication-factor 3 --partitions 1 \
  --config cleanup.policy=delete --config retention.ms=-1 --config retention.bytes=-1
kafka-configs.sh --bootstrap-server kafka:9092 --describe --entity-type topics --entity-name kafkasql-journal
# Expected: cleanup.policy=delete, retention.ms=-1, retention.bytes=-1
```

The migration page creates the journal with 1 partition, the storage and high availability pages show 3. No required count is stated (unverified, U3). The default topic name is `kafkasql-journal`.

## Explicit COMPATIBILITY rule

Sources: [rules](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-intro-to-registry-rules.html), [ccompat](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-confluent-schema-registry-compatibility.html). Through ccompat the `BACKWARD` default applies only to the compatibility-check endpoint, registration does not enforce it unless a rule is set. The level is a decision, see [compatibility-and-evolution](./compatibility-and-evolution.md).

```properties
# application.properties or -D system property (rules page)
apicurio.rules.global.compatibility=BACKWARD
```

The environment-variable form `APICURIO_RULES_GLOBAL_COMPATIBILITY` is not named on the rules page (unverified, U6). Per-artifact REST call (body shape from a partly read OpenAPI file, medium confidence, M4):

```bash
curl -X POST "$REGISTRY/apis/registry/v3/groups/payments/artifacts/orders-value/rules" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"ruleType":"COMPATIBILITY","config":"BACKWARD"}'
```

## OIDC authentication and role-based authorization

Sources: [security](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-registry-security.html), [config reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html) (`quarkus.oidc.tenant-enabled` and `apicurio.auth.role-based-authorization` both default `false`), [official in-memory-with-auth compose](https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/in-memory-with-auth/docker-compose.yml).

```yaml
environment:
  QUARKUS_OIDC_TENANT_ENABLED: "true"
  QUARKUS_OIDC_AUTH_SERVER_URL: "https://keycloak.example.com/realms/registry"
  QUARKUS_OIDC_CLIENT_ID: "registry-api"
  APICURIO_UI_AUTH_OIDC_CLIENT_ID: "apicurio-registry"
  APICURIO_AUTH_ROLE_BASED_AUTHORIZATION: "true"   # spelling (unverified, U22): confirm authorization is active after start
  APICURIO_AUTH_ROLE_SOURCE: "token"   # default; "application" manages roles through /admin/roleMappings
```

Roles: `sr-admin` (global rules), `sr-developer` (writes), `sr-readonly` (reads). There is no default admin. The security page offers `APICURIO_AUTH_ADMIN_OVERRIDE_ENABLED` to create the first admin. More in [security-and-ha](./security-and-ha.md).

## Datasource secrets through `_FILE`

Sources: [Docker install](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-docker.html), [official pg-secrets compose](https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/pg-secrets/docker-compose.yml). Secret files should be `chmod 600` and stay out of version control. The registry logs a warning for a world-readable file and fails to start if a `_FILE` path is missing or unreadable.

```yaml
environment:
  APICURIO_DATASOURCE_USERNAME_FILE: /run/secrets/registry_db_user
  APICURIO_DATASOURCE_PASSWORD_FILE: /run/secrets/registry_db_password
secrets:
  - registry_db_user
  - registry_db_password
```

## Pinned image

Sources: [support policy](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-versioning-support-policy.html) (`3.3.0` is pinned, `latest-snapshot` is unstable and not recommended for production), [Docker Hub tags](https://hub.docker.com/v2/repositories/apicurio/apicurio-registry/tags?page_size=25&name=3.3) (`3.3.4` pushed 2026-11-03, snapshot tags re-pushed 2026-11-04).

```yaml
image: apicurio/apicurio-registry:3.3.4
image: apicurio/apicurio-registry-ui:3.3.4
```

## Backup before a minor upgrade

Sources: [support policy](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-versioning-support-policy.html), [high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html) ("Regularly test your backup and restore procedures"). For KafkaSQL the high availability page recommends mirroring the `kafkasql-.*` topics with MirrorMaker 2.

```bash
pg_dump -Fc -h postgres -U apicurio-registry -d registrydb -f registry-pre-upgrade.dump
```

The support page names `pg_dump` in custom format. The exact flags above are (unverified, U7). Restore into a separate environment and check that it starts.

## 3.x SerDes artifacts

Sources: [migration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html) (`apicurio-registry-serdes-avro-serde` became `apicurio-registry-avro-serde-kafka`), [Maven Central](https://repo1.maven.org/maven2/io/apicurio/) (protobuf and jsonschema `-serde-kafka` directories exist).

```xml
<dependency>
  <groupId>io.apicurio</groupId>
  <artifactId>apicurio-registry-avro-serde-kafka</artifactId>
  <version>3.3.4</version>
</dependency>
```

Release 3.3.4 was confirmed for the Avro artifact only (unverified for Protobuf and JSON Schema, U9). Client usage in [serdes-java](./serdes-java.md).

## Verification loop

```bash
# Registry answers on the management port (path and port from the high availability page)
curl -fs http://localhost:9000/health/ready   # Expected: HTTP 200. Body shape (unverified, U8)
curl -fs http://localhost:9000/health/live
curl -fs http://localhost:9000/metrics | grep apicurio_storage_operation_seconds
# Global rules present (path from the 3.3.4 OpenAPI file, medium confidence, M4)
curl -fs -H "Authorization: Bearer $TOKEN" http://localhost:8080/apis/registry/v3/admin/rules
# Expected: a list that includes COMPATIBILITY
# KafkaSQL topic config: see the KafkaSQL section above
```
