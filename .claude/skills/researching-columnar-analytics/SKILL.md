---
name: researching-columnar-analytics
description: "Researches self-managed columnar / OLAP analytics databases (ClickHouse, Apache Druid, Apache Pinot, DuckDB) into a hallucination-proof, version-absolute knowledge base covering installation, distributed/replicated topology, ingestion, backup, upgrade, hardening, observability, and analytical data modeling (sort keys, partitioning, materialized views). Use when researching a columnar OLAP engine the team will install and operate itself."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. ClickHouse 24.3 deployment=kubernetes-operator)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Columnar / OLAP Analytics Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: ClickHouse | Apache Druid | Apache Pinot | DuckDB
- `TARGET_VERSION`: exact semver
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral columnar/OLAP patterns
- **[Data Modeling](./blueprints/data-modeling.md)** — Sort keys, partitioning, materialized views, dedup
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)**
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)**
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)**
- **[Shared Modeling Principles](../../templates/platform-research/data-modeling-principles.md)**

## Blueprints & Guardrails

### ✅ Always Do

- **Batch ingestion, not row-by-row** — columnar engines penalize tiny inserts heavily
- **Sort/order key driven by filter patterns** — the primary performance lever
- **Partition by time (or natural range) for retention** — enables efficient bulk drop
- **Materialized views / projections for hot query patterns** — pre-aggregate at ingest
- **Label configs by `DEPLOYMENT_MODEL`**

### ⚠️ Ask First

- **Ingestion model** — batch load vs streaming (Kafka ingestion) — impacts topology
- **Update/delete needs** — columnar engines favor append-only; mutations are expensive
- **Query concurrency** — high-concurrency point lookups vs low-concurrency heavy scans
- **`DEPLOYMENT_MODEL`** if unspecified

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Row-by-row inserts | Thousands of tiny parts → merge storm | Batch inserts (min 1000 rows or buffered) |
| Sort key not aligned with filters | Full scans instead of range reads | Order by most-frequent filter columns first |
| Frequent UPDATE/DELETE | Rewrites large column segments; heavy I/O | Append-only + dedup engine (ReplacingMergeTree etc.) |
| String for low-cardinality fields | 10× storage vs dictionary encoding | Dictionary/LowCardinality encoding |
| OLTP point-write workload | Columnar engines are OLAP, not OLTP | Use `researching-rdbms` for transactional workloads |

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

Columnar-specific: **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator`
- **§Data Modeling** — always — see [data-modeling.md](./blueprints/data-modeling.md)

## External Resources

| Engine | Primary Docs | K8s Operator | Release Notes |
|---|---|---|---|
| ClickHouse | clickhouse.com/docs | Altinity ClickHouse Operator | github.com/ClickHouse/ClickHouse/releases |
| Apache Druid | druid.apache.org/docs | Druid Operator (datainfrahq) | github.com/apache/druid/releases |
| Apache Pinot | docs.pinot.apache.org | Pinot K8s Helm | github.com/apache/pinot/releases |
| DuckDB | duckdb.org/docs | (embedded — no operator) | github.com/duckdb/duckdb/releases |
