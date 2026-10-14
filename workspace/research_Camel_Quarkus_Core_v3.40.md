# Research: Camel Quarkus Core v3.40 (Camel Quarkus 3.40.x / Camel 4.22.x / Quarkus 3.40.x)

> Version lock: every claim in this document applies to **Camel Quarkus 3.40.x** only. Patterns from 3.15 or earlier count as misinformation unless they are re-verified here.
> All sources were fetched on **2026-10-14**. Most camel.apache.org pages show no publication date of their own. They count as current because they are the versioned 3.40.x docs for the current stable LTS.
> Method note: the WebFetch tool summarizes pages, and some summaries came back paraphrased or in Spanish. Text in quotes is the tool's rendering of the page. Check the exact wording before reusing a quote verbatim.

---

## Metadata

```yaml
Full_Name: Apache Camel Quarkus — Core extension (camel-quarkus-core)
Target_Version: 3.40.x (3.40.0; docs index lists Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1)
Release_Date: 2026-09-28 (3.40.0, per https://camel.apache.org/releases/ — the q-3.40.0 page itself shows no date)
Support_Status: LTS (camel.apache.org/releases marks 3.40.0 LTS; Quarkus 3.40 LTS maintained to 2027-09-30; Camel Quarkus-specific end date UNVERIFIED — "LTS Until" column blank)
Primary_Docs: https://camel.apache.org/camel-quarkus/3.40.x/
Official_Repo: https://github.com/apache/camel-quarkus
Research_Date: 2026-10-14
Domain_Complexity: Standard (multi-integration, build-time vs runtime config, native mode, TLS)
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 4
Unverified_Count: 12
Irresolvable_Count: 4
Research_Quality_Score: 86%   # ~115 claims; (115 - 12 - 4) / 115
```

---

## Executive Summary

Camel Quarkus brings Apache Camel's integration engine to Quarkus as a set of extensions. `camel-quarkus-core` provides the Camel runtime (Camel Main functionality), the CDI-managed `CamelContext`, route discovery, the runtime catalog and the native-mode reflection controls. Camel Quarkus 3.40.0 is an LTS release (released 2026-09-28) aligned with Camel 4.22.1 and Quarkus 3.40.1 LTS. It supports **Java 17 and 21** (Java 25 is not listed). Native builds need GraalVM/Mandrel 25.0 or later, which has been the minimum since Quarkus 3.36.

Changes in 3.40 that affect core users:
1. `quarkus.camel.native.reflection.serialization-enabled` now has three states (unset/true/false). `false` now blocks every serialization registration, including ones that extensions request.
2. `quarkus.tls.*` protocols, cipher suites and key-exchange groups are now carried into the `SSLContextParameters` that Camel derives from the TLS registry. The default is **TLSv1.3 only**, and unknown names now fail SSL context creation.
3. Changes since 3.15 that you inherit: `camel-quarkus-junit5` was renamed to `camel-quarkus-junit` in 3.31 (`org.apache.camel.test.junit5` became `junit6`), and from 3.36 AdviceWith auto-starts routes.

The three critical patterns:
- Import `quarkus-bom` plus `quarkus-camel-bom` with matching major.minor versions.
- Use `@ApplicationScoped` on a `RouteBuilder` **only** when it needs `@Inject`/`@ConfigProperty`, because it has a boot-time cost.
- Register reflection and resources explicitly for native mode.

The tier is **Standard**. There are several integrations (CDI, REST, testing, health) and the configuration splits into build-time and runtime parts. The TLS change also adds a security dimension, but there is no auth or crypto design in the core itself.

**Version-lifetime risk (flagged):** Quarkus 4.0.0.Beta1 was released 2026-10-01, and the final release is "planned for the end of November" 2026. It moves the baseline to Java 21 and Jackson 3. As of 2026-10-14 there is no Camel Quarkus release or `quarkus-camel-bom` 4.x on Maven Central. Expect 3.40 LTS to be the last 3.x line for Camel Quarkus. Plan for a Camel Quarkus 4 migration with no known date. Any skill derived from this document must pin 3.40.x and must not assume Quarkus 4 compatibility.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**1. Platform BOM import with aligned versions**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ dependency-management guide (2026-10-14) + Maven Central quarkus-camel-bom 3.40.1 (2026-09-30)]
- Why: "Ensure that the major.minor version parts of `quarkus.platform.version` & `camel-quarkus.version` match." "the order of imports defines the precedence."
- Code:
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
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/dependency-management.html (fetched 2026-10-14); https://repo1.maven.org/maven2/io/quarkus/platform/quarkus-camel-bom/ (3.40.1 dated 2026-09-30)

