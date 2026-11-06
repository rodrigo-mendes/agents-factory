---
name: operating-kafka-v4-4
description: "Operates Apache Kafka 4.4.0 (KRaft only) on Docker Compose: replication, security, upgrades incl. 3.9 to 4.4, DR. Use when running or upgrading Kafka 4.4 brokers. Not for ZooKeeper (operating-kafka-v3-9) or Kubernetes (operating-kafka-strimzi-v1-3, operating-kafka-confluent-kubernetes-v3-4)."
---

# Operating Apache Kafka 4.4.0 (KRaft, Docker Compose)

> Version lock: every claim applies to **Apache Kafka 4.4.0** only. Research date **2026-11-04**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page.
> Provenance: the official pages in the [Source Bibliography](./blueprints/unverified-and-risks.md#source-bibliography).

## Version Context

| Item | Value | Source (fetched 2026-11-04) |
|---|---|---|
| Apache Kafka | 4.4.0, released 2026-10-22 | https://kafka.apache.org/community/downloads/ and https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/ |
| Cluster mode | KRaft only. ZooKeeper removed in 4.0.0 (released 2025-03-18) | https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/ |
| Java | Brokers, Connect and tools need Java 17+. 17, 21 and 25 fully supported | https://kafka.apache.org/44/operations/java-version/ |
| Container image | `apache/kafka:4.4.0` (JVM). `apache/kafka-native:4.4.0` is dev and test only | https://kafka.apache.org/44/getting-started/docker/ |
| Last ZooKeeper line | Kafka 3.9 (migration bridge release). See skill `operating-kafka-v3-9` | https://kafka.apache.org/44/operations/kraft/ |

**Version-lifetime risk** (as of 2026-11-04; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- `broker.id` and `kafka-broker-api-versions.sh` are deprecated in 4.4 for removal in 5.0: https://kafka.apache.org/44/getting-started/upgrade/
- Support is best effort for the last 3 releases, one release every 4 months (medium confidence). No official end-of-life table exists (unverified).

## Scope

In scope: broker and controller operations on Docker Compose (dev, CI, staging). Out of scope: ZooKeeper mode (use `operating-kafka-v3-9`), Kubernetes (use `operating-kafka-strimzi-v1-3` or `operating-kafka-confluent-kubernetes-v3-4`), Connect and Streams internals, schema registries. The upgrade of a 3.9 KRaft cluster to 4.4 is covered in [migration-guide](./blueprints/migration-guide.md).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Ask-first decisions](./blueprints/ask-first-decisions.md)
- [Deploy with Docker Compose](./blueprints/deploy-compose.md)
- [High availability, failover, DR](./blueprints/high-availability-dr.md)
- [Observability, KPIs and runbooks](./blueprints/observability.md)
- [Performance tuning](./blueprints/performance-tuning.md)
- [TLS and security](./blueprints/tls-and-security.md)
- [Capacity sizing](./blueprints/capacity-sizing.md)
- [Migration guide 3.9 to 4.4](./blueprints/migration-guide.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

Code and verification commands for each item are in [always-do-patterns](./blueprints/always-do-patterns.md).

Each item rests on at least two versioned official pages.

- **Use replication factor 3 on durable topics** ([topic configs](https://kafka.apache.org/44/configuration/topic-configs/), [design](https://kafka.apache.org/44/design/design/)).
- **Set `min.insync.replicas=2` on durable topics** ([topic configs](https://kafka.apache.org/44/configuration/topic-configs/), [design](https://kafka.apache.org/44/design/design/)).
- **Keep producer `acks=all`** ([producer configs](https://kafka.apache.org/44/configuration/producer-configs/), [design](https://kafka.apache.org/44/design/design/)).
- **Keep producer `enable.idempotence=true`** ([producer configs](https://kafka.apache.org/44/configuration/producer-configs/), [design](https://kafka.apache.org/44/design/design/)).
- **Generate a cluster ID with `kafka-storage.sh random-uuid`** ([KRaft](https://kafka.apache.org/44/operations/kraft/), [quickstart](https://kafka.apache.org/44/getting-started/quickstart/)).
- **Use `SSL` on certificate-authenticated listeners that leave the host** ([SSL](https://kafka.apache.org/44/security/encryption-and-authentication-using-ssl/), [listeners](https://kafka.apache.org/44/security/listener-configuration/)).
- **Mirror to a second cluster with MirrorMaker 2 for DR** ([geo-replication](https://kafka.apache.org/44/operations/geo-replication-cross-cluster-data-mirroring/), [datacenters](https://kafka.apache.org/44/operations/datacenters/)).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Controller placement | Single combined (dev), 3 combined (CI), 3 dedicated + N brokers (critical; the advice to avoid combined mode there rests on one official page, medium confidence, M13). Compose is single-host (medium confidence, M12) | "Is this environment critical, or dev/CI? Compose is single-host, so is multi-host HA needed?" |
| Controller quorum size | Odd quorum of 3 or 5 (2N+1 survives N failures), checked with `kafka-metadata-quorum.sh describe --status` (one official page, medium confidence, M16, M18) | "Do you want 3 or 5 controllers?" |
| Node identity | Unique `node.id` per node; `broker.id` is deprecated (medium confidence, M17) | "Which node ids are free?" |
| Cluster ID | Format every KRaft node with the one generated cluster ID (one official page, medium confidence, M24) | "Which cluster ID do all nodes share?" |
| Authorizer | `StandardAuthorizer` with `super.users` on every node, and `allow.everyone.if.no.acl.found` kept at `false` (one official page, medium confidence, M14) | "Should ACL authorization be enabled on this cluster?" |
| SASL mechanism | `SASL_SSL` on SASL-authenticated listeners that leave the host; SASL/PLAIN only with TLS, with SCRAM-SHA-512 over `SASL_SSL` as the alternative (one official page, medium confidence, M21). SCRAM credentials in the metadata log suit production only on secured controllers (medium confidence, M23) | "Which SASL mechanism do clients support?" |
| Client certificates | `ssl.client.auth=required`; `requested` is discouraged (one official page, medium confidence, M22) | "Do all clients present certificates?" |
| Controller port | Publish only client listener ports; keep the controller listener network-isolated (one official page, medium confidence, M20) | "Which ports must leave the host?" |
| File descriptors | Raise `ulimits: nofile` to at least 100000 (one official page, medium confidence, M19) | "Can the host raise the nofile limit?" |
| Image tag | Pin `apache/kafka:4.4.0`. Avoiding floating tags such as `latest` is factory practice (medium confidence, M15) | "Is pinning `apache/kafka:4.4.0` acceptable?" |
| Static vs dynamic quorum | Static `controller.quorum.voters` (official examples) vs dynamic `controller.quorum.bootstrap.servers`. Static-to-dynamic upgrade sources conflict (medium confidence, U4). Docker env formatting of a dynamic quorum (unverified, U5) | "Will controllers be added or replaced without a rebuild?" |
| Native image | `apache/kafka-native` is described as dev/test only (Docker page). SASL support in 4.4.0 has conflicting official sources (unverified, U1) | "Do you need SASL? Then use the JVM image. Verify with a human before choosing native" |
| Topic auto-creation | `auto.create.topics.enable=false` is factory practice, not in the docs (medium confidence) | "Should topics be created only through explicit tooling?" |
| Certificate rotation | Hot keystore reload is not documented for 4.4 (unverified); plan a rolling restart | "Is a rolling restart acceptable for certificate rotation?" |
| Rolling upgrade order | Controllers first is common practice (unverified) | "Which node order do you want for the roll?" |
| Multi-datacenter | One cluster per DC with MM2 vs a stretched cluster (discouraged by one official page, medium confidence, M29) | "Is cross-DC replication required, and what RPO is acceptable?" |
| Delivery guarantee | At-least-once (default) vs exactly-once (transactions, `read_committed`) | "Do consumers write side effects outside Kafka?" |

Details: [ask-first-decisions](./blueprints/ask-first-decisions.md).

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Apply the official Compose example defaults in production: RF 1, min ISR 1, logs in `/tmp` ([README](https://raw.githubusercontent.com/apache/kafka/4.4/docker/examples/README.md), branch head, supporting; [example](https://raw.githubusercontent.com/apache/kafka/4.4/docker/examples/docker-compose-files/cluster/isolated/plaintext/docker-compose.yml), branch head, supporting; [design](https://kafka.apache.org/44/design/design/), [topic configs](https://kafka.apache.org/44/configuration/topic-configs/)) | RF 3, min ISR 2 and a persistent volume (medium confidence, M1) |
| Create a topic with RF 3 and leave `min.insync.replicas=1` ([topic configs](https://kafka.apache.org/44/configuration/topic-configs/), [design](https://kafka.apache.org/44/design/design/)) | Set `min.insync.replicas=2` |
| Enable `unclean.leader.election.enable` ([design](https://kafka.apache.org/44/design/design/), [topic configs](https://kafka.apache.org/44/configuration/topic-configs/)) | Keep it `false` (default) |
| Add ZooKeeper settings such as `zookeeper.connect` ([KRaft vs ZooKeeper](https://kafka.apache.org/44/getting-started/zk2kraft/), [4.0.0 announcement](https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/)) | KRaft settings. ZooKeeper work goes to `operating-kafka-v3-9` |
| Run a broker older than the `kafka-storage` tool that formatted its directory ([upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/), [4.4.0 announcement](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/)) | Use a broker equal to or newer than the tool |

Details: [never-do-patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `default.replication.factor` | 1 (set 3) | https://kafka.apache.org/44/configuration/broker-configs/ |
| `min.insync.replicas` | 1 (set 2 with RF 3) | https://kafka.apache.org/44/configuration/topic-configs/ |
| `offsets.topic.replication.factor` | 3 | https://kafka.apache.org/44/configuration/broker-configs/ |
| `unclean.leader.election.enable` | false | https://kafka.apache.org/44/configuration/broker-configs/ |
| `replica.lag.time.max.ms` | 30000 | https://kafka.apache.org/44/configuration/broker-configs/ |
| Producer `acks` / `linger.ms` | all / 5 | https://kafka.apache.org/44/configuration/producer-configs/ |
| `ssl.enabled.protocols` | TLSv1.2,TLSv1.3 | https://kafka.apache.org/44/configuration/broker-configs/ |
| Env var mapping | `KAFKA_` prefix, `.` to `_`, `_` to `__`, `-` to `___` | https://raw.githubusercontent.com/apache/kafka/4.4/docker/examples/README.md (branch head, supporting) |
| Controller quorum size | 3 tolerates 1 failure, 5 tolerates 2 | https://kafka.apache.org/44/operations/kraft/ |

Coverage: the broker configs page was read 200000 of 201536 characters (register L1).

## External Resources

All fetched 2026-11-04.

- [Apache Kafka 4.4 documentation](https://kafka.apache.org/44/)
- [4.4.0 release announcement (2026-10-22)](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/)
- [Upgrading to 4.4](https://kafka.apache.org/44/getting-started/upgrade/)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
