---
name: researching-timeseries-db
description: "Researches self-managed time-series databases (InfluxDB, TimescaleDB, VictoriaMetrics, QuestDB) into a hallucination-proof, version-absolute knowledge base covering installation, HA, retention/downsampling, backup, upgrade, hardening, observability, and time-series data modeling (tags vs fields, cardinality, downsampling). Use when researching a time-series database the team will install and operate itself."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. InfluxDB 2.7 / TimescaleDB 2.14 deployment=kubernetes-operator)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Time-Series Database Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: InfluxDB | TimescaleDB | VictoriaMetrics | QuestDB
- `TARGET_VERSION`: exact semver
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral time-series patterns (cardinality, retention, downsampling)
- **[Data Modeling](./blueprints/data-modeling.md)** — Tags vs fields, cardinality budget, chunk sizing
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)**
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)**
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)**
- **[Shared Modeling Principles](../../templates/platform-research/data-modeling-principles.md)**

## Blueprints & Guardrails

### ✅ Always Do

- **Cardinality budget is the #1 concern** — high-cardinality tags/labels cause OOM; document the limit
- **Retention policy from day one** — time-series data grows unbounded without it
- **Downsampling / continuous aggregates** — pre-aggregate old data to reduce storage and speed range queries
- **Every query has a time filter** — unbounded time-range queries scan everything
- **Label configs by `DEPLOYMENT_MODEL`**

### ⚠️ Ask First

- **Data granularity + retention tiers** — raw vs downsampled retention windows
- **Cardinality expectation** — which dimensions, and their distinct-value counts
- **HA topology** — many TSDBs have limited OSS clustering
- **`DEPLOYMENT_MODEL`** if unspecified

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| High-cardinality dimension as an indexed tag/label | Series cardinality explosion → OOM | Store as a field/value, not an indexed dimension |
| No retention policy | Unbounded storage growth | Define retention per measurement from creation |
| Query without time filter | Full-dataset scan | Always bound the time range |
| Storing derived/calculated values only | Cannot recompute with new formula | Store raw; derive via downsampling/continuous aggregates |

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

Time-series-specific: **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator`
- **§Data Modeling** — always — see [data-modeling.md](./blueprints/data-modeling.md)

## External Resources

| Engine | Primary Docs | K8s Operator | Release Notes |
|---|---|---|---|
| InfluxDB | docs.influxdata.com | InfluxDB Helm charts | github.com/influxdata/influxdb/releases |
| TimescaleDB | docs.timescale.com | (PostgreSQL operators: CloudNativePG) | github.com/timescale/timescaledb/releases |
| VictoriaMetrics | docs.victoriametrics.com | VictoriaMetrics Operator | github.com/VictoriaMetrics/VictoriaMetrics/releases |
| QuestDB | questdb.io/docs | QuestDB Helm chart | github.com/questdb/questdb/releases |
