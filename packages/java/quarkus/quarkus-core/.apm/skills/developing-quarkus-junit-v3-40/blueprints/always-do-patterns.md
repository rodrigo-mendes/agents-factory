# Always-Do Patterns: Quarkus JUnit 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Each pattern rests on a versioned 3.40 page. Patterns the research rates medium (profile grouping, separate executions, URL lookup) are in [profiles and resources](./profiles-and-resources.md).

## Contents

1. [Quarkus JUnit dependency](#1-quarkus-junit-dependency)
2. [Surefire argLine](#2-surefire-argline)
3. [JBoss LogManager](#3-jboss-logmanager)
4. [InjectMock on normal-scoped beans](#4-injectmock-on-normal-scoped-beans)

Camel route tests are not covered here: use the skill `developing-camel-quarkus-junit-v3-40`.

## 1. Quarkus JUnit dependency

The 3.40 guide lists `quarkus-junit` and `rest-assured`, both `test` scope. The `-junit5` names are relocation POMs since 3.31 ([migration](./migration-3-31-rename.md)).

```xml
<!-- Quarkus 3.40 -->
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-junit</artifactId>
  <scope>test</scope>
</dependency>
<dependency>
  <groupId>io.rest-assured</groupId>
  <artifactId>rest-assured</artifactId>
  <scope>test</scope>
</dependency>
```

The REST Assured version managed by the BOM is not confirmed (unverified, U2). Sources: https://quarkus.io/version/3.40/guides/getting-started-testing ; https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (official migration wiki)

## 2. Surefire argLine

A custom `<argLine>` must include `@{argLine}`; the property "will automatically include the extra JVM parameters" (the official 3.31 migration guide, verified 2026-10-14, puts it first in its example). JaCoCo needs the same late evaluation.

```xml
<!-- Quarkus 3.40 -->
<configuration>
  <argLine>@{argLine} -Xmx256m</argLine>
</configuration>
```

Sources: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 ; https://quarkus.io/version/3.40/guides/tests-with-coverage

## 3. JBoss LogManager

The 3.40 guide says the default Surefire version does not support JUnit and shows `java.util.logging.manager` as a system property. The concrete Surefire version is a placeholder in the guide (unverified, U4).

```xml
<plugin>
  <artifactId>maven-surefire-plugin</artifactId>
  <version>${surefire-plugin.version}</version> <!-- concrete value: unverified (U4) -->
  <configuration>
    <systemPropertyVariables>
      <java.util.logging.manager>org.jboss.logmanager.LogManager</java.util.logging.manager>
    </systemPropertyVariables>
  </configuration>
</plugin>
```

Source: https://quarkus.io/version/3.40/guides/getting-started-testing

## 4. InjectMock on normal-scoped beans

`@InjectMock` needs `quarkus-junit-mockito` and a normal-scoped bean (`@ApplicationScoped`, `@RequestScoped`). `@Singleton`/`@Dependent` need `@MockitoConfig(convertScopes = true)`, which the guide says to use only with full understanding of the scope change. Beans used during startup are not affected: use an `@Alternative`. Strategy choice: [mocking](./mocking.md).

```java
// Quarkus 3.40
@QuarkusTest
class GreetingTest {
    @InjectMock GreetingService service;                 // @ApplicationScoped bean

    @InjectMock @MockitoConfig(convertScopes = true)
    LegacySingleton legacy;                              // @Singleton bean only

    @Test void greets() {
        Mockito.when(service.greet()).thenReturn("mocked");
        given().when().get("/hello").then().body(is("mocked"));
    }
}
```

Source: https://quarkus.io/version/3.40/guides/getting-started-testing

