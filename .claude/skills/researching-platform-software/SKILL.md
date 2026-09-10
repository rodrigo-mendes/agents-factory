---
name: researching-platform-software
description: "Entry-point that routes platform research requests to the correct specialized sibling skill (researching-streaming-broker, researching-rdbms, researching-document-store, researching-api-gateway, etc.). Use when unsure which sibling covers a specific platform, when you want to invoke platform research by platform name only, or when the platform's category is ambiguous (e.g. Redis can be cache / kv-store / coordination)."
argument-hint: "<platform> <version> [datastore-type=rdbms|document|kv|wide-column|graph|time-series|columnar|vector|object] [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. Kafka 3.7 / MongoDB 7.0 / Kong 3.7 / Redis 7.2 datastore-type=kv)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Platform Software Research — Router / Orchestrator

## Purpose

This skill is a **thin router**: it identifies the correct specialized sibling skill for the requested platform and delegates the actual research to it. It contains **no research logic** of its own — all research templates, output formats, and category-specific patterns live in the sibling skills and in `.claude/templates/platform-research/`.

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: specific platform name — e.g., "Apache Kafka", "MongoDB", "Redis", "Kong", "PostgreSQL"
- `TARGET_VERSION`: semver of the stable release — e.g., "3.7", "7.0", "16"
- `DATASTORE_TYPE` *(disambiguator)*: only needed when the platform can play multiple roles (e.g., Redis: `cache` vs `kv` vs `coordination-analog`)
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: passed through unchanged to the resolved sibling

## Routing Algorithm

1. **Parse** the `<platform>` argument (case-insensitive; strip vendor prefixes like "Apache " when matching).
2. **Consult** [routing-decision-tree.md](./blueprints/routing-decision-tree.md) — an ordered lookup table `platform → sibling`.
3. **Resolve**:
   - **Unique match** → invoke `Skill({ skill: "researching-<sibling>", args: "<passthrough>" })` immediately. Do not produce research output in this skill.
   - **Ambiguous match** (e.g., Redis) → ask the user which role the platform will play; then route to the corresponding sibling.
   - **No match** → do NOT guess. Reply with the 14 sibling names, brief descriptions, and the top 2 candidates most likely to fit.
4. **Passthrough** every additional argument (`deployment=`, `depth=`, `iterations=`) unchanged to the sibling.

## Sibling Skills — Family Map

| Sibling | Family | Representative Platforms |
|---|---|---|
| [researching-streaming-broker](../researching-streaming-broker/SKILL.md) | Streaming & messaging | Apache Kafka, RabbitMQ, Apache Pulsar, NATS, ActiveMQ |
| [researching-cache-store](../researching-cache-store/SKILL.md) | In-memory cache / session | Redis (as cache), Memcached, KeyDB, Dragonfly |
| [researching-coordination-service](../researching-coordination-service/SKILL.md) | Distributed coordination | etcd, Apache ZooKeeper, HashiCorp Consul |
| [researching-search-engine](../researching-search-engine/SKILL.md) | Full-text / analytics search | Elasticsearch, OpenSearch, Solr, Typesense, Meilisearch |
| [researching-api-gateway](../researching-api-gateway/SKILL.md) | API management / gateway | Kong, APISIX, Tyk, Traefik EE, KrakenD, Envoy Gateway |
| [researching-rdbms](../researching-rdbms/SKILL.md) | Relational / NewSQL | PostgreSQL, MySQL, MariaDB, CockroachDB |
| [researching-document-store](../researching-document-store/SKILL.md) | Document database | MongoDB, Couchbase, RavenDB |
| [researching-kv-store](../researching-kv-store/SKILL.md) | Persistent key-value store | Redis (as primary DB), RocksDB, LMDB, TiKV |
| [researching-wide-column-store](../researching-wide-column-store/SKILL.md) | Wide-column database | Apache Cassandra, ScyllaDB, HBase |
| [researching-graph-database](../researching-graph-database/SKILL.md) | Graph database | Neo4j, JanusGraph, ArangoDB, Nebula Graph |
| [researching-timeseries-db](../researching-timeseries-db/SKILL.md) | Time-series database | InfluxDB, TimescaleDB, VictoriaMetrics, QuestDB |
| [researching-columnar-analytics](../researching-columnar-analytics/SKILL.md) | Columnar OLAP | ClickHouse, Apache Druid, Apache Pinot, DuckDB |
| [researching-vector-store](../researching-vector-store/SKILL.md) | Vector / ANN | Milvus, Qdrant, Weaviate, pgvector, Chroma |
| [researching-object-storage](../researching-object-storage/SKILL.md) | S3-compatible object storage | MinIO, Ceph RGW, SeaweedFS, GarageHQ |

