# Data Modeling — Index

Index of the existing data-modeling guidance. The research output's **Data Modeling** section
(see [output-format-base.md](../output-format-base.md)) is included when `PLATFORM_CATEGORY=datastore`;
pick the file matching `DATASTORE_TYPE` below.

## Shared Principles

- [data-modeling-principles.md](../data-modeling-principles.md) — cross-type principles (access-pattern-first)

## Per-Type Guidance (sibling skills)

| DATASTORE_TYPE sibling | Data-modeling file |
|---|---|
| columnar-analytics | [researching-columnar-analytics/blueprints/data-modeling.md](../../../../researching-columnar-analytics/blueprints/data-modeling.md) |
| document-store | [researching-document-store/blueprints/data-modeling.md](../../../../researching-document-store/blueprints/data-modeling.md) |
| graph-database | [researching-graph-database/blueprints/data-modeling.md](../../../../researching-graph-database/blueprints/data-modeling.md) |
| kv-store | [researching-kv-store/blueprints/data-modeling.md](../../../../researching-kv-store/blueprints/data-modeling.md) |
| object-storage | [researching-object-storage/blueprints/data-modeling.md](../../../../researching-object-storage/blueprints/data-modeling.md) |
| rdbms | [researching-rdbms/blueprints/data-modeling.md](../../../../researching-rdbms/blueprints/data-modeling.md) |
| timeseries-db | [researching-timeseries-db/blueprints/data-modeling.md](../../../../researching-timeseries-db/blueprints/data-modeling.md) |
| vector-store | [researching-vector-store/blueprints/data-modeling.md](../../../../researching-vector-store/blueprints/data-modeling.md) |
| wide-column-store | [researching-wide-column-store/blueprints/data-modeling.md](../../../../researching-wide-column-store/blueprints/data-modeling.md) |

> No `data-modeling.md` exists for the non-datastore siblings (api-gateway, cache-store,
> coordination-service, search-engine, streaming-broker). researching-search-engine keeps its
> modeling guidance inside [category-specifics.md](../../../../researching-search-engine/blueprints/category-specifics.md)
> (section "§Data Modeling for Search Engines").
