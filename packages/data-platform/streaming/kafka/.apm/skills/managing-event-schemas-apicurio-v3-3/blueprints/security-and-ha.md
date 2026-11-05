# Security and high availability, Apicurio Registry 3.3.4

Back to [SKILL.md](../SKILL.md). Pages read 2026-11-04: [security](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-registry-security.html), [config reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-config-reference.html), [high availability](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-high-availability.html), [secured Kafka](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-deploying-registry-secured-kafka.html).

## Security checklist

| Item | Setting | Source |
|---|---|---|
| OIDC on | `QUARKUS_OIDC_TENANT_ENABLED=true`, `QUARKUS_OIDC_AUTH_SERVER_URL` | security, config reference |
| Roles on | `APICURIO_AUTH_ROLE_BASED_AUTHORIZATION=true` (spelling unverified, U22). `sr-admin` for global rules, `sr-developer` for writes, `sr-readonly` for reads | security |
| Role source | `token` (default) or `application` (managed through `/admin/roleMappings`) | security |
| First admin | No default admin. `APICURIO_AUTH_ADMIN_OVERRIDE_ENABLED` lets you create one | security |
| Owner-only writes | `APICURIO_AUTH_OWNER_ONLY_AUTHORIZATION` | security |
| Anonymous read | `APICURIO_AUTH_ANONYMOUS_READ_ACCESS_ENABLED` defaults to `false` | security |
| Deletion endpoints | `apicurio.rest.deletion.*` default `false`. The official dev compose files turn them on | config reference |
| CORS | Explicit origins through `QUARKUS_HTTP_CORS_ORIGINS`, not `*`, outside local development | security |
| Proxy-header auth | Only behind a proxy that strips client identity headers | security |
| SerDes TLS | `apicurio.registry.tls.trust-all` stays `false` | [SerDes configuration](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-kafka-client-serdes.html) |
| Secrets | `_FILE` variables ([always-do-patterns](./always-do-patterns.md)) | Docker install |

All options are off by default. HTTP basic client credentials (`APICURIO_AUTHN_BASIC_CLIENT_CREDENTIALS_ENABLED=true`) need OIDC enabled. Kubernetes authentication is experimental and exclusive with OIDC.

## Replicas and storage HA

Source: high availability page.

- The registry and the UI are stateless and scale horizontally (the page example uses 3 registry replicas and 2 UI replicas). Keep at least 2 replicas during updates.
- PostgreSQL: needs replication with automatic failover (Patroni, CloudNativePG or a managed service). Tune Agroal pool validation, timeouts and maximum lifetime for failover.
- KafkaSQL: topics with replication factor 3 and `min.insync.replicas=2`. Every replica consumes the full journal. Do not set a fixed consumer group ID. Topic auto-creation is "not recommended" for HA production, so pre-create the topics with the settings in [always-do-patterns](./always-do-patterns.md).
- Request limits exist but are unlimited by default (`apicurio.limits.config.max-requests-per-second=-1`, config reference).

## Health and metrics on port 9000

Source: high availability page (3.3.x read in full). The corroborating 3.2.x page was read as a targeted extract only (coverage limit L2), so this is kept out of Always Do.

- Health and metrics are served on the dedicated management port 9000: `/health/live`, `/health/ready`, `/metrics`. With TLS enabled, port 9000 serves HTTPS.
- The page calls this "a **breaking change**" for deployments upgraded "from earlier versions". Which release introduced it is not known (unverified, U17). Probes written for 8080 break after such an upgrade.
- Metrics named on the page: `http_server_requests_seconds`, `apicurio_storage_operation_seconds`, `jvm_gc_pause_seconds`.
- Suggested alerts on the page: pod restarts, 5xx rate, storage timeouts, connection-pool exhaustion, Kafka consumer lag.

## Backup and disaster recovery

Source: high availability page, [support policy](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-versioning-support-policy.html).

- PostgreSQL: `pg_dump` and WAL archiving (flags unverified, U7).
- KafkaSQL: mirror the `kafkasql-.*` topics with MirrorMaker 2. Topic data plus the SQL snapshot are the backup for an upgrade.
- Test restores in a separate environment.
- Recovery from a failed upgrade is a restore of the pre-upgrade backup, not an image rollback (medium confidence, M3).

## Sizing

An official sizing guide exists in the 3.3.x index but was not read (coverage limit L7). Do not invent sizing numbers. Supported Kafka and PostgreSQL versions are not stated either (unverified, U2).
