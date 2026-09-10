# Platform Software Research Family

> **Subagent:** `framework-researcher` (with `research-synthesizer` + `section-investigator` helpers) | **Context:** fork | **Model invocation:** disabled
> **Family size:** 15 commands — 1 orchestrator + 14 specialized siblings

A family of research commands for **self-managed platform software** — the storage engines,
messaging brokers, caches, coordination services, search engines, and API gateways that a team
**installs and operates itself** (not the managed cloud equivalents).

---

## When to Use This Family

Use when researching a platform the team runs on its own infrastructure (bare-metal, VM, container,
or Kubernetes) and needs operational depth: installation, HA topology, backup/restore, upgrade,
hardening, observability, and (for data stores) data modeling.

**Distinction from neighboring skills:**

| Skill | Lens | Example |
|-------|------|---------|
| **platform-software family** | Self-managed — the team installs and operates it | "Deploy and operate our own Kafka 3.7 cluster" |
| [`cloud-architecture-researcher`](framework-researcher.md#cloud-architecture-researcher) | Managed cloud service — the provider operates it | "Use Amazon MSK / Amazon RDS" |
| [`researching-technical-frameworks`](framework-researcher.md#researching-technical-frameworks) | Client SDK — how application code calls the platform | "Use the `kafka-python` / `pymongo` client library" |

---

## Two-Level Routing Pattern

```
/researching-platform-software <platform> <version>
        │  (orchestrator — resolves the family via routing-decision-tree.md)
        ↓
/researching-<sibling> <platform> <version>          ← or call the sibling directly
        │  (context: fork)
        ↓
framework-researcher                                  ← the research engine (P0–P5)
        │
        ├─ section-investigator   (parallel sub-investigation, depth=deep/exhaustive)
        └─ research-synthesizer   (merges findings into output-format-base.md)
        ↓
StoryBeat/docs/research_platform_<Platform>_v<Version>.md
```

- **Orchestrator** (`researching-platform-software`): identifies the platform, consults
  `blueprints/routing-decision-tree.md`, and delegates to the correct sibling. It produces **no
  research of its own** — routing only.
- **Direct call**: if you already know the family, call the sibling directly
  (`/researching-streaming-broker Kafka 3.7`).

---

## The 14 Sibling Skills

| Sibling | Family | Representative platforms | Conditional output section |
|---------|--------|--------------------------|-----------------------------|
| `researching-streaming-broker` | Streaming & messaging | Apache Kafka, RabbitMQ, Apache Pulsar, NATS, ActiveMQ | K8s |
| `researching-cache-store` | In-memory cache / session | Redis (as cache), Memcached, KeyDB, Dragonfly | K8s |
| `researching-coordination-service` | Distributed coordination | etcd, Apache ZooKeeper, HashiCorp Consul | K8s |
| `researching-search-engine` | Full-text / analytics search | Elasticsearch, OpenSearch, Solr, Typesense, Meilisearch | K8s + Data Modeling |
| `researching-api-gateway` | API management / gateway | Kong, APISIX, Tyk, Traefik EE, KrakenD, Envoy Gateway | K8s + API Management |
| `researching-rdbms` | Relational / NewSQL | PostgreSQL, MySQL, MariaDB, CockroachDB | K8s + Data Modeling |
| `researching-document-store` | Document database | MongoDB, Couchbase, RavenDB | K8s + Data Modeling |
| `researching-kv-store` | Persistent key-value store | Redis (as DB), RocksDB, LMDB, TiKV | K8s + Data Modeling |
| `researching-wide-column-store` | Wide-column database | Apache Cassandra, ScyllaDB, HBase | K8s + Data Modeling |
| `researching-graph-database` | Graph database | Neo4j, JanusGraph, ArangoDB, Nebula Graph | K8s + Data Modeling |
| `researching-timeseries-db` | Time-series database | InfluxDB, TimescaleDB, VictoriaMetrics, QuestDB | K8s + Data Modeling |
| `researching-columnar-analytics` | Columnar OLAP | ClickHouse, Apache Druid, Apache Pinot, DuckDB | K8s + Data Modeling |
| `researching-vector-store` | Vector / ANN | Milvus, Qdrant, Weaviate, pgvector, Chroma | K8s + Data Modeling |
| `researching-object-storage` | S3-compatible object storage | MinIO, Ceph RGW, SeaweedFS, GarageHQ | K8s + Data Modeling |

---

## Orchestrator Resolution Rules

The orchestrator (`researching-platform-software`) follows
`.claude/skills/researching-platform-software/blueprints/routing-decision-tree.md`:

- **Unique match** → routes to the sibling immediately (case-insensitive; strips vendor prefixes
  like `Apache `, `HashiCorp `).
- **Ambiguous platform** → asks before routing. The canonical case is **Redis**:
  - Cache / session store (data loss on eviction OK) → `researching-cache-store`
  - Primary persistent datastore (must not lose data) → `researching-kv-store`
  - Distributed locking / coordination → `researching-coordination-service`
  - Also: **PostgreSQL + extension** → `researching-timeseries-db` (TimescaleDB) or
    `researching-vector-store` (pgvector), else `researching-rdbms`.
- **Unknown platform** → does NOT guess; returns the 14 sibling names + the two closest candidates
  and asks the user (or proposes adding a row to the routing table).

---

## Shared Assets — `.claude/templates/platform-research/`

Every sibling reuses these shared templates (Claude Code-exclusive; no `.github/` mirror):

| Asset | Purpose |
|-------|---------|
| `output-format-base.md` | The 13-section neutral output skeleton every research file follows |
| `research-scope-operations.md` | §1–§12 operational research scope common to all families |
| `data-modeling-principles.md` | Cross-type modeling principles (datastore siblings import this) |
| `reference-card-template.md` | Canonical skeleton for a per-vendor, version-pinned reference card |
| `reference-card-example-kafka-3.7.md` | A fully-worked instance of the reference-card template |
| `deployment-guides/` | `kubernetes-operator-guide.md`, `container-compose-guide.md`, `vm-and-bare-metal-guide.md` |

**Anti-bias design.** Each sibling separates:
- `blueprints/category-specifics.md` — **vendor-neutral** patterns shared by the whole family
  (uses `{{PLATFORM_SOFTWARE}}` and generic terms), and
- `blueprints/references/<vendor>-<version>.md` — **vendor-specific pinned facts** (exact config
  keys, CLI, YAML), each produced from `reference-card-template.md`.

This keeps research for, say, APISIX from being contaminated by Kong-specific assumptions.

---

## Inputs

| Field | Required | Example |
|-------|:--------:|---------|
| Platform name | ✅ | `Apache Kafka`, `MongoDB`, `Redis`, `Kong` |
| Specific version | ✅ | `3.7`, `7.0`, `7.2`, `16` |
| `datastore-type` (Redis disambiguator) | when ambiguous | `cache` \| `kv` \| `coordination` |
| `deployment` | optional | `bare-metal` \| `vm` \| `container-compose` \| `kubernetes-operator` \| `hybrid` |
| `depth` / `iterations` | optional | `exhaustive` (default) / `5` |

> **Version Absolutism:** "Kafka" is not sufficient — provide "Kafka 3.7". The version is pinned in
> the output filename and in the reference card name.

---

## Call Examples

```
# Auto-route through the orchestrator
/researching-platform-software Kafka 3.7

# Ambiguous — orchestrator asks cache/kv/coordination
/researching-platform-software Redis 7.2

# Call a sibling directly
/researching-document-store MongoDB 7.0 deployment=kubernetes-operator

# API gateway with the API-management conditional section
/researching-api-gateway Kong 3.7 deployment=kubernetes-operator
```

---

## Output Produced

```
StoryBeat/docs/research_platform_<Platform>_v<Version>.md
```

13 mandatory sections (from `output-format-base.md`) plus conditional sections when triggered:
**§Kubernetes Deployment Blueprint** (`deployment=kubernetes-operator`), **§API Management
Specifics** (`researching-api-gateway`), **§Data Modeling** (datastore families).

### Post-Research Verification

```bash
grep -E "^## (Executive Summary|Platform Glossary|Operational Guardrails|Installation|Configuration Reference|HA & Failover|Backup|Upgrade|Observability|Security Hardening|Failure Modes)" \
  StoryBeat/docs/research_platform_*.md
grep -c "references/" StoryBeat/docs/research_platform_*.md   # cites the vendor reference card
```

---

## Next Steps

- Turn a platform research file into an operational skill → `/skill-creator StoryBeat/docs/research_platform_<Platform>_v<Version>.md`
- Evaluate a sibling's behavior (cross-vendor, anti-bias) → `/evaluating-skill-scenarios researching-api-gateway`

---

*See [manual README](README.md) for general navigation, and
[framework-researcher](framework-researcher.md) for the other research commands.*
