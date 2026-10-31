# Reference Index — researching-search-engine

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
| Elasticsearch | elastic.co/guide/en/elasticsearch | ECK: elastic.co/guide/en/cloud-on-k8s | elastic.co/guide/en/elasticsearch/reference/current/release-notes | (unverified) |
| OpenSearch | opensearch.org/docs | OpenSearch K8s Operator (opensearch-project) | opensearch.org/versions | (unverified) |
| Apache Solr | solr.apache.org/guide | SolrCloud on K8s (Solr Operator) | solr.apache.org/downloads.html | (unverified) |
| Typesense | typesense.org/docs | Community Helm charts | github.com/typesense/typesense/releases | (unverified) |
| Meilisearch | meilisearch.com/docs | meilisearch/meilisearch-kubernetes | github.com/meilisearch/meilisearch/releases | (unverified) |

## Documentation Categories

Categories this skill expects each vendor's docs to cover, taken from the headings of
[category-specifics.md](../category-specifics.md):

- Inverted Index Model (Vendor-Neutral)
- Text vs Exact-Match Field Design
- Shard Sizing (Neutral Principles)
- Index Lifecycle Management
- Zero-Downtime Reindex Pattern
- Query Performance Patterns
- Node Roles (for clustered engines)
- Neutral KPIs
- Universal Anti-Patterns
- §Data Modeling for Search Engines
- Ecosystem Adjacencies

## Shared Sources

- [output-format-base.md](../../../researching-platform-software/blueprints/shared/output-format-base.md) — output skeleton; every claim cites an official docs URL with a date
- [research-scope-operations.md](../../../researching-platform-software/blueprints/shared/research-scope-operations.md) — shared research scope §1–§12
- [deployment-guides/](../../../researching-platform-software/blueprints/shared/deployment-guides/) — per-`DEPLOYMENT_MODEL` playbooks
- [evaluation-scenarios.md](../evaluation-scenarios.md) — behavioral test cases for this skill
