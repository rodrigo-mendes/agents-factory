# Never-Do Patterns: Quarkus JUnit 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Sections 1 to 5 rest on versioned 3.40 pages or the official 3.31 migration wiki (unversioned page; the research rates these claims High). The last section lists a research item kept out of SKILL.md.

## Contents

1. [Old -junit5 artifact names](#1-old--junit5-artifact-names)
2. [InjectMock on the wrong scope](#2-injectmock-on-the-wrong-scope)
3. [Removed HTTPS test port property](#3-removed-https-test-port-property)
4. [System property lookups of the test port](#4-system-property-lookups-of-the-test-port)
5. [Injection in QuarkusMainTest](#5-injection-in-quarkusmaintest)
6. [Kept out of SKILL.md](#6-kept-out-of-skillmd)

Camel route-test rules are not covered here: use the skill `developing-camel-quarkus-junit-v3-40`.

## 1. Old -junit5 artifact names

Since 3.31 the `-junit5` artifacts are relocation POMs ("Update the artifactId in your project build file."). The retention period is undocumented (unverified, I2).

```xml
<!-- 🚫 WRONG -->
<artifactId>quarkus-junit5</artifactId>
<artifactId>quarkus-junit5-mockito</artifactId>

<!-- ✅ CORRECT -->
<artifactId>quarkus-junit</artifactId>
<artifactId>quarkus-junit-mockito</artifactId>
```

Sources: https://repo1.maven.org/maven2/io/quarkus/quarkus-junit5/3.40.1/quarkus-junit5-3.40.1.pom ; https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31

## 2. InjectMock on the wrong scope

Only normal-scoped beans can be mocked, and beans used during startup are not affected, so the real bean can run silently.

```java
// 🚫 WRONG
@Singleton class Clock {}
// in the test:
@InjectMock Clock clock;

// ✅ CORRECT
@InjectMock @MockitoConfig(convertScopes = true) Clock clock;
// or make Clock @ApplicationScoped; or use an @Alternative for startup-time beans
```

Source: https://quarkus.io/version/3.40/guides/getting-started-testing

## 3. Removed HTTPS test port property

Release 3.31 removed `quarkus.https.port` and `quarkus.https.test-port` (official Quarkus 3.31 migration guide, verified 2026-10-14; High). Which property replaces them is covered only in the Ask First row "HTTPS test port" in [SKILL.md](../SKILL.md).

```properties
# 🚫 WRONG
quarkus.https.test-port=8444

# ✅ CORRECT: remove the property
```

Sources: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 ; https://quarkus.io/version/3.40/guides/getting-started-testing

## 4. System property lookups of the test port

The official 3.31 migration wiki says `System.getProperty("quarkus.http.test-port")` and `test.url` lookups "will no longer work". The wiki names the Quarkus config system (`ConfigProvider.getConfig().unwrap(SmallRyeConfig.class).getValue(...)`) and the injectable `io.quarkus.vertx.http.HttpServer` as the replacement; it does not name `@TestHTTPResource`/`@TestHTTPEndpoint`. The 3.40 guide sets the port with `quarkus.http.test-port` (default 8081) and its REST Assured sample uses relative paths. URL-injection options (`@TestHTTPResource`, `@TestHTTPEndpoint`, `HttpServer`) are medium confidence: see [profiles and resources](./profiles-and-resources.md#finding-the-test-url-medium-confidence).

```java
// 🚫 WRONG
int port = Integer.getInteger("quarkus.http.test-port");

// ✅ CORRECT: relative path, port from quarkus.http.test-port
given().when().get("/hello").then().statusCode(200);
```

Sources: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 ; https://quarkus.io/version/3.40/guides/getting-started-testing

## 5. Injection in QuarkusMainTest

`@QuarkusMainTest` does not support CDI injection, Panache entities or `@InjectMock`. Mock through a test profile. `@QuarkusIntegrationTest` cannot inject either.

```java
// 🚫 WRONG
@QuarkusMainTest class CliTest { @Inject Service s; @InjectMock Repo r; }

// ✅ CORRECT
@QuarkusMainTest @TestProfile(FakeRepoProfile.class)
class CliTest {
    @Test @Launch(value = {"--name", "x"}, exitCode = 0)
    void runs(LaunchResult result) { assertTrue(result.getOutput().contains("x")); }
}
```

Sources: https://quarkus.io/version/3.40/guides/command-mode-reference ; https://quarkus.io/version/3.40/guides/getting-started-testing

## 6. Kept out of SKILL.md

Research item NP-5 (different profiles or resources on `@Nested` classes; production `@Alternative` mocks in `src/main`) is rated High by the research, but it records no quoted evidence for the claim. It is therefore not a Never Do row. Verify against the [testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing) before relying on it (medium confidence, M9).