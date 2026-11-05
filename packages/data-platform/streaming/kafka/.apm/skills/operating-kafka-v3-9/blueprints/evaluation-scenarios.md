# Evaluation scenarios, operating-kafka-v3-9

Back to [SKILL.md](../SKILL.md). Ten scenarios: canonical, edge, rejection (five misuse cases), trap. Each `query` is a user request; `expected_behavior` is what a correct answer does.

## Scenario 1: canonical, create a durable topic

```json
{
  "skills": ["operating-kafka-v3-9"],
  "query": "Create an orders topic on our 3-broker Kafka 3.9.2 ZooKeeper cluster that must not lose acknowledged writes.",
  "expected_behavior": [
    "Uses replication factor 3 and sets min.insync.replicas=2 on the topic",
    "Keeps producer acks=all and enable.idempotence=true",
    "Keeps unclean.leader.election.enable=false",
    "Connects with --bootstrap-server, not --zookeeper, and verifies with kafka-topics.sh --describe"
  ]
}
```

## Scenario 2: canonical, plan the ZooKeeper to KRaft migration

```json
{
  "skills": ["operating-kafka-v3-9"],
  "query": "Plan the ZooKeeper to KRaft migration of our 3.9 Compose cluster.",
  "expected_behavior": [
    "Requires brokers on 3.9.x (recommends 3.9.2) and inter.broker.protocol.version=3.9 first; notes the page text says 3.9.1 (medium confidence, U3)",
    "Lists the 5 steps: cluster ID, migration-enabled controllers, brokers in migration mode, brokers to KRaft, finalize",
    "Shows the rollback table and says finalize is irreversible",
    "States the runbook rests on one official page (medium confidence) and that the 3-controller layout is human-verify (U26)"
  ]
}
```

## Scenario 3: edge, which patch release

```json
{
  "skills": ["operating-kafka-v3-9"],
  "query": "The migration page says 3.9.1. We run 3.9.2. Is that enough?",
  "expected_behavior": [
    "Says 3.9.2 is expected to satisfy it and includes fixes KAFKA-19480 and KAFKA-19988, but that this is an inference (medium confidence, U3)",
    "Does not claim the page names 3.9.2",
    "Suggests confirming with the Apache community or a test cluster"
  ]
}
```

## Scenario 4: edge, static to dynamic quorum

```json
{
  "skills": ["operating-kafka-v3-9"],
  "query": "We have a static controller.quorum.voters quorum on 3.9. Convert it to dynamic.",
  "expected_behavior": [
    "States that converting static to dynamic is not yet supported in 3.9 and the choice is made at format time",
    "Notes the image formats only with --cluster-id and -c, so dynamic formatting through the image is (unverified, U5)",
    "Asks whether controllers will change without a rebuild"
  ]
}
```

## Scenario 5: rejection, 4.x or KRaft-only request

```json
{
  "skills": ["operating-kafka-v3-9"],
  "query": "Operate our Kafka 4.4 KRaft-only cluster: give me the 4.4 upgrade and KRaft tuning steps.",
  "expected_behavior": [
    "Declines to give 4.x content: this skill covers 3.9.2 only",
    "Points to skill operating-kafka-v4-4",
    "Mentions only that 4.x has no ZooKeeper and that a ZooKeeper cluster must migrate on 3.9 first"
  ]
}
```

## Scenario 6: rejection, Kubernetes request

```json
{
  "skills": ["operating-kafka-v3-9"],
  "query": "Write the Kubernetes manifests to run Kafka 3.9 with ZooKeeper under an operator.",
  "expected_behavior": [
    "Declines: this skill covers Docker Compose only",
    "Points to operating-kafka-strimzi-v1-3 or operating-kafka-confluent-kubernetes-v3-4",
    "Does not produce operator, StatefulSet or CRD manifests"
  ]
}
```

## Scenario 7: rejection, stock image without the command override

```json
{
  "skills": ["operating-kafka-v3-9"],
  "query": "Start a ZooKeeper-mode broker from apache/kafka:3.9.2 with just zookeeper.connect in KAFKA_ environment variables.",
  "expected_behavior": [
    "Explains that the image runs the storage format step at startup and the 3.9 formatter rejects configs without process.roles, so the default CMD fails (medium confidence, U1, inferred from source and not run)",
    "Offers the command override that calls kafka-server-start.sh with a mounted server.properties, and says the whole layout is (unverified, U28)",
    "Notes that with the override the KAFKA_ environment mapping does not run, so settings go in the properties file"
  ]
}
```

## Scenario 8: rejection, stay on 3.9 indefinitely

```json
{
  "skills": ["operating-kafka-v3-9"],
  "query": "We want to stay on Kafka 3.9 with ZooKeeper for the next two years. Is that supported?",
  "expected_behavior": [
    "Warns that 3.9 is the last ZooKeeper line and is listed as archived while only 4.4.0, 4.3.2 and 4.2.2 are supported (medium confidence)",
    "States the 3.9 ZooKeeper page promises critical and security fixes for 12 months after release, and that the start date is not stated (unverified, U4, human-verify)",
    "Says there is no official end-of-life table (U15) and does not invent a date",
    "Recommends migrating to KRaft on 3.9.2, then following operating-kafka-v4-4"
  ]
}
```

## Scenario 9: rejection, copy the official example settings into a persistent cluster

```json
{
  "skills": ["operating-kafka-v3-9"],
  "query": "Copy the settings of the official 3.9 isolated Compose example into our persistent staging cluster, it is the quickest.",
  "expected_behavior": [
    "Refuses: the example sets the offsets and transaction-state replication factor and min ISR to 1, uses KAFKA_LOG_DIRS under /tmp with no volume and a fixed CLUSTER_ID",
    "Explains that the README says the single-replica offsets setting suits only a single node and that the broker config defaults are 3, 3 and 2",
    "Offers RF 3, transaction-state min ISR 2, a named volume for the log dirs and a cluster ID generated with kafka-storage.sh random-uuid"
  ]
}
```

## Scenario 10: anti-pattern trap, finalize immediately

```json
{
  "skills": ["operating-kafka-v3-9"],
  "query": "Move the brokers to KRaft and finalize the migration in the same change window to save time.",
  "expected_behavior": [
    "Advises against it: finalize cannot be reverted and validation in dual-write should come first (single-page guidance, medium confidence)",
    "Shows the rollback table and which steps remain reversible",
    "Asks who signs off finalize and which checks prove dual-write is healthy"
  ]
}
```
