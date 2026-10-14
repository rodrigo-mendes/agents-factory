# Evaluation Scenarios — researching-columnar-analytics

Cross-vendor coverage required: at least one ClickHouse scenario AND at least one non-ClickHouse scenario (Druid, Pinot, or DuckDB).

---

## Scenario 1 — ClickHouse on Kubernetes

**Input**:
```
/researching-columnar-analytics ClickHouse 24.3 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Recommends Altinity ClickHouse Operator
- Documents ReplicatedMergeTree + ClickHouse Keeper (or ZooKeeper) for replication
- Sort key (ORDER BY) aligned with filter patterns; PARTITION BY time
- Batch insert guidance (avoid row-by-row); `parts_to_throw_insert` alert
- LowCardinality encoding for low-cardinality columns
- Materialized views for pre-aggregation
- References `blueprints/references/clickhouse-24.3.md`

**must_not**:
- Recommend row-by-row inserts
- Recommend frequent UPDATE/DELETE without a dedup engine
- Omit the Keeper/ZooKeeper coordination dependency

---

## Scenario 2 — Apache Druid (real-time + batch)

**Input**:
```
/researching-columnar-analytics Apache Druid 30.0 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Documents Druid's tiered architecture: Coordinator, Overlord, Broker, Historical, MiddleManager/Indexer, Router
- Documents deep storage (S3/HDFS) + metadata store (PostgreSQL/MySQL) + ZooKeeper dependencies
- Real-time ingestion from Kafka + rollup at ingestion
- Segment granularity + partitioning
- References `blueprints/references/druid-30.0.md`

**must_not**:
- Use ClickHouse MergeTree terminology for Druid
- Describe Druid as a single-process engine
- Omit the deep-storage + metadata-store + ZooKeeper dependencies

---

## Scenario 3 — DuckDB (embedded OLAP)

**Input**:
```
/researching-columnar-analytics DuckDB 1.0 deployment=bare-metal depth=standard
```

**must_pass**:
- Notes DuckDB is embedded (in-process), single-node analytical engine — no server, no cluster
- Documents its use case: local analytics, embedded in applications, Parquet/Arrow interop
- HA is N/A — the "database" is a file or in-memory; durability via the host application
- References `blueprints/references/duckdb-1.0.md`

**must_not**:
- Recommend a "DuckDB cluster operator" (it's embedded)
- Apply ClickHouse replication concepts to DuckDB
- Describe distributed query fan-out

---

## Scenario 4 — Misuse: OLTP Workload

**Input**:
```
/researching-columnar-analytics ClickHouse 24.3 (workload: high-frequency single-row updates, transactional)
```

**must_pass**:
- Flags that high-frequency point updates + transactions are an OLTP workload, not OLAP
- Recommends `researching-rdbms` for the transactional workload
- If analytics on the same data is needed, suggests CDC (Debezium) from the RDBMS into ClickHouse