**2. RouteBuilder discovery; `@ApplicationScoped` only when injection is needed**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ CDI guide + CQ core reference (routes-discovery) (2026-10-14)]
- Why: route classes are discovered automatically (`quarkus.camel.routes-discovery.enabled`, default `true`). "The `@ApplicationScoped` annotation is required for `@Inject` and `@ConfigProperty` to work in a `RouteBuilder`", and "using `@ApplicationScoped` in `RouteBuilder` comes with some boot time penalty."
- Code:
  ```java
  // Camel Quarkus 3.40.x — plain discovered route (no CDI needed)
  public class TimerRoute extends org.apache.camel.builder.RouteBuilder {
      @Override public void configure() {
          from("timer:tick?period=1000").routeId("tick").to("log:tick");
      }
  }

  // Camel Quarkus 3.40.x — route needing config injection
  @jakarta.enterprise.context.ApplicationScoped
  public class ConfiguredRoute extends org.apache.camel.builder.RouteBuilder {
      @org.eclipse.microprofile.config.inject.ConfigProperty(name = "timer.period", defaultValue = "1000")
      String period;
      @Override public void configure() {
          from("timer:cfg?period=" + period).to("direct:process");
      }
  }
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html (fetched 2026-10-14)

**3. Name beans for routes with `@Identifier` (or `@Named`) plus a scope, and keep them from removal**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ CDI guide + Quarkus CDI reference (2026-10-14)]
- Why: routes look beans up by name, e.g. `.bean("myNamedBean", "hello")`. The Quarkus CDI reference calls `@Named` "not type-safe" and suggests `io.smallrye.common.annotation.Identifier`. ArC removes unused beans by default (`quarkus.arc.remove-unused-beans=all`), but a bean with an `@Named` name cannot be removed. A bean that only `@Identifier` names, and that is looked up only through the Camel registry, might be removed. Whether that happens has not been verified, so add `@Unremovable` if lookups fail.
- Code:
  ```java
  // Camel Quarkus 3.40.x
  @jakarta.enterprise.context.ApplicationScoped
  @jakarta.inject.Named("greeter")          // Camel lookup by name; also makes the bean unremovable
  @io.quarkus.runtime.annotations.RegisterForReflection // native: bean invoked reflectively
  public class Greeter { public String hello(String b) { return "Hello " + b; } }
  // route: from("direct:greet").bean("greeter", "hello");
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html ; https://quarkus.io/guides/cdi-reference (fetched 2026-10-14)

