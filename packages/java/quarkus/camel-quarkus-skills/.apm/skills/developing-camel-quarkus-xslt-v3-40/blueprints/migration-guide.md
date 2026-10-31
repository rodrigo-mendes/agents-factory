# Migration Guide for XSLT Users: Camel Quarkus 3.15 to 3.40

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). "3.15" is only the migration baseline. Confidence: high for the 3.40.0 changes (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html, re-confirmed on https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html). Only the 3.40.0 guide was read for XSLT.

## Breaking changes in 3.40.0 ("XSLT extension changes")

1. External entities and external DTDs in input documents are no longer resolved. `String`, `byte[]` and `InputStream` bodies were already parsed safely by Camel; the change mainly affects `Source` bodies and direct factory calls.
2. `document()` is denied unless a `URIResolver` resolves it. The restriction persists through `reset()` and `setURIResolver(null)`.
3. `quarkus.camel.xslt.features` applies to every template, including runtime-loaded ones. Unsupported features now fail endpoint creation.
4. The Xalan factory becomes the JAXP default. This affects `TransformerFactory.newInstance()` in app code and in the Tika and XML Security extensions.

Not mentioned for `xslt-saxon` in the guide; whether Saxon is affected is (unverified). XSLT-specific changes between 3.15 and 3.40 other than the above are (unverified). Generic ones belong to the core skill; the `camel-quarkus-junit5` to `camel-quarkus-junit` rename (since 3.31) is covered by the skill `developing-camel-quarkus-junit-v3-40`.

## Upgrade steps

1. Bump `quarkus.platform.version` to 3.40.x (BOM procedure in the core skill).
2. Find code now hitting Xalan with restrictions: `grep -rn "TransformerFactory.newInstance\|setAttribute(XMLConstants.ACCESS_EXTERNAL" src/`.
3. Find stylesheets using `document()` outside routes: `grep -rn "document(" src/main/resources`; add a `URIResolver` where needed.
4. Review `quarkus.camel.xslt.features` entries; an unsupported feature now fails endpoint creation.
5. Re-test inputs that use DOCTYPE or entities.

## Compatibility matrix

| Dependency | Version | Source |
|---|---|---|
| Camel | 4.22.1 | https://camel.apache.org/camel-quarkus/latest/ |
| camel-quarkus-xslt | 3.40.0 (Maven Central 2026-09-24) | https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-xslt/ |
| Quarkus | 3.40.x | see the core skill |
| Xalan-J | 2.7.x (unverified) | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html |
