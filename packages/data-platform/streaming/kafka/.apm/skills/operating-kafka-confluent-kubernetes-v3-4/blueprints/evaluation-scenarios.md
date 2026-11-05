# Evaluation scenarios, operating-kafka-confluent-kubernetes-v3-4

Back to [SKILL.md](../SKILL.md). Six scenarios: canonical path, edge case, four misuse or trap cases.

## Scenario 1: Canonical: deploy a KRaft cluster with CFK 3.4.0

```json
{
  "skills": ["operating-kafka-confluent-kubernetes-v3-4"],
  "query": "Deploy a 3-broker Kafka on Kubernetes with Confluent for Kubernetes 3.4 and CP 8.3.",
  "expected_behavior": [
    "Uses KRaftController (3 replicas, odd) plus Kafka (3 replicas), no ZooKeeper",
    "Sets listener authentication and TLS in the first deploy and the same controller listener settings on both CRs",
    "Sets an explicit StorageClass with WaitForFirstConsumer and spec.image.init to confluent-init-container:3.4.0",
    "Labels any assembled YAML (unverified) and suggests kubectl explain kafka.spec for field placement",
    "Asks about license and identity provider before choosing RBAC or simple ACLs"
  ]
}
```

## Scenario 2: Edge: upgrade CFK 3.3 to 3.4.0

```json
{
  "skills": ["operating-kafka-confluent-kubernetes-v3-4"],
  "query": "Upgrade our CFK 3.3 operator to 3.4.0. Brokers have 64Gi memory requests and no jvm overrides.",
  "expected_behavior": [
    "Follows block-reconcile, helm upgrade, init container 3.4.0, enable-reconcile",
    "Warns that the heap default is capped at min(50% of requests.memory, 32Gi) for brokers and pins it in configOverrides.jvm first",
    "Notes one rolling restart and that the 3.4.0 pages changed between 2026-10-27 and 2026-11-02",
    "States that rolling semantics and rollback for CP upgrades are not documented (unverified) instead of promising them"
  ]
}
```

## Scenario 3: Misuse: Strimzi requested

```json
{
  "skills": ["operating-kafka-confluent-kubernetes-v3-4"],
  "query": "Write a Strimzi Kafka custom resource for Kafka 4.4.0.",
  "expected_behavior": [
    "States that Strimzi is out of scope for this skill",
    "Points to operating-kafka-strimzi-v1-3 and does not write Strimzi CRs",
    "May mention that Strimzi 1.3.0 supports Kafka 4.2.0 to 4.3.1 and does not list 4.4.0 (https://strimzi.io/downloads/, read 2026-11-04)"
  ]
}
```

## Scenario 4: Misuse: no license, assume full features

```json
{
  "skills": ["operating-kafka-confluent-kubernetes-v3-4"],
  "query": "We have no Confluent license key. Deploy with RBAC, Self-Balancing and Tiered Storage and assume everything works.",
  "expected_behavior": [
    "Explains the 30-day trial without a key and that RBAC, Self-Balancing and Tiered Storage are Enterprise features per the official license pages (medium confidence, M32)",
    "Describes the documented expiry behavior (Control Center and security plugins fail to start, Confluent Server logs errors) and keeps the wording conflict visible (medium confidence)",
    "Does not guess whether simple ACLs keep working after expiry (unverified) and does not claim a community cp-kafka path (unverified)",
    "Asks whether an Enterprise subscription exists before proceeding"
  ]
}
```

## Scenario 5: Trap: ZooKeeper mode on CP 8.x

```json
{
  "skills": ["operating-kafka-confluent-kubernetes-v3-4"],
  "query": "Create a Zookeeper CR and point Kafka at it on Confluent Platform 8.3 under CFK 3.4.",
  "expected_behavior": [
    "Refuses: ZooKeeper was removed in Confluent Platform 8.0 and KRaft is required on 8.x",
    "Says ZooKeeper mode under CFK 3.4 is limited to CP 7.6 to 7.9 (inference, tagged unverified)",
    "Offers the migration path: from 7.6.x or earlier go to 7.9 on ZooKeeper, run the KRaftMigrationJob, then upgrade to 8.x; from 7.7.x or later migrate on the current version, then upgrade",
    "Does not state KRaftMigrationJob fields as fact (unverified)"
  ]
}
```

## Scenario 6: Misuse: Schema Registry internals

```json
{
  "skills": ["operating-kafka-confluent-kubernetes-v3-4"],
  "query": "Explain how Confluent Schema Registry stores schemas and tune its compatibility checks.",
  "expected_behavior": [
    "States that Schema Registry internals are out of scope",
    "Points to managing-event-schemas-confluent-v8-4",
    "Limits itself to the SchemaRegistry CR, its image and the CFK license context"
  ]
}
```
