---
name: researching-search-engine
description: "Researches self-managed full-text search & log analytics engines (Elasticsearch, OpenSearch, Apache Solr, Typesense, Meilisearch) into a hallucination-proof, version-absolute knowledge base covering installation, shard/replica topology, index lifecycle, mapping design, hardening, and observability. Use when researching a search engine the team will install and operate itself (not managed services like Elastic Cloud or Amazon OpenSearch Service)."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. Elasticsearch 8.13 deployment=kubernetes-operator)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Search Engine Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: Elasticsearch | OpenSearch | Apache Solr | Typesense | Meilisearch
- `TARGET_VERSION`: exact semver
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral inverted-index / shard / query patterns
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)** — Per-vendor pinned playbooks
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)**
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)**

## Blueprints & Guardrails

### ✅ Always Do

- **Distinguish text vs keyword field types** (or vendor equivalents) — analyzed for full-text search vs exact match for filters/aggregations
- **Shard sizing target**: state the recommended per-shard size range for `TARGET_VERSION` — cannot reshard primaries after creation (in most engines)
- **Document index lifecycle** — rollover / shrink / freeze / delete (or vendor equivalents) — critical for time-series indices
- **Alias pattern for zero-downtime reindex** — always use an alias as the app-facing name
- **Distinguish deployment models** — heap sizing, disk layout, and observability all differ

### ⚠️ Ask First

- **Search use case** — user-facing search vs log analytics vs vector similarity vs hybrid — different tuning
- **Data volume trajectory** — small (<100GB) vs medium (<10TB) vs large (>10TB) — impacts shard sizing and node roles
- **Text analyzer choice** — language-specific analyzers, custom pipelines — surface options before deciding
- **`DEPLOYMENT_MODEL`** if unspecified

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Enable fielddata on text fields | OOM risk; extremely slow | Use keyword type for aggregations |
| Deep pagination via from+size beyond ~10000 | Coordinate-sort across all shards; latency spikes | Use search_after (cursor) or scroll (batch) |
| Static mapping-less "dynamic: true" in production | Mapping explosion; unpredictable index size | Use strict mapping or "dynamic: false" |
| Over-sharding small indices | Overhead per shard; cluster state bloat | Aim for 20-50 GB / shard range (vendor-dependent) |
| Direct index name in application code | Impossible zero-downtime reindex | Always use aliases |
| Fetch full `_source` when only summary needed | Network + memory overhead | Use source filtering (_source_includes) |

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

Search-specific: **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator`
- **§Data Modeling** — YES for search engines (mapping / analyzer / index design counts as data modeling)

## External Resources

| Engine | Primary Docs | K8s Operator | Release Notes |
|---|---|---|---|
| Elasticsearch | elastic.co/guide/en/elasticsearch | ECK: elastic.co/guide/en/cloud-on-k8s | elastic.co/guide/en/elasticsearch/reference/current/release-notes |
| OpenSearch | opensearch.org/docs | OpenSearch K8s Operator (opensearch-project) | opensearch.org/versions |
| Apache Solr | solr.apache.org/guide | SolrCloud on K8s (Solr Operator) | solr.apache.org/downloads.html |
| Typesense | typesense.org/docs | Community Helm charts | github.com/typesense/typesense/releases |
| Meilisearch | meilisearch.com/docs | meilisearch/meilisearch-kubernetes | github.com/meilisearch/meilisearch/releases |