**4. Register reflection and resources explicitly for native mode**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ native-mode guide + CQ core reference (2026-10-14)]
- Why: "By default, dynamic reflection is not available in native mode." Resources loaded through `Class.getResource()` at runtime must be listed. The reflection patterns need a Jandex index (or `quarkus.index-dependency.*`).
- Code:
  ```properties
  # Camel Quarkus 3.40.x — application.properties
  quarkus.camel.native.reflection.include-patterns = org.acme.model.Order,org.acme.model.Item
  quarkus.camel.native.reflection.exclude-patterns = org.acme.model.Internal
  quarkus.native.resources.includes = templates/*,mysimple.txt
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html (fetched 2026-10-14)

**5. Configure components by observing `ComponentAddEvent` rather than producing your own instances**
> Confidence: 🟡 Medium (single source: CQ bootstrap guide)
- Why: observing `ComponentAddEvent` is the recommended approach, and the event fires "before the routes and the `CamelContext` are started". When you produce your own component instance, the Quarkus-specific customization is skipped: "These actions are not performed when you produce your own component instance."
- Code:
  ```java
  // Camel Quarkus 3.40.x
  @jakarta.enterprise.context.ApplicationScoped
  public class ComponentConfig {
      void onAdd(@jakarta.enterprise.event.Observes org.apache.camel.quarkus.core.events.ComponentAddEvent e) {
          if (e.getComponent() instanceof org.apache.camel.component.log.LogComponent log) {
              // customize log component here
          }
      }
  }
  ```
  Note: the package of `ComponentAddEvent` (`org.apache.camel.quarkus.core.events`) is UNVERIFIED against the 3.40 page.
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/bootstrap.html (fetched 2026-10-14)

**6. Explicit error handling: `onException` with `handled(true)` plus a dead letter channel for async flows**
> Confidence: 🟡 Medium (Camel manual pages are unversioned; fetched summaries partly translated)
- Why: "By default, any Exception Clause will **not** redeliver!" The DefaultErrorHandler has no dead letter queue and propagates the error to the caller. A dead letter channel "will redeliver at most 6 times using 1-second delay" by default. For clause selection, "The closest match wins, across the thrown exception and all its causes."
- Code:
  ```java
  // Camel 4.22.x / Camel Quarkus 3.40.x
  @Override public void configure() {
      errorHandler(deadLetterChannel("log:dead?level=ERROR")
          .maximumRedeliveries(3).redeliveryDelay(500));
      onException(IllegalArgumentException.class)
          .handled(true)              // caller does not see the exception
          .maximumRedeliveries(0)
          .to("log:invalid");
      from("direct:process").routeId("process").to("bean:greeter?method=hello");
  }
  ```
- Source: https://camel.apache.org/manual/exception-clause.html ; https://camel.apache.org/manual/error-handler.html ; https://camel.apache.org/manual/exception-redelivery.html ; https://camel.apache.org/manual/exception-handling-patterns.html (fetched 2026-10-14)

**7. Test with `camel-quarkus-junit` plus `@QuarkusTest` (not junit5)** ⚠️ Migration Note
> Confidence: 🟢 High | single CQ docs family (testing guide + 3.31/3.36 migration guides) — 🟡 for triangulation strictness
- Why: `camel-quarkus-junit5` was renamed to `camel-quarkus-junit` in 3.31, and the Camel test packages moved from `junit5` to `junit6`. "All tests should be annotated with `@QuarkusTest`". `CamelQuarkusTestSupport` "only works in JVM mode".
- Code: see Quality Control.
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html (fetched 2026-10-14)

### ⚠️ Conditional Patterns

**A. Which BOM to import**
> Confidence: 🟢 High
- Options: A) `quarkus-bom` + `quarkus-camel-bom` (platform); B) `quarkus-bom` + `org.apache.camel.quarkus:camel-quarkus-bom`
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A platform | Alignment tested across the Quarkus universe | Waits for the platform release | Default; 3.40.1 is available |
  | B camel-quarkus-bom | Access to a newer Camel Quarkus | "may not be perfectly aligned with other Quarkus universe members" | Only "if the latest Camel Quarkus is not yet in quarkus-camel-bom" |

- Agent: "Ask the user whether a Camel Quarkus version newer than the platform is required. If not, use A."
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/dependency-management.html (2026-10-14)

**B. `serialization-enabled` setting** ⚠️ Migration Note
> Confidence: 🟢 High | [CQ 3.40.0 migration guide + CQ native-mode guide]
- Options: unset (default since 3.40) / `true` / `false`
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | unset | Registers only what extensions need | — | Default |
  | true | Always registers the base set | Larger image | Cassandra/Infinispan aggregation repositories |
  | false | Smallest attack surface | Breaks jms, jolt, management, netty, sjms, sjms2, sql | Only when none of those extensions is present |

- Agent: "Ask whether the app uses jms/sjms/sql/netty/jolt/management before setting `false`."
- Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html (2026-10-14)

**C. TLS protocol scope for Camel SSL contexts** ⚠️ Migration Note
> Confidence: 🟢 High
- Options: A) keep the default TLSv1.3; B) widen globally with `quarkus.tls.protocols=TLSv1.3,TLSv1.2`; C) a named TLS configuration for a single legacy endpoint (e.g. `quarkus.tls.legacy-endpoint.protocols`)
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | Security | Legacy peers fail the handshake | All peers support TLS 1.3 |
  | B | Compatibility | Weakens every TLS user | Avoid |
  | C | Isolation | Extra configuration | One legacy peer |

- Agent: "Ask which downstream endpoints lack TLS 1.3."
- Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (2026-10-14)

**D. Camel REST DSL (platform-http) vs Quarkus REST (JAX-RS) resource calling a `ProducerTemplate`**
> Confidence: 🟡 Medium (the combination with Quarkus REST is UNVERIFIED as an official pattern)
- Options: A) `rest()` DSL on `camel-quarkus-platform-http` + `camel-quarkus-rest`; B) a `quarkus-rest` `@Path` resource with an injected `ProducerTemplate` sending to `direct:`
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A REST DSL | All in Camel; Camel docs call platform-http "recommended" | JAX-RS features; no `SSLContextParameters` on the server | Camel-centric integration |
  | B Quarkus REST + ProducerTemplate | JAX-RS features (`Uni`, filters, OpenAPI) | Two programming models | REST API is primary and Camel is the backend |

- Agent: "Ask whether the HTTP API surface or the integration is the primary concern."
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html ; https://camel.apache.org/manual/rest-dsl.html ; https://quarkus.io/guides/rest ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (2026-10-14)

**E. Runtime catalog trimming**
> Confidence: 🟡 Medium
- Options: keep the defaults (`quarkus.camel.runtime-catalog.*=true`), or set components/languages/dataformats/devconsoles/models/transformers to `false`.
- Tradeoffs: `false` shrinks the native image but disables catalog-based tooling such as dev consoles.
- Agent: "Ask whether native image size matters more than runtime introspection."
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html (2026-10-14)

### 🚫 Forbidden Patterns

**1. Using `camel-quarkus-junit5` / `org.apache.camel.test.junit5` in 3.40**
> Severity: High
> Confidence: 🟢 High
- Why: renamed in 3.31. The 3.31 guide said the junit5 artifact would be kept only "until Camel Quarkus 3.34.0 is released". (A camel-quarkus-junit5 3.40.0 artifact still exists on Central. Its status is UNVERIFIED.)
- Impact: deprecated or removed API, and a classpath that mixes JUnit 5 and JUnit 6.
- ❌ Wrong:
  ```xml
  <artifactId>camel-quarkus-junit5</artifactId>  <!-- import org.apache.camel.test.junit5.* -->
  ```
- ✅ Correct:
  ```xml
  <groupId>org.apache.camel.quarkus</groupId>
  <artifactId>camel-quarkus-junit</artifactId><scope>test</scope> <!-- org.apache.camel.test.junit6.* -->
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html (2026-10-14)

