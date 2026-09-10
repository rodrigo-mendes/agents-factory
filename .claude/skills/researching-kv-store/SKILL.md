---
name: researching-kv-store
description: "Researches self-managed persistent key-value stores (Redis-as-primary-datastore, RocksDB, LMDB, TiKV) into a hallucination-proof, version-absolute knowledge base covering installation, persistence/durability, HA, backup, hardening, observability, and key-value data modeling. Use when the platform is the primary persistent store (data must survive restart/eviction) — for ephemeral caching use researching-cache-store."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. Redis 7.2 deployment=vm / TiKV 7.5 deployment=kubernetes-operator)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Key-Value Store Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: Redis (as primary DB) | RocksDB | LMDB | TiKV
- `TARGET_VERSION`: exact semver
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral persistent KV patterns
- **[Data Modeling](./blueprints/data-modeling.md)** — Key design, structures, TTL, access patterns
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)**
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)**
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)**
- **[Shared Modeling Principles](../../templates/platform-research/data-modeling-principles.md)**

## Blueprints & Guardrails

### ✅ Always Do

- **Confirm primary-datastore intent** — if data may be lost on eviction, route to `researching-cache-store`
- **Persistence + durability is mandatory** — document the durability mode (WAL/AOF/snapshot) and its RPO
- **Eviction policy = no-eviction for primary datastore** — never silently evict primary data
- **Backup with verified restore** — a KV store as primary datastore needs the same rigor as an RDBMS
- **Label configs by `DEPLOYMENT_MODEL`**

### ⚠️ Ask First

- **Durability level** — fsync-always (no loss, slow) vs fsync-every-second (~1s RPO) vs OS-buffered (fastest, risk)
- **HA topology** — failover pair vs cluster (sharded) — depends on data volume
- **Persistence strategy** — snapshot vs WAL vs both (for Redis: RDB vs AOF vs both)
- **`DEPLOYMENT_MODEL`** if unspecified

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Eviction enabled on primary datastore | Silent data loss when memory fills | `noeviction` (or engine equivalent); scale storage |
| Persistence disabled on primary datastore | Full data loss on restart | Enable WAL/AOF/snapshot with appropriate fsync |
| Treat as a cache (data loss OK) | Wrong operational model | Route to `researching-cache-store` if ephemeral |
| Default auth off | Full data exposure | Enable auth; restrict bind address |
| Backup without restore test | Unrecoverable | Verified restore drill |

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

KV-specific: **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator`
- **§Data Modeling** — always — see [data-modeling.md](./blueprints/data-modeling.md)

## External Resources

| Engine | Primary Docs | K8s Operator | Release Notes |
|---|---|---|---|
| Redis (as DB) | redis.io/docs | Redis Enterprise Operator, spotahome/redis-operator | github.com/redis/redis/releases |
| RocksDB | rocksdb.org / github.com/facebook/rocksdb/wiki | (embedded library — no operator) | github.com/facebook/rocksdb/releases |
| LMDB | lmdb.tech/doc | (embedded library — no operator) | git.openldap.org/openldap/openldap (liblmdb) |
| TiKV | tikv.org/docs | TiDB Operator | github.com/tikv/tikv/releases |
