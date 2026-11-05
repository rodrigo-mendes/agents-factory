---
name: operating-kafka-v3-9
description: "Operates Apache Kafka 3.9.2 (last ZooKeeper line, ZK to KRaft migration) on Docker Compose. Use when running or migrating 3.9 brokers. Not for 4.x or 3.9 to 4.4 upgrades (operating-kafka-v4-4) or Kubernetes (operating-kafka-strimzi-v1-3, operating-kafka-confluent-kubernetes-v3-4)."
---

# Operating Apache Kafka 3.9.2 (ZooKeeper, KRaft dual mode, migration)

> Version lock: every claim applies to **Apache Kafka 3.9.2** only. Research date **2026-11-04**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page.
> Provenance: the official pages in the [Source Bibliography](./blueprints/unverified-and-risks.md#source-bibliography).

> ⚠️ **Lifecycle warning.** Kafka 3.9 is the **last ZooKeeper line**. The downloads page lists 3.9.x under Archived Releases and lists only 4.4.0, 4.3.2 and 4.2.2 as supported ([downloads](https://kafka.apache.org/community/downloads/), partly read: 100000 of 152730 characters, (medium confidence)). The 3.9 ZooKeeper page says the last ZooKeeper-capable 3.x release gets critical bug fixes and security fixes for 12 months after its release, and does not say when that window starts ([ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/), (unverified) start date, U4, human-verify). Use 3.9 to migrate to KRaft, not as a destination.

## Version Context

| Item | Value | Source (fetched 2026-11-04) |
|---|---|---|
| Apache Kafka | 3.9.2, released 2026-02-21, listed as Archived | https://kafka.apache.org/community/downloads/ and https://archive.apache.org/dist/kafka/3.9.2/RELEASE_NOTES.html |
| Metadata modes | ZooKeeper mode (deprecated since 3.5, removed in 4.0) and KRaft. A server with `process.roles` unset runs in ZooKeeper mode | https://kafka.apache.org/39/operations/kraft/ and https://kafka.apache.org/39/operations/zookeeper/ |
| Bridge release | 3.9 is the last release that can run the ZooKeeper-to-KRaft migration | https://kafka.apache.org/44/operations/kraft/ |
| ZooKeeper | 3.8.4 is bundled with 3.9.2 | https://raw.githubusercontent.com/apache/kafka/3.9.2/gradle/dependencies.gradle |
| Java | Brokers: 8, 11, 17, 21 fully supported, 25 best effort. Java 11 is deprecated since 3.7 | https://kafka.apache.org/39/operations/java-version/ |
| Container image | `apache/kafka:3.9.2` exists. ZooKeeper mode in this image needs a command override (medium confidence, U1) | https://hub.docker.com/v2/repositories/apache/kafka/tags/3.9.2 |
| Successor | Kafka 4.4.0 (KRaft only), see skill `operating-kafka-v4-4` | https://kafka.apache.org/community/downloads/ |

**Version-lifetime risk** (as of 2026-11-04; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- No further 3.9.x patch is expected, because 3.9.x is archived (medium confidence, M2). No official per-version end-of-life table exists (unverified, U15).
- ZooKeeper mode is removed in 4.0, so a ZooKeeper cluster cannot upgrade straight to 4.x.

## Scope

In scope: broker, ZooKeeper and KRaft-on-3.9 operations on Docker Compose (dev, CI, staging), and the ZooKeeper-to-KRaft migration on 3.9.2. Out of scope: 4.x operation (use `operating-kafka-v4-4`; the upgrade of a 3.9 KRaft cluster to 4.4 is in its `blueprints/migration-guide.md`), Kubernetes (use `operating-kafka-strimzi-v1-3` or `operating-kafka-confluent-kubernetes-v3-4`), Connect, Streams, schema registries.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Ask-first decisions](./blueprints/ask-first-decisions.md)
- [Deploy a ZooKeeper ensemble with Docker Compose](./blueprints/deploy-compose-zookeeper.md)
- [ZooKeeper ensemble operations](./blueprints/zookeeper-ensemble.md)
- [ZooKeeper and broker security](./blueprints/zookeeper-security.md)
- [ZooKeeper to KRaft migration runbook and rollback](./blueprints/zk-to-kraft-migration.md)
- [High availability, failover, DR, runbooks](./blueprints/high-availability-dr.md)
- [Observability and KPIs](./blueprints/observability.md)
- [Performance tuning](./blueprints/performance-tuning.md)
- [Capacity sizing and defaults](./blueprints/capacity-sizing.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

Code and verification commands for each item are in [always-do-patterns](./blueprints/always-do-patterns.md). Each item rests on at least two official pages.

- **Use replication factor 3 on durable topics** ([topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/), [production example](https://kafka.apache.org/39/operations/kafka-configuration/)).
- **Set `min.insync.replicas=2` on durable topics** ([topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/), [production example](https://kafka.apache.org/39/operations/kafka-configuration/)).
- **Keep producer `acks=all`** ([producer configs](https://kafka.apache.org/39/configuration/producer-configs/), [topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/)).
- **Keep producer `enable.idempotence=true`** ([producer configs](https://kafka.apache.org/39/configuration/producer-configs/), [design](https://kafka.apache.org/39/design/design/)).
- **Keep `unclean.leader.election.enable=false`** ([topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/), [design](https://kafka.apache.org/39/design/design/), [broker configs](https://kafka.apache.org/39/configuration/broker-configs/)).
- **Run an odd number of ZooKeeper servers** ([ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/), [ZooKeeper Admin Guide 3.8.4](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html)).
- **Run at least 3 ZooKeeper servers** ([ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/), [ZooKeeper Admin Guide 3.8.4](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html)).
- **Put the ZooKeeper transaction log on a dedicated device (`dataLogDir`)** ([ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/), [Admin Guide](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html)).
- **Use `SSL` on certificate-authenticated listeners that leave the host** ([SSL](https://kafka.apache.org/39/security/encryption-and-authentication-using-ssl/), [listeners](https://kafka.apache.org/39/security/listener-configuration/)).
- **Use `SASL_SSL` on SASL-authenticated listeners that leave the host** ([SASL](https://kafka.apache.org/39/security/authentication-using-sasl/), [listeners](https://kafka.apache.org/39/security/listener-configuration/)).
- **Map `inter.broker.listener.name` to an SSL listener so inter-broker traffic is encrypted** ([SSL](https://kafka.apache.org/39/security/encryption-and-authentication-using-ssl/), [listeners](https://kafka.apache.org/39/security/listener-configuration/), [running cluster](https://kafka.apache.org/39/security/incorporating-security-features-in-a-running-cluster/)).
- **Keep hostname verification on (`ssl.endpoint.identification.algorithm=https`)** ([SSL](https://kafka.apache.org/39/security/encryption-and-authentication-using-ssl/), [broker configs](https://kafka.apache.org/39/configuration/broker-configs/)).
- **Run brokers on Java 17 or 21** ([Java](https://kafka.apache.org/39/operations/java-version/), [upgrade notes](https://kafka.apache.org/39/getting-started/upgrade/)).
- **Generate the cluster ID once with `kafka-storage.sh random-uuid`** ([KRaft](https://kafka.apache.org/39/operations/kraft/), [quickstart](https://kafka.apache.org/39/getting-started/quickstart/)).
- **Set `inter.broker.protocol.version=3.9` on every broker before provisioning migration controllers** ([KRaft migration](https://kafka.apache.org/39/operations/kraft/), [upgrade notes](https://kafka.apache.org/39/getting-started/upgrade/)).
- **Restart brokers one at a time** ([upgrade notes](https://kafka.apache.org/39/getting-started/upgrade/), [running cluster](https://kafka.apache.org/39/security/incorporating-security-features-in-a-running-cluster/)).
- **Mirror to a second cluster with MirrorMaker 2 for DR** ([datacenters](https://kafka.apache.org/39/operations/datacenters/), [geo-replication](https://kafka.apache.org/39/operations/geo-replication-cross-cluster-data-mirroring/)).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Metadata mode | ZooKeeper (existing clusters only), KRaft dedicated (new 3.9 clusters), KRaft combined (dev/CI; not recommended in critical environments, medium confidence) | "Is this new or existing? When is the migration scheduled?" |
| ZooKeeper-mode broker from the stock image | Default `CMD` formats storage and rejects ZooKeeper configs (medium confidence, U1). Override `command` with `kafka-server-start.sh`. Whole Compose layout is (unverified) | "Do you accept an untested command override?" |
| Cluster ID | Generate once (Always Do); formatting every KRaft node with that same ID rests on one official page (medium confidence, M14). For the migration, use the existing ZooKeeper cluster ID | "Which cluster ID do all nodes share?" |
| Rolling restart pacing | Waiting for the ISR to rejoin before restarting the next broker rests on one official page, the running-cluster security page (medium confidence, M15) | "How will you confirm the ISR is back between restarts?" |
| Migration timing and finalize | Procedure rests on one official page (medium confidence). Finalize is irreversible. Building a 3-controller quorum is human-verify (unverified, U26) | "Is dual-write validated, and who signs off finalize?" |
| Patch for migration | Page says 3.9.1; 3.9.2 includes two migration fixes (medium confidence, U3) | "Is every broker on 3.9.2?" |
| Support window | 12-month statement has an unresolved start date (unverified, U4); 3.9.x archived (medium confidence) | "Can you accept running an archived line until migration?" |
| Quorum type | Static `controller.quorum.voters` vs dynamic. Conversion static to dynamic is not supported in 3.9. Image formatting of dynamic (unverified, U5) | "Will controllers change without a rebuild?" |
| ZooKeeper ensemble size | 3 tolerates 1 failure, 5 tolerates 2, 7 tolerates 3 | "How many ZooKeeper failures must you survive?" |
| Topic auto-creation | `auto.create.topics.enable=false` appears only as an example value (medium confidence) | "Create topics only through tooling?" |
| Multi-datacenter | One cluster per DC with MM2 vs stretched (discouraged) | "What RPO is acceptable?" |
| Delivery guarantee | At-least-once (default) vs exactly-once | "Can consumers tolerate duplicates?" |

Details: [ask-first-decisions](./blueprints/ask-first-decisions.md).

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Run production with `min.insync.replicas=1` and RF 1 ([design](https://kafka.apache.org/39/design/design/), [topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/), [production example](https://kafka.apache.org/39/operations/kafka-configuration/)) | RF 3, `min.insync.replicas=2` |
| Copy the official Compose example's single-replica settings and `/tmp` log dir into a persistent cluster ([design](https://kafka.apache.org/39/design/design/), [topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/), [broker configs](https://kafka.apache.org/39/configuration/broker-configs/); [examples README](https://raw.githubusercontent.com/apache/kafka/3.9/docker/examples/README.md), branch head, supporting; [example](https://raw.githubusercontent.com/apache/kafka/3.9/docker/examples/docker-compose-files/cluster/isolated/plaintext/docker-compose.yml), branch head, supporting) | RF 3, min ISR 2, a named volume for log dirs |
| Enable `unclean.leader.election.enable` on durable topics ([topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/), [design](https://kafka.apache.org/39/design/design/)) | Keep it `false` |
| Plan a direct ZooKeeper-to-4.x upgrade ([4.4 KRaft](https://kafka.apache.org/44/operations/kraft/), [4.0.0 announcement](https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/)) | Migrate to KRaft on 3.9.2 (the bridge release), then follow `operating-kafka-v4-4` |
| Plan to keep ZooKeeper mode as the destination ([ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/), [4.0.0 announcement](https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/)) | Migrate to KRaft on 3.9.2 |
| Stretch one cluster and one ZooKeeper ensemble across datacenters ([datacenters](https://kafka.apache.org/39/operations/datacenters/), [geo-replication](https://kafka.apache.org/39/operations/geo-replication-cross-cluster-data-mirroring/)) | One cluster per DC mirrored with MM2 |
| Let clients reach ZooKeeper or publish its ports ([ZooKeeper auth](https://kafka.apache.org/39/security/zookeeper-authentication/), [Admin Guide](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html)) | Keep ZooKeeper on an internal network, only brokers and admin tools reach it |

Details: [never-do-patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `default.replication.factor` / `min.insync.replicas` | 1 / 1 (set 3 / 2) | https://kafka.apache.org/39/configuration/broker-configs/ |
| `offsets.topic.replication.factor` | 3 | https://kafka.apache.org/39/configuration/broker-configs/ |
| `unclean.leader.election.enable` | false | https://kafka.apache.org/39/configuration/broker-configs/ |
| `replica.lag.time.max.ms` | 30000 | https://kafka.apache.org/39/configuration/broker-configs/ |
| `zookeeper.session.timeout.ms` | 18000 | https://kafka.apache.org/39/configuration/broker-configs/ |
| `inter.broker.protocol.version` default | 3.9-IV0 | https://kafka.apache.org/39/configuration/broker-configs/ |
| Producer `acks` / `linger.ms` | all / 0 | https://kafka.apache.org/39/configuration/producer-configs/ |
| ZooKeeper ensemble tolerance | 3 servers: 1 failure, 5: 2, 7: 3 | https://kafka.apache.org/39/operations/zookeeper/ |
| ZooKeeper `autopurge.purgeInterval` | 0 (off) by default | https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html |
| Env var mapping (image) | `KAFKA_` prefix, `.` to `_`, `_` to `__`, `-` to `___` | https://raw.githubusercontent.com/apache/kafka/3.9/docker/examples/README.md |

## External Resources

All fetched 2026-11-04.

- [Apache Kafka 3.9 documentation](https://kafka.apache.org/39/)
- [3.9.2 release notes](https://archive.apache.org/dist/kafka/3.9.2/RELEASE_NOTES.html)
- [Upgrading to 3.9](https://kafka.apache.org/39/getting-started/upgrade/)
- [Downloads (support status)](https://kafka.apache.org/community/downloads/)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
