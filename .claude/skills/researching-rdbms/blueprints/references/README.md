# Reference Index — researching-rdbms

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
| PostgreSQL | postgresql.org/docs | CloudNativePG, Crunchy Postgres Operator | postgresql.org/docs/release | (unverified) |
| MySQL | dev.mysql.com/doc | Percona XtraDB Cluster Operator, MySQL Operator (Oracle) | dev.mysql.com/doc/relnotes | (unverified) |
| MariaDB | mariadb.com/kb/en/documentation | mariadb-operator | mariadb.com/kb/en/release-notes | (unverified) |
| CockroachDB | cockroachlabs.com/docs | CockroachDB Operator | cockroachlabs.com/docs/releases | (unverified) |

## Documentation Categories

Categories this skill expects each vendor's docs to cover, taken from the headings of
[category-specifics.md](../category-specifics.md):

- Storage & Concurrency Model (Neutral)
- Isolation Level Decision (Neutral)
- HA & Replication (Neutral Topologies)
- Connection Pooling (Neutral)
- Indexing (Neutral Principles)
- Partitioning (Neutral)
- Neutral KPIs
- Universal Anti-Patterns
- Ecosystem Adjacencies (neutral; names in reference cards)

Data-modeling categories, from [data-modeling.md](../data-modeling.md):

- Normal Forms Guide
- Primary Key Strategy
- Index Design
- Partitioning Strategy (PostgreSQL)
- Schema Evolution (RDBMS)
- Connection Pooling

## Shared Sources

- [output-format-base.md](../../../researching-platform-software/blueprints/shared/output-format-base.md) — output skeleton; every claim cites an official docs URL with a date
- [research-scope-operations.md](../../../researching-platform-software/blueprints/shared/research-scope-operations.md) — shared research scope §1–§12
- [deployment-guides/](../../../researching-platform-software/blueprints/shared/deployment-guides/) — per-`DEPLOYMENT_MODEL` playbooks
- [evaluation-scenarios.md](../evaluation-scenarios.md) — behavioral test cases for this skill
