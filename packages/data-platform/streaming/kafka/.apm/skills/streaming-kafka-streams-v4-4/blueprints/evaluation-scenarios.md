# Evaluation scenarios, streaming-kafka-streams-v4-4

Back to [SKILL.md](../SKILL.md). Ten scenarios: canonical, edge, rejection (five misuse cases), trap. Each `query` is a user request; `expected_behavior` is what a correct answer does.

## Scenario 1: canonical, exactly-once counting app

```json
{
  "skills": ["streaming-kafka-streams-v4-4"],
  "query": "Write a Kafka Streams 4.4 app that counts orders per customer with exactly-once and exposes the count through an interactive query.",
  "expected_behavior": [
    "Sets processing.guarantee to StreamsConfig.EXACTLY_ONCE_V2",
    "Names the store with Materialized.as and sets ensure.explicit.internal.resource.naming=true",
    "Sets a StreamsUncaughtExceptionHandler before start() and closes KafkaStreams from a shutdown hook",
    "Closes any KeyValueIterator with try-with-resources and sets a unique application.server per instance for remote queries",
    "Asks whether anything writes outside Kafka in the processing path, because external side effects are not documented as covered (unverified)"
  ]
}
```

## Scenario 2: canonical, add an operator to a running topology

```json
{
  "skills": ["streaming-kafka-streams-v4-4"],
  "query": "We are adding a filter before our groupByKey().count() and will do a rolling deploy. Anything to watch?",
  "expected_behavior": [
    "Explains that generated names come from a global counter, so the store and changelog are renamed and the new changelog is empty",
    "Recommends Materialized.as names and ensure.explicit.internal.resource.naming=true",
    "Does not claim a rolling redeploy is safe with generated names",
    "Mentions that the reset tool is needed after a rename"
  ]
}
```

## Scenario 3: edge, deserialization handler default

```json
{
  "skills": ["streaming-kafka-streams-v4-4"],
  "query": "What is the default deserialization.exception.handler in Kafka Streams 4.4, LogAndContinue or LogAndFail?",
  "expected_behavior": [
    "Reports that the 4.4 config page table and StreamsConfig.java 4.4 disagree (U1) and does not pick a side as fact",
    "Says the code default is LogAndFail (medium confidence) and tells the user to set the handler explicitly",
    "Uses deserialization.exception.handler, not the deprecated default.deserialization.exception.handler"
  ]
}
```

## Scenario 4: edge, classic to streams protocol migration

```json
{
  "skills": ["streaming-kafka-streams-v4-4"],
  "query": "Switch our running app to group.protocol=streams one instance at a time.",
  "expected_behavior": [
    "Refuses the rolling approach: online migration between classic and streams is not supported in 4.4",
    "Gives the offline steps: stop all instances, wait for the session timeout, set group.protocol=streams, start all instances",
    "Asks whether brokers are 4.2+ and whether the app needs warmup tasks or regex subscriptions",
    "Warns not to migrate on 4.2.0 (KAFKA-20254, fixed in 4.2.1)"
  ]
}
```

## Scenario 5: rejection, broker operations

```json
{
  "skills": ["streaming-kafka-streams-v4-4"],
  "query": "Set up a 3-controller KRaft quorum and tune min.insync.replicas on the brokers for my Streams app.",
  "expected_behavior": [
    "Declines broker and controller operations: this skill covers the Streams client library only",
    "Points to the skill operating-kafka-v4-4",
    "May still state the Streams-side setting (internal topic replication.factor) as medium confidence"
  ]
}
```

## Scenario 6: rejection, Kafka Connect

```json
{
  "skills": ["streaming-kafka-streams-v4-4"],
  "query": "Configure a Kafka Connect sink connector that writes my Streams output topic to a database.",
  "expected_behavior": [
    "Declines: Kafka Connect is out of scope",
    "Points to the skill integrating-kafka-connect-v4-4",
    "Offers only the Streams side, such as the output topic name and serdes"
  ]
}
```

## Scenario 7: rejection, removed pre-4.0 API

```json
{
  "skills": ["streaming-kafka-streams-v4-4"],
  "query": "Use streams.setUncaughtExceptionHandler((Thread t, Throwable e) -> log(e)) and stream.transformValues(...) in our 4.4 app.",
  "expected_behavior": [
    "Refuses transformValues (removed in 4.0) and prefers the StreamsUncaughtExceptionHandler variant over the Thread-based one",
    "Shows streams.setUncaughtExceptionHandler(e -> StreamThreadExceptionResponse.SHUTDOWN_CLIENT) and processValues with a FixedKeyProcessor",
    "Warns to compare Topology.describe() when merge-repartition-topics optimization is on (KAFKA-19668)",
    "Notes that the 4.4 write-streams-app page still shows the Thread-based lambda, the upgrade guide is read as removing it, and whether it compiles is inferred (unverified, U2)"
  ]
}
```

## Scenario 8: rejection, Kubernetes deployment

```json
{
  "skills": ["streaming-kafka-streams-v4-4"],
  "query": "Write the Kubernetes Deployment, probes and pod grace period for my Kafka Streams 4.4 app.",
  "expected_behavior": [
    "Declines Kubernetes manifests: this skill covers the Streams client library only",
    "Points to operating-kafka-strimzi-v1-3 or operating-kafka-confluent-kubernetes-v3-4",
    "May still state the Streams side: close KafkaStreams from a shutdown hook with a timeout below the platform's shutdown grace period"
  ]
}
```

## Scenario 9: rejection, schema registry

```json
{
  "skills": ["streaming-kafka-streams-v4-4"],
  "query": "Set up a schema registry and register Avro schemas for my Streams topics.",
  "expected_behavior": [
    "Declines schema registry setup: out of scope for this skill",
    "Points to managing-event-schemas-apicurio-v3-3 or managing-event-schemas-confluent-v8-4",
    "May still state the Streams side: serdes are set through default.key.serde and default.value.serde or per operator"
  ]
}
```

## Scenario 10: anti-pattern trap, exactly_once_beta

```json
{
  "skills": ["streaming-kafka-streams-v4-4"],
  "query": "Our old config has processing.guarantee=exactly_once_beta. Keep it and just bump to 4.4.",
  "expected_behavior": [
    "Refuses to keep it: exactly_once and exactly_once_beta were removed in 4.0 and 4.4 accepts only at_least_once and exactly_once_v2",
    "Changes it to exactly_once_v2 and notes the broker needs to be 2.5 or later",
    "Does not invent alert thresholds for the migration (unverified)"
  ]
}
```
