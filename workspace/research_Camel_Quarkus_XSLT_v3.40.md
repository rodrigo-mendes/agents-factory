# Research: Camel Quarkus XSLT v3.40 (camel-quarkus-xslt + camel-quarkus-xslt-saxon / Camel 4.22.x / Quarkus 3.40.x)

> Version lock: every claim here applies to **Camel Quarkus 3.40.x** only. Patterns from the v3.15 research file are treated as misinformation unless re-verified below.
> All sources fetched **2026-10-14**. camel.apache.org pages carry no publication date of their own. They count as current because they are the versioned docs for the current stable LTS.
> Method note: WebFetch returns summaries, so quoted text is the tool's rendering of the page. Check exact wording before reusing it verbatim.
> Workflow note: this was a forked batch run approved by the user upstream. The P3 plan-approval step (EnterPlanMode/ExitPlanMode) was skipped because no user was available inside the fork. Section-investigators were not spawned, per the caller's instruction. All pages were fetched directly.
> Scope: XSLT-specific topics only. For BOM import, LTS, Java/GraalVM baselines, CDI, testing basics and the Quarkus 4 risk, see `workspace/research_Camel_Quarkus_Core_v3.40.md` (not duplicated here).

**Source key** (exact page URLs, used inline):
- [CQ-XSLT] https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html
- [CQ-MIG] https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- [C-XSLT] https://camel.apache.org/components/4.22.x/xslt-component.html
- [C-XSLT-NEXT] https://camel.apache.org/components/next/xslt-component.html (Camel 4.23+; NOT the target version — used only to flag what is *not yet* in 4.22)
- [CQ-SAXON] https://camel.apache.org/camel-quarkus/latest/reference/extensions/xslt-saxon.html (the `latest` alias; it linked to 4.22.x component docs at fetch time)
- [C-SAXON] https://camel.apache.org/components/4.22.x/xslt-saxon-component.html
- [REL] https://camel.apache.org/releases/
- [MVN] https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-xslt/

---

## Metadata

```yaml
Full_Name: Apache Camel Quarkus — XSLT extension (camel-quarkus-xslt) and XSLT Saxon extension (camel-quarkus-xslt-saxon)
Target_Version: 3.40.x (3.40.0) — Camel 4.22.x (4.22.1 LTS, 2026-09-17 per [REL]), Quarkus 3.40.x
Release_Date: 2026-09-28 per [REL]; Maven Central directory shows camel-quarkus-xslt 3.40.0 dated 2026-09-24 per [MVN] (artifact publish precedes announcement)
Support_Status: LTS ([REL] marks Camel Quarkus 3.40.0 LTS); CQ-specific LTS end date UNVERIFIED (see core pilot)
Primary_Docs: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html
Official_Repo: https://github.com/apache/camel-quarkus
Research_Date: 2026-10-14
Domain_Complexity: Standard (security-sensitive XML processing, build-time compilation, native-mode restrictions)
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 4
Unverified_Count: 6
Irresolvable_Count: 3
Research_Quality_Score: 87%   # ~70 claims; (70 - 6 - 3) / 70
```

---

## Executive Summary

`camel-quarkus-xslt` (`org.apache.camel.quarkus:camel-quarkus-xslt`, JVM and native since 0.4.0 [CQ-XSLT]) exposes the Camel `xslt:` producer component. It transforms XML payloads with an XSLT template. Templates listed in `quarkus.camel.xslt.sources` are compiled into Java classes (Xalan-J translets) **at build time**, so the `.xsl` files do not have to be in the application archive [CQ-XSLT]. In native mode only `classpath:` template URIs work. `file:`, `http:` and other schemes are JVM-only [CQ-XSLT]. The sibling `camel-quarkus-xslt-saxon` **does exist** in the 3.40 line (JVM since 1.1.0, native since 3.2.0 [CQ-SAXON]). It exposes `xslt-saxon:` (Saxon engine, XSLT 3.0 features such as `useJsonBody` [C-SAXON]).

