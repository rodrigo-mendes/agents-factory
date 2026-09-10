# Columnar / OLAP Data Modeling

For columnar analytics databases. Cross-type principles: [shared modeling-principles](../../templates/platform-research/data-modeling-principles.md).

---

## Table Engine / Storage Type Selection

Columnar engines offer multiple storage/table types. Research per engine (names in reference cards):

| Purpose | Neutral concept | Example (ClickHouse) |
|---|---|---|
| Standard append | Base columnar engine | MergeTree |
| Replicated | Base + replication via coordination | ReplicatedMergeTree |
| Pre-summed metrics | Auto-sum on merge | SummingMergeTree |
| Aggregate states | Store partial aggregates | AggregatingMergeTree |
| Deduplication / upsert | Replace by version on merge | ReplacingMergeTree |
| Change-tracking (CDC) | Sign-based collapse | CollapsingMergeTree |

Choose based on whether the workload is append-only, needs dedup, or needs pre-aggregation.

---

## Sort / Order Key Design

The physical sort order determines query performance:

```
Rule:
  1. Columns most frequently used in WHERE filters — most-selective FIRST
  2. Then columns used in GROUP BY
  3. Time column last (or omit if not filtered by time)

Good: ORDER BY (tenant_id, event_type, timestamp)
Bad:  ORDER BY (timestamp)  when queries filter tenant_id first

The sort key doubles as the sparse primary index — it enables skipping data blocks.
```

---

## Partitioning Strategy

```
Partition by time for retention efficiency:
  PARTITION BY toYYYYMM(event_date)   -- monthly partitions

Keep partition count bounded:
  < ~1000 partitions total per table
  Too many partitions → overhead on every query

Bulk retention:
  DROP PARTITION is instant (vs slow row-by-row DELETE)
```

---

## Denormalization for Analytics

Columnar engines favor wide, denormalized tables over normalized star schemas with runtime joins:

- **Pre-join at ingest** — flatten dimensions into the fact table (or use a materialized view that joins on insert)
- **Avoid large-table JOINs at query time** — they are expensive; denormalize instead
- **Dimension lookup tables** — small dimensions can be joined; large ones should be denormalized

Trade-off: storage increases (denormalized data repeats) but query latency drops dramatically.

---

## Low-Cardinality Encoding

```
For columns with < ~10K distinct values (status, country, category, event_type):
  Use dictionary encoding (LowCardinality in ClickHouse, dictionary in Parquet/Druid)
  Result: ~10× storage reduction + faster filtering

For high-cardinality columns (user_id, request_id):
  Do NOT dictionary-encode — the dictionary itself becomes huge
```

---

## Pre-Aggregation Patterns

| Pattern | When to Use |
|---|---|
| Materialized view (aggregate at insert) | Dashboard queries hitting the same GROUP BY repeatedly |
| Rollup at ingestion (Druid/Pinot) | When raw granularity is not needed; reduces row count massively |
| Projection (alternate sort) | Same data queried by different filter columns |

---

## Columnar Data Modeling Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Normalized schema with runtime joins | Slow large-table joins | Denormalize / pre-join at ingest |
| Row-by-row inserts | Merge storm; rejected inserts | Batch inserts (1000+ rows) |
| Sort key misaligned with filters | Full scans | Order by frequent filter columns first |
| Frequent mutations (UPDATE/DELETE) | Heavy segment rewrites | Append + dedup engine (ReplacingMergeTree) |
| String for low-cardinality dimension | 10× storage | Dictionary / LowCardinality encoding |
| Unbounded partition count | Per-query overhead | Time-based bounded partitions |