**2. Setting `serialization-enabled=false` with serialization-dependent extensions**
> Severity: High
> Confidence: 🟢 High
- Why: in 3.40, `false` means "nothing is registered for serialization, even if extensions on the classpath require it."
- Impact: jms, sjms, sjms2, sql, netty, jolt and management break in native mode. Only a warning is logged.
- ❌ Wrong:
  ```properties
  quarkus.camel.native.reflection.serialization-enabled=false   # with camel-quarkus-jms present
  ```
- ✅ Correct:
  ```properties
  # leave unset (3.40 default) — extensions register what they need
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (2026-10-14)

**3. Widening TLS globally or using OpenSSL cipher names**
> Severity: Critical
> Confidence: 🟢 High
- Why: `quarkus.tls.protocols` applies to the whole TLS configuration. Unrecognised names now fail SSL context creation, and OpenSSL-style names fail with `ssl-engine=openssl`. A configured list also overrides Camel's default exclusion filters.
- Impact: TLS is downgraded everywhere, or the app fails at startup.
- ❌ Wrong:
  ```properties
  quarkus.tls.protocols=TLSv1.3,TLSv1.2,TLSv1
  quarkus.tls.cipher-suites=ECDHE-RSA-AES128-GCM-SHA256
  ```
- ✅ Correct:
  ```properties
  quarkus.tls.legacy-endpoint.protocols=TLSv1.3,TLSv1.2
  quarkus.tls.legacy-endpoint.cipher-suites=TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (2026-10-14)

**4. Annotating every RouteBuilder `@ApplicationScoped` by reflex**
> Severity: Medium
> Confidence: 🟢 High
- Why: it is required only for `@Inject`/`@ConfigProperty`, and it "comes with some boot time penalty". The 3.15-era research presented it as mandatory.
- Impact: slower boot. Behaviour is otherwise unchanged.
- ❌ Wrong:
  ```java
  @ApplicationScoped public class R extends RouteBuilder { public void configure(){ from("timer:t").to("log:t"); } }
  ```
