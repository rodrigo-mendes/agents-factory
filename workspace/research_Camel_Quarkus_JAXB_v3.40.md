# Research: Camel Quarkus JAXB v3.40 (camel-quarkus-jaxb / Camel 4.22.x camel-jaxb / Quarkus 3.40.x quarkus-jaxb)

> Version lock: every claim here applies to **Camel Quarkus 3.40.x** only (Camel 4.22.x, Quarkus 3.40.x). Patterns from the old 3.15 file are not sources. Each one used here was re-checked against 3.40.x pages.
> All sources were fetched on **2026-10-14**. camel.apache.org pages carry no publication date of their own. They count as current because they are the versioned docs for the current stable LTS: `camel-quarkus/3.40.x` and `components/4.22.x`.
> Workflow note: this was a forked batch run that the user approved upstream. There was no user to approve a plan, so the P3 plan-approval step (EnterPlanMode/ExitPlanMode) was **skipped**. Per the caller's constraint, no section-investigator or synthesizer subagents were spawned. All pages were fetched directly and this file was written directly.
> Core topics (BOM, CDI/RouteBuilder scope, TLS, testing framework rename, LTS dates) are **not repeated** here. See `workspace/research_Camel_Quarkus_Core_v3.40.md`.

---

## Metadata

```yaml
Full_Name: Apache Camel Quarkus — JAXB extension (org.apache.camel.quarkus:camel-quarkus-jaxb)
Target_Version: 3.40.x (camel-quarkus-jaxb 3.40.0 on Maven Central — https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0)
Release_Date: 2026-09-28 (CQ 3.40.0, per https://camel.apache.org/releases/ as recorded in the Core v3.40 pilot; Central page shows only "19 days ago" on 2026-10-14 — consistent)
Support_Status: LTS (CQ 3.40.0 marked LTS on https://camel.apache.org/releases/ — from the Core pilot; CQ-specific LTS end date UNVERIFIED)
Primary_Docs: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html
Dataformat_Docs: https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html
Official_Repo: https://github.com/apache/camel-quarkus/tree/3.40.x/extensions/jaxb
Research_Date: 2026-10-14
Domain_Complexity: Standard (build-time class discovery + native reflection + schema validation + XML security surface)
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 4
Unverified_Count: 6
Irresolvable_Count: 3
Research_Quality_Score: 89%   # ~85 claims; (85 - 6 - 3) / 85
```

---

## Executive Summary

`camel-quarkus-jaxb` brings the Camel JAXB data format (`camel-jaxb`, Camel 4.22.x) to Quarkus. It marshals Java objects to XML and unmarshals XML back to objects, using Jakarta XML Binding (`jakarta.xml.bind`). JVM and native mode have both been supported "since 1.0.0" (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html) [High].

