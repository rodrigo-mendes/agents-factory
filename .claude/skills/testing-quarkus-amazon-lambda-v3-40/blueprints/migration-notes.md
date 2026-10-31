# Migration Notes

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Breaking changes for the mock event server between 3.31 and 3.40: none found; the other wiki migration guides (3.32 to 3.40) were not read, so their absence is (unverified).

## Breaking changes relevant to Lambda testing

| Item | Change | Source |
|---|---|---|
| `quarkus-test-amazon-lambda`, `io.quarkus.amazon.lambda.test.LambdaClient` | Deprecated since 2.3.0, removed in 3.31; last Central release 3.30.8 | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 ; https://repo1.maven.org/maven2/io/quarkus/quarkus-test-amazon-lambda/maven-metadata.xml |
| `quarkus-junit5` | Renamed `quarkus-junit` (JUnit 6 line) in 3.31; the relocation POM still resolves at 3.40.1 (family fact) | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 |
| `quarkus-junit5-mockito` | Mockito integration is `io.quarkus:quarkus-junit-mockito` at 3.40.1.1, no relocation | https://repo1.maven.org/maven2/io/quarkus/quarkus-junit-mockito/3.40.1.1/quarkus-junit-mockito-3.40.1.1.pom |
| `System.getProperty("quarkus.http.test-port")` | No longer works since 3.31 (family fact); same caution for the mock server port property by analogy (medium confidence) | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 |
| `quarkus.lambda.test-port`, `quarkus.lambda.dev-port` | Not deprecated, but the start-up reads `quarkus.lambda.mock-event-server.*`; use those names (medium confidence) | https://quarkus.io/version/3.40/guides/all-config |

## Upgrade steps (representative)

1. Remove `quarkus-test-amazon-lambda` from the POM or Gradle file.
2. Replace `LambdaClient.invoke(...)` with RestAssured `given().body(in).post()` (plain Lambda) or endpoint calls / `post("/_lambda_")` (HTTP Lambda).
3. Rename `quarkus-junit5` to `quarkus-junit` and `quarkus-junit5-mockito` to `quarkus-junit-mockito` (see `developing-quarkus-junit-v3-40`).
4. Replace `quarkus.lambda.test-port` and `dev-port` with `quarkus.lambda.mock-event-server.test-port` and `dev-port`.
5. Run the guard greps of the [verification loop](./verification-loop.md).

## Compatibility matrix

| Dependency | Min | Max | Notes |
|---|---|---|---|
| `io.quarkus:quarkus-junit` | 3.31 | 3.40.1.1 | JUnit 6 line (family fact) |
| `io.quarkus:quarkus-junit-mockito` | 3.40.1.1 (checked) | 3.40.1.1 | Central POM |
| `io.quarkus:quarkus-test-amazon-lambda` | page not recorded | 3.30.8 | removed; never use with 3.40 |
| `io.quarkus:quarkus-test-security` | 3.40 (guide) | 3.40 | `@QuarkusTest` only |
| quarkus-amazon-services Dev Services | 3.23.x | 3.23.x | pairing with Quarkus 3.40 is (medium confidence) |
| LocalStack image | 4.13 (default) | 4.13 | 3.23.x docs |

## Quarkus 4

Out of scope. Quarkus 4.0.0 is "Upcoming" with no date on https://quarkus.io/releases (High). Quarkiverse 4.0.0.Beta* content is rejected as misinformation for this skill. Pin 3.40.x.
