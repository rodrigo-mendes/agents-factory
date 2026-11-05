# Evaluation scenarios, integrating-kafka-connect-v4-4

Back to [SKILL.md](../SKILL.md). Eight scenarios: canonical, edge, rejection (three misuse cases), trap. Each `query` is a user request; `expected_behavior` is what a correct answer does.

## Scenario 1: canonical, production-shaped distributed worker

```json
{
  "skills": ["integrating-kafka-connect-v4-4"],
  "query": "Write the worker config for a 4.4 Connect cluster on Compose that feeds a database sink.",
  "expected_behavior": [
    "Uses distributed mode with a unique group.id and the three internal topics, replicated; offers replication factor 3 and a one-partition config topic as Ask First items (medium confidence)",
    "Sets connector.client.config.override.policy=Allowlist and keeps REST on a trusted network with HTTPS",
    "Uses a ${file:...} ConfigProvider placeholder for the database password",
    "Tags the Compose entrypoint as (unverified) and asks a human to verify it"
  ]
}
```

## Scenario 2: canonical, sink with a DLQ

```json
{
  "skills": ["integrating-kafka-connect-v4-4"],
  "query": "Some records in the orders topic are malformed. Keep the sink running and keep the bad ones.",
  "expected_behavior": [
    "Sets errors.tolerance=all with errors.deadletterqueue.topic.name and replication factor 3",
    "Keeps errors.log.include.messages=false",
    "Asks who drains the DLQ and notes the Write ACL on the DLQ topic",
    "Points at task-error-metrics such as deadletterqueue-produce-failures"
  ]
}
```

## Scenario 3: edge, connect.protocol default

```json
{
  "skills": ["integrating-kafka-connect-v4-4"],
  "query": "What is the default of connect.protocol in 4.4?",
  "expected_behavior": [
    "Reports that the configs page and the administration page disagree (U3) and does not pick a side as fact",
    "Recommends leaving the key unset (medium confidence)",
    "Does not invent a default"
  ]
}
```

## Scenario 4: edge, exactly-once on an existing cluster

```json
{
  "skills": ["integrating-kafka-connect-v4-4"],
  "query": "Turn on exactly-once for a source connector in our running 4.4 cluster.",
  "expected_behavior": [
    "Asks whether the connector declares exactly-once support and whether the cluster is new",
    "For an existing cluster describes two rolling restarts: exactly.once.source.support=preparing, then enabled",
    "Mentions the TransactionalId ACLs on a secured cluster and read_committed for downstream readers",
    "Does not offer exactly-once on a standalone worker"
  ]
}
```

## Scenario 5: rejection, Connect on Kubernetes

```json
{
  "skills": ["integrating-kafka-connect-v4-4"],
  "query": "Deploy this Connect cluster on Kubernetes with a KafkaConnect resource.",
  "expected_behavior": [
    "States that Kubernetes operator content is out of scope for this skill",
    "Points to operating-kafka-strimzi-v1-3 or operating-kafka-confluent-kubernetes-v3-4",
    "Does not write operator manifests"
  ]
}
```

## Scenario 6: rejection, Debezium connector config

```json
{
  "skills": ["integrating-kafka-connect-v4-4"],
  "query": "Give me the Debezium PostgreSQL connector config for this worker.",
  "expected_behavior": [
    "States that Debezium connector configuration is out of scope and covered by a later unit",
    "Offers only the generic parts: plugin directory layout, ConfigProvider secrets, DLQ and REST creation call",
    "Does not invent Debezium keys"
  ]
}
```

## Scenario 7: rejection, broker configuration

```json
{
  "skills": ["integrating-kafka-connect-v4-4"],
  "query": "Tune the broker's min.insync.replicas and controller quorum for my Connect topics.",
  "expected_behavior": [
    "States that broker configuration is out of scope",
    "Points to operating-kafka-v4-4",
    "Stays on Connect-side keys such as the internal topic replication factors"
  ]
}
```

## Scenario 8: trap, copy the sample worker file

```json
{
  "skills": ["integrating-kafka-connect-v4-4"],
  "query": "Use the sample connect-distributed.properties as is, expose 8083 on all interfaces and put the DB password in the connector JSON.",
  "expected_behavior": [
    "Refuses replication factor 1 on the internal topics and replicates them (3 is the configs-page default, medium confidence)",
    "Refuses an unauthenticated REST port open to untrusted networks and proposes a trusted network and HTTPS; an authenticating proxy is only an Ask First option",
    "Refuses the inline password and uses a ${file:...} placeholder",
    "Sets the Allowlist override policy instead of the default All"
  ]
}
```
