# Migration Guide 3.15 to 3.40 — REST

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Confidence: (medium confidence) for the Camel 4.x rows (unversioned manuals, search summary), versioned pages for the Camel Quarkus rows; sources are the 3.40.x migration index and the Camel 4.22 upgrade guide, both fetched 2026-10-14. Nine intermediate guides were not read (coverage limit L1, see [register](./unverified-and-risks.md#coverage-limits)).

## Behaviour changes relevant to REST

| Change | Detail | Source |
|---|---|---|
| CQ 3.40.0 | No rest, platform-http, openapi or jackson entries; `quarkus.tls` protocols, ciphers and key-exchange groups now apply to Camel SSL contexts built from registered beans (unknown names fail SSL context creation; five settings are not bridged). Effect on the inbound REST/platform-http server: (unverified) | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |
| CQ 3.39.0 | Jolokia and CassandraQL only | https://camel.apache.org/camel-quarkus/next/migration-guide/3.39.0.html |
| CQ 3.31.0 | `camel-quarkus-junit5` renamed `camel-quarkus-junit`; `org.apache.camel.test.junit5` became `org.apache.camel.test.junit6`; the old artifact still resolves as a deprecated stub, removal date (unverified). Stub details: `developing-camel-quarkus-junit-v3-40` | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html |
| Camel 4.5 | `inlineRoutes` default changed from false to true | https://camel.apache.org/manual/rest-dsl.html |
| Camel 4.6 | Contract-first REST DSL (`rest().openApi()`) | https://camel.apache.org/manual/rest-dsl-openapi.html |
| Camel 4.13 | Response validation | https://camel.apache.org/manual/rest-dsl-validation.html |
| Camel 4.22.2 (applies only after upgrading past the pinned 4.22.1; medium confidence) | json/xml binding: responses without Content-Type take it from the verb `produces` (restores pre-4.18.4 behaviour); `fileNameExtWhitelist` exact, case-insensitive match | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html |
| Camel 4.22.1 | REST producer on `vertx-http` strips `Content-Length`, `Host`, `Connection`, `Transfer-Encoding` unless you set your own `headerFilterStrategy` | same URL |
| Camel 4.0 | `camel-atlasmap` removed; `camel-restdsl-swagger-plugin` removed in favour of `camel-restdsl-openapi-plugin`; generated REST DSL defaults to platform-http (search summary, medium confidence) | https://camel.apache.org/manual/camel-4-migration-guide.html |
| CQ 3.40.0 release notes | #9195 openapi-java native warnings and `@JsonValue` rendered as objects; #9153 native build failure with kamelet `DelegatingSchemaResolver` and no camel-jackson | https://camel.apache.org/releases/q-3.40.0/ |

## Upgrade steps

1. Set `quarkus.platform.version` to 3.40.1 for both BOMs (see the core skill).
2. Replace `camel-quarkus-junit5` with `camel-quarkus-junit`; change `junit5` imports to `junit6`.
3. Remove AtlasMap; map with POJO binding plus beans.
4. If a direct route serves several REST verbs, keep it as is (not inlined) or split it.
5. Where possible replace `camel-restdsl-openapi-plugin` code generation with `rest().openApi()` plus `quarkus-maven-plugin` `generate-code`.
6. Re-test the Content-Type of bound responses (4.18.4 to 4.22.0 behaviour differed).

```bash
# Representative: adapt to your environment
grep -rn "camel-quarkus-junit5\|atlasmap\|camel-restdsl-swagger" pom.xml src/
# Expected: no matches after migration
```

## Compatibility matrix

| Dependency | Min | Max | Source |
|---|---|---|---|
| Quarkus platform | 3.40.1 | 3.40.x | https://camel.apache.org/camel-quarkus/latest/ (the `main`-branch example pom also shows 3.40.1, not the 3.40.x tag) |
| Camel | 4.22.1 | 4.22.x | https://camel.apache.org/camel-quarkus/latest/ |
| Java | 17 | 21 | https://camel.apache.org/releases/q-3.40.0/ (cited for Java only) |
| Quarkus 4 / Jackson 3 | no build known | no build known | No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence); Jackson 3 impact (unverified); Quarkus 4.0.0.Beta1 published 2026-10-01: https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ |
