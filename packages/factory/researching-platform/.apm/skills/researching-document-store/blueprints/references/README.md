# Reference Index — researching-document-store

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
| MongoDB | mongodb.com/docs | Percona Operator for MongoDB, MongoDB Community/Enterprise Operator | mongodb.com/docs/manual/release-notes | (unverified) |
| Couchbase | docs.couchbase.com | Couchbase Autonomous Operator | docs.couchbase.com/server/current/release-notes | (unverified) |
| RavenDB | ravendb.net/docs | RavenDB Helm chart | ravendb.net/docs/article-page/latest/csharp/start/whats-new | (unverified) |

## Documentation Categories

Categories this skill expects each vendor's docs to cover, taken from the headings of
[category-specifics.md](../category-specifics.md):

- Document Model (Neutral)
- Durability & Consistency (Neutral)
- HA Topologies (Neutral)
- Sharding Key Selection (Neutral)
- Neutral KPIs
- Universal Anti-Patterns
- §Data Modeling
- Ecosystem Adjacencies (neutral; names in reference cards)

Data-modeling categories, from [data-modeling.md](../data-modeling.md):

- Fundamental Rule: Model for Your Access Patterns
- Embedding vs Referencing Decision Tree
- Embedding Patterns
- Referencing Patterns
- Index Design (MongoDB)
- Schema Validation
- Schema Versioning for Documents

## Shared Sources

- [output-format-base.md](../../../researching-platform-software/blueprints/shared/output-format-base.md) — output skeleton; every claim cites an official docs URL with a date
- [research-scope-operations.md](../../../researching-platform-software/blueprints/shared/research-scope-operations.md) — shared research scope §1–§12
- [deployment-guides/](../../../researching-platform-software/blueprints/shared/deployment-guides/) — per-`DEPLOYMENT_MODEL` playbooks
- [evaluation-scenarios.md](../evaluation-scenarios.md) — behavioral test cases for this skill