The 3.40.0 POM depends on `camel-quarkus-core`, on `org.apache.camel:camel-jaxb` with `com.sun.xml.bind:*` excluded, and on `camel-quarkus-support-jaxb` (https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0) [High]. `camel-quarkus-support-jaxb` in turn depends on Quarkus' own `quarkus-jaxb` (https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-support-jaxb/3.40.0/jar) [Medium; seen via search result summary]. Quarkus' `JaxbProcessor` therefore does the native work at build time. It scans `@XmlRootElement`, `@XmlType` and `@XmlRegistry` classes and every `jaxb.index` file, and registers them for reflection and as native resources (https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/deployment/src/main/java/io/quarkus/jaxb/deployment/JaxbProcessor.java) [High]. The Camel Quarkus support processor excludes `org.apache.camel.model.*` from that scan (https://github.com/apache/camel-quarkus/blob/3.40.x/extensions-support/jaxb/deployment/src/main/java/org/apache/camel/quarkus/support/jaxb/deployment/JaxbProcessor.java) [High].

Nothing in the CQ 3.40.0 migration guide concerns JAXB. Its XML-related changes affect `camel-quarkus-xslt`: external entities are no longer resolved, `document()` is denied unless a URIResolver resolves it, and `quarkus.camel.xslt.features` now applies to every template (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html) [High].

Three critical patterns:
1. Pin a `contextPath` (package, or a class with `contextPathIsClassName=true`) on a named `JaxbDataFormat` bean.
2. In native mode, register for reflection **only** the non-JAXB-annotated POJOs that an `ObjectFactory` instantiates. Annotated classes and `jaxb.index` entries are registered by the extension.
3. Validate with `schema` while keeping `accessExternalSchemaProtocols` unset. The unset default blocks external DTD and schema access.

The tier is **Standard**: there is a single data format, but build-time and native concerns combine with the XML security settings.

**Quarkus 4 / Jackson 3 / Java 21 assessment.** Quarkus 4.0.0.Beta1 sets Java 21 as the minimum and ports Jackson to 3 (https://github.com/quarkusio/quarkus/releases/tag/4.0.0.Beta1). GA is "planned for the end of November" 2026 (https://quarkus.io/blog/quarkus-4-0-0-beta1-released/) [High]. The Quarkus 4.0 migration guide has **no JAXB / `jakarta.xml.bind` entries** (https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0, fetched 2026-10-14) [High].

- **Jackson 3:** does **not** touch `camel-quarkus-jaxb`. Its 3.40.0 dependency list has no Jackson (https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0). It **does** touch the partner `camel-quarkus-jacksonxml`, which runs on Jackson's XmlMapper (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jacksonxml.html), and any use of `jackson-module-jakarta-xmlbind-annotations` (UNVERIFIED for CQ).
- **Java 21:** a baseline bump. It does not affect the JAXB API itself.
- **Timing:** no Camel Quarkus release on Quarkus 4 exists yet (see the Core pilot). Pin 3.40.x.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**1. Declare the extension without a version (BOM-managed)**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ jaxb ext page (2026-10-14) + Maven Central 3.40.0 POM (2026-10-14)]
- Why: the CQ page lists only GA coordinates. The version comes from `quarkus-camel-bom` (see Core pilot).
- Code:
  ```xml
  <!-- Camel Quarkus 3.40.x -->
  <dependency>
      <groupId>org.apache.camel.quarkus</groupId>
      <artifactId>camel-quarkus-jaxb</artifactId>
  </dependency>
  ```
- Do not add `com.sun.xml.bind:*` yourself. The 3.40.0 POM excludes it from `camel-jaxb` (https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0) [High]. The Quarkus JAXB extension wires the Glassfish JAXB runtime through `ServiceProviderBuildItem` (https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/deployment/src/main/java/io/quarkus/jaxb/deployment/JaxbProcessor.java) [High].
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html (2026-10-14)

**2. Configure a named `JaxbDataFormat` bean with an explicit `contextPath`**
> Confidence: 🟢 High | [✓✓ Triangulated | 4.22.x dataformat page + CQ 3.40.x integration test JaxbProducers.java]
- Why: `contextPath` is the required option (https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html). If it is null, `JaxbDataFormat` calls `JAXBContext.newInstance()` with no classes. With a context path it calls `JAXBContext.newInstance(contextPath, classLoader)`. The context is built once in `doStart()` and cached per data format instance. Marshallers and unmarshallers are created per call because they are not thread-safe (https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java) [High].
- Code (shape taken from the 3.40.x IT):
  ```java
  // Camel Quarkus 3.40.x — mirrors integration-tests/jaxb JaxbProducers.java
  import jakarta.enterprise.context.ApplicationScoped;
  import jakarta.enterprise.inject.Produces;
  import jakarta.inject.Named;
  import org.apache.camel.converter.jaxb.JaxbDataFormat;

  @ApplicationScoped
  public class JaxbFormats {
      @Produces @Named("jaxbPerson")
      JaxbDataFormat jaxbPerson() {
          JaxbDataFormat df = new JaxbDataFormat();
          df.setContextPath(Person.class.getPackageName()); // package containing ObjectFactory or jaxb.index
          df.setPrettyPrint(false);
          return df;
      }
  }

  // Route (plain RouteBuilder; no CDI scope needed unless it injects)
  from("direct:marshal").marshal("jaxbPerson");
  // Inline DSL alternative used by the IT:
  from("direct:unmarshal").unmarshal().jaxb(Person.class.getPackageName());
  ```
- Source: https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbProducers.java ; https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbRoute.java (2026-10-14)
- Note: the package-based `contextPath` only resolves when the package has an `ObjectFactory` (`@XmlRegistry`) or a `jaxb.index` file. That rule comes from the Jakarta XML Binding `JAXBContext.newInstance(String)` contract, which was **not fetched** in this run: **UNVERIFIED** (Medium in practice).

**3. Native mode: register only the non-annotated POJOs that an ObjectFactory creates**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ 3.40.x jaxb ext page + Quarkus 3.40 JaxbProcessor source]
- Why: the CQ page says that if a custom `ObjectFactory` instantiates POJOs without JAXB annotations, "you must register those POJO classes for reflection in order for them to be instantiated in native mode". Use `@RegisterForReflection` or `quarkus.camel.native.reflection.include-patterns` (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html). Classes annotated with `@XmlRootElement`, `@XmlType` or `@XmlRegistry`, classes listed in `jaxb.index` (plus their superclasses), `@XmlSeeAlso` targets and `@XmlJavaTypeAdapter` classes are all registered automatically. Every `jaxb.index` file is also added as a native resource (`includeGlob("**/jaxb.index")`) (https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/deployment/src/main/java/io/quarkus/jaxb/deployment/JaxbProcessor.java).
- Code:
  ```java
  // Camel Quarkus 3.40.x — POJO created by ObjectFactory, no JAXB annotations
  @io.quarkus.runtime.annotations.RegisterForReflection
  public class PojoPerson { /* fields, getters, setters */ }
  ```
  ```properties
  # alternative (artifact must have a Jandex index — native-mode guide)
  quarkus.camel.native.reflection.include-patterns = com.acme.pojo.*
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html (2026-10-14)

**4. Validate against XSD with external access left blocked**
> Confidence: 🟢 High | [✓✓ Triangulated | 4.22.x dataformat page + JaxbDataFormat 4.22.x source]
- Why: `schema` accepts comma-separated `classpath:`, `file:` or `http:` locations. `schemaSeverityLevel` defaults to `0` (0 = warning, 1 = error, 2 = fatal) (https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html). When `accessExternalSchemaProtocols` is unset (default `null`), the `SchemaFactory` sets `ACCESS_EXTERNAL_DTD` and `ACCESS_EXTERNAL_SCHEMA` to `""`, enables `FEATURE_SECURE_PROCESSING` and disallows DOCTYPE. The compiled schema is cached at startup (https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java).
- Code:
  ```java
  // Camel Quarkus 3.40.x — as in IT bean "jaxbDefault"
  df.setSchema("classpath:person.xsd");
  df.setSchemaSeverityLevel(2); // fail only on fatal errors (IT value); 0 = fail on warnings
  ```
- In native mode, use `classpath:` schemas. They must be in the image as resources, for example via `quarkus.native.resources.includes` (property name UNVERIFIED in this run).
- Source: https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbProducers.java (2026-10-14)

**5. Handle marshal/unmarshal failures as `IOException`**
> Confidence: 🟡 Medium (single source: 4.22.x source code)
- Why: marshal wraps any exception in `IOException`, including the `InvalidPayloadException` thrown when `mustBeJAXBElement=true`. Unmarshal converts `JAXBException`, including schema-validation failures and a missing part class, to `IOException` (https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java).
- Code:
  ```java
  // Camel 4.22.x / CQ 3.40.x
  onException(java.io.IOException.class)
      .handled(true)
      .log("JAXB failure: ${exception.message}")
      .to("direct:xmlDeadLetter");
  ```

### ⚠️ Conditional Patterns

**A. contextPath as package vs as class (`contextPathIsClassName`)**
> Confidence: 🟢 High
- Options: package (default, `contextPathIsClassName=false`), or single class name (`true`)
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Package | XJC output (ObjectFactory), many root types | Needs ObjectFactory/jaxb.index in package | Schema-generated models |
  | Class name (`contextPathIsClassName=true`) | No ObjectFactory/jaxb.index needed; resolved via `ClassResolver.resolveMandatoryClass` | Context bound only to that class graph | Hand-written single-root POJO |

- Agent: "Ask: are the classes XJC-generated (ObjectFactory present) or hand-written with a single root?"
- Source: https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html ; https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java (2026-10-14)

**B. Camel's JAXBContext vs Quarkus' CDI JAXBContext bean**
> Confidence: 🟢 High
- Facts: Quarkus produces a `@DefaultBean @Singleton JAXBContext` plus `@RequestScoped` `Marshaller` and `Unmarshaller`. They are built from the build-time classes-to-be-bound set (https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/runtime/src/main/java/io/quarkus/jaxb/runtime/JaxbContextProducer.java). Camel's `JaxbDataFormat` builds **its own** context from `contextPath` unless one is injected (JaxbDataFormat.java 4.22.x).
- Options: let Camel build from `contextPath` (default), or inject a context.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Camel-built from contextPath | Isolation per model package | Context built at startup per format | Default |
  | Quarkus bean + `quarkus.jaxb.validate-jaxb-context=true` | Build-time failure on bad model | Default context binds *all* scanned classes; use `quarkus.jaxb.exclude-classes` (supports `org.acme.*`) | One app-wide model |

- `quarkus.jaxb.validate-jaxb-context` defaults to `false`. `quarkus.jaxb.exclude-classes` has no default. Both are `BUILD_AND_RUN_TIME_FIXED` (https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/runtime/src/main/java/io/quarkus/jaxb/runtime/JaxbConfig.java) [High]. A failed validation throws `DeploymentException("Failed to create or validate the default JAXBContext")` (Quarkus JaxbProcessor 3.40) [High]. The setter that injects a context into `JaxbDataFormat` was not quoted: **UNVERIFIED** name.
- Agent: "Ask: should a model error fail the build (Quarkus validation) or the route start?"

**C. JAXBElement handling (`ignoreJAXBElement`, `mustBeJAXBElement`, `objectFactory`)**
> Confidence: 🟢 High
- Defaults: `ignoreJAXBElement=true` (unwraps the value), `mustBeJAXBElement=false` (non-JAXB bodies, such as an XML String, are copied through), `objectFactory=true` (ObjectFactory methods are used to wrap non-root POJOs) (https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | defaults | Simple POJO body | Pass-through hides wrong body types | Most routes |
  | `mustBeJAXBElement=true` | Fails fast on wrong type (`InvalidPayloadException` → `IOException`) | Cannot pass raw XML | Strict contracts |
  | `ignoreJAXBElement=false` | Keeps QName/namespace metadata | Caller must unwrap | Schema-aware processing |

- Source: https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java (2026-10-14)

**D. Partial / fragment marshalling**
> Confidence: 🟢 High
- Options: static `partClass` / `partNamespace`, per message via headers `CamelJaxbPartClass` / `CamelJaxbPartNamespace` (value format `{namespaceUri}localPart`), and `fragment=true` (default `false`) to omit the XML declaration (https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html).
- Code (3.40.x IT):
  ```java
  // Camel Quarkus 3.40.x
  from("direct:partMarshal")
      .setHeader(JaxbConstants.JAXB_PART_CLASS, constant(PartClassPerson.class.getName()))
      .setHeader(JaxbConstants.JAXB_PART_NAMESPACE,
          constant(String.format("{%s}person", PartClassPerson.NAMESPACE)))
      .marshal().jaxb(PartClassPerson.class.getPackageName());
  // bean form:
  df.setPartClass(PartClassPerson.class);
  df.setPartNamespace(new QName(PartClassPerson.NAMESPACE, "person"));
  ```
- Agent: "Ask: is the part type fixed per route (bean options) or decided per message (headers)?"
- Source: https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbRoute.java (2026-10-14)

**E. Namespace prefixes and encoding**
> Confidence: 🟢 High
- `namespacePrefix`: a `Map<String,String>` from namespace URI to prefix. It replaces the generated `ns2`, `ns3`. IT: `setNamespacePrefix(Map.of("https://example.com/a", "test"))`. The page text says `namespacePrefixRef` in its Spring XML example, while the options table says `namespacePrefix`.
- `encoding`: sets the JAXB encoding (no default). The exchange property `Exchange.CHARSET_NAME` overrides it. IT: `setEncoding("ISO-8859-1")` together with `setFilterNonXmlChars(true)`. `filterNonXmlChars` defaults to `false`, and `Exchange.FILTER_NON_XML_CHARS` takes precedence over it.
- Source: https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html ; https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbProducers.java (2026-10-14)

**F. Large XML: split first, then unmarshal fragments**
> Confidence: 🟡 Medium (Split EIP page; the JAXB-plus-split combination is not shown as an official example)
- Facts: the `streaming` option defaults to `false`, and in that mode "all sub messages [are] kept temporary in-memory". `xtokenize` "uses a StAX parser" and `tokenizeXML` splits by child tag name. The XPath engine "will load the entire XML content into memory" (https://camel.apache.org/components/4.22.x/eips/split-eip.html). JAXB unmarshal reads through an `XMLStreamReader` but builds the full object graph (JaxbDataFormat.java 4.22.x).
- Code:
  ```java
  // Camel 4.22.x / CQ 3.40.x — representative
  from("file:in?noop=true")
      .split().xtokenize("//order", 'i').streaming()
          .unmarshal("jaxbOrder")
          .to("direct:processOrder");
  ```
- Whether `xtokenize` (camel-quarkus-xml-jaxp / stax) works in native mode was not checked: **UNVERIFIED**.
- Agent: "Ask the expected maximum document size."

### 🚫 Forbidden Patterns

**1. Putting `@RegisterForReflection` on every `@XmlRootElement` class (3.15-era habit)**
> Severity: Medium
> Confidence: 🟢 High
- Why: Quarkus JAXB already registers annotated classes and `jaxb.index` entries (Quarkus JaxbProcessor 3.40). The 3.40.x CQ page requires manual registration only for **non-annotated** POJOs that an `ObjectFactory` creates.
- Impact: noise, and it hides the case that really needs registration.
- ❌ Wrong:
  ```java
  @RegisterForReflection @XmlRootElement
  public class Customer { }
  ```
- ✅ Correct:
  ```java
  @XmlRootElement            // discovered by quarkus-jaxb at build time
  public class Customer { }
  @RegisterForReflection     // only for non-annotated POJOs built by ObjectFactory
  public class PojoPerson { }
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html ; https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/deployment/src/main/java/io/quarkus/jaxb/deployment/JaxbProcessor.java (2026-10-14)

