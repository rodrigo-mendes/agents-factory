# Native Mode — Camel Quarkus 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Baseline

- Native builds need Mandrel/GraalVM 25.0 or later (minimum since Quarkus 3.36). The docs index lists 25.0.4.1.
- "By default, dynamic reflection is not available in native mode."
- Reflection patterns need a Jandex index, or `quarkus.index-dependency.*`.

## Reflection and resources

```properties
# Camel Quarkus 3.40.x
quarkus.camel.native.reflection.include-patterns = org.acme.model.Order,org.acme.model.Item
quarkus.camel.native.reflection.exclude-patterns = org.acme.model.Internal
quarkus.native.resources.includes = templates/*,mysimple.txt
```

For beans invoked reflectively, annotate with `@io.quarkus.runtime.annotations.RegisterForReflection`.

## serialization-enabled (3 states since 3.40)

| Option | Effect | Best when |
|---|---|---|
| unset (default) | Registers only what extensions need | Default |
| `true` | Always registers the base set; larger image | Cassandra or Infinispan aggregation repositories |
| `false` | Blocks every serialization registration, even those extensions request. Breaks jms, jolt, management, netty, sjms, sjms2, sql. | Only when none of those extensions is present |

Ask before setting `false`: does the app use jms, sjms, sql, netty, jolt or management?

## Runtime catalog trimming

Defaults are `quarkus.camel.runtime-catalog.*=true`. Setting components, languages, dataformats, devconsoles, models or transformers to `false` shrinks the native image but disables catalog-based tooling such as dev consoles (medium confidence).

## Other build-time settings

- `quarkus.camel.expression.extraction-enabled=true` (default) compiles expressions at build time. Consider `on-build-time-analysis-failure=fail`.
- Whether each `quarkus.camel.*` property is build-time or runtime is (unverified) for most properties.

## Verification

```bash
# Representative: adapt to your environment (Camel Quarkus 3.40.x)
mvn verify -Dnative     # needs Mandrel/GraalVM 25
```

Use `@QuarkusIntegrationTest` for native tests. `CamelQuarkusTestSupport` works in JVM mode only (see `developing-camel-quarkus-junit-v3-40`).

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html ; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
