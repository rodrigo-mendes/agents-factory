# Migration: 3.15 Baseline to 3.40 (the 3.31 Rename)

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The 3.15-era names (`quarkus-junit5`, JUnit 5) appear here only as the migration baseline. All breaking changes below were introduced in Quarkus 3.31 (High). Sources: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (official migration wiki, unversioned page) ; https://repo1.maven.org/maven2/io/quarkus/quarkus-junit5/3.40.1/quarkus-junit5-3.40.1.pom ; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html

## Contents

- [Breaking changes](#breaking-changes)
- [Artifact rename table](#artifact-rename-table)
- [Upgrade steps](#upgrade-steps)
- [Compatibility matrix](#compatibility-matrix)

## Breaking changes

- JUnit 5 to JUnit 6 ("We updated to JUnit 6 in place of JUnit 5."). The 3.40.1 BOM sets `junit.jupiter.version` 6.1.3.
- Every `*-junit5` artifact was renamed to `*-junit`; relocations are in place. In 3.40.1 `quarkus-junit5` resolves only as a relocation POM.
- A custom Surefire/Failsafe `<argLine>` must include `@{argLine}`.
- `quarkus.https.port` and `quarkus.https.test-port` were removed; `System.getProperty` port lookups no longer work. The `quarkus.http.test-ssl-port` replacement pairing is inferred (medium confidence, M10).
- Testcontainers 2: some artifacts and packages were renamed (handled by `quarkus update`).
- `quarkus-test-amazon-lambda` / `LambdaClient` were removed (use REST Assured).
- Camel (High, family fact): `camel-quarkus-junit5` became `camel-quarkus-junit` in 3.31; details and the stub status are in the skill `developing-camel-quarkus-junit-v3-40`. When the stub will be removed is unverified (U3).

## Artifact rename table

| Old (baseline) | 3.40 |
|---|---|
| `quarkus-junit5` | `quarkus-junit` |
| `quarkus-junit5-component` | `quarkus-junit-component` |
| `quarkus-junit5-config` | `quarkus-junit-config` |
| `quarkus-junit5-internal` | `quarkus-junit-internal` |
| `quarkus-junit5-mockito` | `quarkus-junit-mockito` |
| `quarkus-junit5-mockito-config` | `quarkus-junit-mockito-config` |
| `io.quarkus.junit5:junit5-virtual-threads` | `io.quarkus.junit:junit-virtual-threads` |

How long the relocation POMs are kept is not documented (unverified, I2). Expect them at risk in Quarkus 4 (inference, medium confidence, M7).

## Upgrade steps

1. Run `quarkus update --stream=3.40` (representative command). The 3.31 guide says the renames are "handled automatically".
2. Replace any remaining `-junit5` artifactIds in your POMs.
3. Make sure any custom `<argLine>` includes `@{argLine}`.
4. Replace system-property port lookups: use the Quarkus config system (`ConfigProvider`/`SmallRyeConfig`) or inject `io.quarkus.vertx.http.HttpServer` (both named by the wiki), or configure `quarkus.http.test-port` and use relative paths; `@TestHTTPResource` is not named by the wiki as the replacement (medium confidence, M3). Replacing `quarkus.https.test-port` with `quarkus.http.test-ssl-port` (medium confidence, M10).
5. For Camel route tests, follow the skill `developing-camel-quarkus-junit-v3-40`.

## Compatibility matrix

| Dependency | Version in 3.40.1 | Source |
|---|---|---|
| JUnit Jupiter | 6.1.3 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/bom/application/pom.xml |
| Mockito | 5.21.0 | same URL (coverage limit, L3: first 100k characters read) |
| REST Assured | unverified (U2) | property not reached in the portion read |
| Camel Quarkus | 3.40.x on Quarkus 3.40.1 / Camel 4.22.1 | https://camel.apache.org/camel-quarkus/latest/ |
| AOT cache test run (medium confidence, L1) | JDK 25+ for `quarkus.package.jar.aot.enabled=true` | https://quarkus.io/version/3.40/guides/getting-started-testing |