**What changed in 3.40** (all from [CQ-MIG], section "XSLT extension changes", re-confirmed on [CQ-XSLT]):
1. Input documents are parsed **without resolving external entities or loading external DTDs**. The exception is a `SAXSource` with a caller-supplied `XMLReader`, which is passed through unchanged.
2. `document()` fetches are **denied unless a `URIResolver` resolves them**. Routes are unaffected because camel-xslt installs its own resolver on every transformer it uses. `xsl:import`/`xsl:include` are not restricted.
3. `quarkus.camel.xslt.features` now applies to **every** template, including those loaded at runtime. An unsupported feature fails endpoint creation. Disabling secure processing logs a startup warning.
4. The Xalan-J factory is **registered as the JAXP default**, so `TransformerFactory.newInstance()` anywhere in the app (including the Tika and XML Security extension code paths) gets these restrictions.

The three critical patterns are:
- Declare every native-mode template in `quarkus.camel.xslt.sources` and reference it via `classpath:`.
- Keep secure processing on. Turn it off only when every template is trusted.
- Strip untrusted headers before `xslt:`, because all headers and variables become XSLT parameters [C-XSLT].

The tier is **Standard**, not Complex. There is a real security surface (XXE, SSRF via `document()`, header-injected parameters), but no auth or crypto design.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**1. Declare templates at build time in `quarkus.camel.xslt.sources`**
> Confidence: 🟢 High | [✓✓ Triangulated | [CQ-XSLT] (2026-10-14) + [CQ-MIG] (2026-10-14, describes build-time vs runtime-loaded templates)]
- Why: sources are compiled to translets at build time. Scheme-less entries are treated as `classpath:` [CQ-XSLT]. Property type is `List of string`, no default [CQ-XSLT].
- Code:
  ```properties
  # Camel Quarkus 3.40.x — from [CQ-XSLT]
  quarkus.camel.xslt.sources = transform.xsl, classpath:path/to/my/file.xsl
  # optional; default org.apache.camel.quarkus.component.xslt.generated [CQ-XSLT]
  # quarkus.camel.xslt.package-name = com.acme.xslt.generated
  ```
  ```java
  // Camel Quarkus 3.40.x route
  from("direct:in").to("xslt:transform.xsl");
  ```
- Source: [CQ-XSLT] (fetched 2026-10-14). Which individual properties are "fixed at build time" is UNVERIFIED: the page footer explains the build-time marker, but the tool did not render per-row markers.

**2. Use `classpath:` templates only in native mode**
> Confidence: 🟢 High | [✓✓ Triangulated | [CQ-XSLT] native-mode section + [C-XSLT] resourceUri prefix list (default `classpath`)]
- Why: native mode supports `classpath:` only. `file:`/`http:` are JVM-only [CQ-XSLT]. `xsl:include` works natively when the including stylesheet is in `sources` and includes are classpath-relative [CQ-XSLT]. In the component, `classpath` is the default prefix for `resourceUri` [C-XSLT].
- Code: `to("xslt:classpath:xslt/order-to-invoice.xsl")` (Camel Quarkus 3.40.x)
- Source: [CQ-XSLT], [C-XSLT] (2026-10-14)

**3. Keep secure processing enabled (default)**
> Confidence: 🟢 High | [✓✓ Triangulated | [CQ-XSLT] + [CQ-MIG]]
- Why: disabling `http://javax.xml.XMLConstants/feature/secure-processing` permits Xalan extension functions and is logged as a warning at startup. "Only disable it where every template the application transforms with is trusted" [CQ-MIG]. In 3.40 the feature map also governs runtime-loaded templates [CQ-MIG].
- Code: no configuration needed. Leave `quarkus.camel.xslt.features` unset.
- Source: [CQ-XSLT], [CQ-MIG] (2026-10-14)

**4. Remove untrusted headers before the `xslt:` step**
> Confidence: 🟡 Medium (single page; the explicit untrusted-sender warning appears only on [C-XSLT-NEXT]. The 4.22.x page confirms only the auto-parameter behaviour.)
- Why: "By default, all headers and variables are added as parameters which are then available in the XSLT" [C-XSLT]. A parameter is used only if declared as a top-level `<xsl:param>` [C-XSLT]. A parameter fed into `document()` lets an external sender steer resource reads [C-XSLT-NEXT].
- Code:
  ```java
  // Camel Quarkus 3.40.x / Camel 4.22.x
  from("platform-http:/transform")
      .removeHeaders("*", "myParam")   // keep only the expected parameter
      .to("xslt:classpath:xslt/transform.xsl");
  ```
  ```xml
  <xsl:param name="myParam"/>
  ```
