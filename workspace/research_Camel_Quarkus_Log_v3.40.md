# Research: Camel Quarkus Log v3.40 (camel-quarkus-log / Camel 4.22.x log component + Log EIP / Quarkus 3.40.x)

> Version lock: every claim here applies to **Camel Quarkus 3.40.x** (Camel 4.22.x, Quarkus 3.40.x). Patterns from 3.15 count as misinformation unless they are re-verified here.
> All sources were fetched on **2026-10-14**. camel.apache.org pages carry no page dates. They count as current because they are the versioned docs (4.22.x / 3.40.x) of the current stable LTS.
> Plan-approval step (P3 EnterPlanMode/ExitPlanMode) was **skipped**: this is a forked batch run, and the user approved the fan-out scheme in the parent session. No section-investigators were spawned (caller constraint). Every page was fetched directly by this agent.
> Scope: log-specific topics only. Core topics (BOM, CDI, RouteBuilder discovery, testing harness, Quarkus 4 risk) live in `research_Camel_Quarkus_Core_v3.40.md` and are referenced, not duplicated.

## Metadata

```yaml
Full_Name: Apache Camel Quarkus Log extension (camel-quarkus-log) — Camel "Log" component + Log EIP
Target_Version: 3.40.x (Camel Quarkus 3.40.0; Camel 4.22.1; Quarkus 3.40.1)
Release_Date: 2026-09-28 (Camel Quarkus 3.40.0, https://camel.apache.org/releases/) ; Camel 4.22.1 2026-09-17 (same page)
Support_Status: LTS (https://camel.apache.org/releases/ marks CQ 3.40.0 and Camel 4.22.x as LTS; "LTS until" not given — IRRESOLVABLE)
Primary_Docs: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/log.html ; https://camel.apache.org/components/4.22.x/log-component.html ; https://camel.apache.org/components/4.22.x/eips/log-eip.html
Official_Repo: https://github.com/apache/camel-quarkus
Research_Date: 2026-10-14
Domain_Complexity: Standard   # multi-concern (Camel options x Quarkus logging x MDC x masking); security-relevant (PII leakage) but no auth/crypto surface
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 4
Unverified_Count: 4
Irresolvable_Count: 2
Research_Quality_Score: 89%   # (54 claims - 4 unverified - 2 irresolvable) / 54
```

---

## Executive Summary