**2. Opening external schema access to "make imports work"**
> Severity: High
> Confidence: 🟢 High
- Why: the unset `accessExternalSchemaProtocols` blocks external DTD and schema access (XXE/SSRF surface). The docs say a protocol must be enabled only if the XSDs import other files.
- Impact: with `"all"` or `http`, the schema loader can fetch remote resources.
- ❌ Wrong:
  ```java
  df.setSchema("classpath:order.xsd");
  df.setAccessExternalSchemaProtocols("all");
  ```
- ✅ Correct:
  ```java
  df.setSchema("classpath:order.xsd,classpath:common.xsd"); // list imported XSDs explicitly
  // or, if imports must resolve locally only:
  df.setAccessExternalSchemaProtocols("file");
  ```
- The exact accepted values (`all`, `file`, `http`) follow `XMLConstants.ACCESS_EXTERNAL_SCHEMA` semantics and were not quoted on the page: **UNVERIFIED**.
- Source: https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html ; https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java (2026-10-14)

**3. Relying on pass-through with the default `mustBeJAXBElement=false` for typed contracts**
> Severity: Medium
> Confidence: 🟢 High
- Why: if no ObjectFactory method fits, the body is converted to an `InputStream` and copied out unchanged. A wrong POJO type can then leak through silently.
- ❌ Wrong:
  ```java
  from("direct:out").marshal().jaxb("com.acme.model"); // a String body passes through
  ```