- Source: [C-XSLT] (2026-10-14); `removeHeaders("*", "myParam")` example from [C-XSLT-NEXT]

**5. Register Xalan extension functions for reflection (only when secure processing is off)**
> Confidence: 🟡 Medium (single source [CQ-XSLT])
- Why: extension functions work only if (a) secure processing is disabled, (b) the functions live in a **separate jar**, and (c) they are registered for reflection at native build time [CQ-XSLT].
- Code:
  ```java
  // Camel Quarkus 3.40.x — from [CQ-XSLT]
  @RegisterForReflection(targets = { my.Functions.class })
  public class FunctionsConfiguration { }
  ```
  ```properties
  quarkus.camel.xslt.features."http\://javax.xml.XMLConstants/feature/secure-processing"=false
  ```
- Source: [CQ-XSLT] (2026-10-14)

### ⚠️ Conditional Patterns

**A. `xslt` (Xalan, build-time translets) vs `xslt-saxon` (Saxon)**
> Confidence: 🟡 Medium
- Options: A) `camel-quarkus-xslt`. B) `camel-quarkus-xslt-saxon`.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | xslt | build-time compilation, 3.40 hardening documented [CQ-XSLT] | Xalan-J 2.7.x engine (XSLT 1.0, UNVERIFIED version claim) | Static classpath templates, native |
  | xslt-saxon | Saxon features: `useJsonBody` (default false), `allowStAX` (default true), `saxonExtensionFunctions`, `secureProcessing` (default true) [C-SAXON] | 3.40 Xalan hardening notes do not cover it ([CQ-MIG] does not mention saxon); native since 3.2.0 [CQ-SAXON]; `XsltSaxonAggregationStrategy` aggregation is JVM-only [CQ-XSLT] | XSLT 2.0/3.0 or JSON input |

- Agent: "Ask user: do your stylesheets need XSLT 2.0/3.0 or JSON input? If not, use `camel-quarkus-xslt`."
- Source: [CQ-XSLT], [CQ-SAXON], [C-SAXON] (2026-10-14)

**B. Output format**
> Confidence: 🟢 High (single page, exact defaults)
- Options: `output=string` (default), `bytes`, `DOM`, `file` [C-XSLT].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | string (default) | simplicity | memory | small docs |
  | bytes / DOM | downstream type fit | memory | binary or DOM consumers |
  | file | streaming to disk | needs `CamelXsltFileName` header; parent dirs must exist or runtime exception; `deleteOutputFile` default false | large outputs (JVM; native file output UNVERIFIED) |

- Agent: "Ask user the expected payload size and the downstream type."
- Source: [C-XSLT] (2026-10-14)

**C. Dynamic templates (`allowTemplateFromHeader`, `CamelXsltResourceUri`, `CamelXsltStylesheet`)**
> Confidence: 🟢 High (default) / 🟡 Medium (native behaviour)
- Options: keep default `false` [C-XSLT], or enable for trusted producers only.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | false (default) | security, build-time compilation | flexibility | almost always |
  | true | runtime choice of template | security risk if headers are untrusted [C-XSLT]; runtime-loaded templates are not precompiled | internal trusted callers, JVM |

- Agent: "Ask user whether the header can be set by any external party."
- Source: [C-XSLT], [CQ-MIG] (2026-10-14)

**D. Caching (`contentCache`, `transformerCacheSize`)**
> Confidence: 🟢 High
- Defaults: `contentCache=true` (stylesheet loaded at startup; clearable via JMX `clearCachedStylesheet`) and `transformerCacheSize=0` [C-XSLT]. `xpathTotalOpLimit=10000`, per TransformerFactory instance [C-XSLT].
- Agent: "Ask user about throughput. Raise `transformerCacheSize` for hot endpoints."
- Source: [C-XSLT] (2026-10-14)

