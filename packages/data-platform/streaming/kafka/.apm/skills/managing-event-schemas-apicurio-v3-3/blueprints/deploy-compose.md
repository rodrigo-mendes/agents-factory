# Deploy with Docker Compose, Apicurio Registry 3.3.4

Back to [SKILL.md](../SKILL.md). Scope: Docker Compose, single host (development, CI, staging). Kubernetes operator deployment is out of scope.

## Status of the file below

The Compose file is this skill's assembly of snippets from the official [Docker install page](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-docker.html) and the official samples [in-memory-with-auth](https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/in-memory-with-auth/docker-compose.yml) and [pg-secrets](https://raw.githubusercontent.com/Apicurio/apicurio-registry/3.3.4/distro/docker-compose/pg-secrets/docker-compose.yml) (read 2026-11-04). Each line traces to an official page. The assembly as a tested whole is (unverified, U20): nobody ran it.

The official samples at tag 3.3.4 are development only: they use `latest-snapshot`, CORS `*`, and turn on deletion endpoints. Do not copy their defaults ([never-do-patterns](./never-do-patterns.md)). The `version:` top-level key of the samples is legacy and left out here.

## PostgreSQL storage, OIDC, RBAC

```yaml
# Representative: adapt hosts, realm and secrets to your environment.
secrets:
  registry_db_user:     { file: ./secrets/db_user.txt }       # chmod 600, not in git
  registry_db_password: { file: ./secrets/db_password.txt }

services:
  postgres:
    image: postgres:15                       # as in the official samples; no support matrix found (unverified, U2)
    environment:
      POSTGRES_USER_FILE: /run/secrets/registry_db_user
      POSTGRES_PASSWORD_FILE: /run/secrets/registry_db_password
      POSTGRES_DB: registrydb
    secrets: [registry_db_user, registry_db_password]
    volumes: [postgres_data:/var/lib/postgresql/data]   # container data path (unverified, U19)

  apicurio-registry:
    image: apicurio/apicurio-registry:3.3.4
    environment:
      APICURIO_STORAGE_KIND: "sql"
      APICURIO_STORAGE_SQL_KIND: "postgresql"
      APICURIO_DATASOURCE_URL: "jdbc:postgresql://postgres:5432/registrydb"
      APICURIO_DATASOURCE_USERNAME_FILE: /run/secrets/registry_db_user
      APICURIO_DATASOURCE_PASSWORD_FILE: /run/secrets/registry_db_password
      QUARKUS_OIDC_TENANT_ENABLED: "true"
      QUARKUS_OIDC_AUTH_SERVER_URL: "https://idp.example.com/realms/registry"
      QUARKUS_OIDC_CLIENT_ID: "registry-api"
      APICURIO_UI_AUTH_OIDC_CLIENT_ID: "apicurio-registry"
      APICURIO_UI_AUTH_OIDC_REDIRECT_URI: "https://registry-ui.example.com/"
      APICURIO_AUTH_ROLE_BASED_AUTHORIZATION: "true"   # spelling (unverified, U22)
      QUARKUS_HTTP_CORS_ORIGINS: "https://registry-ui.example.com"   # not '*'
    secrets: [registry_db_user, registry_db_password]
    ports: ["8080:8080", "9000:9000"]        # 9000 = health and metrics
    depends_on: [postgres]

  apicurio-registry-ui:
    image: apicurio/apicurio-registry-ui:3.3.4
    environment:
      REGISTRY_API_URL: "https://registry.example.com/apis/registry/v3"   # names from the official sample
      REGISTRY_AUTH_TYPE: "oidc"
      REGISTRY_AUTH_URL: "https://idp.example.com/realms/registry"
    ports: ["8888:8080"]

volumes:
  postgres_data: {}
```

The realm URL is the full `/realms/<realm>` path (migration page). The registry-side variable names come from the [security page](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-registry-security.html) and [config reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html). Publish port 9000 only on a trusted network. A Compose `healthcheck` with `curl` inside the image is not confirmed (unverified, U8).

## KafkaSQL variant

Replace the storage variables of `apicurio-registry` (sources: [Docker install](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-installing-registry-docker.html), [config reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html), [high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html)).

```yaml
APICURIO_STORAGE_KIND: "kafkasql"
APICURIO_KAFKASQL_BOOTSTRAP_SERVERS: "kafka:9092"
APICURIO_KAFKASQL_TOPIC: "kafkasql-journal"          # default name
# APICURIO_KAFKASQL_TOPIC_AUTO-CREATE: "false"       # HA page: auto-creation not recommended in HA production. Variable spelling likely wrong, left commented out (unverified, U23)
```

Pre-create the journal topic with the settings in [always-do-patterns](./always-do-patterns.md) first. If Kafka is secured, see item 7 of [ask-first-decisions](./ask-first-decisions.md). For the broker side of the same Compose project, see `operating-kafka-v4-4`.

## Checks after `docker compose up`

```bash
docker compose ps                               # Expected: registry, postgres and ui running
curl -fs http://localhost:9000/health/ready     # Expected: HTTP 200 (body shape unverified, U8)
curl -fs -H "Authorization: Bearer $TOKEN" http://localhost:8080/apis/registry/v3/admin/rules   # Expected: list including COMPATIBILITY
```

The `admin/rules` path comes from the partly read 3.3.4 OpenAPI file (medium confidence, M4).