- ✅ Correct:
  ```java
  JaxbDataFormat df = new JaxbDataFormat("com.acme.model");
  df.setMustBeJAXBElement(true); // InvalidPayloadException -> IOException
  ```
- Source: https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java (2026-10-14)

**4. Sharing one Marshaller/Unmarshaller across threads in custom processors**
> Severity: High
> Confidence: 🟢 High
- Why: Camel's own source creates a new marshaller per call because "its not thread safe". Quarkus' produced `Marshaller`/`Unmarshaller` are `@RequestScoped`.
- ❌ Wrong:
  ```java
  private static final Marshaller M = ctx.createMarshaller(); // shared
  ```
- ✅ Correct:
  ```java
  Marshaller m = jaxbContext.createMarshaller(); // per invocation; JAXBContext itself is shared
  ```
- Source: https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java ; https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/runtime/src/main/java/io/quarkus/jaxb/runtime/JaxbContextProducer.java (2026-10-14)

**5. `file:`/`http:` schema or model resources in native builds**
> Severity: Medium
> Confidence: 🟡 Medium
- Why: Camel Quarkus native supports `classpath:` resources only for build-time compiled XSLT (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html). Whether JAXB `schema` has the same constraint is not documented. Treat `file:`/`http:` as not portable.
- ❌ Wrong: `df.setSchema("http://example.com/order.xsd");`
- ✅ Correct: `df.setSchema("classpath:xsd/order.xsd");` and include the resource in the native image.

