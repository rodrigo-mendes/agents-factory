# Migration Guide: 3.15 conventions to 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). "3.15" appears here only as the migration baseline. Generic 3.x migration steps belong to the core skill.

## Changes (high confidence unless tagged)

- **MDC**: `camel.main.useMdcLogging` and `camel.main.mdcLoggingKeysPattern` are deprecated. Use `camel-quarkus-mdc` (since Camel Quarkus 3.29.0; `camel-mdc` since Camel 4.15). Sources: https://camel.apache.org/components/4.22.x/others/main.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html
- **MDC keys** (medium confidence, unversioned legacy page): the default set includes `camel.threadId`. The legacy list had `camel.stepId` and `camel.transactionKey`, which the new set does not list; re-check dashboards. Sources: https://camel.apache.org/manual/mdc.html ; https://camel.apache.org/components/4.22.x/others/mdc.html
- **Masking**: URI-password and PEM-key masking is documented on the 4.22.x Log EIP page (no earlier-version comparison was made). Source: https://camel.apache.org/components/4.22.x/eips/log-eip.html
- **Option catalog** has grown: `showVariables`, `showRouteId`, `showRouteGroup`, `showCachedStreams`, `sourceLocationLoggerName`, `plain`, `style`. Source: https://camel.apache.org/components/4.22.x/log-component.html
- No log-specific entries were found in the per-version Camel Quarkus migration guides; this run did not re-read each one (medium confidence).

## Upgrade steps

1. Remove `camel.main.useMdcLogging` and `camel.main.mdcLoggingKeysPattern`.
2. Add `org.apache.camel.quarkus:camel-quarkus-mdc` (version from the BOM) and set `quarkus.camel.mdc.enabled=true`.
3. Update `%X{...}` patterns and JSON dashboards to the new key set.
4. Audit every `log:` URI for `showAll`, `showHeaders` and `showProperties`, and add `logMask=true` (and `camel.main.logMask=true`, medium confidence in Camel Quarkus).

## Compatibility

| Dependency | Version | Source |
|---|---|---|
| Camel | 4.22.1 (released 2026-09-17, LTS) | https://camel.apache.org/releases/ |
| Quarkus | 3.40.1; no Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence), see [risks](./unverified-and-risks.md#version-lifetime-risk) | https://camel.apache.org/camel-quarkus/latest/ |
| `camel-quarkus-mdc` | since 3.29.0 | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html |
| Java | 17 and 21 | https://camel.apache.org/releases/q-3.40.0/ |
