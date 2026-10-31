# Vector Data Modeling

For `DATASTORE_TYPE=vector`. Platforms: Milvus, Qdrant, Weaviate, pgvector, Chroma.

---

## Fundamental Concepts

| Concept | Definition |
|---|---|
| Embedding | Dense vector (array of floats) representing semantic meaning of data |
| Dimension | Length of the vector (e.g., 1536 for OpenAI text-embedding-3-small) |
| Distance metric | How similarity is measured — must match model's training metric |
| ANN index | Approximate Nearest Neighbor index — trades perfect recall for speed |
| Recall | Fraction of true nearest neighbors returned — target: > 0.95 for most use cases |

---

## Distance Metric Selection

| Metric | Formula | When to Use |
|---|---|---|
| Cosine similarity | 1 - (A·B)/(|A||B|) | Text/semantic search — most common; model must normalize vectors |
| L2 (Euclidean) | √Σ(Aᵢ-Bᵢ)² | Image similarity; spatial data; when magnitude matters |
| Dot product | A·B | Maximum inner product search; used with unnormalized embeddings |
| Hamming | Count differing bits | Binary embeddings (compact representations) |

**Critical rule**: The distance metric used in the vector store must match the metric used to train the embedding model. Check the model card.

---

## Embedding Model Selection

```
Selection criteria:
  1. Task type: text (sentence-transformers), images (CLIP), code (CodeBERT), multi-modal
  2. Dimension: lower = faster + less memory; higher = better semantic capture
     Common: 384 (MiniLM), 768 (BERT-base), 1024 (large models), 1536 (OpenAI ada-002), 3072 (OpenAI text-embedding-3-large)
  3. Language: multi-lingual vs English-only
  4. License: commercial use allowed?
  5. Latency: embedding time per document (affects indexing pipeline throughput)

Do not mix embeddings from different models in the same collection/index.
Version pin the model — model updates produce incompatible embeddings.
```

---

## Chunking Strategy (for RAG and Document Embeddings)

The chunking strategy determines what unit of text gets embedded:

| Strategy | Chunk Size | When to Use |
|---|---|---|
| Fixed-size | 256–512 tokens | Simple; fast; works for homogeneous documents |
| Sentence-boundary | 1–5 sentences | When sentence integrity matters |
| Paragraph | 1 paragraph | Long-form content; natural semantic boundaries |
| Semantic chunking | Variable (semantic similarity threshold) | Best quality; more compute |
| Recursive character | Adaptive | LangChain default; good general purpose |

### Overlap and Context

```
chunk_overlap: 10–20% of chunk_size
Purpose: ensures context is not lost at chunk boundaries
Example: chunk_size=512 tokens, overlap=50 tokens
         chunk[0]: tokens 0–511
         chunk[1]: tokens 461–972
         chunk[2]: tokens 922–1433

Metadata per chunk (always store):
  - source_document_id: for attribution and updates
  - chunk_index: position within document
  - source_url or file_path: for citations
  - chunk_text: for display without re-fetch
  - created_at: for freshness filtering
```

---

## ANN Index Type Selection

| Index | Algorithm | Memory | Build Time | Query Latency | Best For |
|---|---|---|---|---|---|
| HNSW | Graph-based | High (entire graph in RAM) | Slow | Very fast | Production; recall > 0.95; dataset fits in RAM |
| IVF_FLAT | Inverted file + brute force | Medium | Fast | Medium | Exact recall not needed; large datasets |
| IVF_PQ | IVF + Product Quantization | Very low | Medium | Fast | Memory-constrained; slight recall loss |
| FLAT | Brute force | High (all vectors) | None | Slow | < 100K vectors or when exact recall required |
| ScaNN | Google tree-based | Medium | Medium | Very fast | High-throughput production (specific platforms) |

### HNSW Tuning Parameters

```
m: 16–64 (connectivity — higher = better recall, more memory, slower build)
   Rule of thumb: start with 16 for most use cases

ef_construction: 100–500 (build quality — higher = better index, slower build)
   Rule of thumb: ef_construction = 100–200 for most use cases

ef (search): ≥ top_k (runtime quality — higher = better recall, slower query)
   Rule of thumb: ef = 2× top_k as starting point; benchmark to find sweet spot
```

---

## Hybrid Search Pattern

Combine dense (ANN) and sparse (keyword) retrieval for better precision:

```
Query pipeline:
  1. Dense retrieval: ANN search → top-K candidates by semantic similarity
  2. Sparse retrieval: BM25 search → top-K candidates by keyword match
  3. Fusion: combine ranked lists using RRF (Reciprocal Rank Fusion):
     score(doc) = Σ 1 / (k + rank_in_list_i)  where k=60 is a constant
  4. Reranking (optional): apply cross-encoder model to top-N fused results
     cross-encoder is slower (O(N) inference) but much more accurate
  5. Return top-k from reranked list

When hybrid search improves results:
  + Code search (exact function name + semantic meaning)
  + Legal/medical documents (specific terms + conceptual similarity)
  + Product search (SKU/model number + description similarity)
  + Any domain with specialized vocabulary
```

---

## Vector Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Wrong distance metric for the model | Incorrect similarity rankings — top results are semantically wrong | Check model card; match metric to how model was trained |
| No metadata filtering (searching across all tenants) | Results from other tenants leak; poor precision | Always pre-filter by `tenant_id`, `document_type`, or `language` |
| Storing different model embeddings in same collection | Meaningless distance comparisons between incompatible spaces | Separate collection per embedding model version |
| FLAT index on > 500K vectors | Brute-force search → query latency degrades linearly with dataset size | Switch to HNSW or IVF for datasets > 100K vectors |
| Chunking entire documents as one vector | Large documents lose nuance; single embedding averages everything | Chunk into 256–512 token pieces with overlap |
| No source tracking in metadata | Cannot update or delete specific document's embeddings | Always store `source_document_id` to enable targeted deletion |
| Index rebuild on every new document | Build time O(N) per document | Use HNSW (supports O(log N) incremental inserts) |
