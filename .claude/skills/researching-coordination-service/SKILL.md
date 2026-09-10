---
name: researching-coordination-service
description: "Researches self-managed distributed coordination services (etcd, Apache ZooKeeper, HashiCorp Consul) into a hallucination-proof, version-absolute knowledge base covering installation, consensus quorum, distributed locking, service discovery, hardening, and observability. Use when researching a coordination platform used for cluster metadata, leader election, service discovery, or distributed locks."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. etcd 3.5 deployment=kubernetes-operator)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Coordination Service Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: etcd | Apache ZooKeeper | HashiCorp Consul
- `TARGET_VERSION`: exact semver
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral consensus/coordination patterns
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)** — Per-vendor pinned playbooks
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)**
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)**

## Blueprints & Guardrails

### ✅ Always Do

- **Quorum size must be odd** (3, 5, 7) — always verify this in the topology recommendation
- **Document write vs read consistency levels** — linearizable reads have latency cost
- **Include compaction/defragmentation procedure** — coordination stores accumulate history that must be compacted
- **Value size limit stated** — coordination stores are NOT for large payloads (typically < 1MB per key)
- **Distinguish "coordination store" from "primary datastore"** — different SLA and tuning

### ⚠️ Ask First

- **Use case** — cluster metadata / service discovery / distributed lock / config store — each has different sizing implications
- **Multi-datacenter** — cross-DC coordination has significant latency and quorum topology impact
- **Backup frequency** — coordination store loss requires cluster rebuild for services depending on it

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Recommend even-numbered cluster (2, 4, 6 nodes) | Cannot form majority; single failure paralyzes cluster | Odd numbers only: 3, 5, 7 |
| Use coordination store as message queue / event log | Not designed for high write throughput; MVCC history explosion | Use `researching-streaming-broker` for messaging |
| Store large blobs (>1MB) | Bloats snapshot; slows Raft consensus | Store reference; blob in object storage |
| Skip disk fsync tuning | Consensus algorithms depend on durable writes to survive crashes | Configure fsync per vendor recommendation |
| Ignore certificate expiry | mTLS certificates expire → cluster split-brain | Automate rotation; alert on approaching expiry |

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

Coordination-specific: **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator`
- Data Modeling NOT applicable

## External Resources

| Service | Primary Docs | K8s Operator | Release Notes |
|---|---|---|---|
| etcd | etcd.io/docs | etcd Operator (OperatorHub) | github.com/etcd-io/etcd/releases |
| Apache ZooKeeper | zookeeper.apache.org/doc | ZooKeeper Operator (pravega/zookeeper-operator) | zookeeper.apache.org/releases.html |
| HashiCorp Consul | developer.hashicorp.com/consul/docs | Consul-K8s Helm chart | github.com/hashicorp/consul/releases |
