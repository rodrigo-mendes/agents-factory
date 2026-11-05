---
name: streaming-kafka-streams-v4-4
description: "Builds Kafka Streams 4.4.0 applications in Java: topology, state stores, exactly_once_v2, error handlers, scaling, testing. Use when writing or reviewing Kafka Streams 4.4 code. Not for broker ops (operating-kafka-v4-4) or Connect (integrating-kafka-connect-v4-4)."
---

# Kafka Streams 4.4.0 (Java client library)

> Version lock: every claim applies to **Kafka Streams 4.4.0** (Apache Kafka 4.4.0) only. Research date **2026-11-04**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page.
> Provenance: official pages listed in the [Source Bibliography](./blueprints/unverified-and-risks.md#source-bibliography).

## Version Context

| Item | Value | Source (fetched 2026-11-04) |
|---|---|---|
| Kafka Streams | 4.4.0, released 2026-10-22 | https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/ and https://kafka.apache.org/community/downloads/ |
| Library nature | Client library, not a service. KRaft-era only (ZooKeeper was removed in 4.0.0, released 2025-03-18) | https://kafka.apache.org/44/security/security-model-streams/ and https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/ |
| Java | 17, 21 and 25 fully supported; Java 11 only for a subset of modules that includes streams | https://kafka.apache.org/44/operations/java-version/ |
| Maven coordinates | `org.apache.kafka:kafka-streams:4.4.0`, test: `kafka-streams-test-utils:4.4.0` (same version) | https://kafka.apache.org/44/streams/developer-guide/write-streams-app/ and https://kafka.apache.org/44/streams/developer-guide/testing/ |
| Compatible broker range | The upgrade guide table shows Streams 2.6 to 4.4 compatible with brokers 2.4.x to 4.4.x | https://kafka.apache.org/44/streams/upgrade-guide/ |
| Brokers | EOS v2 needs brokers 2.5+; `group.protocol=streams` needs brokers 4.2+ (static membership 4.4+) | https://kafka.apache.org/44/streams/upgrade-guide/ and https://kafka.apache.org/44/streams/developer-guide/streams-rebalance-protocol/ |

**Version-lifetime risk** (as of 2026-11-04; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- 4.4.0 was released 2026-10-22 and this skill was researched on 2026-11-04. Deprecated for removal in 5.0: `kafka-streams-scala`, headerless `StreamPartitioner#partitions`, `processing.exception.handler.global.enabled`: https://kafka.apache.org/44/streams/upgrade-guide/
- Support is best effort for the last 3 releases (medium confidence). No official end-of-life table exists (unverified).

## Scope

In scope: the Kafka Streams Java library (DSL, Processor API, state, exactly-once, error handling, scaling, testing, metrics). Out of scope: broker and controller operations (use `operating-kafka-v4-4`), Kafka Connect (use `integrating-kafka-connect-v4-4`), Schema Registry (use `managing-event-schemas-apicurio-v3-3` or `managing-event-schemas-confluent-v8-4`), Kubernetes (use `operating-kafka-strimzi-v1-3` or `operating-kafka-confluent-kubernetes-v3-4`).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Ask-first decisions](./blueprints/ask-first-decisions.md)
- [Topology, naming and state](./blueprints/topology-and-state.md)
- [Exactly-once and error handling](./blueprints/exactly-once-and-errors.md)
- [Scaling, standbys and rebalancing](./blueprints/scaling-and-rebalancing.md)
- [Security and internal topics](./blueprints/security-and-internal-topics.md)
- [Testing](./blueprints/testing.md)
- [Observability](./blueprints/observability.md)
- [Migration guide to 4.4](./blueprints/migration-guide.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

Code for each item is in [always-do-patterns](./blueprints/always-do-patterns.md).

- **Set `processing.guarantee=exactly_once_v2` when you need exactly-once** — 4.4 accepts only `at_least_once` and `exactly_once_v2` ([config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/)).
- **Set `deserialization.exception.handler` explicitly** — the `default.deserialization.exception.handler` key is deprecated since 4.0 ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/), [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/)).
- **Set `production.exception.handler` explicitly** — the `default.production.exception.handler` key is deprecated since 4.0 ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/), [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/)).
- **Give every stateful operator an explicit name** — generated names shift when the topology changes ([naming guide](https://kafka.apache.org/44/streams/developer-guide/dsl-topology-naming/), [DSL](https://kafka.apache.org/44/streams/developer-guide/dsl-api/), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/)).
- **Set `ensure.explicit.internal.resource.naming=true` in production** — Streams then refuses to start with generated names ([naming guide](https://kafka.apache.org/44/streams/developer-guide/dsl-topology-naming/), [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/)).
- **Close every store iterator with try-with-resources** — an unclosed iterator can end in an OOM error ([Processor API](https://kafka.apache.org/44/streams/developer-guide/processor-api/), [memory management](https://kafka.apache.org/44/streams/developer-guide/memory-mgmt/)).
- **Close `KafkaStreams` from a JVM shutdown hook** ([writing an app](https://kafka.apache.org/44/streams/developer-guide/write-streams-app/), [memory management](https://kafka.apache.org/44/streams/developer-guide/memory-mgmt/), [KafkaStreams javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/KafkaStreams.html)).
- **Set a `StreamsUncaughtExceptionHandler` before `start()`** — setting it later throws `IllegalStateException` ([KafkaStreams javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/KafkaStreams.html), [response javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/errors/StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.html), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/)).
- **Enable standbys with `num.standby.replicas` of 1 or more for fast failover** ([config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/), [architecture](https://kafka.apache.org/44/streams/architecture/)).
- **Give each instance a unique `application.server` host:port when you use remote interactive queries** ([config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/), [interactive queries](https://kafka.apache.org/44/streams/developer-guide/interactive-queries/)).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Rebalance protocol | `classic` (default; warmups, regex subscriptions) vs `streams` (broker-driven; no warmups, no regex, offline migration only). Under `streams` the client `num.standby.replicas` is ignored and the broker-side `streams.num.standby.replicas` applies (medium confidence, M14) | "Are the brokers 4.2+ (4.4+ for static membership), and does the app need warmup tasks or regex subscriptions?" |
| Processing guarantee | `at_least_once` (commit 30 s, duplicates possible) vs `exactly_once_v2` (commit 100 ms, transactions) | "Can the downstream tolerate duplicates, and does anything write outside Kafka in the processing path?" |
| Transactional state stores | `enable.transactional.statestores` (new in 4.4, default false); tuning defaults (unverified) | "Is EOS used with large stores and long restores?" |
| Deserialization error policy | `LogAndFail` vs `LogAndContinue`, optional dead letter queue; effective default (medium confidence) | "Fail the app or skip bad records, and is a DLQ topic wanted?" |
| Window grace | `ofSizeWithNoGrace` vs `ofSizeAndGrace` | "How out of order can event timestamps be?" |
| Store format | `dsl.store.format` `default` vs `headers` (larger local state) | "Do processors need record headers in state?" |
| Static membership | `group.instance.id` under the streams protocol; needs 4.4 brokers | "Are all brokers on 4.4, and do the topologies keep persistent state?" |
| Internal topic replication | `replication.factor=3` for internal topics (medium confidence) | "Should internal topics use RF 3 and `min.insync.replicas=2`?" |
| Co-partitioning | Same partition count and partitioner for join inputs (medium confidence) | "Do both join inputs have the same partition count and writer partitioning?" |
| Store type | Persistent RocksDB vs in-memory vs versioned (medium confidence) | "Which state size and lookup pattern?" |
| RocksDB memory | Shared `Cache` and `WriteBufferManager` through `rocksdb.config.setter` (medium confidence) | "Is the container memory bounded?" |
| Topic creation | Pre-create input/output topics (medium confidence) | "Who creates the topics, and is auto-creation enabled?" |

Details: [ask-first-decisions](./blueprints/ask-first-decisions.md).

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `processing.guarantee` to `exactly_once` or `exactly_once_beta` — EOS v1 was removed in 4.0 ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/), [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/)) | `StreamsConfig.EXACTLY_ONCE_V2` |
| Leave a store iterator unclosed ([Processor API](https://kafka.apache.org/44/streams/developer-guide/processor-api/), [memory management](https://kafka.apache.org/44/streams/developer-guide/memory-mgmt/), [interactive queries](https://kafka.apache.org/44/streams/developer-guide/interactive-queries/)) | `try (KeyValueIterator<...> it = store.all()) { ... }` |
| Rely on generated names, then roll out a changed topology ([naming guide](https://kafka.apache.org/44/streams/developer-guide/dsl-topology-naming/), [DSL](https://kafka.apache.org/44/streams/developer-guide/dsl-api/)) | `Materialized.as("...")` plus `ensure.explicit.internal.resource.naming=true` |
| Use APIs removed in 4.0: `through`, `transform*`, old `process`, `branch` ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/), [DSL](https://kafka.apache.org/44/streams/developer-guide/dsl-api/)) | `processValues`, `FixedKeyProcessor` |
| Call `KafkaStreams#cleanUp()` while the instance runs ([javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/KafkaStreams.html), [reset tool](https://kafka.apache.org/44/streams/developer-guide/app-reset-tool/)) | Call it only before `start()` or after `close()` |
| Run `kafka-streams-application-reset.sh` on a `group.protocol=streams` group ([reset tool](https://kafka.apache.org/44/streams/developer-guide/app-reset-tool/), [rebalance protocol](https://kafka.apache.org/44/streams/developer-guide/streams-rebalance-protocol/)) | `kafka-streams-groups.sh` |
| Migrate between `classic` and `streams` one instance at a time ([rebalance protocol](https://kafka.apache.org/44/streams/developer-guide/streams-rebalance-protocol/), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/)) | Stop all instances, switch `group.protocol`, start all instances |

Details: [never-do-patterns](./blueprints/never-do-patterns.md).

## Documentation conflict note (outside the tiers)

Not resolved here (unverified, U2): the 4.4 write-streams-app page shows a `Thread.UncaughtExceptionHandler` lambda, and the upgrade guide is read as saying that variant was removed in 4.0. Use the `StreamsUncaughtExceptionHandler` API from the javadoc.

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `processing.guarantee` | `at_least_once` (default), `exactly_once_v2` | https://kafka.apache.org/44/streams/developer-guide/config-streams/ |
| `commit.interval.ms` | 30000, or 100 under EOS | https://kafka.apache.org/44/streams/developer-guide/config-streams/ |
| `statestore.cache.max.bytes` | 10485760 (replaces deprecated `cache.max.bytes.buffering`) | https://kafka.apache.org/44/streams/developer-guide/config-streams/ |
| `acceptable.recovery.lag` | 10000 | https://kafka.apache.org/44/streams/developer-guide/config-streams/ |
| `state.dir` | `${java.io.tmpdir}/kafka-streams` | https://kafka.apache.org/44/streams/developer-guide/config-streams/ |
| `transaction.timeout.ms` under EOS | 10000 set by Streams | https://kafka.apache.org/44/streams/developer-guide/config-streams/ |
| Default serdes | null (set `default.key.serde` and `default.value.serde`) | https://kafka.apache.org/44/streams/developer-guide/datatypes/ |
| Window store retention | 1 day by default | https://kafka.apache.org/44/streams/developer-guide/dsl-api/ |
| `metrics.recording.level` | INFO | https://kafka.apache.org/44/streams/developer-guide/config-streams/ |

## External Resources

All fetched 2026-11-04.

- [Kafka Streams 4.4 documentation](https://kafka.apache.org/44/streams/)
- [Streams upgrade guide 4.4](https://kafka.apache.org/44/streams/upgrade-guide/)
- [4.4.0 release announcement (2026-10-22)](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
