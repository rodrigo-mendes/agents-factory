# RDBMS Data Modeling

For `DATASTORE_TYPE=rdbms`. Platforms: PostgreSQL, MySQL, MariaDB, CockroachDB.

---

## Normal Forms Guide

| Normal Form | Requirement | When to Apply | When to Break |
|---|---|---|---|
| 1NF | Atomic values; no repeating groups | Always — non-negotiable | Never |
| 2NF | No partial dependency on composite PK | When using composite PKs | N/A for single-column PKs |
| 3NF | No transitive dependencies | Standard OLTP | Reporting tables (denormalize for query speed) |
| BCNF | Every determinant is a candidate key | High data integrity requirement | When it conflicts with required functional dependencies |

**Practical guidance**: model in 3NF for OLTP. Add denormalized read tables/materialized views for reporting.

---

## Primary Key Strategy

| Strategy | Type | Use Case | Risk |
|---|---|---|---|
| Sequential integer | `SERIAL` / `BIGINT GENERATED ALWAYS AS IDENTITY` | Internal IDs; most common | Sequential — predictable; hot insert page |
| UUID v4 | `UUID` | Distributed systems; external-facing IDs | Random — index fragmentation; larger size |
| UUID v7 | `UUID` (timestamp-ordered) | UUID with time ordering | Best of both: sortable + opaque |
| Natural key | Business key (e.g., email, code) | When it's truly unique and stable | Business keys change → cascading updates |
| Composite PK | Two+ columns | Junction/join tables | Complex FKs; avoid for entity tables |

---

## Index Design

### Index Selection Rules

1. **Equality conditions** in WHERE: single-column B-tree index (high selectivity only)
2. **Range conditions** in WHERE: B-tree index; put range column last in composite
3. **Multi-column WHERE**: composite index; column order = equality columns first, then range, then sort
4. **Full-text search**: GIN index on `tsvector` column (PostgreSQL)
5. **JSONB queries**: GIN index on the JSONB column; or expression index on specific path
6. **Spatial queries**: GiST index on `geometry` / PostGIS type
7. **Low-selectivity columns** (boolean, status with few values): partial index if filtering on one value

### Write Amplification Estimation

```
Each additional index on a table adds ~1 I/O per write operation to that table.
Table with 5 indexes: 6 I/Os per INSERT (1 table + 5 indexes)
High-write tables: minimize indexes; consider batch writes + fewer covering indexes
```

### Covering Index (Index-Only Scan)

```sql
-- All columns needed by the query are in the index → no heap access
CREATE INDEX idx_orders_covering ON orders (customer_id, status) INCLUDE (total_amount, created_at);
-- Query can be served entirely from the index if it only needs customer_id, status, total_amount, created_at
```

---

## Partitioning Strategy (PostgreSQL)

### When to Partition

- Table exceeds 100M rows, OR
- Query plans routinely show sequential scans that could be partition-pruned, OR
- Bulk deletes needed for old data (DROP PARTITION is instant; DELETE is slow)

### Partition Types

| Type | Use Case | Example |
|---|---|---|
| Range | Time-based data; monotonically increasing key | `PARTITION BY RANGE (created_at)` → monthly partitions |
| List | Fixed discrete values (country, status) | `PARTITION BY LIST (country_code)` |
| Hash | Even distribution when no natural partition key | `PARTITION BY HASH (user_id)` PARTITIONS 8 |

### Partition Key Rules

- **Do not partition on low-cardinality columns** with uneven distribution → hot partitions
- **Include partition key in every query** for partition pruning to work
- **Foreign keys to partitioned tables**: supported in PostgreSQL 12+; performance regression if not pruning

---

## Schema Evolution (RDBMS)

### Online DDL Tools

| Tool | Database | Mechanism | Notes |
|---|---|---|---|
| `pg_repack` | PostgreSQL | Rebuild table live using triggers | Requires `pg_repack` extension; no lock on table |
| `ALTER TABLE ... SET` | PostgreSQL 12+ | Some operations online; others lock | Check `lock_timeout` for short locks |
| `gh-ost` | MySQL/MariaDB | Binary log-based shadow table | No triggers; best choice for MySQL |
| `pt-online-schema-change` | MySQL/MariaDB | Trigger-based shadow table | Mature; avoid on tables with FKs |

### Safe Change Checklist

```
Before any DDL on a table with > 1M rows:
[ ] Test on a copy with production data volume
[ ] Run with lock_timeout = '5s' to avoid long blocking
[ ] Schedule during low-traffic window for operations that cannot be online
[ ] Have rollback plan (inverse DDL + data backfill)
[ ] Monitor replication lag after DDL — DDL may block replica apply
```

---

## Connection Pooling

```
PgBouncer modes:
  Session pooling: 1 backend connection per client session — use when client holds transactions open
  Transaction pooling: connection released after each transaction — most efficient; incompatible with prepared statements
  Statement pooling: connection released after each statement — most aggressive; limited compatibility

Sizing formula (PostgreSQL):
  max_connections (DB) = OS RAM / (connection overhead per connection)
  PostgreSQL connection overhead: ~5–10MB per connection
  PgBouncer pool_size: (max_connections - reserved_for_admin) / number_of_application_servers
```
