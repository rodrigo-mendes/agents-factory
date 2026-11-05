# Topology, naming and state, Kafka Streams 4.4.0

Back to [SKILL.md](../SKILL.md). Code is representative and was not compiled during research (unverified, U17). All pages read 2026-11-04.

## Model

An application defines a processor topology (source, processor and sink nodes) with the DSL or the Processor API ([core concepts](https://kafka.apache.org/44/streams/core-concepts/)). The topology runs as stream tasks. Each input partition maps to one task, so the number of input partitions caps parallelism ([architecture](https://kafka.apache.org/44/streams/architecture/), [running apps](https://kafka.apache.org/44/streams/developer-guide/running-app/)). The DSL models stream-table duality with `KStream`, `KTable` and `GlobalKTable`. Each stateful operator has a local store backed by a replicated, compacted changelog topic, restored by replaying it ([architecture](https://kafka.apache.org/44/streams/architecture/), [Processor API](https://kafka.apache.org/44/streams/developer-guide/processor-api/)).

## Dependencies

Source: [writing an app](https://kafka.apache.org/44/streams/developer-guide/write-streams-app/), [testing](https://kafka.apache.org/44/streams/developer-guide/testing/).

```xml
<dependency><groupId>org.apache.kafka</groupId><artifactId>kafka-streams</artifactId><version>4.4.0</version></dependency>
<dependency><groupId>org.apache.kafka</groupId><artifactId>kafka-clients</artifactId><version>4.4.0</version></dependency>
<dependency><groupId>org.apache.kafka</groupId><artifactId>kafka-streams-test-utils</artifactId><version>4.4.0</version><scope>test</scope></dependency>
```

## Reference application

Representative. Default serdes are null, so set them ([datatypes](https://kafka.apache.org/44/streams/developer-guide/datatypes/)). Passing `props` to `build(props)` matters when `topology.optimization` is set (medium confidence, M6).

```java
Properties props = new Properties();
props.put(StreamsConfig.APPLICATION_ID_CONFIG, "orders-agg");
props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "broker1:9093");
props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.StringSerde.class);
props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.StringSerde.class);
props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2);
props.put(StreamsConfig.ENSURE_EXPLICIT_INTERNAL_RESOURCE_NAMING_CONFIG, true);
props.put(StreamsConfig.DESERIALIZATION_EXCEPTION_HANDLER_CLASS_CONFIG, LogAndContinueExceptionHandler.class); // a choice, see ask-first
props.put(StreamsConfig.ERRORS_DEAD_LETTER_QUEUE_TOPIC_NAME_CONFIG, "orders-agg-dlq");                         // 4.2+

StreamsBuilder builder = new StreamsBuilder();
builder.stream("orders", Consumed.with(Serdes.String(), Serdes.String()))
       .groupByKey()
       .count(Materialized.as("order-count-store"))
       .toStream()
       .to("order-counts", Produced.with(Serdes.String(), Serdes.Long()));
Topology topology = builder.build(props);

KafkaStreams streams = new KafkaStreams(topology, props);
streams.setUncaughtExceptionHandler(e ->
    StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.REPLACE_THREAD); // before start()
Runtime.getRuntime().addShutdownHook(new Thread(() -> streams.close(Duration.ofSeconds(20))));
streams.start();
```

## Processor API with a store

Source: [Processor API](https://kafka.apache.org/44/streams/developer-guide/processor-api/). The page names `Stores` and `persistentKeyValueStore`; the exact `Stores.keyValueStoreBuilder` method is (unverified), see U15.

```java
StoreBuilder<KeyValueStore<String, Long>> countsStore =
    Stores.keyValueStoreBuilder(Stores.persistentKeyValueStore("Counts"), Serdes.String(), Serdes.Long());
Topology t = new Topology();
t.addSource("Source", "input");
t.addProcessor("Process", () -> new WordCountProcessor(), "Source"); // new instance per get() (medium confidence, M3)
t.addStateStore(countsStore, "Process");
t.addSink("Sink", "output", "Process");
// In WordCountProcessor.init(): context.getStateStore("Counts") with the same name as the builder
// Punctuation: context.schedule(Duration.ofSeconds(10), PunctuationType.STREAM_TIME, ts -> {...})
```

Processors that share a `StoreBuilder` are grouped into one subtopology in 4.4 (KAFKA-20464): task IDs change and state is restored from the changelog on first startup ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/)).

## Interactive queries

Sources: [interactive queries](https://kafka.apache.org/44/streams/developer-guide/interactive-queries/), [KafkaStreams javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/KafkaStreams.html). A table or store must be named to be queryable ([DSL](https://kafka.apache.org/44/streams/developer-guide/dsl-api/)).

```java
ReadOnlyKeyValueStore<String, Long> store = streams.store(
    StoreQueryParameters.fromNameAndType("order-count-store", QueryableStoreTypes.keyValueStore()));
Long n = store.get("customer-42");  // InvalidStateStoreException if the store is not queryable
```

Remote queries need a distinct `application.server` per instance and your own RPC layer; discovery goes through the metadata APIs.

## Internal topics

Source: [manage topics](https://kafka.apache.org/44/streams/developer-guide/manage-topics/). Repartition topics use `delete` cleanup with infinite retention; key-value changelogs use `compact`; windowed changelogs use `delete,compact` with 24 h plus window retention; all use `CreateTime`. The naming pattern `<application.id>-<operatorName>-<suffix>` "is not guaranteed for future releases". This page may end abruptly (medium confidence, U13). Security and ACLs: [security and internal topics](./security-and-internal-topics.md).
