---
name: integrating-kafka-connect-v4-4
description: "Integrates Kafka Connect 4.4.0 distributed workers: internal topics, REST security, DLQ, exactly-once sources, plugins. Use when running Connect workers. Not for brokers (operating-kafka-v4-4), Kubernetes (operating-kafka-strimzi-v1-3, operating-kafka-confluent-kubernetes-v3-4), Debezium."
---

# Integrating Kafka Connect 4.4.0 (distributed mode, Docker Compose)

> Version lock: every claim applies to **Kafka Connect 4.4.0** (part of Apache Kafka 4.4.0) only. Research date **2026-11-04**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page.
> Provenance: official pages listed in the [Source Bibliography](./blueprints/unverified-and-risks.md#source-bibliography).

## Version Context

| Item | Value | Source (fetched 2026-11-04) |
|---|---|---|
| Kafka Connect | 4.4.0, shipped with Apache Kafka 4.4.0, released 2026-10-22 | https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/ |
| Java | Connect needs Java 17+ since 4.0.0. 17, 21 and 25 fully supported | https://kafka.apache.org/44/operations/java-version/ and https://kafka.apache.org/44/getting-started/upgrade/ |
| Broker protocol | Connect clients must be on 2.1+ against 4.x brokers | https://kafka.apache.org/44/getting-started/compatibility/ |
| Container image | `apache/kafka:4.4.0` exists. Running Connect from it is not documented (unverified) | https://kafka.apache.org/44/getting-started/docker/ |
| Compatibility with 3.9 brokers | Not researched (unverified, U18). The compatibility page gives only the client protocol floor | https://kafka.apache.org/44/getting-started/compatibility/ |
| New in 4.4.0 | `internal.topics.automatic.creation.enable` and `connect-internal-topics.sh` (KIP-1209) | https://kafka.apache.org/44/getting-started/upgrade/ |

**Version-lifetime risk** (as of 2026-11-04; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Kafka 5.0.0 makes the `Allowlist` client-override policy the default and removes `Principal`: https://kafka.apache.org/44/getting-started/upgrade/
- Support is best effort for the last 3 releases (medium confidence). No official end-of-life table exists (unverified).

## Scope

In scope: the Connect runtime in distributed mode on Docker Compose (dev, CI, staging). Out of scope: broker operations (use `operating-kafka-v4-4`), Kubernetes (use `operating-kafka-strimzi-v1-3` or `operating-kafka-confluent-kubernetes-v3-4`), Debezium connector configuration (later unit), Kafka Streams, schema registry converters.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Ask-first decisions](./blueprints/ask-first-decisions.md)
- [Deploy a worker with Docker Compose](./blueprints/deploy-compose.md)
- [Error handling and DLQ](./blueprints/error-handling-dlq.md)
- [Security](./blueprints/security.md)
- [Observability and operations](./blueprints/observability.md)
- [Migration guide 3.9 to 4.4](./blueprints/migration-guide.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

Code for each item is in [always-do-patterns](./blueprints/always-do-patterns.md).

- **Use distributed mode when the workload needs fault tolerance** ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [overview](https://kafka.apache.org/44/kafka-connect/overview/)).
- **Have the config, offset and status topics exist before workers start** ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/)).
- **Make the three internal topics replicated** ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/)).
- **Expose the REST API only to trusted users and networks** ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [security model](https://kafka.apache.org/44/security/security-model-connect/)).
- **Use an HTTPS REST listener** ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [security model](https://kafka.apache.org/44/security/security-model-connect/)).
- **Set `connector.client.config.override.policy=Allowlist`** ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [security model](https://kafka.apache.org/44/security/security-model-connect/), [upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/)).
- **Reference secrets through a ConfigProvider placeholder, never inline** ([configuration providers](https://kafka.apache.org/44/configuration/configuration-providers/), [security model](https://kafka.apache.org/44/security/security-model-connect/)).
- **Test plugins under `hybrid_warn` or `hybrid_fail` before switching to `service_load`** ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/)).
- **Run Connect 4.4.0 workers on Java 17 or later** ([upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/), [Java version](https://kafka.apache.org/44/operations/java-version/), [quick start](https://kafka.apache.org/44/getting-started/quickstart/)).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Standalone vs distributed | Standalone: one process, no fault tolerance. Distributed: balancing and fault tolerance, needs 3 internal topics | "Does the workload need fault tolerance or exactly-once source delivery?" |
| Error tolerance and DLQ | `none` fails the task. `all` with DLQ keeps flowing. `all` without DLQ loses records | "Are skipped records acceptable, and who drains the DLQ?" |
| Exactly-once sources | New cluster: one rolling start with `enabled`. Existing: `preparing` then `enabled`. Connector must support it | "Does the connector declare exactly-once support, and is the cluster new?" |
| Internal topic creation | IaC creates them, or the 4.4 `internal.topics.automatic.creation.enable` setting (default `true`) does. With `false`, a missing topic fails startup | "Who creates the internal topics before workers start: IaC or the 4.4 auto-creation setting?" |
| REST authentication | Reverse proxy or REST extension (medium confidence). Extension class name (unverified) | "Which identity system fronts the platform?" |
| Converters | JsonConverter in the sample. Avro or Protobuf need a vendor converter (out of scope). Converter semantics from one page (medium confidence) | "Which format do consumers expect?" |
| Internal topic shape and replication | Config topic one partition, all three compacted. Replication factor 3 is the configs default, -1 means the broker default (medium confidence) | "Do you accept this topic shape, or does IaC provision the topics?" |
| Connect cluster `group.id` | Unique per cluster, must not clash with consumer group IDs (medium confidence) | "Which group.id does each Connect cluster use?" |
| Plugin layout | Each plugin with its dependencies in its own direct child directory of `plugin.path` (medium confidence) | "Where are plugins installed?" |
| Plugin discovery mode | `only_scan`, `hybrid_warn` (default), `hybrid_fail`, `service_load` | "Do all installed plugins ship ServiceLoader manifests?" |
| Secured cluster | Client security settings repeated with `producer.` and `consumer.` prefixes (medium confidence) | "Which security protocol do the brokers use?" |
| Running from `apache/kafka:4.4.0` | Not documented for Connect (unverified). Compose is inferred | "Do you accept an inferred Compose entrypoint, verified by a human?" |
| Rolling upgrade | Procedure not in the 4.4 docs (unverified) | "Which worker order and window do you want?" |
| `connect.protocol` | Two official 4.4 pages disagree on the default (medium confidence) | "Can you leave it unset?" |

Details: [ask-first-decisions](./blueprints/ask-first-decisions.md).

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `errors.log.include.messages=true` in production ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/)) | Keep it `false` and route bad records to a DLQ |
| Inline a secret in a connector config ([security model](https://kafka.apache.org/44/security/security-model-connect/), [configuration providers](https://kafka.apache.org/44/configuration/configuration-providers/)) | Use a `${file:...}` ConfigProvider placeholder |
| Open the REST port to untrusted networks without authentication ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [security model](https://kafka.apache.org/44/security/security-model-connect/)) | Trusted network only, HTTPS |
| Leave the override policy at `All` where untrusted users can reach REST ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [security model](https://kafka.apache.org/44/security/security-model-connect/)) | `Allowlist` with a minimal key list |
| Use the deprecated `Principal` override policy ([upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/)) | `Allowlist` |
| Ship the sample file's replication factor 1 ([configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/), [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/); the sample file, branch head, is supporting only: [connect-distributed.properties](https://raw.githubusercontent.com/apache/kafka/4.4/config/connect-distributed.properties)) | Replicate all three internal topics (the factor is an Ask First item) |
| Change offsets of a running connector ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [administration](https://kafka.apache.org/44/kafka-connect/administration/)) | Stop the connector first, then `DELETE` or `PATCH` its offsets |
| Set `bootstrap.resolve.timeout.ms` for Connect 4.4 ([upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/), [4.4.0 announcement](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/)) | Leave it unset. Connect forces it to 0 and ignores positive values |

Details: [never-do-patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| REST port | 8083 | https://kafka.apache.org/44/kafka-connect/user-guide/ |
| `config`/`offset`/`status.storage.replication.factor` | 3 (-1 = broker default) | https://kafka.apache.org/44/configuration/kafka-connect-configs/ |
| `offset.storage.partitions` / `status.storage.partitions` | 25 / 5 | https://kafka.apache.org/44/configuration/kafka-connect-configs/ |
| `connector.client.config.override.policy` | `All` (set `Allowlist`) | https://kafka.apache.org/44/configuration/kafka-connect-configs/ |
| `plugin.discovery` | `hybrid_warn` | https://kafka.apache.org/44/configuration/kafka-connect-configs/ |
| `internal.topics.automatic.creation.enable` | true | https://kafka.apache.org/44/configuration/kafka-connect-configs/ |
| `exactly.once.source.support` | `disabled` | https://kafka.apache.org/44/configuration/kafka-connect-configs/ |
| `errors.tolerance` / `errors.retry.timeout` | `none` / 0 | https://kafka.apache.org/44/configuration/kafka-connect-configs/ |
| `errors.deadletterqueue.topic.replication.factor` | 3 | https://kafka.apache.org/44/configuration/kafka-connect-configs/ |
| `offset.flush.interval.ms` / `offset.flush.timeout.ms` | 60000 / 5000 | https://kafka.apache.org/44/configuration/kafka-connect-configs/ |
| `scheduled.rebalance.max.delay.ms` | 300000 | https://kafka.apache.org/44/configuration/kafka-connect-configs/ |
| `tasks.max` | 1 | https://kafka.apache.org/44/configuration/kafka-connect-configs/ |
| `connect.protocol` default | page conflict, U3 (medium confidence) | https://kafka.apache.org/44/configuration/kafka-connect-configs/ says `sessioned`; https://kafka.apache.org/44/kafka-connect/administration/ says `compatible` |

## External Resources

All fetched 2026-11-04.

- [Kafka Connect user guide, 4.4](https://kafka.apache.org/44/kafka-connect/user-guide/)
- [Kafka Connect configs, 4.4](https://kafka.apache.org/44/configuration/kafka-connect-configs/)
- [Kafka Connect security model, 4.4](https://kafka.apache.org/44/security/security-model-connect/)
- [Upgrading to 4.4](https://kafka.apache.org/44/getting-started/upgrade/)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
