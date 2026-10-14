# Migration Guide to 3.40.x: Camel Quarkus JAXB

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Baseline for the comparison is Camel Quarkus 3.15, named here only as a migration baseline; no pattern in this skill is sourced from 3.15 material.

## Breaking changes in 3.40.0

None for JAXB: the [3.40.0 migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html) has no JAXB heading. Changes that touch JAXB-adjacent code:

| Change | Effect | Source |
|---|---|---|
| XSLT parses inputs with an `XMLReader` that does not resolve external entities or load external DTDs; `document()` is denied unless a URIResolver resolves it; `quarkus.camel.xslt.features` applies to every template and unsupported features fail endpoint creation | Affects JAXB output piped to `xslt:`; also direct `TransformerFactory.newInstance()` use is affected per the research (medium confidence) | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |
| `quarkus.camel.native.reflection.serialization-enabled=false` now vetoes extension registrations | JAXB is not among the listed affected extensions | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |
| `quarkus.tls` settings bridged to Camel SSL contexts built from registered beans | Not JAXB-specific; see the core skill | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |
| Test artifact `camel-quarkus-junit5` renamed `camel-quarkus-junit` | Test classpath and imports (`org.apache.camel.test.junit6`) | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html |

## Option drift from the 3.15 baseline

The 4.22.x option set includes `accessExternalSchemaProtocols` (security), `contentTypeHeader` (default `true`) and `jaxbProviderProperties` ([data format page](https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html)). Which Camel release added each option was not traced: (unverified).

## Upgrade steps

1. Bump `quarkus.platform.version` / `quarkus-camel-bom` to 3.40.x (BOM details: core skill).
2. Re-check native registration: only non-annotated POJOs created by an `ObjectFactory` need `@RegisterForReflection`. Older annotations on JAXB-annotated classes are redundant (medium confidence, inferred from source code), so removal is optional.
3. Check every `schema` option. If imports fail, list the XSDs explicitly before opening protocols (see [schema security](./schema-security.md)).
4. Replace `camel-quarkus-junit5` with `camel-quarkus-junit` and update test imports.
5. Rebuild native: `./mvnw package -Dnative` (representative, output not verified).

## Quarkus 4 outlook (as of 2026-10-14)

- Quarkus 4.0.0.Beta1 sets Java 21 as the minimum and ports Jackson to 3 ([release notes](https://github.com/quarkusio/quarkus/releases/tag/4.0.0.Beta1)); GA is "planned for the end of November" ([blog](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)).
- The [Quarkus 4.0 migration guide](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0) has no JAXB or `jakarta.xml.bind` entries (medium confidence, absence of evidence: the wiki page is unversioned).
- `camel-quarkus-jaxb` has no Jackson dependency in its 3.40.0 POM (medium confidence, the research's reading of [Maven Central](https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0)). Expected impact beyond the Java baseline: none (inference).
- `camel-quarkus-jacksonxml` runs on Jackson's XmlMapper ([page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jacksonxml.html)) and is the extension exposed to Jackson 3. Its options are (unverified).
- No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence). Pin 3.40.x.

## Compatibility matrix

| Dependency | Value | Source |
|---|---|---|
| Camel Quarkus | 3.40.x (3.40.0 on Maven Central) | https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0 |
| Camel (`camel-jaxb`) | 4.22.x (docs index lists 4.22.1) | https://camel.apache.org/camel-quarkus/latest/ |
| Quarkus (`quarkus-jaxb`) | 3.40.x (docs index lists 3.40.1) | https://camel.apache.org/camel-quarkus/latest/ |
| Java | 17 and 21 | https://camel.apache.org/releases/q-3.40.0/ |
| Jakarta XML Binding API | (unverified), not read from the BOM | page not recorded |
