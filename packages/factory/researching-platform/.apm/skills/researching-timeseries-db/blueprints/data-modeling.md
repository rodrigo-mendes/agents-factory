# Time-Series Data Modeling

For `DATASTORE_TYPE=time-series`. Platforms: InfluxDB, TimescaleDB, VictoriaMetrics, QuestDB.

---

## Core Concepts

| Concept | InfluxDB | TimescaleDB | VictoriaMetrics |
|---|---|---|---|
| Data unit | Point (timestamp + tags + fields) | Row in hypertable | Sample (timestamp + labels + value) |
| Partition unit | Bucket (by time) | Chunk (by time + optional space) | Block (by time, internal) |
| Metadata | Tags (indexed, low-cardinality) | Regular columns (indexed) | Labels (indexed, low-cardinality) |
| Measurement | Measurement name | Table name | Metric name |

---

## Tag vs Field Design (InfluxDB / VictoriaMetrics)

**Tags** = dimensions used for filtering and grouping:
- Stored in an index (memory-intensive)
- Must be LOW cardinality (< 100K distinct values per tag)
- Always strings
- Examples: `host`, `region`, `datacenter`, `service_name`, `environment`

**Fields** = measurement values:
- NOT indexed (cannot filter without scanning all points in time range)
- Can be float, integer, string, boolean
- Examples: `cpu_usage`, `memory_bytes`, `request_latency_ms`, `http_status_code`

```
Decision rule:
  "Do I GROUP BY or WHERE this dimension?" → TAG
  "Is this a measurement value I aggregate?" → FIELD
  "Could this dimension have millions of unique values?" → FIELD (never TAG)
```

---

## Series Cardinality Management

**Cardinality** = number of unique tag-set combinations across all measurements.

```
Total series = PRODUCT(unique_values_per_tag_across_all_measurements)

Example: 
  host: 100 values
  service: 50 values  
  endpoint: 200 values
  Total series = 100 × 50 × 200 = 1,000,000 series

Memory impact (InfluxDB): ~1–3KB RAM per active series
1M series = 1–3GB RAM for the index alone

Danger zone: > 10M series → OOM risk
```

### Cardinality Anti-Patterns

| Bad Tag | Cardinality Impact | Correct Alternative |
|---|---|---|
| `user_id` as tag | Millions of distinct values × other tags | Store as a FIELD; query by time range, not by user |
| `ip_address` as tag | Potentially unbounded | Store as field or aggregate before storing |
| `request_id` as tag | One series per request → catastrophic | Always a FIELD |
| `error_message` as tag | Unbounded unique strings | Use a `has_error: true` tag + error_message as FIELD |

---

## Hypertable Design (TimescaleDB)

```sql
-- Create a hypertable (PostgreSQL table + automatic time partitioning)
CREATE TABLE sensor_readings (
  time        TIMESTAMPTZ  NOT NULL,
  sensor_id   INTEGER      NOT NULL,
  location    TEXT         NOT NULL,
  temperature DOUBLE PRECISION,
  humidity    DOUBLE PRECISION
);

-- Convert to hypertable; chunk interval = query range sweet spot
SELECT create_hypertable('sensor_readings', 'time', chunk_time_interval => INTERVAL '1 day');

-- Optional: space partitioning for even distribution across nodes (distributed TimescaleDB)
SELECT create_distributed_hypertable('sensor_readings', 'time', 'sensor_id');
```

### Chunk Interval Sizing

| Data Retention | Query Range | Recommended Chunk Interval |
|---|---|---|
| 7 days | Last 1 hour | 1 hour |
| 30 days | Last 24 hours | 1 day |
| 1 year | Last 7 days | 1 week |
| 5+ years | Last 30 days | 1 month |

Rule: chunk interval ≈ query time range. Too small → too many chunks for range queries. Too large → single chunk too big to process in memory.

---

## Continuous Aggregates / Downsampling

Pre-aggregate old data to reduce storage and speed up range queries:

```sql
-- TimescaleDB: Continuous Aggregate for 5-minute averages
CREATE MATERIALIZED VIEW sensor_readings_5min
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('5 minutes', time) AS bucket,
  sensor_id,
  AVG(temperature) AS avg_temp,
  MAX(temperature) AS max_temp,
  MIN(temperature) AS min_temp
FROM sensor_readings
GROUP BY bucket, sensor_id;

-- Schedule policy: auto-refresh as new data arrives
SELECT add_continuous_aggregate_policy('sensor_readings_5min',
  start_offset => INTERVAL '10 minutes',
  end_offset   => INTERVAL '5 minutes',
  schedule_interval => INTERVAL '5 minutes');
```

### Tiered Retention Policy

```sql
-- Keep raw data for 7 days; aggregate data for 1 year
SELECT add_retention_policy('sensor_readings', INTERVAL '7 days');

-- Enable tiered storage: move old chunks to cheaper storage (TimescaleDB Enterprise)
SELECT add_tiering_policy('sensor_readings', INTERVAL '30 days');
```

---

## Time-Series Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Query without time filter | Full dataset scan — extremely slow at scale | Always include WHERE time > NOW() - INTERVAL '7 days' |
| Storing calculated values instead of raw | Lose ability to recalculate with different formula | Store raw; use continuous aggregates for derived values |
| No retention policy | Storage grows unboundedly | Define retention policy at table/bucket creation time |
| Using VARCHAR/TEXT for numeric measurements | Cannot aggregate; larger storage | Use DOUBLE PRECISION or INTEGER for numeric measurements |
| Back-filling without specifying chunk limits | Single chunk grows too large; compaction OOM | Batch back-fill by chunk boundary; monitor chunk sizes |