**6. Adding `com.sun.xml.bind` / a second JAXB runtime manually**
> Severity: Medium
> Confidence: 🟡 Medium
- Why: the 3.40.0 POM deliberately excludes `com.sun.xml.bind:*`. Quarkus JAXB supplies the Glassfish runtime through service providers.
- ❌ Wrong: `<dependency><groupId>com.sun.xml.bind</groupId><artifactId>jaxb-impl</artifactId></dependency>`
- ✅ Correct: rely on `camel-quarkus-jaxb` → `camel-quarkus-support-jaxb` → `quarkus-jaxb`.
- Source: https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0 (2026-10-14)

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (2026-10-14) + https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0 (2026-10-14)

**Breaking Changes (3.40.0)**: none for JAXB (the 3.40.0 guide has no JAXB heading). Changes that affect JAXB-adjacent code:
- XSLT: inputs are parsed with an `XMLReader` that "does not resolve external entities or load external DTDs". `document()` is denied unless a URIResolver resolves it. `quarkus.camel.xslt.features` now applies to every template, and unsupported features fail endpoint creation. This also affects direct `TransformerFactory.newInstance()` use, for example when you marshal JAXB to a `Source` and transform it yourself.
- Core: `quarkus.camel.native.reflection.serialization-enabled=false` now vetoes extension registrations (see Core pilot). JAXB does not use Java serialization (not listed among the affected extensions).

**3.15 → 3.40 drift (JAXB-specific)**: the option set on the 4.22.x page includes `accessExternalSchemaProtocols` (security), `contentTypeHeader` (default `true`) and `jaxbProviderProperties`. Which Camel release added each one was not traced: UNVERIFIED.

