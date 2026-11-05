# Ask-first decisions, Kafka Streams 4.4.0

Back to [SKILL.md](../SKILL.md). Each decision needs the user's answer before code or config is written. All pages read 2026-11-04. Items marked (medium confidence) rest on one source; items marked (unverified) have none.

## Rebalance protocol: classic or streams

Sources: [rebalance protocol](https://kafka.apache.org/44/streams/developer-guide/streams-rebalance-protocol/), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/), [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `group.protocol=classic` (default) | Warmup tasks, HA and rack-aware client assignor, regex subscriptions, custom main consumer | Client-side assignment | Existing apps, apps that need warmups or pattern subscriptions |
| `group.protocol=streams` | Broker-driven assignment, `kafka-streams-groups.sh`, topology plugin, pluggable broker assignors (4.4), static membership (4.4) | No warmup tasks, no regex subscriptions, no online migration, topology changes need a new group, some client configs ignored | New applications on 4.2+ brokers and clients |

Requirements: brokers and clients 4.2 or later; the `streams.version` feature enabled (default on new 4.2 clusters); `group.coordinator.rebalance.protocols` includes `streams`. Migration from classic is offline only; do not migrate on 4.2.0 (KAFKA-20254, fixed in 4.2.1). Standbys under `streams`: the client `num.standby.replicas` is ignored; set the broker-side group config `streams.num.standby.replicas` instead (medium confidence, M14, [rebalance protocol](https://kafka.apache.org/44/streams/developer-guide/streams-rebalance-protocol/) only). Ask: "Are the brokers 4.2+ (4.4+ for static membership), and does the app need warmup tasks or regex subscriptions?"

## Processing guarantee

Sources: [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/), [core concepts](https://kafka.apache.org/44/streams/core-concepts/), [StreamsConfig.java](https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/StreamsConfig.java).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `at_least_once` (default) | Throughput, commit every 30 s | Duplicates on failure | Idempotent downstreams |
| `exactly_once_v2` | Atomic offsets, state and output | Latency (commit every 100 ms), transactions, at least 3 brokers by default | Read-process-write pipelines that cannot tolerate duplicates |

Exactly-once covers source topic to output topic and state stores. Whether external side effects are covered is not stated; treat them as not covered (unverified, U7). Under EOS Streams sets `transaction.timeout.ms=10000`; it must be at least `commit.interval.ms` and at most the broker `transaction.max.timeout.ms`. Ask: "Does anything write outside Kafka in the processing path?"

## Transactional state stores (new in 4.4)

Sources: [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/), [4.4.0 announcement](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/), [StreamsConfig.java](https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/StreamsConfig.java) (boolean, default false, importance low).

With EOS and `enable.transactional.statestores=true`, stores are no longer wiped and rebuilt on error; only writes since the last commit are lost and replayed. Tuning knobs: `statestore.uncommitted.max.bytes` and `default.interactive.query.isolation.level`. Their defaults are (unverified, U3): the config page does not document them and the `StreamsConfig.java` 4.4 text read on 2026-11-04 did not quote them. Ask: "Is the app on EOS with large stores and long restores?"

## Deserialization error policy

Sources: [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/), [StreamsConfig.java](https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/StreamsConfig.java), [LogAndContinueExceptionHandler.java](https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/errors/LogAndContinueExceptionHandler.java), [DefaultProductionExceptionHandler.java](https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/errors/DefaultProductionExceptionHandler.java).

| Option | Behavior |
|---|---|
| `LogAndFailExceptionHandler` | Streams shuts down. Code default in 4.4, but the config page table says LogAndContinue (medium confidence, U1) |
| `LogAndContinueExceptionHandler` | Logs and skips the record |
| Either built-in handler plus `errors.dead.letter.queue.topic.name` (4.2+) | Built-in handlers read the DLQ topic and build DLQ records |
| Custom handler | Returns a `Response` that can carry DLQ records |

DLQ is not supported for global store or GlobalKTable failures. Always set the handler explicitly. Ask: "Fail the app or skip bad records, and is a DLQ topic wanted?"

## Window grace period

Sources: [TimeWindows javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/kstream/TimeWindows.html), [DSL](https://kafka.apache.org/44/streams/developer-guide/dsl-api/), [core concepts](https://kafka.apache.org/44/streams/core-concepts/).

`TimeWindows.ofSizeWithNoGrace(size)` sets grace to zero, so any out-of-order record after window end is dropped. `ofSizeAndGrace(size, grace)` drops only records that arrive more than `grace` after window end. Window store retention defaults to one day (`Materialized#withRetention`). Ask: "How out of order can event timestamps be?"

## `dsl.store.format`

Sources: [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/). Values `default` or `headers` (4.3+). `headers` enables headers-aware stores and can increase local state size; in 4.4 `suppress()` keeps headers under this format. Ask: "Do processors need record headers in state?"

## Static membership under the streams protocol

Sources: [rebalance protocol](https://kafka.apache.org/44/streams/developer-guide/streams-rebalance-protocol/), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/). `group.instance.id` needs 4.4 brokers; older brokers reject it with `INVALID_REQUEST`, which is fatal to the client. Remove it before downgrading brokers. It gives little benefit for topologies without persistent stores. Ask: "Are all brokers 4.4, and do the topologies keep persistent state?"

## Single-source items (medium confidence)

Each rests on one official page; none is in Always Do or Never Do.

- Internal topic `replication.factor=3` (default -1, the broker default) with broker `min.insync.replicas=2` and `acks=all` (medium confidence, M1): [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/). The same page says a replication factor below 3 "effectively voids EOS" (medium confidence, M12).
- A distinct `state.dir` for each instance on one host; the default is `${java.io.tmpdir}/kafka-streams` (medium confidence, M2): [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/).
- `ProcessorSupplier.get()` returns a new `Processor` each time, never a singleton (medium confidence, M3): [Processor API](https://kafka.apache.org/44/streams/developer-guide/processor-api/).
- Co-partition join inputs: same partition count and same partitioning on all writers (medium confidence, M4); not needed for foreign-key KTable-KTable or GlobalKTable joins: [DSL](https://kafka.apache.org/44/streams/developer-guide/dsl-api/).
- Create input and output topics ahead of time, not through broker auto-creation (medium confidence, M5): [manage topics](https://kafka.apache.org/44/streams/developer-guide/manage-topics/).
- Pass the same `Properties` to `StreamsBuilder.build(props)` when `topology.optimization` is set, otherwise optimizations are not applied (medium confidence, M6): [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/).
- Store type: persistent RocksDB is the recommended default; in-memory is limited by heap; versioned stores (3.5+) support timestamped lookups but not caching or interactive queries, and there is no in-memory versioned store; suppression is not allowed on versioned tables (medium confidence, M8): [Processor API](https://kafka.apache.org/44/streams/developer-guide/processor-api/), [DSL](https://kafka.apache.org/44/streams/developer-guide/dsl-api/).
- RocksDB memory: share one `Cache` and one `WriteBufferManager` in a `RocksDBConfigSetter` set with `rocksdb.config.setter`, do not close the shared objects in `close()`, jemalloc through `LD_PRELOAD` is recommended (medium confidence, M9): [memory management](https://kafka.apache.org/44/streams/developer-guide/memory-mgmt/).
- Do not close state stores in `Processor#close()`; the library manages them (medium confidence, M10): [Processor API](https://kafka.apache.org/44/streams/developer-guide/processor-api/).
- `withLoggingDisabled()` makes a store not fault tolerant and without standby replicas (medium confidence, M11): [Processor API](https://kafka.apache.org/44/streams/developer-guide/processor-api/).
