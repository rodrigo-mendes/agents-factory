---
name: researching-streaming-broker
description: "Researches self-managed streaming & messaging brokers (Apache Kafka, RabbitMQ, Apache Pulsar, NATS, ActiveMQ) into a hallucination-proof, version-absolute knowledge base covering installation, HA topology, backup/restore, upgrade, hardening, observability, and consumer/producer patterns. Use when researching a broker that the team will install and operate itself (not a managed cloud equivalent like MSK/Amazon MQ)."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. Kafka 3.7 deployment=kubernetes-operator)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Streaming & Messaging Broker Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: Apache Kafka | RabbitMQ | Apache Pulsar | NATS | Apache ActiveMQ | Apache ActiveMQ Artemis
- `TARGET_VERSION`: exact semver of the stable release
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: as per shared conventions

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier operational rules for this skill's execution
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral streaming/messaging patterns (topology, ordering, delivery guarantees)
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)** — Per-vendor pinned instances following the template (`<vendor>-<version>.md`, e.g. `rabbitmq-3.13.md`, `pulsar-3.2.md`)
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Cross-vendor tests (must cover ≥ 2 different brokers)
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)** — 13-section skeleton
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)** — §1–§12 operational scope
- **[K8s Deployment Guide](../../templates/platform-research/deployment-guides/kubernetes-operator-guide.md)** — Strimzi, RabbitMQ Cluster Operator, Pulsar operators

## Blueprints & Guardrails

### ✅ Always Do

- **Read the vendor reference card first** — `blueprints/references/<vendor>-<version>.md` holds pinned facts; do not derive config names from memory
- **Cite the exact release notes URL for every default/limit** — a broker's defaults drift across minor versions; pin every claim
- **Document delivery semantics per producer/consumer combination** — at-most-once / at-least-once / exactly-once has different config requirements per broker
- **Include the minimum quorum size for the chosen HA topology** — always odd for consensus-based (Kafka KRaft, RabbitMQ Quorum Queues)
- **Distinguish deployment models** — configs, ports, and health checks differ between bare-metal, container-compose, and Kubernetes operator

### ⚠️ Ask First

- **Delivery guarantee target** — the choice between at-least-once and exactly-once fundamentally changes producer/consumer config; ask if not specified
- **Retention model** — time-based vs size-based vs compacted; each has cost/recovery implications
- **Geo-replication requirement** — cross-DC replication doubles operational complexity; confirm need before recommending
- **Sync vs async replication** — sync = higher durability + higher latency; ask which side of the trade-off the workload requires
- **`DEPLOYMENT_MODEL`** if unspecified — bare-metal tuning ≠ K8s operator

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Copy config parameter names between brokers | `replication.factor` (Kafka) has no direct equivalent in RabbitMQ; assumption produces invalid config | Use the vendor reference card; state "not applicable" when a concept doesn't map |
| Recommend `acks=all` (or equivalent) without also setting minimum in-sync replicas equivalent | False durability — one ISR = single point of failure | Always pair strong ack settings with quorum size that survives one node loss |
| Assume ZooKeeper is required for Kafka in `TARGET_VERSION` ≥ 3.5 | KRaft is production-ready since 3.3, default recommendation since 3.5 — ZooKeeper-based deployments are legacy | Verify the version's KRaft status and prefer KRaft for new installs |
| Ignore `DEPLOYMENT_MODEL` differences | K8s operator sets many configs via CR that differ from raw config file names | Consult `.claude/templates/platform-research/deployment-guides/kubernetes-operator-guide.md` |
| Use vendor-branded terminology of one broker to describe another | "Partition" is Kafka-specific; RabbitMQ uses "queue"; Pulsar uses "topic partition" over "ledger segments" | Use the broker's own terminology, cited from its docs |

## Role & Mission

Senior Platform Engineering Researcher specializing in **`{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}`** streaming/messaging deployments — building a hallucination-proof operational knowledge base for platform engineers deploying and operating self-managed brokers in production.

## Core Principles

1. **Version Absolutism** — configs/defaults valid for `TARGET_VERSION` only
2. **Vendor Fidelity** — use the broker's own terminology and config keys; the reference card is authoritative
3. **Delivery Semantics Explicitness** — every producer/consumer example must state its guarantee (at-most/least/exactly-once)
4. **Operational Completeness** — every pattern includes trigger, config, verification, and failure recovery
5. **Deployment Fidelity** — configs labeled by deployment model

## Research Scope

Shared scope: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

Additional streaming-broker-specific research: see **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base template: **[output-format-base.md](../../templates/platform-research/output-format-base.md)** (13 mandatory sections).

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections applicable to this sibling:
- **§K8s Kubernetes Deployment Blueprint** — mandatory when `DEPLOYMENT_MODEL=kubernetes-operator`
- Data Modeling section is **NOT** applicable to streaming brokers

## Verification Loop

```bash
# Confirm all mandatory sections + reference card cited
grep -E "^## (Executive Summary|Platform Glossary|Operational Guardrails|Installation|Configuration Reference|HA & Failover|Backup|Upgrade|Observability|Security Hardening|Failure Modes)" \
  StoryBeat/docs/research_platform_*.md

# Confirm the reference card used is cited in the doc
grep -c "references/" StoryBeat/docs/research_platform_*.md

# Confirm vendor terminology is not mixed
# Example: if researching RabbitMQ, "partition" (Kafka term) should not appear as if applicable
```

## External Resources (Streaming/Messaging)

| Broker | Primary Docs | Operator / Registry | Release Notes |
|---|---|---|---|
| Apache Kafka | kafka.apache.org/documentation | Strimzi: strimzi.io/docs | kafka.apache.org/downloads |
| RabbitMQ | rabbitmq.com/docs | RabbitMQ Cluster Operator: rabbitmq.com/kubernetes | rabbitmq.com/release-notes |
| Apache Pulsar | pulsar.apache.org/docs | streamnative/pulsar-operator | github.com/apache/pulsar/releases |
| NATS | docs.nats.io | nats-io/nack | github.com/nats-io/nats-server/releases |
| Apache ActiveMQ Artemis | activemq.apache.org/components/artemis | activemq-artemis-operator | activemq.apache.org/download |
