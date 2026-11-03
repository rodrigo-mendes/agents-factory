# Failsafe pom and run modes

Back to [SKILL.md](../SKILL.md). Sources read 2026-11-01: [testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing), [Maven tooling](https://quarkus.io/version/3.40/guides/maven-tooling), [all-config](https://quarkus.io/version/3.40/guides/all-config).

## Contents

- [Failsafe pom](#failsafe-pom)
- [Run modes](#run-modes)
- [Limits of an IT as a design pattern](#limits-of-an-it-as-a-design-pattern)
- [Testing an already running app](#testing-an-already-running-app)
- [Lifecycle](#lifecycle)

## Failsafe pom

```xml
<properties>
  <skipITs>true</skipITs>  <!-- generated default; enable with -DskipITs=false -->
</properties>
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-failsafe-plugin</artifactId>
  <version>${surefire-plugin.version}</version>
  <executions>
    <execution>
      <goals>
        <goal>integration-test</goal>
        <goal>verify</goal>
      </goals>
    </execution>
  </executions>
  <configuration>
    <systemPropertyVariables>
      <native.image.path>${project.build.directory}/${project.build.finalName}-runner</native.image.path>
      <java.util.logging.manager>org.jboss.logmanager.LogManager</java.util.logging.manager>
      <maven.home>${maven.home}</maven.home>
    </systemPropertyVariables>
  </configuration>
</plugin>
```

- `surefire-plugin.version` is a property of the generated project; this skill does not pin a plugin version.
- `verify` is what fails the build on IT failures; `integration-test` alone does not.

## Run modes

Representative commands (unverified):

```bash
./mvnw verify -DskipITs=false                      # jar ITs (fast-jar, default)
./mvnw verify -Dnative                              # native ITs (native profile sets skipITs=false)
./mvnw verify -DskipITs=false -Dquarkus.container-image.build=true   # container ITs
./mvnw verify -DskipITs=true                        # CI without Docker
```

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| jar | speed, no Docker for the app | not the prod image | default PR CI |
| native | proves the native image | build minutes, GraalVM or container build | native is shipped |
| container | tests the shipped image, shared network | needs docker or podman | image is the deliverable |

- Container ITs need `quarkus-container-image-jib|docker|podman` and `quarkus.container-image.build=true`.
- Override the artifact with `quarkus.test.integration-test-artifact-type` (`jar` or `native`).
- Debug the launched app: add `-Dquarkus.test.arg-line="-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=*:5005"`.

## Limits of an IT as a design pattern

- No bean injection and no `@InjectMock`; only `DevServicesContext` and (with quarkus-wiremock) `WireMock`.
- The `prod` profile applies unless `quarkus.test.integration-test-profile` says otherwise; prod-only config (secret sources) must be overridden by a test resource.
- `src/test/resources/application.properties` is not used.
- Design consequence: put business rules in `@QuarkusTest` classes (fast, mockable) and keep ITs for wiring, packaging and end-to-end paths. Reuse by extension where the assertions are identical.

## Testing an already running app

```bash
./mvnw verify -Dquarkus.http.test-host=1.2.3.4 -Dquarkus.http.test-port=4321
```

- HTTPS-only target: `quarkus.http.test-ssl-enabled=true` plus `quarkus.http.test-ssl-port`.
- Test resources and Dev Services do not reach that app (medium confidence, one source).
- Ask whether the environment is shared before running write tests.

## Lifecycle

`package` builds the artifact, then Failsafe `integration-test`: test resources `start()` and Dev Services come up, the artifact is launched (waits `quarkus.test.wait-time`, default `1M`), tests run over HTTP, `stop()` runs, and `verify` fails the build on failures.
