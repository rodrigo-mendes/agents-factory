# Always-Do Patterns: Quarkus ArC 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Patterns 1-5 are tagged High in the research and rest on versioned 3.40 pages; pattern 6 is (medium confidence, L1). Other medium-confidence items (private members, `@Startup`) are in [scopes and injection](./scopes-and-injection.md).

## Contents

1. [Bean-defining annotation](#1-bean-defining-annotation)
2. [Unremovable for programmatic lookup](#2-unremovable-for-programmatic-lookup)
3. [Identifier instead of Named](#3-identifier-instead-of-named)
4. [Index external bean archives](#4-index-external-bean-archives)
5. [RouteBuilder scope only when injecting](#5-routebuilder-scope-only-when-injecting)
6. [Mockito artifact for InjectMock](#6-mockito-artifact-for-injectmock)

## 1. Bean-defining annotation

Discovery uses a single bean archive in annotated mode. A class without a bean-defining annotation is not discovered. Exception: a class that declares producers or observers is treated as `@Dependent`. The [CDI guide](https://quarkus.io/version/3.40/guides/cdi) recommends `@ApplicationScoped` by default; `@Singleton` is slightly faster but has no client proxy and cannot be mocked with `QuarkusMock`.

```java
@ApplicationScoped            // normal scope: lazy client proxy, mockable
public class GreetingService {
    String greet(String n) { return "Hello " + n; }
}
```

Sources: https://quarkus.io/version/3.40/guides/cdi ; https://quarkus.io/version/3.40/guides/cdi-reference

## 2. Unremovable for programmatic lookup

The default is `quarkus.arc.remove-unused-beans=all`. ArC cannot detect lookups through `CDI.current()`, so a bean used only that way may be removed by mistake. Beans annotated `@io.quarkus.arc.Unremovable`, types listed in `quarkus.arc.unremovable-types`, beans covered by an `UnremovableBeanBuildItem`, `@Named` beans and beans with an observer method are never removed.

```java
@ApplicationScoped
@Unremovable                       // io.quarkus.arc.Unremovable
public class LegacyLookup { }      // used only through CDI.current().select(...)
```

Details and the `@Identifier` open question: [bean removal](./bean-removal.md).

Sources: https://quarkus.io/version/3.40/guides/cdi-reference ; https://quarkus.io/version/3.40/guides/cdi-integration

## 3. Identifier instead of Named

The Quarkus [CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference) says to use `@io.smallrye.common.annotation.Identifier` instead of `@Named`, except where an external language such as Qute needs the bean name. This is a recommendation, not a documented failure: the stated reason is that a `@Named`-only bean also gets `@Default` and can become ambiguous (see Ask First in SKILL.md).

```java
@ApplicationScoped @Identifier("primary") class PrimaryClient implements Client {}

@Inject @Identifier("primary") Client client;
```

Sources: https://quarkus.io/version/3.40/guides/cdi-reference ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html

## 4. Index external bean archives

Dependencies are scanned only if they have `beans.xml`, a `META-INF/jandex.idx`, or a `quarkus.index-dependency.<name>.group-id/artifact-id` entry. Otherwise their classes are "not discovered". The page documents the jandex-maven-plugin and the Gradle Jandex plugin; read the versions there.

```properties
quarkus.index-dependency.mylib.group-id=com.acme
quarkus.index-dependency.mylib.artifact-id=acme-model
```

Sources: https://quarkus.io/version/3.40/guides/cdi-reference ; https://quarkus.io/version/3.40/guides/cdi-integration

## 5. RouteBuilder scope only when injecting

The Camel Quarkus CDI guide says the scope is "required for @Inject and @ConfigProperty" and that annotating adds a boot-time penalty, so annotate only when you really need it. A route without injection needs no scope.

```java
// uses @ConfigProperty, so the scope is needed
@ApplicationScoped
public class TimerRoutes extends RouteBuilder {
    @ConfigProperty(name = "timer.period", defaultValue = "1000") String period;
    @Override public void configure() { fromF("timer:foo?period=%s", period).to("log:out"); }
}

// no injection, no scope
public class PlainRoutes extends RouteBuilder {
    @Override public void configure() { from("timer:bar").to("log:out"); }
}
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html

## 6. Mockito artifact for InjectMock

`@InjectMock` and `@InjectSpy` require `quarkus-junit-mockito`. The 3.40 testing guide names `quarkus-junit` and `quarkus-junit-mockito` (medium confidence, L1).

```xml
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-junit-mockito</artifactId>
  <scope>test</scope>
</dependency>
```

Source: https://quarkus.io/version/3.40/guides/getting-started-testing