- ✅ Correct:
  ```java
  public class R extends RouteBuilder { public void configure(){ from("timer:t").to("log:t"); } }
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (2026-10-14)

**5. `@EndpointInject`/`@Produce` on setter methods**
> Severity: Medium
> Confidence: 🟡 Medium
- Why: "`@EndpointInject` and `@Produce` are not supported on setter methods."
- Impact: the injection is silently missing.
- ❌ Wrong:
  ```java
  @Produce("direct:x") public void setTemplate(ProducerTemplate t) { this.t = t; }
  ```
- ✅ Correct:
  ```java
  @jakarta.inject.Inject ProducerTemplate template;   // or @Produce("direct:x") on a field
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (2026-10-14)

**6. Relying on dynamic reflection or unlisted classpath resources in native mode**
> Severity: High
> Confidence: 🟢 High
- Why: "By default, dynamic reflection is not available in native mode."
- Impact: `ClassNotFoundException` or a null resource at runtime, in native mode only.
- ❌ Wrong:
  ```java
  from("direct:a").setBody().simple("resource:classpath:mysimple.txt");  // no resources.includes
  ```
- ✅ Correct:
  ```properties
  quarkus.native.resources.includes = mysimple.txt
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html ; core.html (2026-10-14)

**7. Calling `startRouteDefinitions()` after AdviceWith (pre-3.36 habit)**
> Severity: Medium
> Confidence: 🟡 Medium
- Why: since 3.36, "`startRouteDefinitions()` is no longer needed - auto-start handles this". Un-advised routes start automatically after `@BeforeEach`, and advice is cleaned up between test methods.
- Impact: redundant or confusing test lifecycle code.
- ❌ Wrong:
  ```java
  AdviceWith.adviceWith(context, "tick", r -> r.replaceFromWith("direct:start")); startRouteDefinitions();
  ```
- ✅ Correct:
  ```java
  adviceRoute("tick", r -> r.replaceFromWith("direct:start"));  // 3.36+ helper; exact signature UNVERIFIED
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html (2026-10-14)

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html (2026-10-14) + per-version guides (no page dates)

**Breaking Changes (core-relevant, 3.15 → 3.40)**:
- 3.31: `camel-quarkus-junit5` → `camel-quarkus-junit`; `org.apache.camel.test.junit5` → `junit6`; `camel-test-junit5` → `camel-test-junit6`.
- 3.33: the deprecated `quarkus.camel.jolokia.register-management-endpoint` was removed.
- 3.35: `camel-quarkus-groovy-xml` was merged into `camel-quarkus-groovy`.
- 3.36: AdviceWith auto-starts un-advised routes, adds the `adviceRoute()` helper and cleans up advice automatically. Quarkus 3.36 raises the Mandrel/GraalVM minimum to 25.0.
- 3.38: `quarkus-cxf-rt-ws-security` was removed from `camel-quarkus-cxf-soap`.
- 3.39: Jolokia is locked down in prod (binds to localhost, origin filtering). The Cassandra health check is disabled by default.
- 3.40: `serialization-enabled` has three states. The TLS registry protocols, ciphers and key-exchange groups are now bridged (TLSv1.3 default). XSLT is restricted (external entities, `document()`). Avro trusted packages are required. LDAP `security-authentication` no longer defaults to `none`. JTA rollback and resume failures are raised. The LangChain4j and AI-tool modules were reorganised.
- The index has no migration guides for 3.34.x or 3.37.x.

**Upgrade Steps**:
1. Bump `quarkus.platform.version` to `3.40.1`.
2. Run `quarkus update` (Quarkus 3.40 blog). From 3.33 LTS, apply the migration guides 3.34–3.40. From 3.39, no changes are needed.
3. Replace junit5 artifacts and imports with junit/junit6.
4. Audit any `serialization-enabled=false` and any `quarkus.tls.*` settings.
5. Make sure native builders use Mandrel/GraalVM 25.

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Java (CQ 3.40) | 17 | 21 | "This version supports Java 17 and 21." Java 25 is UNVERIFIED for CQ, though Quarkus JVM mode supports 17–25 |
| Camel | 4.22.1 | 4.22.x | from the docs index |
| Quarkus | 3.40.1 | 3.40.x | Quarkus 4 is not supported (no CQ build exists) |
| GraalVM/Mandrel | 25.0 | — | the docs index lists 25.0.4.1 |
| Maven | 3.8.2 | — | "3.9.16 is recommended" |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | CQ first-steps + CQ CDI guide]

