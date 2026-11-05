# Never-do patterns, Apicurio Registry 3.3.4

Back to [SKILL.md](../SKILL.md). Every row has a wrong form and a correct form. Pages read 2026-11-04. Doc base: `https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/`. The single-source no-downgrade rule is not here: it is in [ask-first-decisions](./ask-first-decisions.md) (medium confidence, M3).

## 1. Log compaction on KafkaSQL topics

Sources: [storage](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-storage-openshift.html), [high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html), [migration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html), [secured Kafka](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-deploying-registry-secured-kafka.html). Impact: lost registry data, or the registry refuses to start.

```bash
# ❌ WRONG
kafka-topics.sh --create --topic kafkasql-journal --config cleanup.policy=compact
# ✅ CORRECT
kafka-topics.sh --create --topic kafkasql-journal \
  --config cleanup.policy=delete --config retention.ms=-1 --config retention.bytes=-1
```

## 2. More than one replica on embedded H2

Sources: [high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html) ("Do not use the default embedded H2 configuration with multiple replicas"), [Docker install](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-docker.html). Impact: replicas serve different data, and all data is lost on restart.

```yaml
# ❌ WRONG: no APICURIO_STORAGE_KIND, so in-memory H2
apicurio-registry:
  image: apicurio/apicurio-registry:3.3.4
  deploy: { replicas: 3 }
# ✅ CORRECT
apicurio-registry:
  image: apicurio/apicurio-registry:3.3.4
  environment:
    APICURIO_STORAGE_KIND: "sql"
    APICURIO_STORAGE_SQL_KIND: "postgresql"
    APICURIO_DATASOURCE_URL: "jdbc:postgresql://postgres:5432/registrydb"
  deploy: { replicas: 3 }
```

## 3. Fixed KafkaSQL consumer group ID

Sources: [high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html) (each replica replays the whole journal into its own embedded H2), [migration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html) (`REGISTRY_KAFKASQL_CONSUMER_GROUP_ID` removed in 3.x), [config reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html) (prefix default `apicurio-`). Impact: replicas start with missing data.

```bash
# ❌ WRONG
REGISTRY_KAFKASQL_CONSUMER_GROUP_ID=apicurio-registry
# ✅ CORRECT
APICURIO_KAFKASQL_CONSUMER_GROUP_PREFIX=apicurio-
```

## 4. 2.x variable names on a 3.3 server

Sources: [migration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-migrating-registry-v2-v3.html), [config reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html). 3.x renamed the settings, and `APICURIO_STORAGE_KIND` is now required. That a server falls back silently to default storage with 2.x names is an inference (unverified, U10). Impact: wrong storage or authentication left off.

```yaml
# ❌ WRONG
environment:
  REGISTRY_DATASOURCE_URL: "jdbc:postgresql://postgres:5432/registrydb"
  AUTH_ENABLED: "true"
  KAFKA_BOOTSTRAP_SERVERS: "kafka:9092"
# ✅ CORRECT
environment:
  APICURIO_STORAGE_KIND: "sql"
  APICURIO_STORAGE_SQL_KIND: "postgresql"
  APICURIO_DATASOURCE_URL: "jdbc:postgresql://postgres:5432/registrydb"
  QUARKUS_OIDC_TENANT_ENABLED: "true"
```

## 5. Avro field without a default

Sources: [compatibility modes](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-compatibility-modes.html), [best practices](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html). Impact: the registry rejects the version, or with `NONE` consumers break.

```json
{"name": "discountCode", "type": "string"}
{"name": "discountCode", "type": ["null", "string"], "default": null}
```

The first line is wrong, the second is correct.

## 6. Protobuf field removed without `reserved`

Same two pages as row 5 (the best-practices page: "Always add `reserved` declarations when you remove Protobuf fields").

```protobuf
// ❌ WRONG: field 2 'coupon' deleted
message Order { string id = 1; int64 total = 3; }
// ✅ CORRECT
message Order { reserved 2; reserved "coupon"; string id = 1; int64 total = 3; }
```

## 7. `latest-snapshot` in production

Sources: [support policy](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-versioning-support-policy.html), [Docker Hub tags](https://hub.docker.com/v2/repositories/apicurio/apicurio-registry/tags?page_size=25&name=3.3).

```yaml
# ❌ WRONG
image: apicurio/apicurio-registry:latest-snapshot
# ✅ CORRECT
image: apicurio/apicurio-registry:3.3.4
```

## 8. Official sample compose files in production

Sources: [in-memory-with-auth](https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/in-memory-with-auth/docker-compose.yml), [pg-secrets](https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/pg-secrets/docker-compose.yml) (both at tag 3.3.4 use `latest-snapshot`), [security](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-registry-security.html) (CORS origins explicit, not `*`, outside local development). The samples also enable deletion endpoints, which stay `false` by default. Impact: unstable image, open CORS, deletable artifacts.

Instead start from the official guidance in the three cited pages (pinned tag, explicit CORS origins, `_FILE` secrets). [deploy-compose](./deploy-compose.md) assembles those snippets in one file, (unverified as a tested whole, U20): run it in a test environment first.
