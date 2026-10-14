# Never-Do Patterns — Camel Quarkus 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Sections 1-4 mirror the Never Do table (High facts only). The last two sections hold patterns that are not High; they are not in the table. Severity wording is low / moderate / high and is unrelated to confidence tags.

## 1. serialization-enabled=false with serialization-dependent extensions (severity: high)

In 3.40, `false` means nothing is registered for serialization, even if extensions on the classpath require it. Jms, sjms, sjms2, sql, netty, jolt and management break in native mode, and only a warning is logged.

```properties
# ❌ WRONG (with camel-quarkus-jms present)
quarkus.camel.native.reflection.serialization-enabled=false
# ✅ CORRECT: leave unset (3.40 default); extensions register what they need
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html

## 2. OpenSSL-style or unknown TLS names (severity: high)

Since 3.40.0, `quarkus.tls.*` protocols and ciphers are bridged into Camel SSL contexts built from registered beans. Unrecognised names fail SSL context creation, OpenSSL-style names fail with `ssl-engine=openssl`, and a configured list overrides Camel's default exclusion filters. Widening the scope globally is a decision, not a prohibition: see [TLS and security](./tls-and-security.md#scope-decision-ask-first).

```properties
# ❌ WRONG (OpenSSL-style name)
quarkus.tls.cipher-suites=ECDHE-RSA-AES128-GCM-SHA256
# ✅ CORRECT: JSSE name
quarkus.tls.cipher-suites=TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html

## 3. @ApplicationScoped on a RouteBuilder with no injection (severity: low)

The annotation is needed only for `@Inject` or `@ConfigProperty`, and it adds boot-time cost only. It is never mandatory (source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html, fetched 2026-10-14).

```java
// ❌ WRONG (no injection used)
@ApplicationScoped public class R extends RouteBuilder { public void configure(){ from("timer:t").to("log:t"); } }
// ✅ CORRECT
public class R extends RouteBuilder { public void configure(){ from("timer:t").to("log:t"); } }
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html

## 4. Dynamic reflection or unlisted resources in native mode (severity: high)

Causes `ClassNotFoundException` or a null resource at runtime, in native mode only.

```java
// ❌ WRONG (no resources.includes)
from("direct:a").setBody().simple("resource:classpath:mysimple.txt");
```
```properties
# ✅ CORRECT
quarkus.native.resources.includes = mysimple.txt
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html

## Medium-confidence patterns (not in the Never Do table)

### @EndpointInject / @Produce on setter methods (severity: moderate) (medium confidence)

Reported as not supported; the injection is silently missing. Single source in the research (M7).

```java
// ❌ WRONG
@Produce("direct:x") public void setTemplate(ProducerTemplate t) { this.t = t; }
// ✅ CORRECT
@jakarta.inject.Inject ProducerTemplate template;   // or @Produce("direct:x") on a field
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html

### startRouteDefinitions() after AdviceWith (severity: low) (medium confidence)

Since 3.36, "`startRouteDefinitions()` is no longer needed - auto-start handles this" (M8). Un-advised routes start automatically after `@BeforeEach`, and advice is cleaned up between test methods. The 3.36+ `adviceRoute()` helper and the Camel test-support API are covered in the skill `developing-camel-quarkus-junit-v3-40`; do not copy signatures from here.

❌ WRONG (pre-3.36 habit): advising a route by hand in the test and then calling `startRouteDefinitions()` explicitly.
✅ CORRECT: rely on auto-start; for the advice helper and its signatures see the skill `developing-camel-quarkus-junit-v3-40`.

Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html

## Prefer camel-quarkus-junit over junit5 (not a hard prohibition)

The 3.31 guide renamed `camel-quarkus-junit5` to `camel-quarkus-junit` (packages `junit5` to `junit6`) and said the old artifact would be kept only "until Camel Quarkus 3.34.0 is released". `camel-quarkus-junit5` 3.40.0 is still published on Maven Central as a deprecated stub (name "Junit5 (Deprecated)", description "DEPRECATED: This artifact has moved to org.apache.camel.quarkus:camel-quarkus-junit", only dependency `camel-quarkus-junit`, no relocation element; [POM](https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom), fetched 2026-10-14). When the stub will be removed is (unverified). Prefer `camel-quarkus-junit`, the only artifact documented in the official 3.40 testing guide.

```xml
<!-- Prefer -->
<artifactId>camel-quarkus-junit</artifactId><scope>test</scope> <!-- org.apache.camel.test.junit6.* -->
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html