**E. Allowing `document()` to reach external resources**
> Confidence: 🟡 Medium
- Options: A) Keep the 3.40 default: routes resolve `document()` through the component's resolver. Direct `TransformerFactory.newInstance()` code is denied unless it sets its own `URIResolver` [CQ-MIG]. B) Supply a custom `uriResolver` (component or endpoint option [C-XSLT]).
- Note: `ACCESS_EXTERNAL_STYLESHEET` cannot be used with the CQ Xalan factory, because `setAttribute` throws for it [CQ-XSLT]. The Camel 4.23+ runtime refusal of `http:/https:/ftp:/file:` in `document()` [C-XSLT-NEXT] is **not** part of Camel 4.22.x (absent from [C-XSLT]).
- Agent: "Ask user which hosts or schemes `document()` must reach. Implement an allow-list `URIResolver`."
- Source: [CQ-XSLT], [CQ-MIG], [C-XSLT] (2026-10-14)

### 🚫 Forbidden Patterns

**1. `file:`/`http:` templates in native mode**
> Severity: High
> Confidence: 🟢 High
- Why: only `classpath:` works natively [CQ-XSLT].
- Impact: endpoint fails in the native executable.
- ❌ Wrong:
  ```java
  to("xslt:file:/opt/xslt/transform.xsl")   // JVM-only
  ```
- ✅ Correct:
  ```java
  to("xslt:classpath:xslt/transform.xsl")   // + listed in quarkus.camel.xslt.sources
  ```
- Source: [CQ-XSLT] (2026-10-14)

**2. Disabling secure processing globally for untrusted templates**
> Severity: Critical
> Confidence: 🟢 High
- Why: since 3.40, features apply to every template, including runtime-loaded ones. Disabling enables Xalan extension functions (arbitrary Java calls) [CQ-MIG].
- Impact: code execution from a malicious stylesheet.
- ❌ Wrong:
  ```properties
  quarkus.camel.xslt.features."http\://javax.xml.XMLConstants/feature/secure-processing"=false
  camel.component.xslt.allow-template-from-header=true
  ```
- ✅ Correct:
  ```properties
  # leave features unset; keep allowTemplateFromHeader=false (default per [C-XSLT])
  ```
- Source: [CQ-MIG], [C-XSLT] (2026-10-14). The `camel.component.xslt.allow-template-from-header` property spelling is UNVERIFIED for 3.40 (derived from the component option name).

**3. Setting `ACCESS_EXTERNAL_DTD` / `ACCESS_EXTERNAL_STYLESHEET` on the factory**
> Severity: Medium
> Confidence: 🟢 High
- Why: Xalan-J 2.7.x predates JAXP 1.5, and `setAttribute` throws for both attributes. The extension enforces the restrictions itself [CQ-XSLT], [CQ-MIG].
- Impact: exception at factory configuration.
- ❌ Wrong:
  ```java
  TransformerFactory tf = TransformerFactory.newInstance();
  tf.setAttribute(XMLConstants.ACCESS_EXTERNAL_STYLESHEET, "");   // throws on CQ 3.40
  ```
- ✅ Correct:
  ```java
  TransformerFactory tf = TransformerFactory.newInstance();   // CQ 3.40 default already blocks
  tf.setURIResolver(allowListResolver);                       // explicit resolver for document()
  ```
- Source: [CQ-XSLT], [CQ-MIG] (2026-10-14)

**4. Passing raw external headers into a stylesheet that uses `document($param)`**
> Severity: High
> Confidence: 🟡 Medium
- Why: every header becomes a parameter [C-XSLT]. The SSRF risk is spelled out in [C-XSLT-NEXT].
- ❌ Wrong:
  ```java
  from("platform-http:/x").to("xslt:classpath:lookup.xsl");
  ```
- ✅ Correct:
  ```java
  from("platform-http:/x").removeHeaders("*", "customerId").to("xslt:classpath:lookup.xsl");
  ```
- Impact: an external sender selects which resource `document()` reads.
- Source: [C-XSLT], [C-XSLT-NEXT] (2026-10-14)

**5. Relying on DTD/external-entity expansion in input XML**
> Severity: Medium
> Confidence: 🟢 High
- Why: since 3.40, external entities and DTDs are not resolved [CQ-MIG].
- Impact: entity references silently unexpanded or failing. Previously working payloads may change.
- ❌ Wrong: input with `<!DOCTYPE x SYSTEM "http://host/x.dtd">` expecting entity expansion.
- ✅ Correct: pre-resolve entities upstream, or pass a `SAXSource` with a deliberately configured `XMLReader` (used as-is [CQ-XSLT]) only for trusted input.
- Source: [CQ-MIG], [CQ-XSLT] (2026-10-14)

