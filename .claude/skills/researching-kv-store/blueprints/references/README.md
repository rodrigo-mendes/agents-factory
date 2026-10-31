# Reference Index — researching-kv-store

Index of the official sources and documentation categories already named in this skill's
[SKILL.md](../../SKILL.md) and blueprints. It adds no new facts.

> **Status:** no per-vendor reference cards (`<vendor>-<version>.md`) exist in this folder yet.
> Create them from the [reference card template](../../../researching-platform-software/blueprints/shared/reference-card-template.md)
> (worked example: [reference-card-example-kafka-3.7.md](../../../researching-platform-software/blueprints/shared/reference-card-example-kafka-3.7.md)).

## Official Sources (from SKILL.md → External Resources)

> Entries are copied verbatim. SKILL.md records no fetch date for any of them, so each is
> **(unverified)** until a dated fetch is recorded in a vendor reference card.

| Engine | Primary Docs | K8s Operator | Release Notes | Status |
|---|---|---|---|---|
| Redis (as DB) | redis.io/docs | Redis Enterprise Operator, spotahome/redis-operator | github.com/redis/redis/releases | (unverified) |
| RocksDB | rocksdb.org / github.com/facebook/rocksdb/wiki | (embedded library — no operator) | github.com/facebook/rocksdb/releases | (unverified) |
| LMDB | lmdb.tech/doc | (embedded library — no operator) | git.openldap.org/openldap/openldap (liblmdb) | (unverified) |
| TiKV | tikv.org/docs | TiDB Operator | github.com/tikv/tikv/releases | (unverified) |

## Documentation Categories

Categories this skill expects each vendor's docs to cover, taken from the headings of
[category-specifics.md](../category-specifics.md):

- Cache vs Primary-Datastore Distinction
- Storage Engine Model (Neutral)
- Durability Modes (Neutral)
- HA Topologies (Neutral)
- Key Design (Neutral)
- Neutral KPIs
- Universal Anti-Patterns
- §Data Modeling
- Ecosystem Adjacencies (neutral; names in reference cards)

Data-modeling categories, from [data-modeling.md](../data-modeling.md):

- Key Design Principles
- Value Structure Selection
- TTL Strategy (Primary Datastore)
- Access-Pattern-First Design
- Secondary Index Patterns
- KV Data Modeling Anti-Patterns

## Shared Sources

- [output-format-base.md](../../../researching-platform-software/blueprints/shared/output-format-base.md) — output skeleton; every claim cites an official docs URL with a date
- [research-scope-operations.md](../../../researching-platform-software/blueprints/shared/research-scope-operations.md) — shared research scope §1–§12
- [deployment-guides/](../../../researching-platform-software/blueprints/shared/deployment-guides/) — per-`DEPLOYMENT_MODEL` playbooks
- [evaluation-scenarios.md](../evaluation-scenarios.md) — behavioral test cases for this skill
