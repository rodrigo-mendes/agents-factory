# Quarkus Logging Integration

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Backend

Camel and the Log EIP write through SLF4J. Quarkus adapts SLF4J to JBoss LogManager, so levels and formats use `quarkus.log.*`. Source: https://quarkus.io/guides/logging (medium confidence, unversioned "Latest" guide)

## Levels (medium confidence: read on the unversioned "Latest" guide)

- `quarkus.log.level` defaults to `INFO`; per-category config is `quarkus.log.category."<name>".level` (quotes required, default `INFO`).
- `quarkus.log.min-level` defaults to `DEBUG` and is build-time. See [never-do 5](./never-do-patterns.md#5-runtime-trace-below-min-level-severity-moderate).
- The `log:` path is the category, so `log:com.acme.orders` is controlled by `quarkus.log.category."com.acme.orders".level`.

Source: https://quarkus.io/guides/logging (the research notes the 3.40 selector exists but did not record reading these values there: value page not recorded for 3.40)

## Text versus JSON (medium confidence: JSON claims from the Quarkus 3.40 guide, coverage of the page not recorded)

| Option | Optimizes | Sacrifices |
|---|---|---|
| Text pattern with `%X{...}` (default pattern `%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n`) | Readability | Parseability |
| `quarkus-logging-json` (`log-format` = `default`, `ecs` or `gcp`) | Aggregation; MDC as `mdc` object or root fields (`mdc.flat-fields`, default `false`) | Format and colour settings are ignored; `pretty-print` (default `false`) breaks some parsers |

`print-details` in JSON is described as "costly" (reads caller info). Disable JSON in dev and test:

```properties
%dev.quarkus.log.console.json.enabled=false
%test.quarkus.log.console.json.enabled=false
quarkus.log.console.json.log-format=ecs
```

Sources: https://quarkus.io/guides/logging ; https://quarkus.io/version/3.40/guides/logging

## Production starter

```properties
camel.main.logMask=true
quarkus.camel.mdc.enabled=true
quarkus.log.category."org.apache.camel".level=WARN
quarkus.log.category."com.acme".level=INFO
```

`camel.main.logMask` here is (medium confidence) in Camel Quarkus; also set `logMask=true` on the sensitive URIs.
