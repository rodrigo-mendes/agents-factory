# Integration Examples: Quarkus JUnit 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Camel route-test examples are not covered here: use the skill `developing-camel-quarkus-junit-v3-40`.

## Contents

- [Command-mode test](#command-mode-test)
- [REST Assured](#rest-assured)

## Command-mode test

Source: https://quarkus.io/version/3.40/guides/command-mode-reference

```java
@QuarkusMainTest
class CliTest {
    @Test @Launch(value = {}, exitCode = 1)
    void failsWithoutArgs(LaunchResult r) { }
    @Test void manual(QuarkusMainLauncher launcher) { LaunchResult r = launcher.launch("--x"); }
}
```

`@QuarkusMainIntegrationTest` runs the built jar or native executable.

## REST Assured

Source: https://quarkus.io/version/3.40/guides/getting-started-testing. `@TestHTTPEndpoint(GreetingResource.class)` prefixes the resource path (medium confidence, M3); the default port is 8081. See the full class in [test types](./test-types.md#lifecycle). The REST Assured version in the BOM is unverified (U2).
