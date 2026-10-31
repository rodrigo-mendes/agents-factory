---
name: developing-quarkus-junit-v3-40
description: "Guides Quarkus 3.40 testing with quarkus-junit (formerly quarkus-junit5): @QuarkusTest, profiles, test resources, @InjectMock. Use when writing or migrating generic tests in Quarkus apps. Not for Camel route tests (see developing-camel-quarkus-junit-v3-40), Quarkus 4 or other versions."
---

# Testing with Quarkus JUnit 3.40.x

> Version lock: every claim applies to **Quarkus 3.40.x** (`io.quarkus:quarkus-junit`, artifact checked at 3.40.1) only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Camel route tests are out of scope: use the skill `developing-camel-quarkus-junit-v3-40`.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Quarkus | 3.40 released 2026-09-30, LTS, community-maintained until 2027-09-30 (High) | https://quarkus.io/releases |
| Java | 17 and 21 (High) | https://camel.apache.org/releases/q-3.40.0/ |
| Test dependency | `io.quarkus:quarkus-junit` + `io.rest-assured:rest-assured`, both `test` scope | https://quarkus.io/version/3.40/guides/getting-started-testing |
| Rename `quarkus-junit5` to `quarkus-junit` | Quarkus 3.31, together with the move to JUnit 6 (official migration wiki, unversioned page for 3.31) | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 |
| `quarkus-junit5` 3.40.1 | still resolves, only as a relocation POM pointing to `quarkus-junit` | https://repo1.maven.org/maven2/io/quarkus/quarkus-junit5/3.40.1/quarkus-junit5-3.40.1.pom |
| JUnit Jupiter / Mockito (BOM 3.40.1) | 6.1.3 / 5.21.0 (coverage limit, L3: first 100k characters of the BOM read) | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/bom/application/pom.xml |
| Testing guide coverage | read to 100,000 of 108,136 characters (coverage limit, L1) | https://quarkus.io/version/3.40/guides/getting-started-testing |
| Maven / GraalVM | page not recorded (unverified, U6) | page not recorded |
| Camel test artifact (family fact, High) | `camel-quarkus-junit` (renamed from `camel-quarkus-junit5` in 3.31); details live in `developing-camel-quarkus-junit-v3-40` | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 becomes the base ([source](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)). Pin 3.40.x; do not mix Quarkus 4 test patterns into this skill.
- How long the `-junit5` relocation POMs are kept is not documented (unverified, I2). Migrate now.
- The Camel Quarkus-specific support end date for 3.40 is not published (unverified, U5).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Test types and lifecycle](./blueprints/test-types.md)
- [Mocking strategies](./blueprints/mocking.md)
- [Profiles, test resources, Dev Services and ports](./blueprints/profiles-and-resources.md)
- [Migration 3.15 baseline to 3.40 (3.31 rename)](./blueprints/migration-3-31-rename.md)
- [Integration examples (command mode, REST Assured)](./blueprints/integration-examples.md)
- [Unverified and irresolvable register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Prefer `io.quarkus:quarkus-junit` (test scope) as the test dependency.** The 3.40 guide lists only `quarkus-junit` and `rest-assured` ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)). See [patterns](./blueprints/always-do-patterns.md#1-quarkus-junit-dependency).
- **Include `@{argLine}` in any custom Surefire or Failsafe `<argLine>`.** The property "will automatically include the extra JVM parameters" (official Quarkus 3.31 migration guide, verified 2026-10-14: [wiki](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31); [coverage guide](https://quarkus.io/version/3.40/guides/tests-with-coverage)). See [patterns](./blueprints/always-do-patterns.md#2-surefire-argline).
- **Follow the 3.40 guide's Surefire setup, which includes `java.util.logging.manager` = `org.jboss.logmanager.LogManager`.** ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)). See [patterns](./blueprints/always-do-patterns.md#3-jboss-logmanager).
- **Use `@InjectMock` only on normal-scoped beans.** ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)). See [patterns](./blueprints/always-do-patterns.md#4-injectmock-on-normal-scoped-beans); requirements and exceptions in [mocking](./blueprints/mocking.md#scope-rules-for-injectmock).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Mocking strategy | `@Alternative`/`@Mock` (works for startup beans, global) vs `QuarkusMock` (no Mockito) vs `@InjectMock` (needs `quarkus-junit-mockito`; `@Singleton`/`@Dependent` need `@MockitoConfig(convertScopes = true)`; startup beans unaffected) vs `@InjectSpy` (real bean, observers still run) ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)); see [mocking](./blueprints/mocking.md) | "Is the bean used at startup, and which scope has it?" |
| Group tests by profile (medium confidence) | A different `@TestProfile` shuts Quarkus down and starts it again; each profile costs one restart ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)); see [profiles](./blueprints/profiles-and-resources.md#test-profiles-medium-confidence) | "How many distinct profiles will the suite need?" |
| Separate `@QuarkusTest` and `@QuarkusIntegrationTest` runs (medium confidence) | The guide says they should not share one execution and splits them on the `io.quarkus.test.junit.QuarkusTest` tag; integration tests run the packaged artifact with no injection ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)) | "Does CI run Surefire and Failsafe separately?" |
| Finding the test URL (medium confidence) | `@TestHTTPResource` / `@TestHTTPEndpoint` ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing); the 3.31 wiki does not name them as the replacement for system-property lookup), or injecting `io.quarkus.vertx.http.HttpServer` ([official migration wiki](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)) | "Does the test need the port, or only a relative path?" |
| HTTPS test port (medium confidence, M10) | `quarkus.https.test-port` was removed in 3.31 (High); that `quarkus.http.test-ssl-port` is its replacement is inferred from the sentence order of the [official migration wiki](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31); the [testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing) documents `quarkus.http.test-ssl-port` | "Do the tests need HTTPS, and on which port?" |
| Test resource scope (medium confidence) | `@QuarkusTestResource` (global unless `restrictToAnnotatedClass = true`) vs `@WithTestResource` (`scope`: `MATCHING_RESOURCES` default, `RESTRICTED_TO_CLASS`, `GLOBAL`); the 3.40 page does not call `@QuarkusTestResource` deprecated (absence of evidence) | "Must resources be isolated per test class?" |
| Dev Services vs explicit resource | Dev Services are automatic for unconfigured services, need a container runtime and switch off when connection config is set ([Dev Services guide](https://quarkus.io/version/3.40/guides/dev-services), coverage limit L2); a `QuarkusTestResourceLifecycleManager` is explicit. Behaviour across profile restarts is (unverified, U1) | "Does CI have a container runtime, and is the connection config pinned?" |
| Fixed vs random test port | Default `quarkus.http.test-port` is 8081; `0` picks a random port ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)) | "Do parallel CI jobs share one host?" |
| JUnit parallel execution | No 3.40 page covers it with `@QuarkusTest` (unverified, I1); run sequentially, parallelize per module or fork | "Is parallel execution a hard requirement?" |
| Surefire version | The guide uses a placeholder, the concrete value is (unverified, U4) | "Which Surefire version does the build pin?" |

