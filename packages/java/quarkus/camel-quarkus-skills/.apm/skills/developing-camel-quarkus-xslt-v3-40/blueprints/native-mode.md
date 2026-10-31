# Native Mode for XSLT (Camel Quarkus 3.40.x)

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html unless stated.

## Rules (high confidence)

- `camel-quarkus-xslt` is supported in JVM and native mode since 0.4.0.
- Only `classpath:` template URIs work natively. `file:`, `http:` and other schemes are JVM-only.
- Templates listed in `quarkus.camel.xslt.sources` are precompiled. `xsl:include` works natively when the including stylesheet is in `sources` and the includes are classpath-relative.
- `xsl:messaging` is listed as JVM-only on the extension page (the page's spelling; the exact feature name was not re-checked, see the [register](./unverified-and-risks.md)).
- `XsltSaxonAggregationStrategy` aggregation is JVM-only.

## Medium confidence and unverified in native mode

- (medium confidence) `camel-quarkus-xslt-saxon` is native since 3.2.0 (https://camel.apache.org/camel-quarkus/latest/reference/extensions/xslt-saxon.html, unversioned `latest` alias).
- `bean:` and `ref:` template URIs (unverified; the extension page says only `classpath:` works natively).
- `output=file` in a native executable (unverified).
- Which `quarkus.camel.xslt.*` properties are fixed at build time (unverified): the extension page's build-time markers were not established. As a precaution, rebuild after changing `sources`, `package-name` or `features`.
- `xsl:messaging` feature name (unverified).

## Recommended test flow

Classpath and translet problems appear only in native, so run the native integration tests; no XSLT-specific testing guidance exists on the extension page (medium confidence). Commands are representative; adapt them to your build.

```bash
./mvnw clean verify          # JVM tests; expected: BUILD SUCCESS
./mvnw verify -Dnative       # native build + @QuarkusIntegrationTest; expected: BUILD SUCCESS
grep -rn "xslt:file:\|xslt:http" src/main/java   # expected: no output (native-safe)
grep -n "quarkus.camel.xslt.sources" src/main/resources/application.properties  # expected: 1 match
```

General native guidance (charsets, reflection) lives in the core skill.
