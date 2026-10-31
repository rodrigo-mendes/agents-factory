# Reference Index — researching-timeseries-db

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
| InfluxDB | docs.influxdata.com | InfluxDB Helm charts | github.com/influxdata/influxdb/releases | (unverified) |
| TimescaleDB | docs.timescale.com | (PostgreSQL operators: CloudNativePG) | github.com/timescale/timescaledb/releases | (unverified) |
| VictoriaMetrics | docs.victoriametrics.com | VictoriaMetrics Operator | github.com/VictoriaMetrics/VictoriaMetrics/releases | (unverified) |
| QuestDB | questdb.io/docs | QuestDB Helm chart | github.com/questdb/questdb/releases | (unverified) |

## Documentation Categories

Categories this skill expects each vendor's docs to cover, taken from the headings of
[category-specifics.md](../category-specifics.md):

- Time-Series Model (Neutral)
- Cardinality Management (The Core Concern)
- Retention & Downsampling (Neutral)
- Chunk / Partition Sizing (Neutral)
- HA Topologies (Neutral)
- Neutral KPIs
- Universal Anti-Patterns
- §Data Modeling
- Ecosystem Adjacencies (neutral; names in reference cards)

Data-modeling categories, from [data-modeling.md](../data-modeling.md):

- Core Concepts
- Tag vs Field Design (InfluxDB / VictoriaMetrics)
- Series Cardinality Management
- Hypertable Design (TimescaleDB)
- Continuous Aggregates / Downsampling
- Time-Series Anti-Patterns

## Shared Sources

- [output-format-base.md](../../../researching-platform-software/blueprints/shared/output-format-base.md) — output skeleton; every claim cites an official docs URL with a date
- [research-scope-operations.md](../../../researching-platform-software/blueprints/shared/research-scope-operations.md) — shared research scope §1–§12
- [deployment-guides/](../../../researching-platform-software/blueprints/shared/deployment-guides/) — per-`DEPLOYMENT_MODEL` playbooks
- [evaluation-scenarios.md](../evaluation-scenarios.md) — behavioral test cases for this skill
