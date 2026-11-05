# Always-do patterns, Kafka Streams 4.4.0

Back to [SKILL.md](../SKILL.md). All code is representative (adapt names), and it was not compiled during research (unverified, U17). Caveats and options live in [ask-first-decisions](./ask-first-decisions.md). All pages read 2026-11-04.

## Exactly-once with `exactly_once_v2`

Sources: [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/) (EOS v1 removed in 4.0). The 4.4 validator accepts `at_least_once` and `exactly_once_v2` only.

```java
props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2);
```

## New handler keys instead of `default.*`

Sources: [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/) (deprecated since 4.0), [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/). Supporting reference, branch head, not a counted page: [StreamsConfig.java 4.4](https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/StreamsConfig.java) (the new key wins when both are set). The effective default of the deserialization handler is a docs conflict, see U1; always set it explicitly.

```java
props.put(StreamsConfig.DESERIALIZATION_EXCEPTION_HANDLER_CLASS_CONFIG,
          LogAndFailExceptionHandler.class);
```

## Explicit operator names

Source: [naming guide](https://kafka.apache.org/44/streams/developer-guide/dsl-topology-naming/). Names come from a global counter, so adding a processor renames the store and its changelog. The guide says a rolling redeploy of the updated topology is then impossible.

```java
stream.filter((k, v) -> v != null && v.length() >= 6)
      .groupByKey()
      .count(Materialized.as("Purchase_count_store"))
      .toStream()
      .to("output");
```

The page names these classes for naming: `Named`, `Consumed`, `Produced`, `Materialized`, `Grouped`, `Joined`, `StreamJoined`. The exact factory methods beyond `Named.as`, `Consumed.as`, `Produced.as` and `Materialized.as` are (unverified), see U15.

## Enforce explicit names

Sources: [naming guide](https://kafka.apache.org/44/streams/developer-guide/dsl-topology-naming/), [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/) (default false, importance high).

```java
props.put(StreamsConfig.ENSURE_EXPLICIT_INTERNAL_RESOURCE_NAMING_CONFIG, true);
```

## Close store iterators

Sources: [Processor API](https://kafka.apache.org/44/streams/developer-guide/processor-api/), [memory management](https://kafka.apache.org/44/streams/developer-guide/memory-mgmt/), [interactive queries](https://kafka.apache.org/44/streams/developer-guide/interactive-queries/) (close the iterator even if `next()` throws).

```java
try (KeyValueIterator<String, Long> it = store.range("a", "f")) {
    while (it.hasNext()) { KeyValue<String, Long> kv = it.next(); /* ... */ }
}
```

## Close `KafkaStreams` from a shutdown hook

Sources: [writing an app](https://kafka.apache.org/44/streams/developer-guide/write-streams-app/), [memory management](https://kafka.apache.org/44/streams/developer-guide/memory-mgmt/), [KafkaStreams javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/KafkaStreams.html) (`close()` blocks until all threads stop). Since 4.3 RocksDB stores keep the changelog offset in the store with the WAL disabled, so an unclean exit can force a full task restore.

```java
Runtime.getRuntime().addShutdownHook(new Thread(() -> streams.close(Duration.ofSeconds(20))));
```

The 20-second value is an example (unverified, U14). Keep the timeout below the shutdown grace period of the platform that runs the app (memory-management page). Grace-period settings are platform content: for Kubernetes use `operating-kafka-strimzi-v1-3` or `operating-kafka-confluent-kubernetes-v3-4`.

## Uncaught exception handler before `start()`

Sources: [KafkaStreams javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/KafkaStreams.html) (must be set before start, must be thread safe), [response values javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/errors/StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.html): `REPLACE_THREAD`, `SHUTDOWN_CLIENT`, `SHUTDOWN_APPLICATION`.

```java
streams.setUncaughtExceptionHandler(ex ->
    StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.REPLACE_THREAD);
streams.start();
```

The response to return is a design choice, see [exactly-once and errors](./exactly-once-and-errors.md).

## Standbys for fast failover

Sources: [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/) (provision n+1 instances for n standbys), [architecture](https://kafka.apache.org/44/streams/architecture/), [running apps](https://kafka.apache.org/44/streams/developer-guide/running-app/).

```java
// 1 or more; the value is a capacity choice (n standbys need n+1 instances)
props.put(StreamsConfig.NUM_STANDBY_REPLICAS_CONFIG, 1);
```

The `group.protocol=streams` caveat is an Ask First item (rebalance protocol); see [ask-first-decisions](./ask-first-decisions.md#rebalance-protocol-classic-or-streams).

## Unique `application.server` per instance

Sources: [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/) (must differ for each instance), [interactive queries](https://kafka.apache.org/44/streams/developer-guide/interactive-queries/), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/) (validated at `StreamsConfig` creation in 4.4; an invalid value throws `ConfigException`).

```java
props.put(StreamsConfig.APPLICATION_SERVER_CONFIG, "host1:8080"); // one distinct host:port per instance
```

Kafka Streams provides no RPC layer for remote queries; add one, for example a REST API.
