---
name: researching-document-store
description: "Researches self-managed document databases (MongoDB, Couchbase, RavenDB) into a hallucination-proof, version-absolute knowledge base covering installation, replica-set/sharding HA, backup/PITR, upgrade, hardening, observability, and document data modeling (embedding vs referencing, indexing). Use when researching a document database the team will install and operate itself (not managed services like Atlas or DocumentDB)."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. MongoDB 7.0 deployment=kubernetes-operator)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Document Store Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: MongoDB | Couchbase | RavenDB
- `TARGET_VERSION`: exact semver
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral document DB patterns
- **[Data Modeling](./blueprints/data-modeling.md)** — Embed vs reference, indexing, schema evolution
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)**
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)**
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)**
- **[Shared Modeling Principles](../../templates/platform-research/data-modeling-principles.md)**

## Blueprints & Guardrails

### ✅ Always Do

- **Read the vendor reference card first** — document size limits, index types, and consistency options are vendor-specific
- **Document the replica/quorum model** — write concern and read concern (or equivalents) determine durability and consistency
- **State the document size limit** — every document DB has one; unbounded arrays approach it
- **Backup with PITR** — logical + physical tooling with verified restore
- **Label configs by `DEPLOYMENT_MODEL`**

### ⚠️ Ask First

- **Replica set vs sharded cluster** — single replica set (simpler) vs sharded (horizontal scale) — depends on data volume + throughput
- **Write/read concern level** — durability vs latency trade-off
- **Sharding key** (if sharded) — the single most consequential design decision
- **`DEPLOYMENT_MODEL`** if unspecified

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Standalone (non-replica-set) in production | No HA; no failover | Minimum 3-member replica set |
| Unbounded array growth in a document | Approaches document size limit; slow full-doc rewrites | Reference pattern or bucket pattern |
| Default auth disabled | Anyone on the network reads/writes all data | Enable auth; least-privilege roles |
| Cross-shard transactions in the hot path | High latency; distributed coordination | Design schema so common writes are single-shard |
| Backup without tested restore | Unrecoverable | Verified restore drill |

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

Document-specific: **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator`
- **§Data Modeling** — always — see [data-modeling.md](./blueprints/data-modeling.md)

## External Resources

| Engine | Primary Docs | K8s Operator | Release Notes |
|---|---|---|---|
| MongoDB | mongodb.com/docs | Percona Operator for MongoDB, MongoDB Community/Enterprise Operator | mongodb.com/docs/manual/release-notes |
| Couchbase | docs.couchbase.com | Couchbase Autonomous Operator | docs.couchbase.com/server/current/release-notes |
| RavenDB | ravendb.net/docs | RavenDB Helm chart | ravendb.net/docs/article-page/latest/csharp/start/whats-new |