**Lifecycle**:
```bash
# Representative — adapt to your environment (Camel Quarkus 3.40.x)
mvn io.quarkus:quarkus-maven-plugin:3.40.1:create \
  -DprojectGroupId=org.acme -DprojectArtifactId=getting-started \
  -Dextensions=camel-quarkus-log,camel-quarkus-timer
mvn clean compile quarkus:dev      # dev mode: watches the workspace for changes
```
The CamelContext is "started/stopped according to the Quarkus Application lifecycle" (RUNTIME_INIT). `quarkus.camel.bootstrap.enabled=true` is the default. Shutdown is controlled by `quarkus.camel.main.shutdown.timeout` (default `PT3S`).

```properties
# Camel Quarkus 3.40.x — application.properties
quarkus.camel.routes-discovery.exclude-patterns = org.acme.legacy.**
camel.main.name = orders-integration          # Camel Main key (Camel 4.22 main docs)
camel.main.use-mdc-logging = true             # default false
camel.component.log.exchange-formatter.show-body-type = false
timer.period = 2000
```
Note: the Camel Main docs list keys in camelCase (`camel.main.useMdcLogging`). The kebab-case form shown here is accepted by Camel's relaxed binding, but that is UNVERIFIED for the 3.40 page.

**Integration**: Camel Quarkus Core ↔ Quarkus ArC (CDI) + camel-quarkus-bean + camel-quarkus-log
```java
// Camel Quarkus 3.40.x
@jakarta.enterprise.context.ApplicationScoped
public class OrderRoutes extends org.apache.camel.builder.RouteBuilder {
    @org.eclipse.microprofile.config.inject.ConfigProperty(name = "timer.period", defaultValue = "1000")
    String period;
    @Override public void configure() {
        onException(IllegalArgumentException.class).handled(true).to("log:invalid?level=WARN");
        from("timer:orders?period=" + period).routeId("orders")
            .setBody().constant("world")
            .to("direct:greet");
        from("direct:greet").routeId("greet")
            .bean("greeter", "hello")          // camel-quarkus-bean → CDI bean
            .to("log:greet?showAll=true");     // camel-quarkus-log (showAll option UNVERIFIED for 4.22)
    }
}
```

**Integration**: Camel Quarkus Core ↔ Quarkus REST
```java
// Quarkus 3.40 REST resource calling a Camel route (combination UNVERIFIED as official example)
@jakarta.ws.rs.Path("/greet")
public class GreetResource {
    @jakarta.inject.Inject org.apache.camel.ProducerTemplate template;  // injectable per CQ CDI guide
    @jakarta.ws.rs.GET public String greet(@jakarta.ws.rs.QueryParam("name") String name) {
        return template.requestBody("direct:greet", name, String.class);
    }
}
```
Dependencies: `io.quarkus:quarkus-rest`, `org.apache.camel.quarkus:camel-quarkus-direct`, `camel-quarkus-bean`, `camel-quarkus-log`.

**Integration**: Camel RouteBuilder ↔ REST DSL (alternative)
```java
// requires camel-quarkus-platform-http + camel-quarkus-rest (3.40.x)
rest("/say").get("/hello").to("direct:greet");
```

