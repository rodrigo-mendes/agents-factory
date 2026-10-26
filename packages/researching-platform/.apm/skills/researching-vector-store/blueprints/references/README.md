# Reference Index — researching-vector-store

Index of the official sources and documentation categories already named in this skill's
[SKILL.md](../../SKILL.md) and blueprints. It adds no new facts.

> **Status:** no per-vendor reference cards (`<vendor>-<version>.md`) exist in this folder yet.
> Create them from the [reference card template](../../../researching-platform-software/blueprints/shared/reference-card-template.md)
> (worked example: [reference-card-example-kafka-3.7.md](../../../researching-platform-software/blueprints/shared/reference-card-example-kafka-3.7.md)).

## Official Sources (from SKILL.md → External Resources)

> Entries are copied verbatim. SKILL.md records no fetch date for any of them, so each is
> **(unverified)** until a dated fetch is recorded in a vendor reference card.

| Engine | Primary Docs | K8s Operator | Release Notes | Status |
|---|---|---|---|---|
| Milvus | milvus.io/docs | Milvus Operator | github.com/milvus-io/milvus/releases | (unverified) |
| Qdrant | qdrant.tech/documentation | Qdrant Helm / Operator | github.com/qdrant/qdrant/releases | (unverified) |
| Weaviate | weaviate.io/developers/weaviate | Weaviate Helm | github.com/weaviate/weaviate/releases | (unverified) |
| pgvector | github.com/pgvector/pgvector | (PostgreSQL extension — CloudNativePG) | github.com/pgvector/pgvector/releases | (unverified) |
| Chroma | docs.trychroma.com | Chroma Helm | github.com/chroma-core/chroma/releases | (unverified) |

## Documentation Categories

Categories this skill expects each vendor's docs to cover, taken from the headings of
[category-specifics.md](../category-specifics.md):

- Vector Model (Neutral)
- Distance Metric Selection (Neutral)
- ANN Index Type Selection (Neutral)
- Index Parameter Tuning (Neutral)
- Metadata Filtering (Neutral)
- Hybrid Search (Neutral)
- HA Topologies (Neutral)
- Neutral KPIs
- Universal Anti-Patterns
- §Data Modeling
- Ecosystem Adjacencies (neutral; names in reference cards)

Data-modeling categories, from [data-modeling.md](../data-modeling.md):

- Fundamental Concepts
- Distance Metric Selection
- Embedding Model Selection
- Chunking Strategy (for RAG and Document Embeddings)
- ANN Index Type Selection
- Hybrid Search Pattern
- Vector Anti-Patterns

## Shared Sources

- [output-format-base.md](../../../researching-platform-software/blueprints/shared/output-format-base.md) — output skeleton; every claim cites an official docs URL with a date
- [research-scope-operations.md](../../../researching-platform-software/blueprints/shared/research-scope-operations.md) — shared research scope §1–§12
- [deployment-guides/](../../../researching-platform-software/blueprints/shared/deployment-guides/) — per-`DEPLOYMENT_MODEL` playbooks
- [evaluation-scenarios.md](../evaluation-scenarios.md) — behavioral test cases for this skill
