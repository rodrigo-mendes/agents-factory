# Platform software commands

Fifteen commands research self-hosted platforms: databases, brokers, gateways, caches and search.
Each one covers a single datastore family, and they all share the same deployment options.

If you do not know which family your platform belongs to, start with the orchestrator
`/researching-platform-software`. It picks the right sibling for you.

## Which command?

| Your platform | Command |
|---|---|
| Not sure | [`/researching-platform-software`](../../packages/factory/researching-platform/README.md#researching-platform-software) (orchestrator, routes for you) |
| PostgreSQL, MySQL, MariaDB (relational) | [`/researching-rdbms`](../../packages/factory/researching-platform/README.md#researching-rdbms) |
| MongoDB and other document stores | [`/researching-document-store`](../../packages/factory/researching-platform/README.md#researching-document-store) |
| Key-value stores (for example Redis as a store, TiKV) | [`/researching-kv-store`](../../packages/factory/researching-platform/README.md#researching-kv-store) |
| Caches (for example Redis or Memcached as a cache) | [`/researching-cache-store`](../../packages/factory/researching-platform/README.md#researching-cache-store) |
| Cassandra, ScyllaDB (wide-column) | [`/researching-wide-column-store`](../../packages/factory/researching-platform/README.md#researching-wide-column-store) |
| Neo4j and other graph databases | [`/researching-graph-database`](../../packages/factory/researching-platform/README.md#researching-graph-database) |
| InfluxDB, TimescaleDB (time series) | [`/researching-timeseries-db`](../../packages/factory/researching-platform/README.md#researching-timeseries-db) |
| ClickHouse and other columnar analytics | [`/researching-columnar-analytics`](../../packages/factory/researching-platform/README.md#researching-columnar-analytics) |
| Qdrant, Milvus (vector stores) | [`/researching-vector-store`](../../packages/factory/researching-platform/README.md#researching-vector-store) |
| Elasticsearch and other search engines | [`/researching-search-engine`](../../packages/factory/researching-platform/README.md#researching-search-engine) |
| Kafka and other streaming brokers | [`/researching-streaming-broker`](../../packages/factory/researching-platform/README.md#researching-streaming-broker) |
| MinIO and other object storage | [`/researching-object-storage`](../../packages/factory/researching-platform/README.md#researching-object-storage) |
| Kong, APISIX and other API gateways | [`/researching-api-gateway`](../../packages/factory/researching-platform/README.md#researching-api-gateway) |
| etcd, ZooKeeper (coordination) | [`/researching-coordination-service`](../../packages/factory/researching-platform/README.md#researching-coordination-service) |

Some platforms appear in more than one family. Redis, for example, can be a key-value store or a
cache. Pick the one that matches the question you are asking.

## Arguments

Every sibling takes the same pattern:

```
/<command> <platform> <version> [deployment=<mode>] [depth=<level>] [iterations=<n>]
```

| Argument | Values |
|---|---|
| `deployment` | `bare-metal`, `vm`, `container-compose`, `kubernetes-operator`, `hybrid` |
| `depth` | `standard`, `deep`, `exhaustive` (default) |
| `iterations` | Number of research passes. Default 5. |

The orchestrator also takes `datastore-type=` (for example `kv`, `document`, `vector`) to force a
family.

## Examples

Route automatically:

```
/researching-platform-software Kafka 3.7
```

Pick the family yourself, with a deployment mode:

```
/researching-document-store MongoDB 7.0 deployment=kubernetes-operator depth=deep iterations=3
```

Two different families for the same name:

```
/researching-kv-store Redis 7.2 deployment=vm
/researching-cache-store Redis 7.2 deployment=vm
```

## What you get

Each run produces a research file for the platform. Families that have modeling guidance also get
it in the file. The Kafka package in this repository is an example of the kind of output a
platform research can lead to: [`kafka`](../../packages/data-platform/streaming/kafka/README.md).

## Common mistakes

- Using a version that is too old. Research pins the version you give, so use the version you run.
- Leaving out `deployment=`. The result then covers all modes, which is longer and less precise.

## Related

- Package: [`researching-platform`](../../packages/factory/researching-platform/README.md).
- Agent: `framework-researcher` ([subagents](../agents/README.md)).
- Next step: [`/skill-creator`](factory-authoring.md) turns the research into a skill.