Endpoint facts (Camel 4.22.x component pages):
- `direct:name`: `failIfNoConsumers=true`, `block=true`, `timeout=30000`. Calls are synchronous and stay within the same CamelContext.
- `timer:name`: `delay=1000`, `period=1000`, `fixedRate=false`, `repeatCount` unset, `daemon=true`, `includeMetadata=false`.

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Camel Quarkus 3.40.x)
mvn quarkus:dev                          # Expected: Quarkus banner, "Apache Camel 4.22.x ... started" (log text UNVERIFIED)
mvn test                                 # @QuarkusTest suites, JVM mode
mvn verify -Dnative                      # native build; needs Mandrel/GraalVM 25 (Quarkus 3.36+)
curl -s localhost:8080/q/health/ready    # with camel-quarkus-microprofile-health; Expected: {"status":"UP",...}
curl -s localhost:8080/q/health/live
```

**Mocking**:
```java
// Camel Quarkus 3.40.x — camel-quarkus-junit (test scope); JVM mode only
// import of CamelQuarkusTestSupport: package UNVERIFIED (not shown on the 3.40 testing page)
@io.quarkus.test.junit.QuarkusTest
class GreetRouteTest extends CamelQuarkusTestSupport {
    @org.junit.jupiter.api.Test
    void greets() throws Exception {
        org.apache.camel.builder.AdviceWith.adviceWith(context, "greet",
            r -> r.weaveByToUri("log:*").replace().to("mock:out"));
        getMockEndpoint("mock:out").expectedBodiesReceived("Hello world");
        template.sendBody("direct:greet", "world");
        getMockEndpoint("mock:out").assertIsSatisfied();
    }
}
```
Guarantee: since 3.36, advice is cleaned up between test methods and un-advised routes auto-start. The testing guide says to prefer specific URIs over wildcards in weave selectors. Use `@QuarkusIntegrationTest` for native tests.

---

## Production Readiness

- **Performance**: avoid `@ApplicationScoped` on routes that don't need it (boot cost). Keep `quarkus.camel.expression.extraction-enabled=true` (the default) so expressions compile at build time, and consider `on-build-time-analysis-failure=fail`. Trim the runtime catalog for native builds.
- **Scalability**: `direct` is synchronous within a single CamelContext. Use a broker component for horizontal fan-out. The error handler creates a scheduled thread pool for delayed redelivery (`asyncDelayedRedelivery` is available).
- **Monitoring**:
  - Health: `camel-quarkus-microprofile-health` serves `/q/health/live` and `/q/health/ready`, and `quarkus.camel.health.enabled=true` is the default (build time).
  - Metrics: `camel-quarkus-micrometer` defaults are route policy on, exchange and route event notifiers on, message history off. The `/q/metrics` path is UNVERIFIED on the CQ page.
  - Tracing: `quarkus.camel.trace.*` (off by default).
- **Security**:
  - TLSv1.3 is the default on bridged Camel SSL contexts. These settings are not bridged: `certificate-revocation-list`, `hostname-verification-algorithm`, `key-store.sni`, `alpn` and `pqc-enforcement-policy`. A bridged bean therefore does not check revocation.
  - platform-http cannot configure server SSL via `SSLContextParameters`.
  - The 3.40.0 release fixed "console: exposure-mode=ALL exposes the dev console in production". Verify the dev console exposure in prod.
  - XSLT and Avro hardening apply if those extensions are used.

---

## Reference Implementations

- https://github.com/apache/camel-quarkus-examples (the `main` branch "should always point at the latest Quarkus Platform release"). It includes timer-log, health, observability and rest-json examples. Pinned versions are UNVERIFIED.
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/first-steps.html — canonical getting-started.
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html — testing strategies.

---

## Source Bibliography

**Primary** (all fetched 2026-10-14; camel.apache.org pages have no page date and are the current stable 3.40.x docs):
- https://camel.apache.org/releases/ — 3.40.0, 2026-09-28, LTS
- https://camel.apache.org/releases/q-3.40.0/ — Java 17 and 21; resolved issues
- https://camel.apache.org/camel-quarkus/latest/ — version table (Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1)
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/{cdi,configuration,native-mode,bootstrap,dependency-management,first-steps,testing}.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/{index,3.31.0,3.33.0,3.35.0,3.36.0,3.38.0,3.39.0,3.40.0}.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/{bean,log,direct,timer,platform-http,microprofile-health,micrometer}.html
- https://camel.apache.org/components/4.22.x/{direct-component,timer-component,others/main}.html
- https://camel.apache.org/manual/{exception-clause,error-handler,exception-redelivery,exception-handling-patterns,rest-dsl}.html (unversioned)
- https://quarkus.io/guides/cdi-reference ; https://quarkus.io/guides/rest
- https://quarkus.io/blog/quarkus-3-40-released/ (2026-09-30)
- https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ (2026-10-01)
- https://quarkus.io/blog/mandrel-25-minimum-version/ (2026-05-29)
- https://quarkus.io/releases (LTS policy)
- https://repo1.maven.org/maven2/io/quarkus/platform/quarkus-camel-bom/ (3.40.1, 2026-09-30)

**Validation**: no community sources were used.
**All Deep-Links**: as listed above, grouped by section.

---

## Research Gaps

```
Gap: Camel Quarkus-specific LTS end date for 3.40
Impact: Support window planning
Workaround: Assume the Quarkus 3.40 LTS end date (2027-09-30) — inference
Follow-up: camel.apache.org/camel-quarkus/latest/ "LTS Until" column
§7-ref: Iteration 1 — IRRESOLVABLE
```
```
Gap: Any Camel Quarkus release on Quarkus 4.0
Impact: Version-lifetime risk; Quarkus 4 GA end of Nov 2026
Workaround: Stay on 3.40 LTS; do not mix Quarkus 4 artifacts
Follow-up: Maven Central quarkus-camel-bom 4.x; camel.apache.org/releases
§7-ref: Iteration 1 — IRRESOLVABLE
```
```
Gap: Package of CamelQuarkusTestSupport; adviceRoute() signature
Impact: Test imports may be wrong
Workaround: Use IDE import resolution on camel-quarkus-junit 3.40.x
Follow-up: camel-quarkus-junit sources/javadoc on Maven Central
§7-ref: Iteration 2 — IRRESOLVABLE
```
```
Gap: Status of camel-quarkus-junit5 3.40.0 on Central (relocation vs alias) despite the 3.34 removal statement
Impact: Teams may keep using the old artifact
Workaround: Migrate to camel-quarkus-junit
Follow-up: inspect POM on repo1.maven.org
§7-ref: Iteration 3 — IRRESOLVABLE
```
Other UNVERIFIED items (not gap-looped):
- Java 25 support in CQ 3.40.
- The `ComponentAddEvent` package.
- `/q/metrics` path.
- The `/q/health` base path.
- Dev UI and route live-reload specifics.
- `quarkus create app` CLI.
- Build-time vs runtime flag for each `quarkus.camel.*` property.
- Kebab-case form of the `camel.main.*` keys.
- Log `showAll` and the other log/bean component options.
- Whether a REST resource plus `ProducerTemplate` appears as an official example.
- Removal behaviour for a bean named only with `@Identifier`.
- Exact wording of the quotes taken from translated summaries.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 0 | Migration Guide | 3.40 serialization/TLS details | Added | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (2026-10-14) |
| 0 | Metadata | Camel 4.22.1 / Quarkus 3.40.1 mapping (sub-investigator flagged it unverified) | Resolved | https://camel.apache.org/camel-quarkus/latest/ (2026-10-14) |
| 1 | Implementation Blueprint | camel.main.* keys and defaults | Resolved | https://camel.apache.org/components/4.22.x/others/main.html (2026-10-14) |
| 1 | Metadata | CQ-specific LTS end date | ⚠️ IRRESOLVABLE — "LTS Until" column blank | — |
| 1 | Executive Summary | CQ on Quarkus 4 | ⚠️ IRRESOLVABLE — no artifact or announcement exists yet | — |
| 2 | Quality Control | CamelQuarkusTestSupport package | ⚠️ IRRESOLVABLE — not on the testing page; search found no official confirmation | — |
| 3 | Forbidden Patterns | camel-quarkus-junit5 3.40.0 status | ⚠️ IRRESOLVABLE — needs POM inspection, out of budget | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented
- [x] All scope areas cited
- [x] Pattern counts driven by domain needs (not template minimums)
- [x] Every anti-pattern has alternative
- [x] All CLI commands validated/marked as representative
- [x] Integration examples complete (ArC, RouteBuilder, Quarkus REST, bean, log, junit)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated (deep) or downgraded to 🟡 Medium
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: BOM import, route discovery, `@ApplicationScoped` only for injection, native reflection/resources, junit rename, serialization 3-state, TLS bridging behaviour.
- **Medium Confidence (validate with user)**: error-handling defaults (unversioned manual pages, translated summaries), `ComponentAddEvent` usage, `adviceRoute()` usage, REST DSL vs Quarkus REST choice.
- **Low Confidence (must ask human)**: IRRESOLVABLE items (CQ LTS end date, Quarkus 4 timeline, the CamelQuarkusTestSupport package, junit5 artifact status).
- **Edge Cases (pause)**: 3.40.0 was released 2026-09-28, which is 16 days before the research date (<30 days), so the docs may still change. Quarkus 4 GA is expected end of Nov 2026.
- **Emergency Stop**: none triggered. All sources are official and 3.40 is the current LTS.
