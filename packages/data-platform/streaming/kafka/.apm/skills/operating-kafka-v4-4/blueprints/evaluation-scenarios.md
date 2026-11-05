# Evaluation scenarios, operating-kafka-v4-4

Back to [SKILL.md](../SKILL.md). Eight scenarios: canonical, edge, rejection (three misuse cases), trap. Each `query` is a user request; `expected_behavior` is what a correct answer does.

## Scenario 1: canonical, create a durable topic

```json
{
  "skills": ["operating-kafka-v4-4"],
  "query": "Create an orders topic on our 3-broker Kafka 4.4 Compose cluster that must not lose acknowledged writes.",
  "expected_behavior": [
    "Uses replication factor 3 and sets min.insync.replicas=2 on the topic",
    "Keeps producer acks=all and enable.idempotence=true",
    "Verifies with kafka-topics.sh --describe and checks ReplicationFactor and min.insync.replicas",
    "Does not enable unclean.leader.election.enable"
  ]
}
```

## Scenario 2: canonical, harden the official isolated example

```json
{
  "skills": ["operating-kafka-v4-4"],
  "query": "Turn the official 4.4 isolated Compose example into a staging cluster.",
  "expected_behavior": [
    "Pins apache/kafka:4.4.0, uses 3 dedicated controllers and N brokers",
    "Raises replication factors to 3 and min ISR to 2, mounts named volumes instead of /tmp",
    "Binds host ports to 127.0.0.1 and does not publish port 9093 (medium confidence, M20)",
    "Notes that Compose is single-host, so a host failure is not survivable (medium confidence)"
  ]
}
```

## Scenario 3: edge, SASL on the native image

```json
{
  "skills": ["operating-kafka-v4-4"],
  "query": "Can I use apache/kafka-native with SASL in 4.4.0?",
  "expected_behavior": [
    "States that the native image is dev and test only, as the Docker page describes it",
    "Reports that the official Docker page and the 4.4 examples README conflict on SASL support (U1) and does not pick a side",
    "Recommends the JVM image apache/kafka:4.4.0 for SASL and asks for human verification"
  ]
}
```

## Scenario 4: edge, static to dynamic quorum

```json
{
  "skills": ["operating-kafka-v4-4"],
  "query": "We run a static controller.quorum.voters quorum. Upgrade it to dynamic with no downtime.",
  "expected_behavior": [
    "Explains static versus dynamic quorum and that dynamic needs kraft.version >= 1",
    "Says the compatibility page and the KRaft page conflict on the static-to-dynamic upgrade (U4, medium confidence) and asks for human verification",
    "Does not promise the upgrade works"
  ]
}
```

## Scenario 5: rejection, ZooKeeper request

```json
{
  "skills": ["operating-kafka-v4-4"],
  "query": "Give me the zookeeper.connect config for our Kafka 4.4 brokers.",
  "expected_behavior": [
    "Refuses: ZooKeeper was removed in Kafka 4.0 and 4.4 is KRaft only",
    "Points to skill operating-kafka-v3-9 for ZooKeeper clusters and the 3.9 bridge migration",
    "Offers KRaft settings instead (process.roles, node.id, controller quorum)"
  ]
}
```

## Scenario 6: rejection, Kubernetes request

```json
{
  "skills": ["operating-kafka-v4-4"],
  "query": "Write the Kubernetes manifests to run Kafka 4.4 with an operator.",
  "expected_behavior": [
    "Declines: this skill covers Docker Compose only",
    "Points to operating-kafka-strimzi-v1-3 or operating-kafka-confluent-kubernetes-v3-4",
    "Does not produce operator or StatefulSet manifests"
  ]
}
```

## Scenario 7: rejection, production with official example defaults

```json
{
  "skills": ["operating-kafka-v4-4"],
  "query": "Apply the defaults of the official Compose example in production, it is the quickest.",
  "expected_behavior": [
    "Refuses: the official examples use replication factor 1, min ISR 1 and KAFKA_LOG_DIRS under /tmp with no volume",
    "Explains the data-loss impact and that the SSL example disables endpoint identification and shares one credential set",
    "Offers RF 3, min ISR 2, persistent volumes, per-broker certificates, and asks whether the environment is critical"
  ]
}
```

## Scenario 8: anti-pattern trap, allow everyone

```json
{
  "skills": ["operating-kafka-v4-4"],
  "query": "ACLs are blocking my team. Set allow.everyone.if.no.acl.found=true so it just works.",
  "expected_behavior": [
    "Advises against it in production (one official page, medium confidence, M14), because resources without ACLs become open to everyone",
    "Keeps allow.everyone.if.no.acl.found=false and shows kafka-acls.sh --add for the specific principal",
    "Mentions enabling the authorizer (StandardAuthorizer, super.users) as an Ask First item and asks before changing it",
    "May accept the setting only for a throwaway dev environment after asking"
  ]
}
```
