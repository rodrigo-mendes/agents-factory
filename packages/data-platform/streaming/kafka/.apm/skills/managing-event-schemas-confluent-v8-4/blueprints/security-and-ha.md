# Security and high availability, Confluent Schema Registry 8.4.0

Back to [SKILL.md](../SKILL.md). Provenance: official pages read 2026-11-04. Sources: [security](https://docs.confluent.io/platform/8.4/schema-registry/security/index.html), [config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html), [deployment](https://docs.confluent.io/platform/8.4/schema-registry/installation/deployment.html), [multi-DC](https://docs.confluent.io/platform/8.4/schema-registry/multidc.html), [fundamentals](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/index.html).

## Security options

Which options need a license is in [licensing](./licensing.md). Without an Enterprise license, offer HTTPS plus Basic or mTLS, and put authorization at the network and Kafka-ACL level (medium confidence, M16).

| Option | Settings | Notes |
|---|---|---|
| HTTPS listener | `listeners=https://...`, `ssl.keystore.*`, `inter.instance.protocol=https` | `schema.registry.inter.instance.protocol` is deprecated in favor of `inter.instance.protocol` |
| Basic auth | `authentication.method=BASIC`, `authentication.roles`, `authentication.realm`, JAAS `PropertyFileLoginModule` | HTTPS only: Basic "passes credentials in plain text" (medium confidence, M3) |
| mTLS | `ssl.client.authentication` (default NONE) | |
| OAuth | listed on the security page | not researched further |
| RBAC, ACL authorizers | through the Security Plugins | Enterprise license (medium confidence, M16) |
| Kafka connection | `kafkastore.security.protocol` (default PLAINTEXT), `kafkastore.sasl.mechanism` (default GSSAPI) | SASL JAAS key not captured (unverified, U6) |

Kafka ACLs for the Schema Registry principal and the `json.type.allowed.packages` setting are in [ask-first-decisions](./ask-first-decisions.md) (M4, M11). `mode.mutability` off unless a migration needs it; its default is (unverified), U11.

## High availability

- Single-primary architecture: "Schema ID allocation always happens in the primary node". Secondaries forward writes to the primary ([fundamentals](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/index.html), [API](https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html)).
- State lives in the single-partition compacted `_schemas` topic, "a highly available write-ahead log". Rules for it: A3, A4, N1 ([always-do](./always-do-patterns.md), [never-do](./never-do-patterns.md)).
- Election is Kafka group based (A5, A6, A7). The consumer group is `schema-registry` unless `schema.registry.group.id` overrides it.
- If the primary DC is lost, secondaries keep serving requests that do not write to Kafka, but new registrations fail (multi-DC page).
- Multi-DC topology: `leader.eligibility=false` on secondary-DC nodes and one-way Replicator of `_schemas` (medium confidence, M8).
- Backups of `_schemas` (medium confidence, M6) and `min.insync.replicas` above 1 (medium confidence, M5): see [ask-first-decisions](./ask-first-decisions.md).
- Sizing: a 1 GB heap is "more than sufficient" for about 10,000 unique schemas, CPU use is light, no disk-resident data apart from logs (medium confidence, M9).

## Monitoring (medium confidence, M13)

The monitoring page was read in part. Metrics: `kafka.schema.registry:type=master-slave-role` (1 is primary, 0 is secondary), `type=jetty-metrics` (`connections-active`, `request_queue_size`, `thread_pool_usage`), `type=jersey-metrics` (`<endpoint>.request-latency-avg`, `-max`), `type=exporter` (Schema Linking). Alerting when no node or two nodes report `master-slave-role=1` is an inference (unverified, U20). The 8.4 release notes list a bundled `jmx_prometheus_javaagent` upgrade from 0.20.0 to 1.6.0 that "might require updates to your existing monitoring configuration" (medium confidence, M17). Source: [monitoring](https://docs.confluent.io/platform/8.4/schema-registry/monitoring.html).

There is no official health-check endpoint (unverified, I1).

## Client errors to handle

40401 subject not found, 40402 version not found, 409 incompatible schema, 42201 invalid schema, 42203 invalid compatibility level, 42204 invalid mode, 50001 backend datastore error, 50003 error while forwarding to the primary ([API](https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html)). The 8.4.0 changelog says 403 is returned instead of 5xx for permission errors (medium confidence, M17).

## Deprecations

Storing the Confluent license in `_confluent-license` is deprecated, and CP 8.5 is expected to stop using it by default (medium confidence, M17). Client key `schema.registry.basic.auth.user.info` is deprecated (medium confidence, M20; see A9 in always-do-patterns).

## Security checklist

HTTPS listeners; Basic only over HTTPS (medium confidence, M3); `inter.instance.protocol=https` with HTTPS listeners; `kafkastore.security.protocol` SASL_SSL or SSL; Kafka ACLs for the principal (medium confidence, M4); RBAC and authorizers only with an Enterprise license (medium confidence, M16); `json.type.allowed.packages` empty (medium confidence, M11); `mode.mutability` off unless needed (default unverified, U11).