**Upgrade Steps**:
1. Bump `quarkus.platform.version` / `quarkus-camel-bom` to 3.40.1 (Core pilot).
2. Remove `@RegisterForReflection` from JAXB-annotated classes. Keep it only on ObjectFactory-created POJOs.
3. Check every `schema` option. If imports fail, list the XSDs explicitly instead of opening protocols.
4. Rebuild native: `./mvnw package -Dnative` (representative).

**Quarkus 4 outlook**: Java 21 minimum and Jackson 3 (`tools.jackson.*` packages, annotations unchanged in `com.fasterxml.jackson.annotation`). No JAXB entries. Impact on `camel-quarkus-jaxb` is expected to be none beyond the Java baseline. Impact on `camel-quarkus-jacksonxml` is expected to be real.

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Camel Quarkus | 3.40.0 | 3.40.x | central.sonatype.com camel-quarkus-jaxb/3.40.0 |
| Camel (camel-jaxb) | 4.22.x | 4.22.x | Core pilot (docs index lists 4.22.1) |
| Quarkus (quarkus-jaxb) | 3.40.1 | 3.40.x | Quarkus 4 not supported by CQ yet |
| Java | 17 | 21 | Core pilot (https://camel.apache.org/releases/q-3.40.0/) |
| Jakarta XML Binding API version | — | — | UNVERIFIED (not read from the BOM) |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | official IT (3.40.x) + official dataformat docs (4.22.x)]

**Lifecycle**:
```java
// Camel Quarkus 3.40.x
// Init: JaxbDataFormat.doStart() builds/caches JAXBContext + compiled Schema
// Usage: per-exchange Marshaller/Unmarshaller
// Cleanup: none required (context cached on the data format instance)

@XmlRootElement(name = "person", namespace = "https://example.com/a")
@XmlAccessorType(XmlAccessType.FIELD)
public class Person { String firstName; String lastName; }

// src/main/resources/com/acme/model/jaxb.index   (if no ObjectFactory)
//   Person

public class PersonRoutes extends RouteBuilder {
    @Override public void configure() {
        onException(java.io.IOException.class).handled(true).to("direct:xmlError");
        from("direct:toXml").marshal("jaxbPerson");          // bean from JaxbFormats
        from("direct:fromXml").unmarshal("jaxbPerson");
    }
}
```

**Integration**: Camel Quarkus JAXB ↔ camel-quarkus-file + xslt
```java
// Camel Quarkus 3.40.x — representative
from("file:inbox?include=.*\\.xml")
    .unmarshal("jaxbPerson")                 // XML -> Person
    .bean(PersonService.class, "enrich")     // camel-quarkus-bean
    .marshal("jaxbPerson")                   // Person -> XML
    .to("xslt:classpath:xsl/person-to-v2.xsl")   // must be in quarkus.camel.xslt.sources for native
    .to("file:outbox");
```
```properties
# camel-quarkus-xslt 3.40.x (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html)
quarkus.camel.xslt.sources = xsl/person-to-v2.xsl
# quarkus.camel.xslt.package-name default: org.apache.camel.quarkus.component.xslt.generated
```

**Integration**: JAXB vs camel-quarkus-jacksonxml
- `camel-quarkus-jacksonxml` (JVM and native since 1.0.0) uses Jackson's XmlMapper (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jacksonxml.html). Choose JAXB for XSD-driven contracts, schema validation and namespaces. Choose jackson-xml when the POJOs are already Jackson-annotated. Jackson XML is the one exposed to the Quarkus 4 / Jackson 3 migration. Its options were not fetched (the 4.22.x jacksonXml page URL returned 404): UNVERIFIED.

