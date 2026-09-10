---
name: researching-graph-database
description: "Researches self-managed graph databases (Neo4j, JanusGraph, ArangoDB, Nebula Graph) into a hallucination-proof, version-absolute knowledge base covering installation, cluster/causal-consistency HA, backup, upgrade, hardening, observability, and graph data modeling (nodes/edges, traversal, super-node mitigation). Use when researching a graph database the team will install and operate itself (not managed services like Neptune)."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. Neo4j 5.20 deployment=kubernetes-operator)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Graph Database Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: Neo4j | JanusGraph | ArangoDB | Nebula Graph
- `TARGET_VERSION`: exact semver
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral node/edge/traversal patterns
- **[Data Modeling](./blueprints/data-modeling.md)** — Node/edge granularity, property placement, super-nodes
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)**
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)**
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)**
- **[Shared Modeling Principles](../../templates/platform-research/data-modeling-principles.md)**

## Blueprints & Guardrails

### ✅ Always Do

- **Validate the use case is traversal-heavy** — if the workload is tabular/aggregation, a graph DB is the wrong tool
- **Index the start-node lookup property** — traversals begin at an indexed anchor node
- **Bound variable-length traversals** — always set an upper hop limit
- **Document the storage backend** — native graph (Neo4j) vs pluggable backend (JanusGraph on Cassandra/HBase)
- **Label configs by `DEPLOYMENT_MODEL`**

### ⚠️ Ask First

- **Consistency model** — causal cluster (Neo4j) vs backend-derived (JanusGraph) — impacts read staleness
- **Query language** — Cypher / Gremlin / GQL / nGQL — depends on the engine
- **Super-node likelihood** — high-degree nodes need mitigation strategy
- **`DEPLOYMENT_MODEL`** if unspecified

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Unbounded variable-length path (`*` or `*1..`) | May traverse the entire graph → OOM | Always bound: `*1..5` |
| Missing index on start-node property | Full node scan per query | Index every property used to anchor a traversal |
| Super-nodes without mitigation | Traversal OOM; query-plan degradation | Bucket nodes / edge-type filtering / pagination |
| Graph for tabular aggregation | Graph engines are not columnar | Use RDBMS/columnar for analytics; graph for traversal |
| Storing large blobs in node properties | Memory pressure | Store reference; blob in object storage |

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

Graph-specific: **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator`
- **§Data Modeling** — always — see [data-modeling.md](./blueprints/data-modeling.md)

## External Resources

| Engine | Primary Docs | K8s Operator | Release Notes |
|---|---|---|---|
| Neo4j | neo4j.com/docs | Neo4j Helm charts | neo4j.com/release-notes |
| JanusGraph | docs.janusgraph.org | (runs on Cassandra/HBase + ES/Solr) | github.com/JanusGraph/janusgraph/releases |
| ArangoDB | docs.arangodb.com | ArangoDB Kubernetes Operator | github.com/arangodb/arangodb/releases |
| Nebula Graph | docs.nebula-graph.io | Nebula Operator | github.com/vesoft-inc/nebula/releases |
