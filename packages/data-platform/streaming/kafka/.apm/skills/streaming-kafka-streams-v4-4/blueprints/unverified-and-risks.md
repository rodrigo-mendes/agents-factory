# Unverified and risks register, Kafka Streams 4.4.0

Back to [SKILL.md](../SKILL.md). Provenance: the [Source Bibliography](#source-bibliography) below (official pages, read 2026-11-04). Ids U1 to U13 and U20 are conflicts and gaps found while reading; U14 to U19 were added from inline (unverified) marks. U1, U2 and U3 are conflicts or gaps that this skill does not resolve: a human must verify them. Descriptive facts cited to one versioned page carry no tag; recommendations, prohibitions and anything in Always Do or Never Do need two or more versioned pages, otherwise they sit outside the tiers as (medium confidence) with a row below. The research tracked a memory-page cache-key conflict as a resolved item; it is not an open item here (see Known stale documentation).

## Version-lifetime risk

- Kafka 4.4.0 was released 2026-10-22 (downloads page [S32], https://kafka.apache.org/community/downloads/, read 2026-11-04). A 4.4.1 fix release is expected (unverified, U18).
- 4.3.0 had a native memory leak (KAFKA-20616); the upgrade guide recommends 4.3.1: https://kafka.apache.org/44/streams/upgrade-guide/
- Deprecated for removal in 5.0: `kafka-streams-scala` (KIP-1244), headerless `StreamPartitioner#partitions` (KIP-1321), `processing.exception.handler.global.enabled`: https://kafka.apache.org/44/streams/upgrade-guide/
- Support policy: the Apache wiki says rolling upgrades are tested from the last 3 releases, bugfix releases are attempted for the last 3, and a release ships every 4 months (medium confidence, M13). No official per-version end-of-life table exists (unverified, U19).
- The successor release number and date are not known as of 2026-11-04. Re-check the downloads page before relying on this skill after any release after 4.4.0.

## Known stale documentation

- `cache.max.bytes.buffering` on the memory-management page is deprecated since 3.4; the config page and `StreamsConfig.java` agree on `statestore.cache.max.bytes` (resolved).
- The 4.4 monitoring page lists some ratio metrics under the wrong MBean.
- The write-streams-app page shows the removed `Thread.UncaughtExceptionHandler` lambda (U2).

## Unverified (U1..U20): 20 items

| ID | Item | Tag | Note |
|---|---|---|---|
| U1 | `deserialization.exception.handler` default: config page table says LogAndContinue, `StreamsConfig.java` 4.4 defines LogAndFail | (medium confidence) | Conflict kept. Code default used; set the handler explicitly. Human-verify |
| U2 | The write-streams-app page uses the `Thread.UncaughtExceptionHandler` variant that the upgrade guide says was removed in 4.0; the javadoc has only the `StreamsUncaughtExceptionHandler` variant | (unverified) | Official pages conflict. The compile failure on 4.4 is inferred. Human-verify |
| U3 | Defaults of `statestore.uncommitted.max.bytes` and `default.interactive.query.isolation.level` (KIP-892) | (unverified) | Not on any page read. Read `StreamsConfig.java` 4.4 definitions. Human-verify |
| U4 | Which `MockProcessorContext` is deprecated (KIP-1070) and which is current in test-utils | (unverified) | See testing |
| U5 | ACLs on transactional IDs for EOS | (unverified) | Not on the Streams security pages |
| U6 | Single rolling bounce from 3.5 to 4.3 to 4.4 | (unverified) | Inferred from the upgrade guide |
| U7 | Exactly-once coverage of external side effects | (unverified) | Core concepts is silent; treat as not covered |
| U8 | Streams alert thresholds | (unverified) | The monitoring page names none |
| U9 | `kafka-streams-groups.sh --reset-offsets` with `--all-input-topics --to-earliest` | (unverified) | The page names `--all-input-topics` only for `--delete-offsets` |
| U10 | `TopologyTestDriver` is `AutoCloseable`; caching effect inside the driver | (unverified) | The page shows an explicit `close()` |
| U11 | Bundled RocksDB version in 4.4 (only 9.7.3 for 4.0 is stated) | (unverified) | |
| U12 | `allow.os.group.write.access` default | (unverified) | Exists since 4.2 (KIP-1230) |
| U13 | Manage-topics page: the summarizer said the internal topics list appears cut off, though no truncation note came back | (medium confidence) | Content may end abruptly for the internal-topic config list |
| U14 | The 20-second `close()` timeout is an example value | (unverified) | Guidance is only to stay below the termination grace period |
| U15 | Exact naming factory methods beyond `Named.as`, `Consumed.as`, `Produced.as`, `Materialized.as`, and the exact `Stores.keyValueStoreBuilder` method | (unverified) | The pages name the classes |
| U16 | Observed error message when `exactly_once` is configured on 4.4 | (unverified) | Rejection is inferred from the validator code |
| U17 | The assembled example programs were not compiled | (unverified) | Representative code only |
| U18 | A 4.4.1 fix release is expected | (unverified) | Inference from the 4.3.0 leak and the release recency |
| U19 | Official per-version end-of-life table | (unverified) | None found; wiki policy only (M13) |
| U20 | `processing.exception.handler.global.enabled`: the upgrade guide deprecates it for removal in 5.0, the config page recommends enabling it | (medium confidence) | Two official 4.4 pages conflict. Not resolved here. Human-verify |

## Irresolvable (I1..): 0 items

No separate irresolvable class is kept. Facts that cannot be resolved from documentation are listed once above as U-ids (U1, U2, U3, U20) with a human-verify note.

## Medium confidence (M1..M14): 14 items

| ID | Claim | Tag |
|---|---|---|
| M1 | Internal topic `replication.factor=3` with broker `min.insync.replicas=2` and `acks=all` (one source: config page) | (medium confidence) |
| M2 | A distinct `state.dir` per instance on one host | (medium confidence) |
| M3 | `ProcessorSupplier.get()` returns a new `Processor` each time | (medium confidence) |
| M4 | Co-partition join inputs (same partition count and partitioner) | (medium confidence) |
| M5 | Create input and output topics ahead of time | (medium confidence) |
| M6 | Pass the same `Properties` to `StreamsBuilder.build(props)` when `topology.optimization` is set | (medium confidence) |
| M7 | Close `TopologyTestDriver` after each test | (medium confidence) |
| M8 | Store type guidance: persistent default, in-memory, versioned limits | (medium confidence) |
| M9 | RocksDB memory bounding with a shared `Cache` and `WriteBufferManager` | (medium confidence) |
| M10 | Do not close state stores in `Processor#close()` | (medium confidence) |
| M11 | `withLoggingDisabled()` removes fault tolerance and standbys | (medium confidence) |
| M12 | Replication factor below 3 "effectively voids EOS" | (medium confidence) |
| M13 | Support policy from the Apache wiki Time Based Release Plan, last edited 2024-07-09 | (medium confidence) |
| M14 | Under `group.protocol=streams` the client `num.standby.replicas` is ignored; the broker-side `streams.num.standby.replicas` applies (rebalance protocol page, one page) | (medium confidence) |

## Coverage limits (L1..L4): 4 items

| ID | Limit |
|---|---|
| L1 | Every page was read through WebFetch, which returns a summarized page, not verbatim text |
| L2 | The 4.4 Streams quickstart and tutorial were not read |
| L3 | The downloads page (S32) was read for the first 100000 of 152730 characters |
| L4 | The 4.0.0 announcement (S31) does not mention the 3.9 bridge release; the ZooKeeper removal was confirmed in part (ZooKeeper is not relevant to the Streams library) |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) | SKILL.md Version Context, support policy | M13 |
| (unverified) | SKILL.md Version Context, end-of-life table | U19 |
| (medium confidence) | SKILL.md Ask First: deserialization default, internal topic RF, co-partitioning, store type, RocksDB memory, topic creation | U1, M1, M4, M8, M9, M5 |
| (unverified) | SKILL.md Ask First, transactional store defaults | U3 |
| (unverified) | always-do-patterns.md | U14, U15, U17 |
| (unverified) | never-do-patterns.md | U2, U9, U16 |
| (medium confidence) | ask-first-decisions.md | U1, M1, M2, M3, M4, M5, M6, M8, M9, M10, M11, M12 |
| (unverified) | ask-first-decisions.md | U3, U7 |
| (medium confidence) | topology-and-state.md | M3, M6, U13 |
| (unverified) | topology-and-state.md | U15, U17 |
| (unverified) | SKILL.md documentation conflict note (outside the tiers), Thread-based uncaught exception handler | U2 |
| (medium confidence) | exactly-once-and-errors.md | M1, M12, U1, U20 |
| (unverified) | exactly-once-and-errors.md | U2, U3, U5, U7 |
| (unverified) | migration-guide.md, Thread-based handler | U2 |
| (medium confidence) | SKILL.md Ask First rebalance protocol row; ask-first-decisions.md rebalance protocol; scaling-and-rebalancing.md standbys | M14 |
| (medium confidence) | scaling-and-rebalancing.md | M9 |
| (unverified) | scaling-and-rebalancing.md | U9, U11 |
| (medium confidence) | security-and-internal-topics.md | M1, M2, M5, U13 |
| (unverified) | security-and-internal-topics.md | U5, U12 |
| (medium confidence) | testing.md | M7 |
| (unverified) | testing.md | U4, U10, U17 |
| (unverified) | observability.md | U8 |
| (unverified) | migration-guide.md | U6, U11 |
| (medium confidence) | evaluation-scenarios.md | U1, M1 |
| (unverified) | evaluation-scenarios.md | U2, U7, U8 |

## Source Bibliography

All pages read 2026-11-04.

| ID | Title | URL |
|---|---|---|
| S1 | Kafka Streams section index, AK 4.4.X | https://kafka.apache.org/44/streams/ |
| S2 | Streams Upgrade Guide, AK 4.4.X | https://kafka.apache.org/44/streams/upgrade-guide/ |
| S3 | Configuring a Streams Application | https://kafka.apache.org/44/streams/developer-guide/config-streams/ |
| S4 | StreamsConfig.java (apache/kafka, branch 4.4 head; supporting reference, not a counted page) | https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/StreamsConfig.java |
| S5 | Core Concepts | https://kafka.apache.org/44/streams/core-concepts/ |
| S6 | Architecture | https://kafka.apache.org/44/streams/architecture/ |
| S7 | Streams DSL | https://kafka.apache.org/44/streams/developer-guide/dsl-api/ |
| S8 | Naming Operators in a Streams DSL application | https://kafka.apache.org/44/streams/developer-guide/dsl-topology-naming/ |
| S9 | Processor API | https://kafka.apache.org/44/streams/developer-guide/processor-api/ |
| S10 | Testing a Streams Application | https://kafka.apache.org/44/streams/developer-guide/testing/ |
| S11 | Interactive Queries | https://kafka.apache.org/44/streams/developer-guide/interactive-queries/ |
| S12 | Running Streams Applications | https://kafka.apache.org/44/streams/developer-guide/running-app/ |
| S13 | Managing Streams Application Topics | https://kafka.apache.org/44/streams/developer-guide/manage-topics/ |
| S14 | Streams Rebalance Protocol | https://kafka.apache.org/44/streams/developer-guide/streams-rebalance-protocol/ |
| S15 | Memory Management | https://kafka.apache.org/44/streams/developer-guide/memory-mgmt/ |
| S16 | Streams Security | https://kafka.apache.org/44/streams/developer-guide/security/ |
| S17 | Writing a Streams Application | https://kafka.apache.org/44/streams/developer-guide/write-streams-app/ |
| S18 | Application Reset Tool | https://kafka.apache.org/44/streams/developer-guide/app-reset-tool/ |
| S19 | Monitoring (Streams section) | https://kafka.apache.org/44/operations/monitoring/ |
| S20 | StreamsUncaughtExceptionHandler javadoc, 4.4.0 | https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/errors/StreamsUncaughtExceptionHandler.html |
| S21 | StreamThreadExceptionResponse javadoc, 4.4.0 | https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/errors/StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.html |
| S22 | Apache Kafka 4.4.0 Release Announcement (2026-10-22) | https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/ |
| S23 | TimeWindows javadoc, 4.4.0 | https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/kstream/TimeWindows.html |
| S24 | KafkaStreams javadoc, 4.4.0 | https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/KafkaStreams.html |
| S25 | Kafka Streams Security Model | https://kafka.apache.org/44/security/security-model-streams/ |
| S26 | Data Types and Serialization | https://kafka.apache.org/44/streams/developer-guide/datatypes/ |
| S27 | LogAndContinueExceptionHandler.java (branch 4.4) | https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/errors/LogAndContinueExceptionHandler.java |
| S28 | DefaultProductionExceptionHandler.java (branch 4.4) | https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/errors/DefaultProductionExceptionHandler.java |
| S29 | Kafka Streams Groups Tool | https://kafka.apache.org/44/streams/developer-guide/kafka-streams-group-sh/ |
| S30 | Java Version | https://kafka.apache.org/44/operations/java-version/ |
| S31 | Apache Kafka 4.0.0 Release Announcement (2025-03-18) | https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/ |
| S32 | Downloads page (Apache Kafka project) | https://kafka.apache.org/community/downloads/ |
| W1 | Time Based Release Plan (Apache Kafka wiki), official Apache wiki, read 2026-11-04 | https://cwiki.apache.org/confluence/display/KAFKA/Time+Based+Release+Plan |