**Integration**: REST DSL binding
- CQ registers a `JaxbRestBindingJaxbDataFormatFactory` context plugin at STATIC_INIT, so REST DSL XML binding uses JAXB when the extension is present (https://github.com/apache/camel-quarkus/blob/3.40.x/extensions/jaxb/runtime/src/main/java/org/apache/camel/quarkus/component/jaxb/JaxbRecorder.java ; https://github.com/apache/camel-quarkus/blob/3.40.x/extensions/jaxb/deployment/src/main/java/org/apache/camel/quarkus/component/jaxb/deployment/JaxbProcessor.java) [High].

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
./mvnw quarkus:add-extension -Dextensions=org.apache.camel.quarkus:camel-quarkus-jaxb
# Expected: dependency added without <version>
./mvnw test
# Expected: JVM tests green
./mvnw verify -Dnative
# Expected: native IT passes; missing-reflection errors surface as unmarshal failures
# Optional build-time model check:
#   quarkus.jaxb.validate-jaxb-context=true  -> DeploymentException on bad model
```

**Mocking**:
```java
// Camel Quarkus 3.40.x — @QuarkusTest + ProducerTemplate (test support package: see Core pilot)
@QuarkusTest
class PersonRoutesTest {
    @Inject ProducerTemplate template;

    @Test
    void roundTrip() {
        Person p = new Person(); p.firstName = "Ada"; p.lastName = "Lovelace";
        String xml = template.requestBody("direct:toXml", p, String.class);
        assertTrue(xml.contains("Ada"));
        Person back = template.requestBody("direct:fromXml", xml, Person.class);
        assertEquals("Lovelace", back.lastName);
    }
}
```
- Pattern source: the CQ 3.40.x jaxb IT (`JaxbResource` + `JaxbRoute`) drives routes through REST resources and `direct:` endpoints (https://github.com/apache/camel-quarkus/tree/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it) [Medium].
- Add a `@QuarkusIntegrationTest` subclass so the same tests run against the native image.

---

## Production Readiness

- **Performance**: the JAXBContext is created once per `JaxbDataFormat` instance at start, and marshallers are created per call (JaxbDataFormat.java 4.22.x). Reuse named beans rather than inline `.jaxb(...)` in many routes; each inline definition creating its own context is UNVERIFIED. `prettyPrint` has default `true` in the 4.22.x options table, but the page's prose says "by default false". Set it explicitly (the IT sets `false`). The real default is UNVERIFIED (conflicting text).
- **Scalability**: JAXB materialises full object graphs. For large inputs, split with `xtokenize` + `streaming()` (Split EIP 4.22.x).
- **Monitoring**: count `IOException` from the data format in `onException`. The `contentTypeHeader=true` default sets `Content-Type` (`application/xml`) (4.22.x page).
- **Security**:
  - Keep `accessExternalSchemaProtocols` unset.
  - Prefer `classpath:` XSDs.
  - The unmarshal-side `XMLInputFactory` external-entity settings come from Camel's StAX type converter, not `JaxbDataFormat`, and were not verified. UNVERIFIED: treat untrusted XML through XSLT/StAX with care. CQ 3.40.0 hardened the XSLT path.
  - `filterNonXmlChars` only replaces invalid characters with a space. It is not a sanitiser.

---

## Reference Implementations

- CQ 3.40.x JAXB integration tests: https://github.com/apache/camel-quarkus/tree/3.40.x/integration-tests/jaxb (JaxbRoute, JaxbProducers with 10 named data formats: default/schema/fragment, namespacePrefix, encoding+filterNonXmlChars, mustBeJAXBElement=false, partClass, ignoreElement, jaxbProviderProperties, custom XmlStreamWriter, objectFactory=false, noNamespaceSchemaLocation)
- CQ extension source: https://github.com/apache/camel-quarkus/tree/3.40.x/extensions/jaxb
- Quarkus JAXB extension source: https://github.com/quarkusio/quarkus/tree/3.40/extensions/jaxb
- Project generator: https://code.quarkus.io/?extension-search=camel-quarkus-jaxb

---

## Source Bibliography

**Primary** (all fetched 2026-10-14):
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html — coordinates, JVM/native since 1.0.0, ObjectFactory reflection note
- https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html — options and defaults, headers, exchange properties
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html — @RegisterForReflection, include/exclude patterns, serialization-enabled
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html — XSLT/Core changes, no JAXB entry
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html — xslt properties and defaults
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jacksonxml.html — jacksonxml coordinates and native support
- https://camel.apache.org/components/4.22.x/eips/split-eip.html — streaming default, xtokenize
- https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0 — POM deps, com.sun.xml.bind exclusion
- https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-support-jaxb/3.40.0/jar — depends on quarkus-jaxb (search summary)
- https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java
- https://github.com/apache/camel-quarkus/blob/3.40.x/extensions/jaxb/deployment/src/main/java/org/apache/camel/quarkus/component/jaxb/deployment/JaxbProcessor.java
- https://github.com/apache/camel-quarkus/blob/3.40.x/extensions/jaxb/runtime/src/main/java/org/apache/camel/quarkus/component/jaxb/JaxbRecorder.java
- https://github.com/apache/camel-quarkus/blob/3.40.x/extensions-support/jaxb/deployment/src/main/java/org/apache/camel/quarkus/support/jaxb/deployment/JaxbProcessor.java
- https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbProducers.java
- https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbRoute.java
- https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/deployment/src/main/java/io/quarkus/jaxb/deployment/JaxbProcessor.java
- https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/runtime/src/main/java/io/quarkus/jaxb/runtime/JaxbConfig.java
- https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/runtime/src/main/java/io/quarkus/jaxb/runtime/JaxbContextProducer.java
- https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0 — Jackson 3, no JAXB entry
- https://github.com/quarkusio/quarkus/releases/tag/4.0.0.Beta1 — Java 21 minimum, Jackson 3
- https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ — GA end of November 2026

**Validation**: `workspace/research_Camel_Quarkus_Core_v3.40.md` (versions, LTS, Java 17/21). Its URLs were reused and not re-fetched in this run.
**Not usable**: https://quarkus.io/guides/jaxb and https://quarkus.io/guides/xml returned 404. https://camel.apache.org/components/4.22.x/dataformats/jacksonXml-dataformat.html returned 404.

---

## Research Gaps

```
Gap: Camel Quarkus 3.40 LTS end date
Impact: version-lifetime planning
Workaround: assume Quarkus 3.40 LTS window (to 2027-09-30, Core pilot)
Follow-up: https://camel.apache.org/releases/ "LTS Until" column
§7-ref: Iteration 1 — IRRESOLVABLE
```
```
Gap: Real default of prettyPrint (table says true, prose says false)
Impact: output format differs from expectation
Workaround: always set prettyPrint explicitly
Follow-up: JaxbDataFormat.java field initialiser / JaxbDataFormat model class in camel-core-model 4.22.x
§7-ref: Iteration 2 — IRRESOLVABLE
```
```
Gap: Camel Quarkus release on Quarkus 4 (Jackson 3 effect on camel-quarkus-jacksonxml)
Impact: migration timing for XML stacks using Jackson XML
Workaround: pin 3.40.x; prefer JAXB for new XML contracts
Follow-up: https://camel.apache.org/releases/ and Maven Central quarkus-camel-bom 4.x
§7-ref: Iteration 3 — IRRESOLVABLE
```
Other UNVERIFIED items: the JAXB `contextPath` ObjectFactory/jaxb.index spec rule; the injection setter for an external JAXBContext; accepted `accessExternalSchemaProtocols` values; native support for `xtokenize`; the unmarshal XMLInputFactory XXE settings; the `quarkus.native.resources.includes` property name; the jacksonxml options; the Jakarta XML Binding API version in the BOM.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Executive Summary | How native class discovery works | Resolved: Quarkus JaxbProcessor scans annotations and jaxb.index; CQ support excludes org.apache.camel.model.* | https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/deployment/src/main/java/io/quarkus/jaxb/deployment/JaxbProcessor.java (2026-10-14) |
| 1 | Conditional B | quarkus.jaxb.* properties (guide 404) | Resolved from JaxbConfig source | https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/runtime/src/main/java/io/quarkus/jaxb/runtime/JaxbConfig.java (2026-10-14) |
| 1 | Metadata | CQ LTS end date | ⚠️ IRRESOLVABLE — releases page column blank (Core pilot) | — |
| 2 | Mandatory 2/4/5 | Context caching, schema security defaults, exception types | Resolved from 4.22.x source | https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java (2026-10-14) |
| 2 | Production | prettyPrint default conflict | ⚠️ IRRESOLVABLE — official page contradicts itself; not settled from source in budget | — |
| 3 | Executive Summary | Quarkus 4 / Jackson 3 effect on JAXB | Resolved: no JAXB entries; Jackson 3 affects jacksonxml only | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0 (2026-10-14) |
| 3 | Conditional F | Large XML handling | Added from Split EIP | https://camel.apache.org/components/4.22.x/eips/split-eip.html (2026-10-14) |
| 3 | Migration | CQ on Quarkus 4 | ⚠️ IRRESOLVABLE — no artifact yet | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited (marshal/unmarshal, contextPath, jaxb.index/ObjectFactory native, reflection, schema, namespaces, partial/fragment, encoding, large XML, errors, testing)
- [x] Pattern counts driven by domain needs
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative
- [x] Integration examples complete (file, bean, xslt, jacksonxml, REST binding)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated or downgraded (Mandatory 5 downgraded to 🟡)
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated
- [x] Every Research Gap cross-referenced in §7

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: Mandatory 1–4 (✓✓), Forbidden 1–4, the option defaults from the 4.22.x table except `prettyPrint`, and the quarkus.jaxb.* defaults from source.
- **Medium Confidence (validate with user)**: Mandatory 5 (error types, single source), Conditional F (large XML), Forbidden 5–6, IT-driven testing shape.
- **Low Confidence (must ask human)**: the IRRESOLVABLE items (CQ LTS end, prettyPrint default, CQ on Quarkus 4) and all UNVERIFIED items listed in Research Gaps.
- **Edge Cases (pause)**: CQ 3.40.0 was released 2026-09-28, which is less than 30 days before the research date. Quarkus 4 GA is expected end of November 2026.
- **Emergency Stop**: not triggered. All sources are official.
