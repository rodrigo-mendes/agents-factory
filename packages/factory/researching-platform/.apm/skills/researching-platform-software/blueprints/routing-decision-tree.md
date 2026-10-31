# Routing Decision Tree

Ordered lookup table used by `researching-platform-software` (orchestrator) to map a `<platform>` argument to the correct sibling skill. Matching is **case-insensitive** and strips vendor prefixes like `Apache `, `The `, `HashiCorp `.

---

## Direct Lookup (unambiguous platforms)

| Platform | Aliases | Sibling |
|---|---|---|
| Apache Kafka | kafka | `researching-streaming-broker` |
| RabbitMQ | rabbit, amqp | `researching-streaming-broker` |
| Apache Pulsar | pulsar | `researching-streaming-broker` |
| NATS | nats-server, jetstream | `researching-streaming-broker` |
| Apache ActiveMQ | activemq, artemis | `researching-streaming-broker` |
| Memcached | memcache | `researching-cache-store` |
| KeyDB | | `researching-cache-store` |
| Dragonfly | dragonflydb | `researching-cache-store` |
| etcd | | `researching-coordination-service` |
| Apache ZooKeeper | zookeeper, zk | `researching-coordination-service` |
| HashiCorp Consul | consul | `researching-coordination-service` |
| Elasticsearch | elastic, es | `researching-search-engine` |
| OpenSearch | | `researching-search-engine` |
| Apache Solr | solr | `researching-search-engine` |
| Typesense | | `researching-search-engine` |
| Meilisearch | | `researching-search-engine` |
| Kong Gateway | kong | `researching-api-gateway` |
| Apache APISIX | apisix | `researching-api-gateway` |
| Tyk | tyk-gateway | `researching-api-gateway` |
| Traefik Enterprise | traefik-ee, traefik-hub | `researching-api-gateway` |
| KrakenD | | `researching-api-gateway` |
| Envoy Gateway | envoy-gateway | `researching-api-gateway` |
| PostgreSQL | postgres, pg | `researching-rdbms` |
| MySQL | | `researching-rdbms` |
| MariaDB | | `researching-rdbms` |
| CockroachDB | cockroach | `researching-rdbms` |
| MongoDB | mongo | `researching-document-store` |
| Couchbase | | `researching-document-store` |
| RavenDB | | `researching-document-store` |
| RocksDB | | `researching-kv-store` |
| LMDB | | `researching-kv-store` |
| TiKV | | `researching-kv-store` |
| Apache Cassandra | cassandra | `researching-wide-column-store` |
| ScyllaDB | scylla | `researching-wide-column-store` |
| Apache HBase | hbase | `researching-wide-column-store` |
| Neo4j | | `researching-graph-database` |
| JanusGraph | | `researching-graph-database` |
| ArangoDB | arango | `researching-graph-database` |
| Nebula Graph | nebula | `researching-graph-database` |
| InfluxDB | influx | `researching-timeseries-db` |
| TimescaleDB | timescale | `researching-timeseries-db` |
| VictoriaMetrics | vm | `researching-timeseries-db` |
| QuestDB | | `researching-timeseries-db` |
| ClickHouse | | `researching-columnar-analytics` |
| Apache Druid | druid | `researching-columnar-analytics` |
| Apache Pinot | pinot | `researching-columnar-analytics` |
| DuckDB | | `researching-columnar-analytics` |
| Milvus | | `researching-vector-store` |
| Qdrant | | `researching-vector-store` |
| Weaviate | | `researching-vector-store` |
| Chroma | chromadb | `researching-vector-store` |
| pgvector | | `researching-vector-store` |
| MinIO | | `researching-object-storage` |
| Ceph RGW | ceph, rados-gateway | `researching-object-storage` |
| SeaweedFS | seaweed | `researching-object-storage` |
| GarageHQ | garage | `researching-object-storage` |

---

## Ambiguous Platforms (require disambiguation)

Ask the user which role the platform will play, then route.

### Redis

| Role | `datastore-type=` | Sibling |
|---|---|---|
| Ephemeral cache / session store | `cache` (default when in doubt) | `researching-cache-store` |
| Primary persistent key-value store (AOF+RDB, no eviction) | `kv` | `researching-kv-store` |
| Coordination / distributed locking (Redlock, Redisson) | `coordination-analog` | `researching-coordination-service` |

**Ask**: "Redis has three legitimate roles. Which are you deploying it for?
1. Cache / session store (data expected to be lost on eviction) → `researching-cache-store`
2. Primary datastore with persistence (data must not be lost) → `researching-kv-store`
3. Distributed coordination / locking → `researching-coordination-service`"

### Elasticsearch / OpenSearch

| Use | Sibling |
|---|---|
| Full-text search, log analytics, ILM | `researching-search-engine` (default) |
| Vector similarity search only (kNN via `dense_vector`) | Ask: consider `researching-vector-store` if that's the primary use case; but ES may still be the right choice for hybrid search |

### PostgreSQL

| Use | Sibling |
|---|---|
| Relational OLTP / hybrid workload | `researching-rdbms` (default) |
| Time-series with TimescaleDB extension | `researching-timeseries-db` |
| Vector store with pgvector extension | `researching-vector-store` |

If the user provides the extension explicitly ("PostgreSQL with pgvector"), route to the specialized sibling; otherwise default to `researching-rdbms` and note extensions available.

### Cassandra vs ScyllaDB naming clashes

Both map to `researching-wide-column-store`. No ambiguity — but the sibling's references cards separate them (different tuning parameters).

---

## No-Match Fallback

If a platform is not in the direct lookup or ambiguous list, respond with:

```
I could not identify the family for "{{PLATFORM_SOFTWARE}}". Available sibling skills:

  1. researching-streaming-broker       — messaging & event streaming
  2. researching-cache-store            — in-memory cache / session
  3. researching-coordination-service   — distributed coordination (etcd, ZK, Consul)
  4. researching-search-engine          — full-text search & log analytics
  5. researching-api-gateway            — API management & gateway
  6. researching-rdbms                  — relational / NewSQL
  7. researching-document-store         — document database
  8. researching-kv-store               — persistent key-value store
  9. researching-wide-column-store      — Cassandra-family
  10. researching-graph-database        — graph / knowledge graph
  11. researching-timeseries-db         — time-series data
  12. researching-columnar-analytics    — OLAP / analytics
  13. researching-vector-store          — vector / ANN
  14. researching-object-storage        — S3-compatible object storage

Top 2 candidates based on the platform name: [ candidate 1 ], [ candidate 2 ]
Which family fits, or is this a platform we should add to the routing table?
```

**Do NOT invent a route**. Missing entries in this table are a signal to update the table, not to guess.

---

## Update Procedure

To add a new platform to the routing table:

1. Confirm the platform's category by consulting the sibling's `category-specifics.md` — does it fit the family definition?
2. Add a row to the appropriate section above
3. Add a reference card at `.claude/skills/researching-<sibling>/blueprints/references/<platform>-<version>.md`
4. Update the sibling's `evaluation-scenarios.md` to include a scenario for the new platform (verifies routing + content correctness)