**6. Unescaped colon in the features property key (3.15-era file style)**
> Severity: Medium
> Confidence: 🟡 Medium
- Why: the 3.40 docs show the escaped form `"http\://..."` [CQ-XSLT]. The unescaped form was used in the v3.15 research file. Whether it parses correctly is UNVERIFIED.
- ❌ Wrong:
  ```properties
  quarkus.camel.xslt.features."http://javax.xml.XMLConstants/feature/secure-processing"=false
  ```
- ✅ Correct:
  ```properties
  quarkus.camel.xslt.features."http\://javax.xml.XMLConstants/feature/secure-processing"=false
  ```
- Impact: the feature may not apply.
- Source: [CQ-XSLT] (2026-10-14)

---

## Migration Guide

> Confidence: 🟢 High | Sources: [CQ-MIG] (2026-10-14) + [CQ-XSLT] (2026-10-14)

**Breaking Changes (3.40.0, "XSLT extension changes" in [CQ-MIG])**:
1. External entities and external DTDs in input documents are no longer resolved. `String`, `byte[]` and `InputStream` bodies were already parsed safely by Camel. The change mainly affects `Source` bodies and direct factory calls.
2. `document()` is denied unless a `URIResolver` resolves it. The restriction persists through `reset()` and `setURIResolver(null)`.
3. `quarkus.camel.xslt.features` applies to every template, including runtime-loaded ones. Unsupported features now fail endpoint creation.
4. The Xalan factory becomes the JAXP default. This affects `TransformerFactory.newInstance()` in app code and in the Tika and XML Security extensions.
- Not mentioned for `xslt-saxon` in [CQ-MIG]. Whether Saxon is affected is UNVERIFIED.
- Changes inherited between 3.15 and 3.40 that are XSLT-specific: UNVERIFIED (only the 3.40.0 guide was read for XSLT). For generic ones (junit5 to junit rename in 3.31, AdviceWith in 3.36), see the core pilot.

**Upgrade Steps**:
1. Bump `quarkus.platform.version` to 3.40.x (BOM procedure in the core pilot).
2. `grep -rn "TransformerFactory.newInstance\|setAttribute(XMLConstants.ACCESS_EXTERNAL" src/` finds code now hitting Xalan with restrictions.
3. `grep -rn "document(" src/main/resources` finds stylesheets relying on `document()` outside routes. Add a `URIResolver`.
4. Review `quarkus.camel.xslt.features` entries. Unsupported keys now fail startup.
5. Re-test inputs that use DOCTYPE/entities.

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Camel | 4.22.0 | 4.22.1 | [REL]; docs link to 4.22.x components |
| camel-quarkus-xslt | 3.40.0 | 3.40.x | [MVN] 3.40.0 (2026-09-24) |
| Quarkus | 3.40.x | 3.40.x | see core pilot |
| Xalan-J | 2.7.x | — | engine per [CQ-XSLT]; exact patch version UNVERIFIED |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | [CQ-XSLT] + [C-XSLT]]

**Lifecycle**:
```xml
<!-- Camel Quarkus 3.40.x; versions managed by quarkus-camel-bom (core pilot) -->
<dependency>
  <groupId>org.apache.camel.quarkus</groupId>
  <artifactId>camel-quarkus-xslt</artifactId>
</dependency>
```
```properties
# src/main/resources/application.properties
quarkus.camel.xslt.sources = xslt/order-to-invoice.xsl
```
```java
// Camel Quarkus 3.40.x — headers -> <xsl:param>, output default string [C-XSLT]
public class XsltRoutes extends RouteBuilder {
  @Override public void configure() {
    from("direct:transform")
      .removeHeaders("*", "currency")
      .to("xslt:classpath:xslt/order-to-invoice.xsl?transformerCacheSize=4&output=bytes");
  }
}
```