### 🚫 Never Do

Rows 1, 3 and 4 rest on the official Quarkus 3.31 migration guide, verified 2026-10-14 (High). The ✅ of row 3 deliberately omits the replacement property: that pairing is medium confidence (M10, see Ask First).

| ❌ Don't | ✅ Instead |
|---|---|
| Add `quarkus-junit5` or `quarkus-junit5-mockito` to new 3.40 code; since 3.31 they resolve only as relocation POMs ([official migration wiki](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31), [POM](https://repo1.maven.org/maven2/io/quarkus/quarkus-junit5/3.40.1/quarkus-junit5-3.40.1.pom)) | `quarkus-junit` and `quarkus-junit-mockito` ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)) |
| Use `@InjectMock` on a `@Singleton`/`@Dependent` bean without `convertScopes`, or on a bean used during startup ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)) | `@MockitoConfig(convertScopes = true)`, an `@ApplicationScoped` bean, or an `@Alternative` for startup beans ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)) |
| Set `quarkus.https.test-port` or `quarkus.https.port`; 3.31 removed them (official Quarkus 3.31 migration guide, verified 2026-10-14: [wiki](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)) | Remove the property |
| Read the test port with `System.getProperty("quarkus.http.test-port")` or `test.url`; since 3.31 these "will no longer work" (official Quarkus 3.31 migration guide, verified 2026-10-14: [wiki](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)) | Read it through the Quarkus config system (`ConfigProvider.getConfig().unwrap(SmallRyeConfig.class).getValue(...)`) or inject `io.quarkus.vertx.http.HttpServer` ([wiki](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)); or set `quarkus.http.test-port` (default 8081, `0` = random) and use relative paths as in the guide's sample ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)) |
| Use `@Inject`, Panache entities or `@InjectMock` in `@QuarkusMainTest` ([command mode](https://quarkus.io/version/3.40/guides/command-mode-reference)) | `@QuarkusMainTest` with a `@TestProfile` that swaps the dependency, and `@Launch`/`LaunchResult` ([command mode](https://quarkus.io/version/3.40/guides/command-mode-reference)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `quarkus.http.test-port` | `8081` default; `0` = random; `quarkus.http.test-ssl-port` alongside | https://quarkus.io/version/3.40/guides/getting-started-testing |
| `quarkus.http.test-timeout` | `30s` default (REST Assured) | https://quarkus.io/version/3.40/guides/getting-started-testing |
| `quarkus.test.hang-detection-timeout` | 10 minutes default | https://quarkus.io/version/3.40/guides/getting-started-testing |
| `@QuarkusIntegrationTest` profile (medium confidence) | `prod` by default; change with `quarkus.test.integration-test-profile` | https://quarkus.io/version/3.40/guides/getting-started-testing |
| AOT cache test run (medium confidence, L1) | needs JDK 25+ for `quarkus.package.jar.aot.enabled=true` | https://quarkus.io/version/3.40/guides/getting-started-testing |
| `quarkus.test.continuous-testing` | `paused` default (`enabled`, `disabled`) | https://quarkus.io/version/3.40/guides/continuous-testing |
| `quarkus.test.exclude-tags` | `slow` default; ignored when `include-tags` is set | https://quarkus.io/version/3.40/guides/continuous-testing |
| `quarkus.test.exclude-pattern` | `.*\.IT[^.]+\|.*IT\|.*ITCase` default | https://quarkus.io/version/3.40/guides/continuous-testing |
| `quarkus.jacoco.data-file` | `target/jacoco-quarkus.exec`; needs `io.quarkus:quarkus-jacoco` (test scope) | https://quarkus.io/version/3.40/guides/tests-with-coverage |
| `quarkus.jacoco.report-location` | page states both `target/jacoco-report` and `target/jacoco-reports` (unverified, I3); set it explicitly | https://quarkus.io/version/3.40/guides/tests-with-coverage |
| REST Assured version in the BOM | (unverified, U2) not in the portion of the BOM read | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/bom/application/pom.xml |
| `camel-quarkus-junit5` 3.40.0 on Maven Central | Deprecated stub (High); removal date (unverified, U3); see `developing-camel-quarkus-junit-v3-40` | https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom |
| Representative commands | `./mvnw test`, `./mvnw verify -Dnative`, `./mvnw quarkus:test` | page not recorded |

## External Resources

All fetched 2026-10-14. Versioned quarkus.io pages are the 3.40 guides.

- Testing guide: https://quarkus.io/version/3.40/guides/getting-started-testing
- Command mode: https://quarkus.io/version/3.40/guides/command-mode-reference
- Continuous testing: https://quarkus.io/version/3.40/guides/continuous-testing
- Coverage: https://quarkus.io/version/3.40/guides/tests-with-coverage
- Dev Services: https://quarkus.io/version/3.40/guides/dev-services
- Quarkus 3.31 migration guide (official wiki): https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
