# Graph Database — Neutral Category Specifics

Patterns for graph databases. Vendor-specific query language, config keys, and index syntax live in `references/<vendor>-<version>.md`.

---

## When a Graph Database Fits

Graph databases excel when:
- Relationships are first-class and traversal-heavy (friends-of-friends, shortest path, impact analysis)
- Relationship attributes matter (weight, timestamp on the edge)
- The relationship schema evolves organically

They do NOT fit:
- Tabular aggregations (use RDBMS/columnar)
- Simple key lookup with no traversal (use KV store)
- Full-text search (use search engine)

If the workload is not traversal-centric, flag the mismatch and suggest the appropriate sibling.

---

## Graph Model (Neutral)

| Concept | What to research per engine |
|---|---|
| Node / vertex | Entity with identity; labels/tags; properties |
| Edge / relationship | Typed, directed connection; edge properties |
| Storage model | Native (index-free adjacency) vs pluggable backend |
| Query language | Cypher / Gremlin / GQL / nGQL — engine-specific |
| Index | Which properties can be indexed; index-backed anchor lookup |
| Consistency | Causal cluster / backend-derived / eventual |

---

## Traversal Performance (Neutral)

- **Anchor node lookup must be indexed** — every traversal starts by finding a node via an indexed property; without the index it is a full scan
- **Index-free adjacency** (native graph engines) makes hop traversal O(1) per edge — but does NOT eliminate super-node cost
- **Bound variable-length paths** — always set an upper hop limit to prevent whole-graph exploration
- **Direction awareness** — traversing with vs against edge direction has different cost in some engines

---

## Super-Node Problem (Neutral)

A super-node is a vertex with a very high degree (millions of edges — a celebrity, a popular tag):

- Traversing all edges of a super-node is expensive and can OOM
- Detection: query nodes ordered by degree; flag those above a threshold (e.g., 10,000+ edges)
- Mitigation (neutral):
  1. Filter by edge type/property BEFORE traversal
  2. Introduce intermediate bucket nodes to split the fan-out
  3. Paginate the traversal
  4. Denormalize the specific high-frequency query

---

## HA Topologies (Neutral)

1. **Causal / consensus cluster** — core nodes with consensus (Raft) for writes + read replicas; automatic failover
2. **Backend-derived HA** (JanusGraph) — HA inherited from the storage backend (Cassandra/HBase)
3. **Sharded cluster** (ArangoDB, Nebula) — data partitioned across nodes; coordinator tier
4. **Single node + backup** — dev/test only

Document the read-consistency model (causal consistency with bookmarks, eventual, strong).

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Query latency p99 | Traversal health | > SLA |
| Page cache hit ratio (native engines) | Memory effectiveness | low → disk-bound traversals |
| Heap usage (JVM engines) | Memory pressure | > 75% |
| Transaction throughput | Write baseline | anomaly |
| Replication lag (cluster) | Replica health | > threshold |
| Store size / growth | Capacity | trend |

---

## Universal Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Unbounded variable-length path | Whole-graph traversal; OOM | Bound hops: `*1..5` |
| Missing index on anchor property | Full node scan per query | Index all anchor-lookup properties |
| Super-node without mitigation | Traversal OOM | Edge-type filter / bucket nodes / pagination |
| Modeling relationships as node properties | Loses graph structure; behaves like a table | Explicit edges with types |
| Graph for aggregation queries | Not columnar-optimized | RDBMS/columnar for analytics |
| Large blobs in properties | Memory pressure | Reference; blob in object storage |
| One giant graph without multi-tenancy | Cross-tenant leakage; degraded performance | Separate databases or tenant_id property + index + filter |

---

## §Data Modeling

Full guidance: [data-modeling.md](./data-modeling.md). Cross-type principles: [shared modeling-principles](../../templates/platform-research/data-modeling-principles.md).

---

## Ecosystem Adjacencies (neutral; names in reference cards)

- Query browser / visualization (Neo4j Browser, ArangoDB Web UI, Nebula Studio)
- Bulk import tools
- Backup tooling
- Graph algorithms library (GDS, etc.)
- Monitoring exporters
