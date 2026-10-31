# Reference Index — researching-coordination-service

Index of the official sources and documentation categories already named in this skill's
[SKILL.md](../../SKILL.md) and blueprints. It adds no new facts.

> **Status:** no per-vendor reference cards (`<vendor>-<version>.md`) exist in this folder yet.
> Create them from the [reference card template](../../../researching-platform-software/blueprints/shared/reference-card-template.md)
> (worked example: [reference-card-example-kafka-3.7.md](../../../researching-platform-software/blueprints/shared/reference-card-example-kafka-3.7.md)).

## Official Sources (from SKILL.md → External Resources)

> Entries are copied verbatim. SKILL.md records no fetch date for any of them, so each is
> **(unverified)** until a dated fetch is recorded in a vendor reference card.

| Service | Primary Docs | K8s Operator | Release Notes | Status |
|---|---|---|---|---|
| etcd | etcd.io/docs | etcd Operator (OperatorHub) | github.com/etcd-io/etcd/releases | (unverified) |
| Apache ZooKeeper | zookeeper.apache.org/doc | ZooKeeper Operator (pravega/zookeeper-operator) | zookeeper.apache.org/releases.html | (unverified) |
| HashiCorp Consul | developer.hashicorp.com/consul/docs | Consul-K8s Helm chart | github.com/hashicorp/consul/releases | (unverified) |

## Documentation Categories

Categories this skill expects each vendor's docs to cover, taken from the headings of
[category-specifics.md](../category-specifics.md):

- Purpose of a Coordination Store
- Consensus Algorithm Model (Vendor-Neutral)
- Cluster Sizing Guidelines
- Read Consistency Trade-off
- Distributed Locking Pattern
- Service Discovery Pattern
- Compaction / Defragmentation
- Neutral KPIs
- Universal Anti-Patterns
- Ecosystem Adjacencies

## Shared Sources

- [output-format-base.md](../../../researching-platform-software/blueprints/shared/output-format-base.md) — output skeleton; every claim cites an official docs URL with a date
- [research-scope-operations.md](../../../researching-platform-software/blueprints/shared/research-scope-operations.md) — shared research scope §1–§12
- [deployment-guides/](../../../researching-platform-software/blueprints/shared/deployment-guides/) — per-`DEPLOYMENT_MODEL` playbooks
- [evaluation-scenarios.md](../evaluation-scenarios.md) — behavioral test cases for this skill
