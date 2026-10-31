# Always-Do Patterns — Camel Quarkus 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## 1. BOM import

Confidence: high (dependency-management guide, 2026-10-14, plus Maven Central `quarkus-camel-bom` 3.40.1, 2026-09-30).
The major.minor parts of `quarkus.platform.version` and `camel-quarkus.version` must match.

Import order defines precedence (unverified: the quoted wording comes from a tool summary; re-check before quoting verbatim).

```xml
<!-- Camel Quarkus 3.40.x -->
<properties>
  <quarkus.platform.version>3.40.1</quarkus.platform.version>
</properties>
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>io.quarkus.platform</groupId>
      <artifactId>quarkus-bom</artifactId>
      <version>${quarkus.platform.version}</version>
      <type>pom</type><scope>import</scope>
    </dependency>
    <dependency>
      <groupId>io.quarkus.platform</groupId>
      <artifactId>quarkus-camel-bom</artifactId>
      <version>${quarkus.platform.version}</version>
      <type>pom</type><scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/dependency-management.html

## 2. RouteBuilder discovery

Confidence: high (CDI guide plus core reference). Route classes are discovered automatically. `@ApplicationScoped` is needed for `@Inject` and `@ConfigProperty` in a RouteBuilder, and it has a boot-time cost. It is not needed otherwise.

```java
// Camel Quarkus 3.40.x: plain discovered route
public class TimerRoute extends org.apache.camel.builder.RouteBuilder {
    @Override public void configure() {
        from("timer:tick?period=1000").routeId("tick").to("log:tick");
    }
}

// Route needing config injection
@jakarta.enterprise.context.ApplicationScoped
public class ConfiguredRoute extends org.apache.camel.builder.RouteBuilder {
    @org.eclipse.microprofile.config.inject.ConfigProperty(name = "timer.period", defaultValue = "1000")
    String period;
    @Override public void configure() {
        from("timer:cfg?period=" + period).to("direct:process");
    }
}
```

Exclude classes with `quarkus.camel.routes-discovery.exclude-patterns = org.acme.legacy.**`.
Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html

## 3. Named beans

Confidence: high for `@Named` and for `@Identifier` lookup. Routes look beans up by name, for example `.bean("greeter", "hello")`. ArC removes unused beans by default (`quarkus.arc.remove-unused-beans=all`), but a bean with an `@Named` name cannot be removed.

```java
// Camel Quarkus 3.40.x
@jakarta.enterprise.context.ApplicationScoped
@jakarta.inject.Named("greeter")
@io.quarkus.runtime.annotations.RegisterForReflection // native: bean invoked reflectively
public class Greeter { public String hello(String b) { return "Hello " + b; } }
// route: from("direct:greet").bean("greeter", "hello");
```

`@Identifier` (High for lookup, verified 2026-10-14): the Camel Quarkus CDI page says "As an alternative to @Named, you may also use io.smallrye.common.annotation.Identifier to name and identify a bean". The Quarkus CDI reference says "Instead of `@Named`, use `@io.smallrye.common.annotation.Identifier`" (exception: an external language such as Qute needs the bean name). Whether ArC removes an `@Identifier`-only bean looked up solely through the Camel registry is (unverified): the CDI reference lists only `@Named`, observers and explicit exclusions as unremovable. Add `@io.quarkus.arc.Unremovable` to such a bean.
Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html ; https://quarkus.io/version/3.40/guides/cdi-reference

## 4. Native reflection and resources

Confidence: high. "By default, dynamic reflection is not available in native mode." Resources read via `Class.getResource()` must be listed. Reflection patterns need a Jandex index (or `quarkus.index-dependency.*`). More in [native-mode.md](./native-mode.md).

```properties
# Camel Quarkus 3.40.x: application.properties
quarkus.camel.native.reflection.include-patterns = org.acme.model.Order,org.acme.model.Item
quarkus.camel.native.reflection.exclude-patterns = org.acme.model.Internal
quarkus.native.resources.includes = templates/*,mysimple.txt
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html ; core.html

## 5. Testing artifact

Confidence: high on the rename (3.31 migration guide) and on the testing guide. Use `camel-quarkus-junit` (test scope), `org.apache.camel.test.junit6.*`, `@QuarkusTest`. Test-support class details live in the skill `developing-camel-quarkus-junit-v3-40`. See [integration-examples.md](./integration-examples.md#testing).

```xml
<dependency>
  <groupId>org.apache.camel.quarkus</groupId>
  <artifactId>camel-quarkus-junit</artifactId>
  <scope>test</scope>
</dependency>
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html
