# Time-Series Database — Neutral Category Specifics

Patterns for time-series databases. Vendor-specific config keys, query language, and retention mechanisms live in `references/<vendor>-<version>.md`.

---

## Time-Series Model (Neutral)

| Concept | What to research per engine |
|---|---|
| Data point / sample | timestamp + dimensions + measurement value(s) |
| Dimensions (tags/labels) | Indexed metadata for filtering/grouping — MUST be low cardinality |
| Measurement values (fields) | The numeric quantities — not indexed |
| Time partitioning | Chunk/bucket/shard by time window |
| Retention | Automatic deletion of old data |
| Downsampling | Pre-aggregation of old data to coarser granularity |

---

## Cardinality Management (The Core Concern)

Series cardinality = number of unique dimension-set combinations. It is the primary scaling limit:

```
Total series ≈ PRODUCT(distinct values of each indexed dimension)

Example:
  host: 100 × service: 50 × endpoint: 200 = 1,000,000 series

Memory impact: ~1–3 KB RAM per active series (engine-dependent)
Danger zone: > 10M series → OOM risk on typical hardware
```

Rule: never make a high-cardinality attribute (user_id, request_id, IP) an indexed dimension — store it as a value/field. Document the cardinality budget explicitly.

---

## Retention & Downsampling (Neutral)

Tiered retention reduces storage while preserving history:

| Data Age | Granularity | Storage Tier |
|---|---|---|
| 0–7 days | Raw (seconds) | Hot (NVMe) |
| 7–90 days | 1-minute aggregate | Warm (SSD) |
| 90 days–2 years | 5-min / 1-hour aggregate | Cold (HDD/object) |
| > 2 years | 1-day aggregate | Archive / delete |

The reference card names the vendor mechanism (retention policy, continuous aggregate, downsampling task, recording rule).

---

## Chunk / Partition Sizing (Neutral)

Time-series engines partition data by time window:

- Chunk interval ≈ typical query time range (so a query touches few chunks)
- Too small → many chunks; range queries touch many partitions
- Too large → single chunk too big to process in memory
- The reference card gives the engine-specific parameter and default

---

## HA Topologies (Neutral)

Note: many time-series databases have **limited OSS clustering**. Research honestly:

1. **Single-node + backup** — common for OSS editions; document backup rigor
2. **Replication (RDBMS-derived)** — TimescaleDB inherits PostgreSQL replication
3. **Horizontally scaled cluster** — VictoriaMetrics (vminsert/vmstorage/vmselect), enterprise editions
4. **Federated / remote-write** — Prometheus-compatible remote storage patterns

Be explicit about what HA the OSS edition provides vs enterprise-only clustering.

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Active series count / cardinality | The scaling limit | approaching cardinality budget |
| Ingestion rate (points/sec) | Throughput | drops below baseline |
| Query latency p99 | Query health | > SLA |
| Disk usage / growth | Capacity | trend vs retention |
| Compaction / compression status | Storage efficiency | backlog |
| Memory usage | Cardinality pressure | rising with series count |
| Dropped/rejected points | Overload / cardinality limit hit | non-zero |

---

## Universal Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| High-cardinality indexed dimension | Cardinality explosion; OOM | Store as field/value, not tag/label |
| No retention policy | Unbounded storage | Define retention from day one |
| Query without time filter | Full-dataset scan | Always bound time range |
| Storing only derived values | Cannot recompute | Store raw; downsample for aggregates |
| Out-of-order writes without tolerance config | Rejected points or compaction overhead | Configure ingestion window / out-of-order tolerance |
| VARCHAR/TEXT for numeric measurement | Cannot aggregate; larger storage | Numeric type for measurement values |

---

## §Data Modeling

Full guidance: [data-modeling.md](./data-modeling.md). Cross-type principles: [shared modeling-principles](../../templates/platform-research/data-modeling-principles.md).

---

## Ecosystem Adjacencies (neutral; names in reference cards)

- Collection agents (Telegraf, Prometheus, Vector, Fluent Bit)
- Visualization (Grafana, Chronograf)
- Downsampling / recording rules tooling
- Backup tooling
- Client libraries per language
