# Exactly-once and error handling, Kafka Streams 4.4.0

Back to [SKILL.md](../SKILL.md). Representative code. All pages read 2026-11-04.

## Exactly-once

Sources: [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/), [StreamsConfig.java](https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/StreamsConfig.java), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/).

- Only `at_least_once` (default) and `exactly_once_v2` are accepted in 4.4; EOS v1 values were removed in 4.0.
- EOS v2 needs brokers 2.5 or later.
- Under EOS, `commit.interval.ms` defaults to 100 instead of 30000, consumers use `read_committed`, and producers use idempotence.
- Streams sets `transaction.timeout.ms=10000` under EOS; it must be at least `commit.interval.ms` and at most the broker `transaction.max.timeout.ms`.
- The config page says a replication factor below 3 "effectively voids EOS" (medium confidence, M12). The recommended internal topic `replication.factor=3` with broker `min.insync.replicas=2` is (medium confidence, M1). Broker settings belong to `operating-kafka-v4-4`.
- Exactly-once coverage of side effects outside Kafka is not documented; treat as not covered (unverified, U7).
- ACLs on transactional IDs for EOS are not documented on the Streams security pages (unverified, U5).

## Transactional state stores

See [ask-first-decisions](./ask-first-decisions.md#transactional-state-stores-new-in-44). The tuning defaults are (unverified, U3).

## Uncaught exceptions in stream threads

Sources: [KafkaStreams javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/KafkaStreams.html), [StreamsUncaughtExceptionHandler javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/errors/StreamsUncaughtExceptionHandler.html), [response values](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/errors/StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.html).

| Response | Meaning |
|---|---|
| `REPLACE_THREAD` | Replace the failed stream thread and continue |
| `SHUTDOWN_CLIENT` | Shut down this `KafkaStreams` client |
| `SHUTDOWN_APPLICATION` | Shut down all clients of the application |

The handler must be set before `start()` (otherwise `IllegalStateException`) and must be thread safe.

```java
streams.setUncaughtExceptionHandler(ex ->
    StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.SHUTDOWN_CLIENT);
streams.start();
```

The upgrade guide is read as saying the `Thread.UncaughtExceptionHandler` variant was removed in 4.0, while the write-streams-app page still shows it and the javadoc lists only the `StreamsUncaughtExceptionHandler` variant (unverified, U2, not resolved here).

## Deserialization and production handlers

Sources: [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/), [StreamsConfig.java](https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/StreamsConfig.java).

- Keys: `deserialization.exception.handler`, `production.exception.handler`. The `default.*` keys are deprecated since 4.0; `StreamsConfig` checks the new key first and logs a warning when both are set.
- Docs conflict U1: the config page table lists `LogAndContinueExceptionHandler` as the deserialization default; `StreamsConfig.java` 4.4 defines `LogAndFailExceptionHandler`. This skill does not resolve it: the code default is used (medium confidence). Set the handler explicitly.
- Since 4.0 the production handler is called on `TimeoutException` and can return `RETRY` (KIP-1065).
- Since 4.2 `ProductionExceptionHandlerResponse`, `handle` and `handleSerializationException` are deprecated for `Response`, `handleError` and `handleSerializationError` (KIP-1034).
- Docs conflict (medium confidence, U20): the upgrade guide deprecates `processing.exception.handler.global.enabled` with removal in 5.0, yet the config page recommends enabling it now. Not resolved here; a human must verify.

```java
props.put(StreamsConfig.DESERIALIZATION_EXCEPTION_HANDLER_CLASS_CONFIG, LogAndContinueExceptionHandler.class);
props.put(StreamsConfig.ERRORS_DEAD_LETTER_QUEUE_TOPIC_NAME_CONFIG, "orders-agg-dlq"); // 4.2+
```

Built-in handlers read the DLQ topic and build DLQ records ([LogAndContinueExceptionHandler.java](https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/errors/LogAndContinueExceptionHandler.java), [DefaultProductionExceptionHandler.java](https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/errors/DefaultProductionExceptionHandler.java)). DLQ is not supported for global store or GlobalKTable failures.

## Window lateness

See [ask-first-decisions](./ask-first-decisions.md#window-grace-period). Monitor drops with the task metric `dropped-records-rate` ([observability](./observability.md)).

## Verification

```bash
# Representative. Adapt to your environment
grep -rn "processing.guarantee\|PROCESSING_GUARANTEE" src/
# Expected: only EXACTLY_ONCE_V2 or exactly_once_v2 or at_least_once
```
