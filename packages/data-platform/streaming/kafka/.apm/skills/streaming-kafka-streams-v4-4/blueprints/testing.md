# Testing, Kafka Streams 4.4.0

Back to [SKILL.md](../SKILL.md). Source for everything here: [testing page](https://kafka.apache.org/44/streams/developer-guide/testing/) (read 2026-11-04) unless stated. Code is representative and was not compiled during research (unverified, U17).

## Setup

`kafka-streams-test-utils` must have the same version as `kafka-streams`: 4.4.0, test scope. `TopologyTestDriver` runs a topology without a broker.

```bash
mvn -q test
# Expected: topology tests pass with no broker running
```

## TopologyTestDriver

Close the driver after each test (medium confidence, M7). The page shows an explicit `close()`; using try-with-resources assumes `AutoCloseable` (unverified, U10), so the example uses try/finally.

```java
TopologyTestDriver driver = new TopologyTestDriver(topology, props);
try {
    TestInputTopic<String, String> in =
        driver.createInputTopic("orders", new StringSerializer(), new StringSerializer());
    TestOutputTopic<String, Long> out =
        driver.createOutputTopic("order-counts", new StringDeserializer(), new LongDeserializer());
    in.pipeInput("customer-42", "o1");
    in.pipeInput("customer-42", "o2");
    assertEquals(new KeyValue<>("customer-42", 1L), out.readKeyValue());
    assertEquals(new KeyValue<>("customer-42", 2L), out.readKeyValue());
    assertTrue(out.isEmpty());
    KeyValueStore<String, Long> store = driver.getKeyValueStore("order-count-store");
    assertEquals(2L, store.get("customer-42"));
    driver.advanceWallClockTime(Duration.ofSeconds(20));  // fires WALL_CLOCK_TIME punctuators
} finally {
    driver.close();
}
```

- Event-time punctuators fire from record timestamps. Wall-clock punctuators fire only through `advanceWallClockTime`.
- One output per input assumes caching does not hold records back in the driver (unverified, U10); the page does not discuss caching.
- Store lookups by name work because the operator is named (see [topology and state](./topology-and-state.md)).

## Unit-testing one Processor

`MockProcessorContext` from test-utils captures forwards, commits and scheduled punctuators, but does not run punctuators by itself. Register in-memory stores with logging disabled. The 4.0 upgrade notes (KIP-1070) deprecated a `MockProcessorContext` (the old-API class) while the testing page shows a generic `MockProcessorContext<String, Long>` and does not mark it deprecated ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/)). Which package is current is (unverified, U4).

## Coverage

Only the testing page above was used. Integration tests against real brokers are outside this skill's sources (see coverage limits in the [register](./unverified-and-risks.md#coverage-limits-l1l4-4-items)).