`camel-quarkus-log` (groupId `org.apache.camel.quarkus`) packages the Camel **Log** component (`log:loggerName`, producer only, "Since Camel 1.1"). It is supported in JVM and native mode "since 0.0.1". The extension page has no configuration of its own and defers to the Camel 4.22.x component page (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/log.html). The **Log EIP** (`.log("...")`) is part of the Camel core model. It is not part of this artifact. The official guidance: the EIP is "much lighter and meant for logging human logs", and the component is for logging message content with fine control (https://camel.apache.org/components/4.22.x/eips/log-eip.html). Both write through SLF4J. In Quarkus, SLF4J goes through an adapter to JBoss LogManager, so levels and formats are controlled with `quarkus.log.*` (https://quarkus.io/guides/logging).

Changes relevant to 3.40 compared with the 3.15-era conventions:
1. **MDC moved to a dedicated module.** `camel.main.useMdcLogging` and `mdcLoggingKeysPattern` are **deprecated** in favour of the `camel-mdc` component (Camel 4.15+). The Quarkus wrapper is `camel-quarkus-mdc` (since 3.29.0), configured with `quarkus.camel.mdc.*`.
2. **Masking scope is now documented.** The default `DefaultMaskingFormatter` masks key-named values, URI userinfo passwords and PEM private-key blocks.
3. **The endpoint option catalog has grown.** It now includes `showVariables`, `showRouteId`, `showRouteGroup`, `showCachedStreams`, `sourceLocationLoggerName`, `plain` and `style`.

Three critical patterns:
- (a) Keep `showAll`, `showHeaders` and `showProperties` off by default, and turn on `logMask=true` (`camel.main.logMask`) wherever bodies or headers may carry secrets.
- (b) Control Camel verbosity with `quarkus.log.category."org.apache.camel".level`. Remember that `quarkus.log.min-level` (default `DEBUG`) is **build-time** and removes TRACE paths.
- (c) Use `camel-quarkus-mdc` with `quarkus.camel.mdc.enabled=true` for correlation IDs, and render them with `%X{camel.exchangeId}` or the JSON `mdc` object.

Tier: **Standard**. The surface spans several integrations (Quarkus logging, JSON logging, MDC) and has a real data-leak risk. It has no auth or crypto surface.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**1. Use the Log component for message dumps and the Log EIP for human messages**
> Confidence: 🟢 High | [✓✓ Triangulated | log-eip.html (2026-10-14) + log-component.html (2026-10-14)]
- Why: The EIP is "much lighter and meant for logging human logs". The component gives fine control over what is printed: `show*` options, `maxChars`, `style`, `multiline`.
- Code:
  ```java
  // Camel Quarkus 3.40.x / Camel 4.22.x
  from("platform-http:/orders")
      .routeId("orders")
      .log(LoggingLevel.INFO, "Received order ${header.orderId}")          // EIP: logName defaults to route id
      .to("log:com.acme.orders?level=DEBUG&showExchangeId=true&showBodyType=true&maxChars=2000");
  ```
- Defaults: EIP `loggingLevel=INFO`, `logName` = route id (https://camel.apache.org/components/4.22.x/eips/log-eip.html). Component `level=INFO`, `maxChars=10000`, `showBody=true`, `showBodyType=true`, `multiline=false`, `showAll=false`, `showHeaders=false`, `style=Default` (https://camel.apache.org/components/4.22.x/log-component.html). — High
- Source: https://camel.apache.org/components/4.22.x/eips/log-eip.html ; https://camel.apache.org/components/4.22.x/log-component.html (2026-10-14)

**2. Turn on log masking wherever payloads or headers may carry secrets or PII**
> Confidence: 🟢 High | [✓✓ Triangulated | log-component.html + log-eip.html + main.html (2026-10-14)]
- Why: `logMask` defaults to `false` on the endpoint (https://camel.apache.org/components/4.22.x/log-component.html) and on `camel.main.logMask` (https://camel.apache.org/components/4.22.x/others/main.html). The context-level setting also covers the Log EIP (https://camel.apache.org/components/4.22.x/eips/log-eip.html). `DefaultMaskingFormatter` also masks URI userinfo passwords and PEM private keys. Certificates and public keys are not masked (log-eip.html).
- Code:
  ```properties
  # Camel Quarkus 3.40.x — application.properties
  camel.main.logMask=true
  ```
  ```java
  // Custom formatter: must implement org.apache.camel.spi.MaskingFormatter and be bound as "CamelCustomLogMask"
  @ApplicationScoped @Named("CamelCustomLogMask")
  public class PanMask implements org.apache.camel.spi.MaskingFormatter {
      public String format(String source) { return source.replaceAll("\\b\\d{12,19}\\b", "****"); }
  }
  ```
- Note: `camel.main.*` is honoured in Camel Quarkus via camel-quarkus-core. The 3.40.x command-mode guide says this only for the `camel.main.durationMax*` family ("available via camel-quarkus-core", https://camel.apache.org/camel-quarkus/3.40.x/user-guide/command-mode.html). That `logMask` behaves the same way is an inference — 🟡 Medium.
- Source: as cited above (2026-10-14)

**3. Control Camel logger verbosity with Quarkus categories, and respect the build-time min-level**
> Confidence: 🟢 High | [✓✓ Triangulated | quarkus.io/guides/logging + log-component.html (category = loggerName)]
- Why: The `log:` path parameter is the logging category (https://camel.apache.org/components/4.22.x/log-component.html), and Quarkus routes SLF4J to JBoss LogManager. Category config uses `quarkus.log.category."<name>".level` (quotes required, default `INFO`). `quarkus.log.level` defaults to `INFO`. `quarkus.log.min-level` defaults to `DEBUG` and is **build-time**: TRACE needs a lowered min-level, otherwise the guarded code is removed as dead code in native builds (https://quarkus.io/guides/logging — "Latest" selector; the 3.40 selector exists).
- Code:
  ```properties
  # Camel Quarkus 3.40.x
  quarkus.log.category."org.apache.camel".level=INFO
  quarkus.log.category."com.acme.orders".level=DEBUG
  # TRACE for one category needs the build-time floor lowered too:
  quarkus.log.category."com.acme.orders".min-level=TRACE
  ```
- Source: https://quarkus.io/guides/logging (2026-10-14)

**4. Use camel-quarkus-mdc for correlation, not deprecated useMdcLogging**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ mdc extension page 3.40.x + Camel mdc component 4.22.x + main.html deprecation]
- Why: `camel.main.useMdcLogging` (default `false`) is marked "deprecated, use camel-mdc component instead", and `mdcLoggingKeysPattern` is "Deprecated" (https://camel.apache.org/components/4.22.x/others/main.html). `camel-mdc` is available since Camel 4.15 (https://camel.apache.org/components/4.22.x/others/mdc.html). The CQ extension `camel-quarkus-mdc` has existed since 3.29.0, in JVM and native, with `quarkus.camel.mdc.enabled` (default `false`), `quarkus.camel.mdc.custom-exchange-headers` and `quarkus.camel.mdc.custom-exchange-properties` (`*` wildcard) (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html). Default keys: `camel.breadcrumbId`, `camel.exchangeId`, `camel.messageId`, `camel.correlationId`, `camel.routeId`, `camel.contextId`, `camel.threadId`, each included only if present (mdc.html). Do not combine with `setUseMDCLogging(true)` (mdc.html).
- Code:
  ```properties
  # Camel Quarkus 3.40.x  (dependency: org.apache.camel.quarkus:camel-quarkus-mdc)
  quarkus.camel.mdc.enabled=true
  quarkus.camel.mdc.custom-exchange-headers=X-Correlation-Id
  quarkus.log.console.format=%d{HH:mm:ss,SSS} %-5p [%c] (%t) [%X{camel.exchangeId}] %s%e%n
  ```
- Source: as cited above (2026-10-14)

**5. Enable stream caching (default on) before logging streaming bodies**
> Confidence: 🟡 Medium | single source per claim
- Why: Logging a stream-based body "may cause the message body to be empty afterward" (log-eip.html). `showStreams` can consume the stream (log-component.html). `camel.main.streamCachingEnabled` defaults to `true` (https://camel.apache.org/components/4.22.x/others/main.html). The stream-caching manual page is ambiguous on this point (https://camel.apache.org/manual/stream-caching.html).
- Code:
  ```properties
  # Camel Quarkus 3.40.x — keep the default; do not disable if you log bodies
  camel.main.streamCachingEnabled=true
  ```
- Source: as cited above (2026-10-14)

### ⚠️ Conditional Patterns

**A. Plain text console vs JSON (structured) logging**
> Confidence: 🟢 High
- Options: default console pattern `%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n`; or the `quarkus-logging-json` extension.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Text pattern + `%X{...}` | Readability | Parseability | Local dev/test |
  | `quarkus-logging-json` (`log-format`=`default`/`ecs`/`gcp`) | Log aggregation, MDC as `mdc` object or root fields (`mdc.flat-fields`, default `false`) | Format/colour settings ignored; `pretty-print` (default `false`) breaks some parsers | Kubernetes/ELK/GCP |

- Agent: "Ask user which log backend or format the platform ingests (ECS, GCP, generic)." Disable JSON in dev and test with `%dev.quarkus.log.console.json.enabled=false` and `%test.quarkus.log.console.json.enabled=false`.
- Source: https://quarkus.io/guides/logging ; https://quarkus.io/version/3.40/guides/logging (2026-10-14)

**B. Per-message logging vs throughput logging**
> Confidence: 🟢 High
- Options: regular logging (default, one line per exchange); throughput logging (set `groupSize`, or `groupInterval` with `groupDelay`; `groupActiveOnly` default `true`).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Regular | Per-message forensics | Log volume, I/O | Low-volume / debug |
  | Throughput (`groupSize=1000`) | Volume (stats per group) | No message content | High-volume routes |

- Agent: "Ask the expected messages/sec and whether the content is needed."
- Source: https://camel.apache.org/components/4.22.x/log-component.html (2026-10-14)

**C. Custom ExchangeFormatter (global vs per-endpoint)**
> Confidence: 🟢 High
- Options: configure `camel.component.log.exchange-formatter` in properties (example in https://camel.apache.org/camel-quarkus/3.40.x/user-guide/configuration.html); bind a bean named `logFormatter` (auto-detected; applies to every Log endpoint); or use several `LogComponent` beans for per-endpoint formatters (log-component.html).
- Agent: "Ask whether one format is enough for all endpoints."
- Code:
  ```properties
  # Camel Quarkus 3.40.x (verbatim example from the CQ 3.40.x configuration guide)
  camel.component.log.exchange-formatter = #class:org.apache.camel.support.processor.DefaultExchangeFormatter
  camel.component.log.exchange-formatter.show-exchange-pattern = false
  camel.component.log.exchange-formatter.show-body-type = false
  ```
- Source: as cited (2026-10-14)

**D. Logger name strategy for the Log EIP**
> Confidence: 🟡 Medium
- Options: route id (default); `logName` per EIP; global `camel.main.logName` ("The global name to use for Log EIP", main.html); `CamelLogEipName` via `camel.main.globalOptions` (log-eip.html); source `file:line` when `camel.main.sourceLocationEnabled=true` (default `false`, main.html).
- Agent: "Ask whether the operations team filters by route id or by class/package."
- Source: https://camel.apache.org/components/4.22.x/eips/log-eip.html ; https://camel.apache.org/components/4.22.x/others/main.html (2026-10-14)

### 🚫 Forbidden Patterns

**1. showAll / showHeaders / showProperties in production without masking**
> Severity: Critical
> Confidence: 🟢 High
- Why: These options dump all headers and properties, which often include `Authorization` headers, tokens and credentials. All default to `false` for a reason (log-component.html).
- Impact: Secret or PII leakage into the log aggregator. Compliance breach.
- ❌ Wrong:
  ```java
  .to("log:debug?showAll=true&multiline=true")
  ```
- ✅ Correct:
  ```java
  .to("log:com.acme.audit?showExchangeId=true&showRouteId=true&showBodyType=true&logMask=true&maxChars=500")
  ```
- Source: https://camel.apache.org/components/4.22.x/log-component.html (2026-10-14)

**2. Deprecated MDC switch (and mixing it with camel-mdc)**
> Severity: High
> Confidence: 🟢 High
- Why: `useMdcLogging` is deprecated (main.html), and mdc.html says not to enable it together with camel-mdc.
- Impact: Duplicate or conflicting MDC handling. The setting will be removed later.
- ❌ Wrong:
  ```properties
  camel.main.useMdcLogging=true
  quarkus.camel.mdc.enabled=true
  ```
- ✅ Correct:
  ```properties
  quarkus.camel.mdc.enabled=true
  ```
- Source: https://camel.apache.org/components/4.22.x/others/main.html ; https://camel.apache.org/components/4.22.x/others/mdc.html (2026-10-14)

**3. Expecting runtime TRACE when min-level is above it**
> Severity: Medium
> Confidence: 🟢 High
- Why: `quarkus.log.min-level` (default `DEBUG`) is build-time. Below that floor, the log code is optimised away (https://quarkus.io/guides/logging).
- Impact: TRACE never appears, even after changing the level at runtime.
- ❌ Wrong:
  ```properties
  quarkus.log.category."org.apache.camel".level=TRACE
  ```
- ✅ Correct:
  ```properties
  quarkus.log.category."org.apache.camel".level=TRACE
  quarkus.log.category."org.apache.camel".min-level=TRACE
  ```
- Source: https://quarkus.io/guides/logging (2026-10-14)

**4. Logging streaming bodies with stream caching disabled**
> Severity: High
> Confidence: 🟡 Medium
- Why: The body may be empty afterwards (log-eip.html; `showStreams` caveat in log-component.html).
- Impact: Downstream endpoints receive an empty payload.
- ❌ Wrong:
  ```properties
  camel.main.streamCachingEnabled=false
  # route: from("platform-http:/up").log("${body}").to("file:in")
  ```
- ✅ Correct:
  ```properties
  camel.main.streamCachingEnabled=true
  ```
- Source: https://camel.apache.org/components/4.22.x/eips/log-eip.html ; https://camel.apache.org/components/4.22.x/others/main.html (2026-10-14)

**5. Using setters from 3.15-era recipes for MDC keys pattern**
> Severity: Medium
> Confidence: 🟢 High
- Why: `camel.main.mdcLoggingKeysPattern` is deprecated (main.html). Header and property propagation now uses `quarkus.camel.mdc.custom-exchange-headers` and `quarkus.camel.mdc.custom-exchange-properties` (CQ mdc page).
- ❌ Wrong:
  ```properties
  camel.main.mdcLoggingKeysPattern=myKey*
  ```
- ✅ Correct:
  ```properties
  quarkus.camel.mdc.custom-exchange-properties=myKey*
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html (2026-10-14)

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://camel.apache.org/components/4.22.x/others/main.html (2026-10-14) + https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html (2026-10-14). Generic 3.x migration steps: see research_Camel_Quarkus_Core_v3.40.md (migration-guide index).

**Breaking / behavioural changes vs 3.15 conventions**:
- MDC: `useMdcLogging` and `mdcLoggingKeysPattern` are deprecated. Use `camel-quarkus-mdc` (since CQ 3.29.0; Camel camel-mdc since 4.15). ⚠️ Migration Note
- `camel-mdc` key set includes `camel.threadId`. The legacy key list included `camel.stepId` and `camel.transactionKey` (https://camel.apache.org/manual/mdc.html). The new default set does not list them (mdc.html) — re-check dashboards that rely on them. ⚠️ Migration Note
- Masking now documents URI-password and PEM-key masking (log-eip.html).
- No log-specific entries were found in the per-version CQ migration guides (the core pilot read 3.31–3.40; this run did not re-read each one — 🟡 Medium).

**Upgrade Steps**:
1. Remove `camel.main.useMdcLogging` and `camel.main.mdcLoggingKeysPattern`.
2. Add `org.apache.camel.quarkus:camel-quarkus-mdc` (version from the BOM) and set `quarkus.camel.mdc.enabled=true`.
3. Update `%X{...}` patterns and JSON dashboards to the new key set.
4. Audit every `log:` URI for `showAll`, `showHeaders` and `showProperties`, and add `camel.main.logMask=true`.

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Camel | 4.22.1 | 4.22.x | https://camel.apache.org/releases/ (4.22.1 LTS 2026-09-17) |
| Quarkus | 3.40.x | 3.40.x | Quarkus 4 unsupported — see core pilot (re-verified there) |
| camel-quarkus-mdc | 3.29.0 (since) | 3.40.x | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | CQ configuration guide + log-component.html + quarkus logging guide]

**Lifecycle**:
```xml
<!-- Camel Quarkus 3.40.x — versions from the BOM (see core pilot) -->
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-log</artifactId></dependency>
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-mdc</artifactId></dependency>
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-logging-json</artifactId></dependency>
```
```java
// Camel Quarkus 3.40.x
public class OrderRoutes extends RouteBuilder {
    @Override public void configure() {
        from("timer:orders?period=5000").routeId("orders")
            .setBody(constant("{\"pan\":\"4111111111111111\"}"))
            .log("Processing exchange")                                   // EIP, logger name = "orders"
            .to("log:com.acme.orders?showExchangeId=true&logMask=true");    // component
        from("timer:bulk?period=10").to("log:com.acme.bulk?groupInterval=10000&groupDelay=5000");
    }
}
```
```properties
# Camel Quarkus 3.40.x — application.properties
camel.main.logMask=true
quarkus.camel.mdc.enabled=true
quarkus.log.category."org.apache.camel".level=WARN
quarkus.log.category."com.acme".level=INFO
%dev.quarkus.log.console.json.enabled=false
%test.quarkus.log.console.json.enabled=false
quarkus.log.console.json.log-format=ecs
```

**Integration**: Camel Quarkus Log ↔ camel-quarkus-bean (custom formatter / mask as CDI beans)
```java
// Camel Quarkus 3.40.x — beans resolved from the registry by name
@ApplicationScoped @Named("logFormatter")
public class CompactFormatter implements org.apache.camel.spi.ExchangeFormatter {
    public String format(org.apache.camel.Exchange e) { return e.getExchangeId() + " " + e.getMessage().getBody(String.class); }
}
```
Native mode: camel-quarkus-log is supported in native mode since 0.0.1 (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/log.html). The CQ native-mode guide has no logging-specific notes (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html). Beans used only through registry lookup may need reflection registration — see the core pilot. — 🟡 Medium

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Camel Quarkus 3.40.x)
mvn quarkus:dev                      # expect log lines with category com.acme.orders and masked "pan"
mvn verify -Dnative                  # native build; expect same log output
grep -rn "showAll=true\|useMdcLogging" src/   # expect: no matches
```

**Mocking**:
```java
// Camel Quarkus 3.40.x — assert routing, not log text; replace the log endpoint with a mock (see core pilot testing section)
@QuarkusTest
class OrderRoutesTest {
    @Inject CamelContext ctx;
    @Test void logsOnce() throws Exception {
        AdviceWith.adviceWith(ctx, "orders", a -> a.weaveByToUri("log:com.acme.orders*").replace().to("mock:log"));
        MockEndpoint m = ctx.getEndpoint("mock:log", MockEndpoint.class);
        m.expectedMinimumMessageCount(1);
        m.assertIsSatisfied(10000);
    }
}
```
Capturing the actual log text in tests with a Quarkus-specific API: UNVERIFIED (no official CQ 3.40.x page found).

---

## Production Readiness

- **Performance**: Default `maxChars=10000` caps each line. `showFuture` blocks until the Future completes. `lazyStartProducer` delays the first message. Throughput logging reduces volume (log-component.html). `print-details` in JSON is "costly" (reads caller info, https://quarkus.io/version/3.40/guides/logging). Quantitative overhead figures: UNVERIFIED.
- **Scalability**: Use throughput logging (`groupSize` or `groupInterval`) for high-rate routes.
- **Monitoring**: MDC keys `camel.exchangeId`, `camel.routeId`, `camel.correlationId` and `camel.breadcrumbId` (breadcrumb needs `camel.main.useBreadcrumb=true`, default `false`, main.html).
- **Security**: `camel.main.logMask=true`. No `showAll`, `showHeaders` or `showProperties` in prod. A custom `CamelCustomLogMask` for domain PII. `camel.main.logExhaustedMessageBody` defaults to `false`; keep it off unless masked (main.html). JSON `excluded-keys` can drop sensitive MDC fields (quarkus.io 3.40 logging).
- **MDC in async**: Quarkus keeps MDC across Vert.x duplicated contexts, `ManagedExecutor` and `executeBlocking` (https://quarkus.io/version/3.40/guides/logging). How this interplays with camel-mdc on Camel async threads: UNVERIFIED.

---

## Reference Implementations

- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/log.html — extension page
- https://camel.apache.org/components/4.22.x/log-component.html — options, masking, formatter, throughput
- https://camel.apache.org/components/4.22.x/eips/log-eip.html — EIP options
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/configuration.html — `camel.component.log.exchange-formatter` example
- https://github.com/apache/camel-quarkus (integration-tests/log module) — not opened in this run

---

## Source Bibliography

**Primary** (all fetched 2026-10-14; no page dates, versioned for current stable LTS):
- https://camel.apache.org/releases/ — CQ 3.40.0 2026-09-28 LTS; Camel 4.22.1 2026-09-17
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/log.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html (no logging content)
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/configuration.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/command-mode.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html (no logging content)
- https://camel.apache.org/components/4.22.x/log-component.html
- https://camel.apache.org/components/4.22.x/eips/log-eip.html
- https://camel.apache.org/components/4.22.x/others/mdc.html
- https://camel.apache.org/components/4.22.x/others/main.html
- https://camel.apache.org/manual/mdc.html (legacy MDC, marked deprecated)
- https://camel.apache.org/manual/stream-caching.html (ambiguous; not relied on for defaults)
- https://quarkus.io/guides/logging ("Latest") and https://quarkus.io/version/3.40/guides/logging (JSON/MDC propagation part)

**Validation**: Maven Central camel-quarkus-mdc 3.40.0 and camel-quarkus-log 3.40.0 artifact pages (central.sonatype.com, found via search, not opened).

---

## Research Gaps

```
Gap: Which quarkus.camel.mdc.* properties are fixed at build time
Impact: Runtime override of quarkus.camel.mdc.enabled may silently fail
Workaround: Set it in application.properties at build time
Follow-up: CQ 3.40.x mdc extension page lock icons / MdcConfig source in apache/camel-quarkus
§7-ref: Iteration 2 — IRRESOLVABLE
```
```
Gap: Camel Quarkus 3.40 LTS end date
Impact: Support planning
Workaround: Quarkus 3.40 LTS horizon (see core pilot)
Follow-up: https://camel.apache.org/releases/ "LTS until" column
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap (UNVERIFIED): log-eip.html says the EIP logs "only ... Simple language", yet logLanguage/camel.main.logLanguage exist
Gap (UNVERIFIED): quantitative performance overhead of log component
Gap (UNVERIFIED): camel-mdc vs Quarkus Vert.x MDC propagation on Camel async threads
Gap (UNVERIFIED): official Quarkus/CQ API for asserting log output in tests
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Guardrails | Log component options (showAll etc., left UNVERIFIED by core pilot) | Resolved — full option table with defaults | https://camel.apache.org/components/4.22.x/log-component.html (2026-10-14) |
| 1 | Guardrails | Log EIP URL (manual/log-eip.html returned 404) | Resolved — versioned eips/log-eip.html | https://camel.apache.org/components/4.22.x/eips/log-eip.html (2026-10-14) |
| 1 | Guardrails | MDC mechanism in 4.22 | Resolved — camel-mdc + camel-quarkus-mdc | mdc.html (4.22.x) ; CQ 3.40.x mdc.html (2026-10-14) |
| 2 | Guardrails | camel.main.logMask / logName / useMdcLogging defaults | Resolved | https://camel.apache.org/components/4.22.x/others/main.html (2026-10-14) |
| 2 | Guardrails | Stream caching default | Resolved via main.html (`true`) | main.html (2026-10-14) |
| 2 | Research Gaps | mdc build-time fixed props | ⚠️ IRRESOLVABLE — page shows legend without per-property marking in fetched text | — |
| 3 | Guardrails | camel.main.* honoured in CQ | Updated → Medium (only durationMax* family stated) | https://camel.apache.org/camel-quarkus/3.40.x/user-guide/command-mode.html (2026-10-14) |
| 3 | Metadata | LTS end date | ⚠️ IRRESOLVABLE — releases page has no "LTS until" value | https://camel.apache.org/releases/ |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented
- [x] All scope areas cited (options, EIP vs component, categories, MDC, masking, performance, native, structured, testing)
- [x] Pattern counts driven by domain needs
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative
- [x] Integration examples complete (Quarkus logging, JSON, bean, mdc; core by reference)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated or downgraded to 🟡 (pattern 5 downgraded)
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated
- [x] Every Research Gap cross-referenced

---

## Agent Operation Notes

- **High Confidence**: option defaults from log-component.html; EIP defaults; masking; Quarkus category/min-level; camel-quarkus-mdc properties; useMdcLogging deprecation.
- **Medium Confidence**: `camel.main.*` support breadth in CQ; stream-caching guidance; logger-name strategy; native-mode bean reflection; absence of log-specific migration entries.
- **Low Confidence / must ask**: UNVERIFIED items (logLanguage contradiction, perf figures, async MDC interplay, log-capture testing) and the IRRESOLVABLE items (mdc build-time props, LTS end date).
- **Edge Cases**: CQ 3.40.0 released 2026-09-28, 16 days before research (<30 days). Docs may still change.
- **Emergency Stop**: not triggered (all sources official).
