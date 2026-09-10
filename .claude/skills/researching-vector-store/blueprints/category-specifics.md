# Vector Store — Neutral Category Specifics

Patterns for vector / ANN databases. Vendor-specific config keys, index parameters, and API shapes live in `references/<vendor>-<version>.md`.

---

## Vector Model (Neutral)

| Concept | What to research per engine |
|---|---|
| Vector / embedding | Dense float array; dimension must match the embedding model |
| Distance metric | Cosine / L2 / dot product — must match model training |
| ANN index | HNSW / IVF / PQ / FLAT — recall vs speed vs memory trade-off |
| Collection / class | Named container of vectors + metadata |
| Metadata / payload | Filterable attributes stored alongside vectors |
| Hybrid search | Dense (ANN) + sparse (BM25/keyword) fusion |

---

## Distance Metric Selection (Neutral)

| Metric | Use When |
|---|---|
| Cosine similarity | Semantic text search (most common); model normalizes vectors |
| L2 (Euclidean) | Image similarity; spatial; magnitude matters |
| Dot product | Max-inner-product search; unnormalized embeddings |

**Critical rule**: the metric MUST match how the embedding model was trained (check the model card). A mismatch produces semantically wrong rankings.

---

## ANN Index Type Selection (Neutral)

| Index | Memory | Build | Query | Best For |
|---|---|---|---|---|
| HNSW | High (graph in RAM) | Slow | Very fast | Production; recall >0.95; fits in RAM; incremental inserts |
| IVF (FLAT/PQ) | Medium/Low | Fast | Medium | Large datasets; memory-constrained (PQ) |
| PQ (Product Quantization) | Very low | Medium | Fast | Memory-constrained; tolerate slight recall loss |
| FLAT (brute force) | High | None | Slow | < ~100K vectors; exact recall required |

Rule: above ~100K–1M vectors, never use FLAT. HNSW is the common production default; IVF/PQ for memory constraints.

---

## Index Parameter Tuning (Neutral)

- **HNSW `m`** (graph connectivity): higher = better recall, more memory, slower build
- **HNSW `ef_construction`**: higher = better index quality, slower build
- **HNSW `ef` (search)**: higher = better recall, slower query; set ≥ top_k
- **IVF `nlist` / `nprobe`**: partitions searched — recall vs speed

The reference card gives the vendor parameter names and sane defaults for `TARGET_VERSION`.

---

## Metadata Filtering (Neutral)

Always pre-filter vectors by metadata before or during ANN search:

- **Tenant isolation** — filter by `tenant_id` to prevent cross-tenant leakage
- **Type / corpus filtering** — restrict to the relevant document type
- **Freshness** — filter by `created_at` for recency
- **Pre-filter vs post-filter** — pre-filtering (during search) is more accurate than filtering results afterward; the reference card documents which the engine supports

---

## Hybrid Search (Neutral)

Combine dense (semantic) + sparse (keyword) retrieval for precision:

```
1. Dense retrieval: ANN search → top-K by semantic similarity
2. Sparse retrieval: BM25/keyword → top-K by term match
3. Fusion: Reciprocal Rank Fusion (RRF) or weighted score
4. Rerank (optional): cross-encoder model on the fused top-N
```

Use when specialized vocabulary matters (code, legal, product SKUs).

---

## HA Topologies (Neutral)

1. **Distributed cluster** — Milvus (query/data/index nodes + etcd + object storage), Qdrant (Raft-based sharding + replication), Weaviate (Raft for schema + per-class RF)
2. **RDBMS-inherited** — pgvector inherits PostgreSQL HA
3. **Single node / embedded** — Chroma (often embedded or single-server)

Document the coordination + storage dependencies per engine (etcd, object storage, PostgreSQL).

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Query latency p99 | Search health | > SLA |
| Recall (measured against ground truth) | Search quality | below target |
| Index build time / status | Ingestion health | backlog |
| Memory usage | Capacity (HNSW is RAM-heavy) | approaching limit |
| Vector count / collection size | Growth | trend |
| Insert throughput | Ingestion baseline | drops |

---

## Universal Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Wrong distance metric | Wrong rankings | Match metric to model training |
| FLAT index at scale | Latency grows linearly | HNSW/IVF above ~100K vectors |
| No metadata pre-filter | Cross-tenant leakage; poor precision | Pre-filter by tenant/type |
| Mixed-model embeddings in one collection | Incompatible vector spaces | Collection per model/version |
| Raw text as payload | Storage bloat; no dedup | Store reference + minimal metadata |
| Rebuild index per insert | O(N) per document | HNSW incremental inserts or batch IVF builds |

---

## §Data Modeling

Full guidance: [data-modeling.md](./data-modeling.md). Cross-type principles: [shared modeling-principles](../../templates/platform-research/data-modeling-principles.md).

---

## Ecosystem Adjacencies (neutral; names in reference cards)

- Embedding model serving (the vector source)
- Chunking / ingestion pipeline (for RAG)
- Reranker model (cross-encoder)
- Client libraries per language
- Monitoring exporters
