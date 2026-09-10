# Evaluation Scenarios — researching-vector-store

Cross-vendor coverage required: at least one Milvus/Qdrant scenario AND at least one pgvector scenario (extension model differs).

---

## Scenario 1 — Qdrant on Kubernetes

**Input**:
```
/researching-vector-store Qdrant 1.9 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Documents Qdrant's Raft-based clustering: sharding + replication factor
- HNSW index with `m` / `ef_construct` / `ef` tuning
- Distance metric selection (Cosine/Euclidean/Dot) matched to embedding model
- Metadata payload filtering (pre-filter during search)
- Recommends Qdrant Helm/Operator
- References `blueprints/references/qdrant-1.9.md`

**must_not**:
- Recommend FLAT index for a large production dataset
- Omit metadata filtering
- Mismatch distance metric to model

---

## Scenario 2 — Milvus on Kubernetes

**Input**:
```
/researching-vector-store Milvus 2.4 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Documents Milvus's distributed architecture: query/data/index/proxy nodes + etcd (metadata) + object storage (MinIO/S3) + message queue (Pulsar/Kafka)
- Recommends Milvus Operator
- Index types: HNSW, IVF_FLAT, IVF_PQ, DiskANN — selection by scale/memory
- References `blueprints/references/milvus-2.4.md`

**must_not**:
- Describe Milvus as a single-binary store (it has multiple node types + dependencies)
- Omit the etcd + object storage + message queue dependencies

---

## Scenario 3 — pgvector (PostgreSQL extension)

**Input**:
```
/researching-vector-store pgvector 0.7 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Notes pgvector is a PostgreSQL extension — inherits PostgreSQL HA/backup/operations
- Cross-references `researching-rdbms` for base PostgreSQL operations
- Documents pgvector index types: HNSW and IVFFlat (added in specific versions)
- Documents that vector search shares resources with the relational workload (tuning trade-off)
- References `blueprints/references/pgvector-0.7.md`

**must_not**:
- Describe pgvector as a standalone vector database
- Ignore the PostgreSQL foundation (shared_buffers, connection limits still apply)
- Use Milvus/Qdrant cluster concepts for pgvector

---

## Scenario 4 — RAG Chunking Design

**Input**:
```
/researching-vector-store Qdrant 1.9 (workload: RAG over technical documentation)
```

**must_pass**:
- Recommends chunking strategy (256-512 tokens, 10-20% overlap)
- Recommends hybrid search (dense + BM25) for code/technical terms
- Recommends storing source_document_id + chunk_index in metadata for targeted updates
- Matches distance metric to the chosen embedding model
