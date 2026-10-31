# Reference Index — researching-cache-store

Index of the official sources and documentation categories already named in this skill's
[SKILL.md](../../SKILL.md) and blueprints. It adds no new facts.

> **Status:** no per-vendor reference cards (`<vendor>-<version>.md`) exist in this folder yet.
> Create them from the [reference card template](../../../researching-platform-software/blueprints/shared/reference-card-template.md)
> (worked example: [reference-card-example-kafka-3.7.md](../../../researching-platform-software/blueprints/shared/reference-card-example-kafka-3.7.md)).

## Official Sources (from SKILL.md → External Resources)

> Entries are copied verbatim. SKILL.md records no fetch date for any of them, so each is
> **(unverified)** until a dated fetch is recorded in a vendor reference card.

| Cache | Primary Docs | K8s Operator | Release Notes | Status |
|---|---|---|---|---|
| Redis | redis.io/docs | Redis Operator (spotahome), Redis Enterprise Operator | github.com/redis/redis/releases | (unverified) |
| Memcached | memcached.org / github.com/memcached/memcached/wiki | Bitnami Helm chart | github.com/memcached/memcached/wiki/ReleaseNotes | (unverified) |
| KeyDB | docs.keydb.dev | Community Helm charts | github.com/Snapchat/KeyDB/releases | (unverified) |
| Dragonfly | dragonflydb.io/docs | Dragonfly Operator (dragonflydb/dragonfly-operator) | github.com/dragonflydb/dragonfly/releases | (unverified) |

## Documentation Categories

Categories this skill expects each vendor's docs to cover, taken from the headings of
[category-specifics.md](../category-specifics.md):

- Cache Patterns (Vendor-Neutral)
- TTL Discipline
- Eviction Policy Choice
- Cache Stampede Mitigation
- Neutral KPIs
- HA Considerations for Caches
- Universal Anti-Patterns (Caches)
- Ecosystem Adjacencies

## Shared Sources

- [output-format-base.md](../../../researching-platform-software/blueprints/shared/output-format-base.md) — output skeleton; every claim cites an official docs URL with a date
- [research-scope-operations.md](../../../researching-platform-software/blueprints/shared/research-scope-operations.md) — shared research scope §1–§12
- [deployment-guides/](../../../researching-platform-software/blueprints/shared/deployment-guides/) — per-`DEPLOYMENT_MODEL` playbooks
- [evaluation-scenarios.md](../evaluation-scenarios.md) — behavioral test cases for this skill
