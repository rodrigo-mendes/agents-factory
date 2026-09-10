---
name: researching-wide-column-store
description: "Researches self-managed wide-column databases (Apache Cassandra, ScyllaDB, Apache HBase) into a hallucination-proof, version-absolute knowledge base covering installation, ring/replication topology, backup, upgrade, hardening, observability, and query-first data modeling. Use when researching a wide-column database the team will install and operate itself (not managed services like Keyspaces or Bigtable)."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. Cassandra 5.0 deployment=kubernetes-operator / ScyllaDB 6.0)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Wide-Column Store Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: Apache Cassandra | ScyllaDB | Apache HBase
- `TARGET_VERSION`: exact semver
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral ring/partition/consistency patterns
- **[Data Modeling](./blueprints/data-modeling.md)** — Query-first design, partition/clustering keys
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)**
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)**
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)**
- **[Shared Modeling Principles](../../templates/platform-research/data-modeling-principles.md)**

## Blueprints & Guardrails

### ✅ Always Do

- **Query-first modeling** — design one table per query pattern; never entity-first
- **Partition key must be high-cardinality and evenly distributed** — hot partitions are the #1 failure mode
- **Document consistency level per operation** — QUORUM/LOCAL_QUORUM vs ONE vs ALL
- **Replication factor + strategy** — NetworkTopologyStrategy for multi-DC; RF=3 typical
- **Label configs by `DEPLOYMENT_MODEL`**

### ⚠️ Ask First

- **Consistency vs availability** — the tunable consistency level per read/write
- **Compaction strategy** — STCS vs LCS vs TWCS depends on read/write/TTL profile
- **Multi-DC topology** — RF per datacenter; local quorum reads
- **`DEPLOYMENT_MODEL`** if unspecified

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Low-cardinality partition key | Hot partition; one node saturated | High-cardinality key; add bucket suffix |
| Unbounded partition growth | Slow reads; node imbalance | Time-bucket the partition key; add TTL |
| Explicit DELETEs at high rate | Tombstone flood → read degradation | Use TTL instead of deletes; tune gc_grace |
| ALLOW FILTERING in production | Full partition scan; latency spikes | Create a new table for the query pattern |
| Entity-first modeling | Queries need ALLOW FILTERING or secondary indexes | Query-first: one table per access pattern |

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

Wide-column-specific: **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator` (K8ssandra, Scylla Operator)
- **§Data Modeling** — always — see [data-modeling.md](./blueprints/data-modeling.md)

## External Resources

| Engine | Primary Docs | K8s Operator | Release Notes |
|---|---|---|---|
| Apache Cassandra | cassandra.apache.org/doc | K8ssandra Operator | github.com/apache/cassandra/blob/trunk/CHANGES.txt |
| ScyllaDB | docs.scylladb.com | Scylla Operator | github.com/scylladb/scylladb/releases |
| Apache HBase | hbase.apache.org/book.html | (Helm charts; runs on HDFS) | hbase.apache.org/downloads.html |
