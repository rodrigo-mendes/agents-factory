# Search Engine — Neutral Category Specifics

Patterns for full-text search & analytics engines. Vendor-specific config keys, mapping DSL, and query syntax live in `references/<vendor>-<version>.md`.

---

## Inverted Index Model (Vendor-Neutral)

Every engine in this family builds an **inverted index**: term → list of documents containing that term. The neutral vocabulary:

| Neutral concept | What it means | Reference card provides |
|---|---|---|
| Index / collection | Named container of searchable documents | Creation API, settings, immutability rules |
| Document | A JSON record to be indexed | Size limits, nested/object handling |
| Field | An attribute of a document | Field type system (text/keyword/numeric/date/geo/vector) |
| Analyzer | Tokenization + normalization pipeline for text fields | Built-in analyzers, custom pipeline config |
| Shard / partition | Horizontal split of an index for scale | Whether primaries can be resized after creation |
| Replica | Copy of a shard for HA + read scaling | Replication mechanism, consistency |
| Segment | Immutable unit within a shard (Lucene-based engines) | Merge policy, force-merge behavior |

---

## Text vs Exact-Match Field Design

The single most important modeling decision in every search engine:

| Field intent | Type (neutral) | Analyzed? | Use for |
|---|---|---|---|
| Full-text search | "text" / analyzed | Yes — tokenized, normalized | Match queries, relevance scoring |
| Exact match / filter / sort / aggregate | "keyword" / not-analyzed | No — stored verbatim | Term filters, sorting, faceting, aggregations |
| Both | multi-field (text + keyword sub-field) | Both | When a field needs full-text AND exact operations |

**Trap**: aggregating or sorting on an analyzed text field is either forbidden or requires expensive fielddata (OOM risk). Always use the exact-match sub-field for aggregations.

---

## Shard Sizing (Neutral Principles)

- **Target shard size**: most Lucene-based engines perform best with shards in a bounded size range (commonly cited: tens of GB per shard). The reference card gives the exact recommendation for `TARGET_VERSION`.
- **Primary shard count is often immutable** — chosen at index creation; changing requires reindex. Some engines offer split/shrink APIs.
- **Over-sharding** (many tiny shards) wastes memory on cluster state and per-shard overhead.
- **Under-sharding** (few huge shards) limits parallelism and slows recovery.
- **Formula**: `primary_shards ≈ expected_index_size / target_shard_size`, rounded, with headroom for growth.

---

## Index Lifecycle Management

For time-series / append-heavy data (logs, metrics, events), use lifecycle automation:

```
Phase progression (neutral):
  Hot    → actively indexed + queried; fastest storage
  Warm   → no longer indexed; still queried; can shrink/force-merge; cheaper storage
  Cold   → rarely queried; heavily compressed; cheapest local storage
  Frozen → searchable snapshot on object storage; minimal local footprint
  Delete → removed after retention period

Rollover trigger (neutral): create new index when current reaches size / age / doc-count threshold
Alias: the app always writes to / reads from an alias, never a concrete index name
```

The reference card names the vendor-specific mechanism (ILM in Elasticsearch, ISM in OpenSearch, TRA in Solr, etc.).

---

## Zero-Downtime Reindex Pattern

```
1. Application reads from and writes to an ALIAS (e.g., "products") — never a concrete index
2. Create new index "products_v2" with updated mapping
3. Reindex data from products_v1 → products_v2 (bulk copy)
4. Catch up on writes that arrived during reindex (dual-write or change-log replay)
5. Atomically switch the alias: products → products_v2
6. Delete products_v1 after verification
```

---

## Query Performance Patterns

| Concern | Neutral guidance |
|---|---|
| Deep pagination | Never use offset+limit beyond a few thousand — use cursor (search_after) or batch (scroll/PIT) |
| Source filtering | Fetch only needed fields; avoid returning large `_source` when a summary suffices |
| Filter vs query context | Filters (yes/no, cacheable) are cheaper than scoring queries; use filter context for exact constraints |
| Aggregation cardinality | High-cardinality aggregations are memory-intensive; bound them |
| Relevance tuning | Document the scoring model (BM25 default in most modern engines); custom boosting per field |

---

## Node Roles (for clustered engines)

| Role (neutral) | Responsibility |
|---|---|
| Coordinator | Routes queries, merges results (every node can do this) |
| Master/controller-eligible | Cluster state management, shard allocation (odd number: 3, 5) |
| Data (hot/warm/cold tiers) | Holds shards; serves index + query |
| Ingest | Pre-processing pipeline before indexing |

Small clusters combine roles; large clusters dedicate master-eligible nodes to prevent instability under load.

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Cluster health status | Overall availability | not "green" (yellow = unassigned replicas; red = unassigned primaries) |
| Indexing rate | Ingest throughput | drops below baseline |
| Search latency p99 | Query health | > SLA |
| JVM heap usage (JVM engines) | Memory pressure | > 75% sustained → GC pressure |
| GC pause time | Stability | frequent long pauses |
| Unassigned shards | Recovery health | > 0 sustained |
| Pending tasks | Cluster coordination backlog | growing queue |
| Disk watermark | Storage headroom | above low/high/flood watermark |

---

## Universal Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Fielddata on analyzed text | OOM; very slow | Use exact-match (keyword) sub-field for aggregation/sort |
| Dynamic mapping unbounded in production | Mapping explosion; unpredictable size | Strict or disabled dynamic mapping; explicit field limit |
| Deep offset pagination | O(offset) coordinate-sort; latency | Cursor-based (search_after) pagination |
| Direct index name in app | No zero-downtime reindex | Always front with an alias |
| Over-sharding small indices | Cluster-state bloat; per-shard overhead | Size shards to the recommended range |
| Single master-eligible node in production | Split-brain risk; no quorum | Odd number (3) of dedicated master-eligible nodes |
| Ignoring disk watermarks | Shards relocated or index blocked when disk fills | Monitor watermarks; alert before flood stage |

---

## §Data Modeling for Search Engines

Search-engine data modeling = **mapping + analyzer + index design**:

1. **Field mapping**: choose type per field driven by access pattern (search vs filter vs aggregate vs sort)
2. **Analyzer selection**: language-specific tokenization, stemming, synonyms, stop-words
3. **Denormalization**: search engines favor flat/denormalized documents; nested/parent-child relationships have query cost
4. **Index-per-tenant vs shared index**: multi-tenancy strategy (routing key vs separate indices)
5. **Time-based index strategy**: for logs/events, roll indices by time window + ILM

Cross-type modeling principles: [data-modeling-principles.md](../../templates/platform-research/data-modeling-principles.md).

---

## Ecosystem Adjacencies

Neutral list (vendor names in reference cards):

- Visualization / dashboards (Kibana, OpenSearch Dashboards, Solr Admin UI)
- Ingest pipelines (Logstash, Fluent Bit, Data Prepper, Vector)
- Client libraries per language
- Snapshot / backup repositories (object storage integration)
- Query analyzers / slow-log tooling
