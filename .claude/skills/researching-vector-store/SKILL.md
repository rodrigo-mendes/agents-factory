---
name: researching-vector-store
description: "Researches self-managed vector / ANN databases (Milvus, Qdrant, Weaviate, pgvector, Chroma) into a hallucination-proof, version-absolute knowledge base covering installation, index topology, HA, backup, upgrade, hardening, observability, and vector data modeling (distance metrics, index types, chunking, hybrid search). Use when researching a vector database the team will install and operate itself."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. Qdrant 1.9 deployment=kubernetes-operator / Milvus 2.4)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Vector Store Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: Milvus | Qdrant | Weaviate | pgvector | Chroma
- `TARGET_VERSION`: exact semver
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral ANN/index/distance patterns
- **[Data Modeling](./blueprints/data-modeling.md)** — Distance metric, index type, chunking, hybrid search
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)**
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)**
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)**
- **[Shared Modeling Principles](../../templates/platform-research/data-modeling-principles.md)**

## Blueprints & Guardrails

### ✅ Always Do

- **Match distance metric to the embedding model** — cosine/L2/dot must match how the model was trained
- **Choose index type by scale + recall target** — HNSW (fast, memory-heavy) vs IVF (scalable) vs FLAT (exact, small only)
- **Always pre-filter by metadata** — tenant/type filtering before ANN search
- **Store source references, not raw text blobs** — enables targeted update/delete
- **Label configs by `DEPLOYMENT_MODEL`**

### ⚠️ Ask First

- **Embedding model + dimension** — determines vector_size and distance metric
- **Recall vs latency vs memory target** — drives index type and parameters
- **Hybrid search need** — dense + sparse (BM25) fusion for keyword-critical domains
- **`DEPLOYMENT_MODEL`** if unspecified

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Wrong distance metric for the model | Semantically wrong rankings | Match metric to model's training |
| FLAT index at scale (>1M vectors) | Linear scan; latency grows unboundedly | HNSW or IVF above ~100K vectors |
| No metadata pre-filtering | Cross-tenant leakage; poor precision | Filter by metadata before ANN |
| Mixing embeddings from different models | Incompatible vector spaces | Separate collection per model/version |
| Storing raw text as the vector payload | Storage bloat; no dedup | Store reference + minimal metadata |

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

Vector-specific: **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator`
- **§Data Modeling** — always — see [data-modeling.md](./blueprints/data-modeling.md)

## External Resources

| Engine | Primary Docs | K8s Operator | Release Notes |
|---|---|---|---|
| Milvus | milvus.io/docs | Milvus Operator | github.com/milvus-io/milvus/releases |
| Qdrant | qdrant.tech/documentation | Qdrant Helm / Operator | github.com/qdrant/qdrant/releases |
| Weaviate | weaviate.io/developers/weaviate | Weaviate Helm | github.com/weaviate/weaviate/releases |
| pgvector | github.com/pgvector/pgvector | (PostgreSQL extension — CloudNativePG) | github.com/pgvector/pgvector/releases |
| Chroma | docs.trychroma.com | Chroma Helm | github.com/chroma-core/chroma/releases |
