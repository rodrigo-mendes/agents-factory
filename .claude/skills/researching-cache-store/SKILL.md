---
name: researching-cache-store
description: "Researches self-managed in-memory cache / session stores (Redis-as-cache, Memcached, KeyDB, Dragonfly) into a hallucination-proof, version-absolute knowledge base covering installation, HA topology, eviction policies, persistence trade-offs, hardening, and observability. Use when the platform is deployed as an ephemeral cache (data expected to be lost on eviction) — for Redis as primary datastore use researching-kv-store; for coordination use researching-coordination-service."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. Redis 7.2 deployment=vm / Memcached 1.6 deployment=kubernetes-operator)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Cache Store Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: Redis | Memcached | KeyDB | Dragonfly (as ephemeral cache)
- `TARGET_VERSION`: exact semver
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier rules
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral cache patterns (cache-aside, TTL discipline, eviction, stampede)
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)** — Per-vendor pinned playbooks
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Cross-vendor tests
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)** — 13-section skeleton
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)** — §1–§12 operational scope

## Blueprints & Guardrails

### ✅ Always Do

- **Confirm the platform is used as a cache, not a primary datastore** — if data must survive eviction or a full restart, route to `researching-kv-store` instead
- **Cite eviction policy defaults for `TARGET_VERSION`** — behavior on `maxmemory` reached differs across versions and platforms
- **Document TTL discipline** — every cache entry pattern should have an explicit TTL rationale
- **Distinguish deployment models** — sidecar vs shared cluster vs remote pool have different HA implications
- **Include cache-hit-ratio KPI with alert threshold** — the primary health signal for a cache

### ⚠️ Ask First

- **Persistence vs pure-cache** — even if the primary use is cache, some deployments enable AOF/RDB for warm restart; confirm intent
- **Cluster mode vs single-node with failover** — trade-off between horizontal scalability and simplicity
- **Multi-tenant cache** — key-prefixing scheme, per-tenant limits, or separate instances per tenant

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Recommend a cache without authentication in production | Any network peer can flush / read cache | Require auth mechanism per vendor reference card |
| Confuse cache eviction (data loss OK) with primary datastore eviction (data loss NOT OK) | Wrong operational model = wrong config recommendations | Confirm role via orchestrator; route to `researching-kv-store` if primary datastore |
| Assume all cache platforms support persistence | Memcached has no persistence; Redis has RDB/AOF | Check the reference card's persistence section |
| Omit `maxmemory-policy` (or equivalent) recommendation | Defaults differ per vendor and lead to unpredictable behavior at limit | Always specify eviction policy explicitly |

## Role & Mission

Senior Platform Engineering Researcher specializing in **`{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}`** ephemeral cache deployments — covering installation, HA, eviction, hardening, and observability for platform engineers.

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

Cache-specific: see **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator`
- Data Modeling NOT applicable to caches (see `researching-kv-store` if data modeling is needed)

## External Resources

| Cache | Primary Docs | K8s Operator | Release Notes |
|---|---|---|---|
| Redis | redis.io/docs | Redis Operator (spotahome), Redis Enterprise Operator | github.com/redis/redis/releases |
| Memcached | memcached.org / github.com/memcached/memcached/wiki | Bitnami Helm chart | github.com/memcached/memcached/wiki/ReleaseNotes |
| KeyDB | docs.keydb.dev | Community Helm charts | github.com/Snapchat/KeyDB/releases |
| Dragonfly | dragonflydb.io/docs | Dragonfly Operator (dragonflydb/dragonfly-operator) | github.com/dragonflydb/dragonfly/releases |
