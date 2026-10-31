# Never-Do Patterns: Camel Quarkus JAXB 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Part 1 holds the three rows of the SKILL.md Never Do table (High, versioned official page). Part 2 holds **advisory** items that are not Never Do rows because their evidence is source code or medium confidence; they must not be quoted as documented prohibitions.

Contents: [1 native registration](#1-unregistered-objectfactory-pojos-in-native-builds) · [2 ApplicationScoped](#2-applicationscoped-on-a-routebuilder-that-injects-nothing) · [3 junit5](#3-camel-quarkus-junit5-in-tests) · [A com.sun.xml.bind](#a-adding-comsunxmlbind-or-a-second-jaxb-runtime-medium-confidence) · [B pass-through](#b-relying-on-pass-through-for-typed-contracts-source-code) · [C shared marshaller](#c-sharing-one-marshaller-across-threads-source-code) · [D file/http schema](#d-file-or-http-schema-in-native-builds-medium-confidence) · [E external protocols](#e-opening-external-schema-protocols-to-make-imports-work) · [F redundant reflection](#f-registerforreflection-on-already-annotated-classes-medium-confidence)

## Part 1: Never Do rows

### 1. Unregistered ObjectFactory POJOs in native builds

The page says POJOs without JAXB annotations that a custom `ObjectFactory` instantiates "must" be registered for reflection in native mode.

```java
// ❌ WRONG: created by ObjectFactory, no JAXB annotations, not registered (the page says registration is needed for instantiation in native mode)
public class PojoPerson { }
// ✅ CORRECT
@io.quarkus.runtime.annotations.RegisterForReflection
public class PojoPerson { }
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html

### 2. @ApplicationScoped on a RouteBuilder that injects nothing

The CDI page says the scope is needed only for `@Inject` and `@ConfigProperty` and adds a boot-time penalty. It is not mandatory on a `RouteBuilder` unless the route injects.

```java
// ❌ WRONG: scope with nothing injected
@ApplicationScoped
public class PersonRoutes extends RouteBuilder { /* from(...).marshal("jaxbPerson") */ }
// ✅ CORRECT
public class PersonRoutes extends RouteBuilder { /* same routes */ }
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html

### 3. camel-quarkus-junit5 in tests

`camel-quarkus-junit5` was renamed `camel-quarkus-junit` (since 3.31, High); the only test artifact in the 3.40 testing guide is `camel-quarkus-junit`. The stub details and the Quarkus-side rename are in skills `developing-camel-quarkus-junit-v3-40` and `developing-quarkus-junit-v3-40`. The release that removes the stub is (unverified).

```xml
<!-- ❌ WRONG -->
<artifactId>camel-quarkus-junit5</artifactId>
<!-- ✅ CORRECT -->
<artifactId>camel-quarkus-junit</artifactId>
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html

## Part 2: Advisory items (not Never Do rows)

### A. Adding com.sun.xml.bind or a second JAXB runtime (medium confidence)

The 3.40.0 POM excludes `com.sun.xml.bind:*` from `camel-jaxb`, and Quarkus supplies the Glassfish runtime through service providers (source code). Single source, so advisory: rely on `camel-quarkus-jaxb`.

```xml
<!-- avoid -->  <dependency><groupId>com.sun.xml.bind</groupId><artifactId>jaxb-impl</artifactId></dependency>
<!-- prefer -->  camel-quarkus-jaxb alone
```

Sources: https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0 ; https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/deployment/src/main/java/io/quarkus/jaxb/deployment/JaxbProcessor.java

### B. Relying on pass-through for typed contracts (source code)

With `mustBeJAXBElement=false` (the documented default) a non-JAXB body such as an XML `String` is copied through. In the 4.22.x source an unmatched body is converted to an `InputStream` and copied unchanged, so a wrong type can leak through. The "typed contract" framing is the research's reading. For strict contracts set `mustBeJAXBElement=true` (failure surfaces as `InvalidPayloadException` wrapped in `IOException`, (medium confidence)).

```java
// risk: a String body passes through marshal()
from("direct:out").marshal().jaxb("com.acme.model");
// stricter
JaxbDataFormat df = new JaxbDataFormat("com.acme.model");
df.setMustBeJAXBElement(true);
```

Sources: https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html ; https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java

### C. Sharing one Marshaller across threads (source code)

Camel's own source creates a new marshaller per call because it is not thread-safe; the Quarkus-produced `Marshaller` and `Unmarshaller` are `@RequestScoped`. The `JAXBContext` itself is shared. Evidence is source code, not a documentation page.

```java
// avoid
private static final Marshaller M = ctx.createMarshaller();
// prefer: one marshaller per invocation, shared JAXBContext
Marshaller m = jaxbContext.createMarshaller();
```

Sources: https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java ; https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/runtime/src/main/java/io/quarkus/jaxb/runtime/JaxbContextProducer.java

### D. file: or http: schema in native builds (medium confidence)

Camel Quarkus native supports `classpath:` resources only for build-time compiled XSLT ([xslt page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html)). Whether the JAXB `schema` option has the same constraint is not documented. Treat `file:` and `http:` as not portable and prefer `classpath:xsd/order.xsd`, with the resource included in the image (the `quarkus.native.resources.includes` name for this is (unverified)).

### E. Opening external schema protocols to make imports work

```java
// avoid unless the XSDs really import other files
df.setSchema("classpath:order.xsd");
df.setAccessExternalSchemaProtocols("all");
// prefer: list the imported XSDs explicitly
df.setSchema("classpath:order.xsd,classpath:common.xsd");
```

The security consequence (remote fetch, XXE/SSRF surface) is the research's reasoning from the 4.22.x source, and the documented rule is only "enable a protocol if the XSDs import other files"; so this is an Always Do caveat, not a Never Do row. Accepted values are (unverified). Sources: https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html ; https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java

### F. @RegisterForReflection on already-annotated classes (medium confidence)

Quarkus registers `@XmlRootElement`, `@XmlType`, `@XmlRegistry` classes and `jaxb.index` entries itself, so adding `@RegisterForReflection` to them is redundant. This is (medium confidence, inferred from source code, not documented behaviour); the impact is only noise (harmless). It is not a prohibition. Use the annotation where the page requires it (Always Do 3).

Source: https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/deployment/src/main/java/io/quarkus/jaxb/deployment/JaxbProcessor.java