## Shared assets (reused by all siblings)

Located in `.claude/templates/platform-research/`:

- [output-format-base.md](../../templates/platform-research/output-format-base.md) — 13-section neutral output template
- [research-scope-operations.md](../../templates/platform-research/research-scope-operations.md) — §1–§12 operational research scope common to all families
- [data-modeling-principles.md](../../templates/platform-research/data-modeling-principles.md) — cross-type modeling principles (siblings of datastore families import this)
- [deployment-guides/](../../templates/platform-research/deployment-guides/) — kubernetes-operator, container-compose, vm-and-bare-metal playbooks

## Blueprints & Guardrails

### ✅ Always Do

- **Always route — never research inline.** This skill's only output is the routing decision or the resolved sibling invocation. Do not populate research sections here.
- **Preserve arguments verbatim** when forwarding to the sibling — no reformatting, no defaults injection beyond what the sibling schema requires.
- **Log the routing decision** in the first line of the response (`Routing "<platform> <version>" → researching-<sibling>`).

### ⚠️ Ask First

- **Ambiguous platform** — Redis is the canonical case (`cache-store` vs `kv-store` vs `coordination-analog`); also PostgreSQL when someone asks "PostgreSQL as vector store" (route to `researching-vector-store` if they mean pgvector, else `researching-rdbms`).
- **Category-crossing platform** — e.g., Elasticsearch used as a document store (route to `researching-search-engine` regardless; note the trade-off).
- **Unknown platform not in decision tree** — do not invent a sibling; ask which sibling family fits best based on the two closest candidates.

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Produce research content in this skill's output | Duplicates sibling logic; creates two sources of truth per platform | Route only; delegate all content to sibling |
| Guess a sibling when the platform is unknown | Anti-hallucination: guessing binds the wrong template to the platform | Return the sibling list and top 2 candidates; ask the user |
| Route Redis to a single sibling without disambiguation | Redis has 3 legitimate roles; wrong template = wrong operational guidance | Always ask which role when the user says "Redis" without `datastore-type=` |
| Bypass the decision tree with heuristic matching | Untraceable routing = untestable routing | Every routing decision must trace to a rule in routing-decision-tree.md |

## Verification

```bash
# Confirm the routing table is present and non-empty
test -s .claude/skills/researching-platform-software/blueprints/routing-decision-tree.md && echo OK

# Confirm all 14 sibling skills exist
for f in streaming-broker cache-store coordination-service search-engine api-gateway \
         rdbms document-store kv-store wide-column-store graph-database \
         timeseries-db columnar-analytics vector-store object-storage; do
  test -f ".claude/skills/researching-$f/SKILL.md" || echo "MISSING: researching-$f"
done
```

## Related Skills

- [cloud-architecture-researcher](../cloud-architecture-researcher/SKILL.md) — for the **managed** cloud equivalent (RDS, MSK, DocumentDB) — different lens: managed by the provider, not by the team
- [researching-technical-frameworks](../researching-technical-frameworks/SKILL.md) — for **client SDKs** (pymongo, kafka-python, jedis) — different concern: how to call the platform from application code
