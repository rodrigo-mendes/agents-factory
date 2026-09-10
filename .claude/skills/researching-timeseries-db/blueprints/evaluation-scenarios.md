# Evaluation Scenarios — researching-timeseries-db

Cross-vendor coverage required: at least one InfluxDB scenario AND at least one non-InfluxDB scenario (TimescaleDB, VictoriaMetrics, or QuestDB).

---

## Scenario 1 — InfluxDB on VM

**Input**:
```
/researching-timeseries-db InfluxDB 2.7 deployment=vm depth=standard
```

**must_pass**:
- Uses InfluxDB terminology: bucket, measurement, tag, field, point, Flux/InfluxQL, TSM engine
- Cardinality budget: tags are indexed (low cardinality); fields are not — user_id/IP must be a field
- Retention policy per bucket + downsampling tasks
- Notes OSS is single-node; clustering is InfluxDB Enterprise/Cloud
- KPIs: series cardinality, ingest rate, `SHOW SERIES CARDINALITY`
- References `blueprints/references/influxdb-2.7.md`

**must_not**:
- Recommend high-cardinality tags (user_id as tag)
- Claim OSS InfluxDB has built-in HA clustering
- Omit retention policy

---

## Scenario 2 — TimescaleDB on Kubernetes

**Input**:
```
/researching-timeseries-db TimescaleDB 2.14 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Notes TimescaleDB is a PostgreSQL extension — inherits PostgreSQL HA (streaming replication, CloudNativePG)
- Cross-references `researching-rdbms` for base PostgreSQL operations
- Documents hypertables, chunk_time_interval sizing, continuous aggregates, compression policies
- Uses SQL (not Flux/InfluxQL)
- References `blueprints/references/timescaledb-2.14.md`

**must_not**:
- Use InfluxDB tag/field model for TimescaleDB (it uses PostgreSQL columns)
- Ignore the PostgreSQL foundation
- Recommend InfluxDB retention-policy syntax

---

## Scenario 3 — VictoriaMetrics (horizontally scalable)

**Input**:
```
/researching-timeseries-db VictoriaMetrics 1.100 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Documents the cluster architecture: vminsert (stateless) + vmstorage (stateful, RF-configurable) + vmselect (stateless)
- Recommends VictoriaMetrics Operator
- Documents Prometheus remote-write compatibility and MetricsQL
- Cardinality limits: `-maxHourlySeries`, `-maxLabelsPerTimeseries`
- References `blueprints/references/victoriametrics-1.100.md`

**must_not**:
- Describe VictoriaMetrics as single-node only (the cluster version scales horizontally)
- Use InfluxDB bucket/measurement terminology

---

## Scenario 4 — Cardinality Explosion Prevention

**Input**:
```
/researching-timeseries-db InfluxDB 2.7 (workload: per-user API latency metrics, millions of users)
```

**must_pass**:
- Warns that user_id as a tag causes cardinality explosion (millions of series)
- Recommends storing user_id as a field, or pre-aggregating per-endpoint (not per-user)
- Provides the cardinality calculation showing the risk
