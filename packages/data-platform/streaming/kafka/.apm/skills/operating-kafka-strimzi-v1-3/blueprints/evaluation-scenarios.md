# Evaluation scenarios, operating-kafka-strimzi-v1-3

Back to [SKILL.md](../SKILL.md). Eight scenarios: canonical (2), edge (1), rejection (4 misuse cases), trap (1). Each `query` is a user request; `expected_behavior` is what a correct answer does.

## Scenario 1: canonical, new production cluster

```json
{
  "skills": ["operating-kafka-strimzi-v1-3"],
  "query": "Give me a production Kafka cluster on Strimzi 1.3.1 with dedicated controllers and brokers.",
  "expected_behavior": [
    "Uses apiVersion kafka.strimzi.io/v1 for Kafka and KafkaNodePool, with a controller pool and a broker pool labelled strimzi.io/cluster",
    "Uses a Kafka version from the 1.3.1 list (4.3.2), not 4.4.0",
    "Sets replication factor 3 and min.insync.replicas 2, and authenticates every client listener",
    "Tags any assembled hardened overlay as (unverified) and suggests kubectl apply --dry-run=server"
  ]
}
```

## Scenario 2: canonical, shrink the broker pool

```json
{
  "skills": ["operating-kafka-strimzi-v1-3"],
  "query": "Scale the broker node pool from 4 to 3 replicas.",
  "expected_behavior": [
    "Creates a KafkaRebalance with mode remove-brokers and the broker id, waits for ProposalReady, approves, waits for Ready",
    "Lowers KafkaNodePool.spec.replicas only after the node holds no partition replicas",
    "Does not use strimzi.io/skip-broker-scaledown-check",
    "Asks whether a human must review data movement (manual approval vs auto-approval)"
  ]
}
```

## Scenario 3: edge, upgrade on 2026-11-04 (the day 1.3.1 was tagged)

```json
{
  "skills": ["operating-kafka-strimzi-v1-3"],
  "query": "Upgrade our operator to 1.3.1 with Helm and show the 1.3.1 docs page for the procedure.",
  "expected_behavior": [
    "States that 1.3.1 has no versioned docs yet and that the procedure comes from the 1.3.0 docs plus the 1.3.1 release notes (the 1.3.1 docs URL returned 404 on 2026-11-04)",
    "Says the CRDs must be applied separately because helm upgrade does not update them, and marks the CRD order, the CRD file name and a 1.3.1 chart as (unverified)",
    "Gives the order: Kubernetes, operator, spec.kafka.version, metadataVersion last",
    "Does not claim a support or end-of-life date (no per-release support policy was found)"
  ]
}
```

## Scenario 4: rejection, ZooKeeper mode

```json
{
  "skills": ["operating-kafka-strimzi-v1-3"],
  "query": "Deploy Kafka with Strimzi 1.3.x in ZooKeeper mode with 3 ZooKeeper nodes.",
  "expected_behavior": [
    "Refuses: Strimzi 1.3.x does not support ZooKeeper-based clusters; it is KRaft only (ZooKeeper support was removed in Strimzi 0.46) (medium confidence, M22)",
    "Offers KRaft controller and broker node pools instead",
    "Points to operating-kafka-v3-9 for ZooKeeper broker facts, and to migration on Strimzi 0.45.x for existing ZooKeeper clusters (medium confidence, M22)"
  ]
}
```

## Scenario 5: rejection, Kafka 4.4.0 on Strimzi 1.3.x

```json
{
  "skills": ["operating-kafka-strimzi-v1-3"],
  "query": "Run Kafka 4.4.0 on our Strimzi 1.3.1 operator by setting spec.kafka.version: 4.4.0.",
  "expected_behavior": [
    "States 4.4.0 is not in the supported list of Strimzi 1.3.x (4.2.0 to 4.3.2 on 1.3.1) and refuses to set it (https://strimzi.io/downloads/, read 2026-11-04)",
    "Suggests 4.3.2 on 1.3.1",
    "Says Kafka 4.4.0 is not supported by this Strimzi line; for 4.4 broker facts on Compose see operating-kafka-v4-4; for Confluent Platform on Kubernetes see operating-kafka-confluent-kubernetes-v3-4"
  ]
}
```

## Scenario 6: rejection, Confluent for Kubernetes

```json
{
  "skills": ["operating-kafka-strimzi-v1-3"],
  "query": "Set up Confluent for Kubernetes with Control Center using this skill.",
  "expected_behavior": [
    "Says Confluent for Kubernetes is out of scope for this skill",
    "Points to operating-kafka-confluent-kubernetes-v3-4",
    "Does not mix Strimzi custom resources with Confluent ones"
  ]
}
```

## Scenario 7: rejection, copy old manifests

```json
{
  "skills": ["operating-kafka-strimzi-v1-3"],
  "query": "Copy the v1beta2 manifests and the operator 0.40.0 pins from the old operator guide into our repo.",
  "expected_behavior": [
    "Refuses: the CRD API is v1 only since 1.0.0 and v1beta2 was removed",
    "Refuses the 0.40.0 pin and the Kafka 3.7.0 version as unsupported on 1.3.x",
    "Offers kafka.strimzi.io/v1 manifests based on the 1.3.0 official example and a supported Kafka version"
  ]
}
```

## Scenario 8: anti-pattern trap, restart and OAuth secret

```json
{
  "skills": ["operating-kafka-strimzi-v1-3"],
  "query": "Just kubectl delete pod the broker to restart it, and paste the OAuth client secret straight into listenerConfig.",
  "expected_behavior": [
    "Rejects deleting the pod and uses the strimzi.io/manual-rolling-update=\"true\" annotation on the Pod",
    "Rejects the clear-text secret and uses a Kubernetes Secret read through a configuration provider",
    "Notes the placeholder syntax is (unverified) and that custom authentication replaces the deprecated oauth type"
  ]
}
```
