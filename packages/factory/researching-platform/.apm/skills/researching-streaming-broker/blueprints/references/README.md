# Reference Index — researching-streaming-broker

Index of the official sources and documentation categories already named in this skill's
[SKILL.md](../../SKILL.md) and blueprints. It adds no new facts.

> **Status:** no per-vendor reference cards (`<vendor>-<version>.md`) exist in this folder yet.
> Create them from the [reference card template](../../../researching-platform-software/blueprints/shared/reference-card-template.md)
> (worked example: [reference-card-example-kafka-3.7.md](../../../researching-platform-software/blueprints/shared/reference-card-example-kafka-3.7.md)).

## Official Sources (from SKILL.md → External Resources)

> Entries are copied verbatim. SKILL.md records no fetch date for any of them, so each is
> **(unverified)** until a dated fetch is recorded in a vendor reference card.

| Broker | Primary Docs | Operator / Registry | Release Notes | Status |
|---|---|---|---|---|
| Apache Kafka | kafka.apache.org/documentation | Strimzi: strimzi.io/docs | kafka.apache.org/downloads | (unverified) |
| RabbitMQ | rabbitmq.com/docs | RabbitMQ Cluster Operator: rabbitmq.com/kubernetes | rabbitmq.com/release-notes | (unverified) |
| Apache Pulsar | pulsar.apache.org/docs | streamnative/pulsar-operator | github.com/apache/pulsar/releases | (unverified) |
| NATS | docs.nats.io | nats-io/nack | github.com/nats-io/nats-server/releases | (unverified) |
| Apache ActiveMQ Artemis | activemq.apache.org/components/artemis | activemq-artemis-operator | activemq.apache.org/download | (unverified) |

## Documentation Categories

Categories this skill expects each vendor's docs to cover, taken from the headings of
[category-specifics.md](../category-specifics.md):

- Broker Roles & Terminology (Neutral Vocabulary)
- Delivery Guarantee Selection
- Ordering Guarantees
- HA Topology Neutral Model
- Backpressure & Flow Control
- Dead Letter Handling
- Neutral KPIs (all brokers)
- Universal Anti-Patterns (all brokers)
- Ecosystem Adjacencies

## Shared Sources

- [output-format-base.md](../../../researching-platform-software/blueprints/shared/output-format-base.md) — output skeleton; every claim cites an official docs URL with a date
- [research-scope-operations.md](../../../researching-platform-software/blueprints/shared/research-scope-operations.md) — shared research scope §1–§12
- [deployment-guides/](../../../researching-platform-software/blueprints/shared/deployment-guides/) — per-`DEPLOYMENT_MODEL` playbooks
- [evaluation-scenarios.md](../evaluation-scenarios.md) — behavioral test cases for this skill
