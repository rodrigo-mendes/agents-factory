---
name: researching-rdbms
description: "Researches self-managed relational / NewSQL databases (PostgreSQL, MySQL, MariaDB, CockroachDB) into a hallucination-proof, version-absolute knowledge base covering installation, replication/HA, backup/PITR, upgrade, hardening, observability, and data modeling (normalization, indexing, partitioning). Use when researching a relational database the team will install and operate itself (not managed services like RDS/Cloud SQL/Aurora)."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. PostgreSQL 16 deployment=kubernetes-operator / MySQL 8.4)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Relational Database (RDBMS) Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: PostgreSQL | MySQL | MariaDB | CockroachDB
- `TARGET_VERSION`: exact semver
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral RDBMS patterns (MVCC, isolation, indexing, partitioning)
- **[Data Modeling](./blueprints/data-modeling.md)** — Normalization, index design, partitioning, online migration
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)** — Per-vendor pinned playbooks
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)**
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)**
- **[Shared Modeling Principles](../../templates/platform-research/data-modeling-principles.md)**

## Blueprints & Guardrails

### ✅ Always Do

- **Read the vendor reference card first** — PostgreSQL `shared_buffers` ≠ MySQL `innodb_buffer_pool_size`; config keys are vendor-specific
- **Document the isolation level default and options** — Read Committed vs Repeatable Read vs Serializable behaviors differ per engine
- **Include connection pooling recommendation** — every RDBMS at scale needs a pooler (PgBouncer, ProxySQL, built-in)
- **Backup must include PITR** — logical + physical + WAL/binlog archiving with a verified restore procedure
- **Label configs by `DEPLOYMENT_MODEL`** — buffer sizing differs bare-metal vs container (cgroup limits) vs K8s

### ⚠️ Ask First

- **Replication mode** — async (lower latency, potential data loss) vs sync (zero data loss, higher latency) vs semi-sync
- **HA orchestration** — Patroni / Orchestrator / built-in vs manual failover
- **Partitioning need** — only when table size / retention warrants it
- **`DEPLOYMENT_MODEL`** if unspecified

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Copy config keys between engines | `synchronous_commit` (PG) has no MySQL equivalent | Use vendor reference card |
| Run without connection pooling at scale | Connection exhaustion; per-connection memory blows up | Deploy PgBouncer / ProxySQL / built-in pooler |
| Ignore autovacuum / purge tuning | Table bloat (PG) / undo growth (MySQL) → slow queries | Tune per vendor for hot tables |
| Single-AZ / single-node for production | No HA; failure = outage | Primary + standby with automatic failover |
| Backup without tested restore | "Backup" that cannot restore is not a backup | Document + verify restore drill |
| Over-index every column | Write amplification; storage bloat | Index only high-selectivity columns in WHERE/JOIN/ORDER BY |

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

RDBMS-specific: **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator` (CloudNativePG, Percona, etc.)
- **§Data Modeling** — always for this sibling — see [data-modeling.md](./blueprints/data-modeling.md)

## External Resources

| Engine | Primary Docs | K8s Operator | Release Notes |
|---|---|---|---|
| PostgreSQL | postgresql.org/docs | CloudNativePG, Crunchy Postgres Operator | postgresql.org/docs/release |
| MySQL | dev.mysql.com/doc | Percona XtraDB Cluster Operator, MySQL Operator (Oracle) | dev.mysql.com/doc/relnotes |
| MariaDB | mariadb.com/kb/en/documentation | mariadb-operator | mariadb.com/kb/en/release-notes |
| CockroachDB | cockroachlabs.com/docs | CockroachDB Operator | cockroachlabs.com/docs/releases |
