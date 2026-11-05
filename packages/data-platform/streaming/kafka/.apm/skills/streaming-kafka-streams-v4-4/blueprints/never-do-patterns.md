# Never-do patterns, Kafka Streams 4.4.0

Back to [SKILL.md](../SKILL.md). Every row has an alternative; each alternative is High confidence except where a tag says otherwise (the reset-tool flags, U9). All sources read 2026-11-04. Code is representative.

## processing.guarantee exactly_once or exactly_once_beta (risk: high)

Why: EOS v1 was removed in 4.0 and the 4.4 validator accepts only `at_least_once` and `exactly_once_v2` ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/), [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/)). Config validation therefore rejects the value; the exact error message was not observed (unverified, U16).

```java
// 🚫 WRONG
props.put("processing.guarantee", "exactly_once");
props.put("processing.guarantee", "exactly_once_beta");
// ✅ CORRECT
props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2);
```

Detection: `grep -rnE "exactly_once(_beta)?\b" src/ --include=*.java --include=*.properties`.

## Unclosed store iterator (risk: high)

Why: memory grows until OOM ([Processor API](https://kafka.apache.org/44/streams/developer-guide/processor-api/), [memory management](https://kafka.apache.org/44/streams/developer-guide/memory-mgmt/), [interactive queries](https://kafka.apache.org/44/streams/developer-guide/interactive-queries/)).

```java
// 🚫 WRONG
KeyValueIterator<String, Long> it = store.all();
while (it.hasNext()) { process(it.next()); }
// ✅ CORRECT
try (KeyValueIterator<String, Long> it = store.all()) {
    while (it.hasNext()) { process(it.next()); }
}
```

## Generated names plus rolling redeploy of a changed topology (risk: high)

Why: the store and its changelog are renamed, the new changelog is empty, and aggregates restart from nothing; the reset tool is then needed ([naming guide](https://kafka.apache.org/44/streams/developer-guide/dsl-topology-naming/), [DSL](https://kafka.apache.org/44/streams/developer-guide/dsl-api/), [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/)).

```java
// 🚫 WRONG: store name like ...-STATE-STORE-0000000002
stream.groupByKey().count();
// ✅ CORRECT
stream.groupByKey().count(Materialized.as("Purchase_count_store"));
// plus: props.put(StreamsConfig.ENSURE_EXPLICIT_INTERNAL_RESOURCE_NAMING_CONFIG, true);
```

Detection: `grep -nE "\.count\(\)|\.aggregate\([^,]*\)\s*;|\.reduce\([^,]*\)\s*;" src/main/java -r` finds unnamed stateful calls (heuristic).

## APIs removed in 4.0 (risk: high)

Why: `KStream#through`, `transform`, `transformValues`, `flatTransform`, `flatTransformValues`, the old `process`, and `KStream#branch` were removed in 4.0 ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/), [DSL](https://kafka.apache.org/44/streams/developer-guide/dsl-api/)). The `setUncaughtExceptionHandler(Thread.UncaughtExceptionHandler)` variant is handled separately below (unverified, U2).

```java
// 🚫 WRONG
stream.transformValues(MyTransformer::new);
// (unverified, U2) the Thread-based variant, shown on the write-streams-app page:
streams.setUncaughtExceptionHandler((Thread t, Throwable e) -> log(e));
// ✅ CORRECT
stream.processValues(MyFixedKeyProcessor::new);  // FixedKeyProcessor / ContextualFixedKeyProcessor
streams.setUncaughtExceptionHandler(e ->
    StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.SHUTDOWN_CLIENT);
```

Migration caution (KAFKA-19668): moving from `transformValues()` to `processValues()` with the merge-repartition-topics optimization may be unsafe. Compare `Topology.describe()` before and after ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/), [DSL](https://kafka.apache.org/44/streams/developer-guide/dsl-api/)).

Docs conflict, kept open (U2): the [writing an app](https://kafka.apache.org/44/streams/developer-guide/write-streams-app/) page still shows a `Thread.UncaughtExceptionHandler` lambda, while the [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/) is read as saying the variant was removed in 4.0 and the [KafkaStreams javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/KafkaStreams.html) lists only the `StreamsUncaughtExceptionHandler` variant. Whether it compiles on 4.4 is inferred (unverified, U2). A human must verify which page is current; use the javadoc API meanwhile.

## `cleanUp()` while the instance runs (risk: moderate)

Why: `cleanUp()` may be called only before `start()` or after `close()`, and it deletes all local state for the application ID; state is restored on the next start ([KafkaStreams javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/KafkaStreams.html), [reset tool](https://kafka.apache.org/44/streams/developer-guide/app-reset-tool/)).

```java
// 🚫 WRONG
streams.start();
streams.cleanUp();
// ✅ CORRECT
streams.cleanUp();   // only before start() or after close(), for example after an application reset
streams.start();
```

## Application reset script on a streams group (risk: moderate)

Why: for `group.protocol=streams` the reset tool page points to the Streams groups CLI, and the rebalance protocol page says that tool replaces the reset script ([reset tool](https://kafka.apache.org/44/streams/developer-guide/app-reset-tool/), [rebalance protocol](https://kafka.apache.org/44/streams/developer-guide/streams-rebalance-protocol/), [groups tool](https://kafka.apache.org/44/streams/developer-guide/kafka-streams-group-sh/)).

```bash
# 🚫 WRONG (streams group)
bin/kafka-streams-application-reset.sh --application-id my-app --input-topics in
# ✅ CORRECT. Representative, instances stopped and group empty
bin/kafka-streams-groups.sh --bootstrap-server localhost:9092 --reset-offsets --group my-app --all-input-topics --to-earliest --dry-run
# Expected: planned offset changes, nothing applied (--dry-run flag combination is (unverified), U9)
```

## Online migration between `classic` and `streams` (risk: high)

Why: not supported in 4.4 ([rebalance protocol](https://kafka.apache.org/44/streams/developer-guide/streams-rebalance-protocol/), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/)). Do not switch `group.protocol` on one instance at a time.

Alternative: stop all instances, wait for the session timeout (or force a leave), set `group.protocol=streams`, start all instances. Only committed offsets carry over. Also do not migrate classic to streams on 4.2.0 (KAFKA-20254, fixed in 4.2.1), see [scaling and rebalancing](./scaling-and-rebalancing.md).

## Candidates kept out of this list

Closing state stores in `Processor#close()`, `withLoggingDisabled()` while expecting fault tolerance, and replication factor below 3 with EOS each rest on one source. They are in [ask-first-decisions](./ask-first-decisions.md) (medium confidence).
