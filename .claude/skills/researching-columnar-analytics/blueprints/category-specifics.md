# Columnar / OLAP — Neutral Category Specifics

Patterns for columnar analytics databases. Vendor-specific engines, config keys, and SQL dialect live in `references/<vendor>-<version>.md`.

---

## Columnar Model (Neutral)

| Concept | What to research per engine |
|---|---|
| Column-oriented storage | Data stored by column → efficient aggregation on few columns of wide tables |
| Immutable segments/parts | Data written in immutable files; background merge/compaction |
| Sort / order key | Physical sort order — the primary read-performance lever |
| Partitioning | Usually by time — enables efficient retention drop |
| Materialized view / projection | Pre-aggregation or alternate sort at ingest time |
| Compression / encoding | Dictionary, delta, run-length — per-column codecs |

---

## Ingestion Model (Neutral)

Columnar engines are optimized for **bulk append**, not transactional writes:

- **Batch inserts** — accumulate rows (thousands+) before inserting; tiny inserts create many small segments
- **Streaming ingestion** — some engines (Druid, Pinot) ingest directly from Kafka with real-time + historical tiers
- **Merge/compaction** — background process merges small segments into larger ones; monitor backlog

Rule: never insert row-by-row. Buffer at the application or use the engine's async insert / buffer table.

---

## Sort Key / Order Key Design (Neutral)

The single most important performance decision:

```
Rule: order by the columns most frequently used in WHERE filters, most-selective first,
      then columns used for GROUP BY, then time.

Good: ORDER BY (tenant_id, event_type, timestamp)
Bad:  ORDER BY (timestamp) when most queries filter by tenant_id first
```

A well-chosen sort key turns full scans into range reads.

---

## Partitioning (Neutral)

- Partition by time (day/month) for time-series analytics → efficient bulk DROP PARTITION for retention
- Keep total partition count bounded (thousands, not millions) — too many partitions add overhead
- Partition pruning: queries filtering on the partition key skip irrelevant partitions

---

## Pre-Aggregation (Neutral)

| Mechanism | Purpose |
|---|---|
| Materialized view | Maintain a pre-aggregated / re-sorted copy updated at insert time |
| Projection | Alternate sort order of the same data, chosen automatically by the optimizer |
| Rollup (Druid/Pinot) | Aggregate at ingestion granularity to reduce row count |

Use for hot dashboard queries that would otherwise scan raw data repeatedly.

---

## HA Topologies (Neutral)

1. **Replicated shards** — data sharded + each shard replicated (ClickHouse ReplicatedMergeTree + Keeper/ZooKeeper)
2. **Tiered service roles** — Druid/Pinot separate ingestion, storage (historical), and query (broker) tiers
3. **Distributed query** — a query fans out across shards and merges results
4. **Single node / embedded** — DuckDB is embedded (in-process); no server HA

Document the coordination dependency (ClickHouse Keeper/ZooKeeper, Druid coordinator, Pinot controller).

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Query latency p99 | Query health | > SLA |
| Insert rate / parts created | Ingestion health | too many small parts (merge can't keep up) |
| Merge/compaction backlog | Storage efficiency | growing |
| Memory per query | Resource pressure | approaching limit; OOM risk |
| Disk usage / compression ratio | Capacity | trend |
| Replication delay | Replica health | > threshold |
| Rejected inserts (too many parts) | Ingestion overload | non-zero |

---

## Universal Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Row-by-row inserts | Merge storm; rejected inserts | Batch (1000+ rows) or async buffer |
| Sort key not aligned with filters | Full scans | Order by most-frequent filter columns first |
| Frequent UPDATE/DELETE | Heavy segment rewrites | Append-only + dedup engine / rollup |
| String for low-cardinality columns | 10× storage | Dictionary / LowCardinality encoding |
| Millions of partitions | Overhead; slow queries | Bounded partition count (time-based) |
| OLTP point-write workload | Wrong engine class | Use `researching-rdbms` |

---

## §Data Modeling

Full guidance: [data-modeling.md](./data-modeling.md). Cross-type principles: [shared modeling-principles](../../templates/platform-research/data-modeling-principles.md).

---

## Ecosystem Adjacencies (neutral; names in reference cards)

- Streaming ingestion (Kafka connectors, real-time ingestion tiers)
- BI / visualization (Grafana, Superset, Metabase)
- Coordination dependency (ZooKeeper/Keeper for ClickHouse; coordinator/controller for Druid/Pinot)
- Backup tooling
- Client libraries per language