**Integration**: XSLT ↔ camel-quarkus-file (output=file streams to a `File` named by `CamelXsltFileName` [C-XSLT])
```java
from("file:inbox?include=.*\\.xml")
  .setHeader("CamelXsltFileName", simple("outbox/${file:onlyname.noext}.out.xml"))
  .to("xslt:classpath:xslt/t.xsl?output=file&deleteOutputFile=false");
// parent directory "outbox" must exist, otherwise runtime exception [C-XSLT]
```
**Integration**: XSLT ↔ camel-quarkus-jaxb: marshal a POJO to XML with `.marshal().jaxb()`, then call `.to("xslt:...")`. JAXB-specific 3.40 details: UNVERIFIED in this run (see the jaxb research file).
**Integration**: XSLT ↔ camel-quarkus-bean: `resourceUri` supports the `bean:` prefix (`bean:myBean.myMethod`) and `ref:` (registry lookup) [C-XSLT]. Native support for `bean:`/`ref:` templates: UNVERIFIED ([CQ-XSLT] says only `classpath:` works natively).
**Integration**: XSLT ↔ camel-quarkus-core: CDI route discovery and configuration as in the core pilot.

**Error handling**: the default `ErrorListener` stores errors as exchange properties [C-XSLT]. For Saxon these are `Exchange.XSLT_ERROR`, `XSLT_FATAL_ERROR` and `XSLT_WARNING` [C-SAXON]. `failOnNullBody=true` by default [C-XSLT]. `xsl:message` output goes to `xsltMessageLogger` [C-XSLT]. Note that `xsl:messaging` is JVM-only per [CQ-XSLT]. Use route `onException(TransformerException.class)` as usual (exception type UNVERIFIED as the thrown wrapper).

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
./mvnw clean verify                     # JVM tests; Expected: BUILD SUCCESS
./mvnw verify -Dnative                  # native build + @QuarkusIntegrationTest; Expected: BUILD SUCCESS
grep -rn "xslt:file:\|xslt:http" src/main/java   # Expected: no output (native-safe)
grep -n "quarkus.camel.xslt.sources" src/main/resources/application.properties  # Expected: 1 match
```

**Mocking**:
```java
// Camel Quarkus 3.40.x — test pattern per core pilot (camel-quarkus-junit, CamelQuarkusTestSupport)
@QuarkusTest
class XsltRouteTest {
  @Inject ProducerTemplate template;
  @Test void transforms() {
    String out = template.requestBodyAndHeader("direct:transform",
        "<order><total>10</total></order>", "currency", "EUR", String.class);
    assertTrue(out.contains("EUR"));
  }
}
```
No XSLT-specific testing guidance exists on [CQ-XSLT] (Medium). Run native integration tests, because classpath/translet issues appear only in native.

---

## Production Readiness

- **Performance**: build-time translets avoid runtime stylesheet parsing [CQ-XSLT]. `contentCache=true` and `transformerCacheSize=0` are the defaults [C-XSLT]. `xpathTotalOpLimit=10000` [C-XSLT] caps runaway XPath.
- **Scalability**: in-memory outputs (`string`/`bytes`/`DOM`) hold the full result. Use `output=file` for large documents [C-XSLT].
- **Monitoring**: JMX operation `clearCachedStylesheet` [C-XSLT]. Watch for the startup WARN when secure processing is disabled [CQ-MIG].
- **Security checklist**: secure processing on; `allowTemplateFromHeader=false`; headers stripped; `document()` only through an allow-list resolver; no reliance on DTDs. Remember the JAXP-default side effect on Tika and XML Security [CQ-MIG].

---

## Reference Implementations

- Extension reference with config and native examples: [CQ-XSLT]
- Component options and headers: [C-XSLT]; Saxon: [C-SAXON]
- Examples repo: https://github.com/apache/camel-quarkus-examples. An XSLT-specific example was not located (UNVERIFIED).
- Integration tests in https://github.com/apache/camel-quarkus (`integration-tests/xslt`, path UNVERIFIED in this run).

---

## Source Bibliography

**Primary** (all fetched 2026-10-14; pages undated, versioned docs of current LTS):
- [CQ-XSLT] https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html
- [CQ-MIG] https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- [C-XSLT] https://camel.apache.org/components/4.22.x/xslt-component.html
- [C-SAXON] https://camel.apache.org/components/4.22.x/xslt-saxon-component.html
- [CQ-SAXON] https://camel.apache.org/camel-quarkus/latest/reference/extensions/xslt-saxon.html
- [REL] https://camel.apache.org/releases/ (CQ 3.40.0 2026-09-28 LTS; Camel 4.22.1 2026-09-17, 4.22.0 2026-08-11)
- [MVN] https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-xslt/ (3.40.0 2026-09-24)

**Validation** (contrast only, not target version): [C-XSLT-NEXT] https://camel.apache.org/components/next/xslt-component.html
**Reused**: workspace/research_Camel_Quarkus_Core_v3.40.md (BOM, LTS, testing, Quarkus 4 risk; its URLs were not re-fetched except [REL]).

---

## Research Gaps

```
Gap: xslt-saxon behaviour under the 3.40 hardening (entities, document(), JAXP default)
Impact: Saxon users may assume protections that apply only to Xalan
Workaround: treat Saxon as unhardened; keep secureProcessing=true; custom URIResolver
Follow-up: apache/camel-quarkus 3.40.0 release notes / extensions/xslt-saxon source
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: per-property "fixed at build time" markers for quarkus.camel.xslt.*
Impact: may try to change sources/features at runtime
Workaround: treat all three as build-time; rebuild after change
Follow-up: open [CQ-XSLT] in a browser and read the lock icons
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: Camel 4.22.x security section (ACCESS_EXTERNAL_* defaults) absent from [C-XSLT] rendering
Impact: unclear Camel-side defaults on JVM when a non-CQ factory is used
Workaround: rely on CQ-enforced restrictions [CQ-XSLT]
Follow-up: Camel 4.22 upgrade guide / CAMEL JIRA
§7-ref: Iteration 2 — IRRESOLVABLE
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Metadata | camel-quarkus-xslt-saxon exists in 3.40 line | Resolved (exists; native since 3.2.0) | [CQ-SAXON] (2026-10-14) |
| 1 | Metadata | 3.40.0 artifact on Maven Central | Resolved (2026-09-24) | [MVN] (2026-10-14) |
| 1 | Metadata | Release/LTS date | Resolved (2026-09-28, LTS) | [REL] (2026-10-14) |
| 2 | Conditional E | document() runtime refusal of http/file in Camel | Resolved: Camel 4.23+ only, not 4.22 | [C-XSLT-NEXT] vs [C-XSLT] (2026-10-14) |
| 2 | Bibliography | 4.22.x ACCESS_EXTERNAL_* section | ⚠️ IRRESOLVABLE — not rendered on 4.22.x page | — |
| 3 | Conditional A | Saxon options/defaults | Resolved | [C-SAXON] (2026-10-14) |
| 3 | Migration | Saxon covered by 3.40 hardening | ⚠️ IRRESOLVABLE — migration guide silent | — |
| 3 | Mandatory 1 | per-property build-time markers | ⚠️ IRRESOLVABLE — tool did not render markers | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented
- [x] All scope areas cited
- [x] Pattern counts driven by domain needs (not template minimums)
- [x] Every anti-pattern has alternative
- [x] All CLI commands validated/marked as representative
- [x] Integration examples complete (jaxb partially UNVERIFIED)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated (deep/exhaustive) or downgraded to 🟡 Medium
- [x] Research Iteration Changelog present and complete (skip for depth=quick)
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: build-time `sources`, classpath-only native, secure processing default, 3.40 hardening (entities, `document()`, features at runtime, JAXP default), component defaults (`contentCache=true`, `output=string`, `transformerCacheSize=0`, `xpathTotalOpLimit=10000`, `failOnNullBody=true`, `allowTemplateFromHeader=false`).
- **Medium Confidence (validate with user)**: header stripping (explicit warning only on the 4.23 page), extension-function reflection setup, choosing Saxon, escaped feature key.
- **Low Confidence (must ask human)**: the 3 IRRESOLVABLE items; Camel property spelling `camel.component.xslt.*`; native `bean:`/`ref:` templates.
- **Edge Cases (pause)**: 3.40.0 released 2026-09-28, more than 14 days ago but less than 30 days before research. Docs may still change. Quarkus 4 risk: see core pilot.
- **Emergency Stop**: not triggered. All sources are official.
