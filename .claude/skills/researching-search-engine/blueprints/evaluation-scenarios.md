# Evaluation Scenarios — researching-search-engine

Cross-vendor coverage required: at least one Elasticsearch/OpenSearch scenario AND at least one non-Lucene-heavyweight scenario (Solr differs; Typesense/Meilisearch are architecturally different).

---

## Scenario 1 — Elasticsearch on Kubernetes (ECK)

**Input**:
```
/researching-search-engine Elasticsearch 8.13 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Recommends Elastic Cloud on Kubernetes (ECK) as the official operator
- Documents JVM heap sizing: 50% of RAM, capped at ~26-32GB (compressed OOP threshold)
- Documents ILM (Index Lifecycle Management) for hot/warm/cold/frozen tiers
- Recommends 3 dedicated master-eligible nodes for production
- Documents text vs keyword field mapping; ESR-style compound behavior
- Includes `## Data Modeling` section (mapping + analyzer design)
- KPIs: cluster health status, JVM heap, unassigned shards, search latency
- References `blueprints/references/elasticsearch-8.13.md`

**must_not**:
- Enable fielddata on text fields
- Recommend deep from+size pagination
- Omit alias-for-reindex pattern

---

## Scenario 2 — Apache Solr (SolrCloud) on VM

**Input**:
```
/researching-search-engine Apache Solr 9.6 deployment=vm depth=standard
```

**must_pass**:
- Uses Solr terminology: collection, core, shard, replica, SolrCloud, ZooKeeper ensemble (Solr depends on ZK for coordination)
- Documents that SolrCloud requires an external ZooKeeper ensemble (or embedded for dev) — architectural difference from Elasticsearch's built-in coordination
- Documents schema.xml / managed-schema field definitions and analyzers
- Documents replica types (NRT, TLOG, PULL) — Solr-specific
- KPIs: Solr-specific metrics via JMX / Metrics API
- References `blueprints/references/solr-9.6.md`

**must_not**:
- Describe Solr as having built-in cluster coordination like Elasticsearch (it uses ZooKeeper)
- Use Elasticsearch ILM terminology for Solr
- Reference ECK (Elasticsearch operator) for Solr

---

## Scenario 3 — Meilisearch (lightweight, single-binary)

**Input**:
```
/researching-search-engine Meilisearch 1.8 deployment=container-compose depth=standard
```

**must_pass**:
- Notes Meilisearch's architecturally different model: single binary, embedded LMDB storage, typo-tolerance-first, not Lucene-based
- Documents that Meilisearch (as of 1.8) is primarily single-node; HA/sharding is limited vs Elasticsearch
- Documents its index settings: searchable attributes, filterable attributes, ranking rules
- Uses Meilisearch's master key auth model
- References `blueprints/references/meilisearch-1.8.md`

**must_not**:
- Apply Elasticsearch shard/replica sizing to Meilisearch (different architecture)
- Recommend JVM heap tuning (Meilisearch is Rust, not JVM)
- Assume ILM / lifecycle management exists in the Elasticsearch sense

---

## Scenario 4 — Vector Search Boundary

**Input**:
```
/researching-search-engine Elasticsearch 8.13 (primary use: vector similarity search)
```

**must_pass**:
- Notes that Elasticsearch supports dense_vector + kNN, but if vector search is the ONLY use case, consider `researching-vector-store` (Milvus/Qdrant) for specialized performance
- Documents hybrid search (BM25 + dense_vector) as ES's strength when both text and vector matter
- Routes appropriately or gives the trade-off

---

## Scenario 5 — Mapping Explosion Prevention

**Input**:
```
/researching-search-engine Elasticsearch 8.13 (workload: arbitrary user-defined JSON documents)
```

**must_pass**:
- Warns about mapping explosion from dynamic fields
- Recommends `dynamic: false` or `dynamic: strict` + explicit field limit (`index.mapping.total_fields.limit`)
- Suggests flattened field type for arbitrary key-value objects
