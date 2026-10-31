# MDC Correlation with camel-quarkus-mdc

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Setup (high confidence)

- Dependency: `org.apache.camel.quarkus:camel-quarkus-mdc`, version from the BOM. Available in JVM and native since Camel Quarkus 3.29.0. Camel's own `camel-mdc` exists since Camel 4.15.
- Properties: `quarkus.camel.mdc.enabled` (default `false`), `quarkus.camel.mdc.custom-exchange-headers`, `quarkus.camel.mdc.custom-exchange-properties` (`*` wildcard).
- Default keys, each included only if present: `camel.breadcrumbId`, `camel.exchangeId`, `camel.messageId`, `camel.correlationId`, `camel.routeId`, `camel.contextId`, `camel.threadId`.
- `camel.breadcrumbId` needs `camel.main.useBreadcrumb=true` (default `false`).
- Do not combine with the deprecated `camel.main.useMdcLogging` / `setUseMDCLogging(true)`.

```properties
quarkus.camel.mdc.enabled=true
quarkus.camel.mdc.custom-exchange-headers=X-Correlation-Id
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html ; https://camel.apache.org/components/4.22.x/others/mdc.html ; https://camel.apache.org/components/4.22.x/others/main.html

## Rendering the MDC in Quarkus log output

Console format pattern with `%X{...}` (medium confidence, read on the unversioned "Latest" guide):

```properties
# Text console
quarkus.log.console.format=%d{HH:mm:ss,SSS} %-5p [%c] (%t) [%X{camel.exchangeId}] %s%e%n
```

For JSON output the MDC appears as an `mdc` object, or as root fields when `mdc.flat-fields` is enabled (default `false`) (medium confidence, JSON claims from the Quarkus 3.40 guide, coverage not recorded). See [Quarkus logging](./quarkus-logging.md).

Sources: https://quarkus.io/guides/logging ; https://quarkus.io/version/3.40/guides/logging

## Key set versus the legacy manual page

(medium confidence: the legacy page is unversioned.) The legacy manual page lists `camel.stepId` and `camel.transactionKey`; the new default set does not list them. Re-check dashboards that rely on them. Source: https://camel.apache.org/manual/mdc.html (marked deprecated).

## Not confirmed

- Which `quarkus.camel.mdc.*` properties are fixed at build time: (unverified) (the fetched page text had no per-property marking; register U8, not resolvable from documentation). Set `quarkus.camel.mdc.enabled` in `application.properties` at build time rather than overriding it at runtime.
- How camel-mdc interplays with Quarkus Vert.x MDC propagation on Camel async threads: (unverified). Quarkus itself keeps MDC across Vert.x duplicated contexts, `ManagedExecutor` and `executeBlocking` (medium confidence, Quarkus 3.40 guide coverage not recorded: https://quarkus.io/version/3.40/guides/logging).

See the [register](./unverified-and-risks.md).
