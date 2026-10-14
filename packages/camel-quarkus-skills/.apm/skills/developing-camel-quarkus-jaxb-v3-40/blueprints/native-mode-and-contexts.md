# Native Mode and JAXB Contexts: Camel Quarkus JAXB 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

Contents: [Native discovery](#native-discovery) · [Camel context vs Quarkus context](#camel-context-vs-quarkus-context) · [Partial and fragment marshalling](#partial-and-fragment-marshalling) · [JAXBElement handling](#jaxbelement-handling) · [Namespaces and encoding](#namespaces-and-encoding) · [Large XML](#large-xml)

## Native discovery

Documented (High): JVM and native mode are supported "since 1.0.0", and POJOs created by a custom `ObjectFactory` without JAXB annotations must be registered ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html)).

Source-code reading (medium confidence, branch-head source code: the URLs point to the branches `3.40` and `3.40.x`, not to tags; not a documentation page):
- The Quarkus `JaxbProcessor` scans `@XmlRootElement`, `@XmlType`, `@XmlRegistry` classes and every `jaxb.index` file, registers them for reflection, plus superclasses of `jaxb.index` entries, `@XmlSeeAlso` targets and `@XmlJavaTypeAdapter` classes. Every `jaxb.index` is added as a native resource (`**/jaxb.index`). [JaxbProcessor](https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/deployment/src/main/java/io/quarkus/jaxb/deployment/JaxbProcessor.java)
- The Camel Quarkus support processor excludes `org.apache.camel.model.*` from that scan. [support JaxbProcessor](https://github.com/apache/camel-quarkus/blob/3.40.x/extensions-support/jaxb/deployment/src/main/java/org/apache/camel/quarkus/support/jaxb/deployment/JaxbProcessor.java)
- The chain `camel-quarkus-jaxb` to `camel-quarkus-support-jaxb` to `quarkus-jaxb` is (medium confidence) (search summary of the [support artifact](https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-support-jaxb/3.40.0/jar)).

Native checklist:
1. Annotated classes and `jaxb.index` packages: nothing to do.
2. ObjectFactory-created non-annotated POJOs: `@RegisterForReflection` or `quarkus.camel.native.reflection.include-patterns` (needs a Jandex index per the [native guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html)).
3. Schemas: use `classpath:` and make sure the resources are in the image. The property name `quarkus.native.resources.includes` for this is (unverified).
4. Test the native image with an HTTP-only `@QuarkusIntegrationTest` (REST Assured against the REST resources; no `@Inject`). Shape and limits: skill `developing-camel-quarkus-junit-v3-40` (see also [integration examples](./integration-examples.md#testing)).

## Camel context vs Quarkus context

Quarkus produces a `@DefaultBean @Singleton JAXBContext` plus `@RequestScoped` `Marshaller` and `Unmarshaller`, built from the build-time classes-to-be-bound set ([JaxbContextProducer](https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/runtime/src/main/java/io/quarkus/jaxb/runtime/JaxbContextProducer.java), source code). Camel's `JaxbDataFormat` builds its own context from `contextPath` unless one is injected ([JaxbDataFormat.java](https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java)). The setter that injects a context is (unverified).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Camel-built from `contextPath` (default) | Isolation per model package | One context built at start per format | Default |
| Quarkus bean + `quarkus.jaxb.validate-jaxb-context=true` | Build-time failure on a bad model | Default context binds all scanned classes; narrow with `quarkus.jaxb.exclude-classes` (supports `org.acme.*`) | One app-wide model |

`quarkus.jaxb.validate-jaxb-context` defaults to `false`; `quarkus.jaxb.exclude-classes` has no default; both are `BUILD_AND_RUN_TIME_FIXED` ([JaxbConfig](https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/runtime/src/main/java/io/quarkus/jaxb/runtime/JaxbConfig.java)). A failed validation throws `DeploymentException("Failed to create or validate the default JAXBContext")` (JaxbProcessor, source code).

## Partial and fragment marshalling

Options (documented): static `partClass` / `partNamespace`, per-message headers `CamelJaxbPartClass` / `CamelJaxbPartNamespace` (value format `{namespaceUri}localPart`), and `fragment=true` (default `false`) to omit the XML declaration ([data format page](https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html)).

```java
// Camel Quarkus 3.40.x, from the integration test JaxbRoute
from("direct:partMarshal")
    .setHeader(JaxbConstants.JAXB_PART_CLASS, constant(PartClassPerson.class.getName()))
    .setHeader(JaxbConstants.JAXB_PART_NAMESPACE,
        constant(String.format("{%s}person", PartClassPerson.NAMESPACE)))
    .marshal().jaxb(PartClassPerson.class.getPackageName());
// bean form
df.setPartClass(PartClassPerson.class);
df.setPartNamespace(new QName(PartClassPerson.NAMESPACE, "person"));
```

Source: https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbRoute.java

## JAXBElement handling

Defaults (page): `ignoreJAXBElement=true` (unwraps the value), `mustBeJAXBElement=false` (non-JAXB bodies are copied through), `objectFactory=true` (ObjectFactory methods wrap non-root POJOs).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Defaults | Simple POJO body | Pass-through hides wrong body types | Most routes |
| `mustBeJAXBElement=true` | Fails fast (`InvalidPayloadException` wrapped in `IOException`, medium confidence) | Cannot pass raw XML | Strict contracts |
| `ignoreJAXBElement=false` | Keeps QName and namespace metadata | Caller must unwrap | Schema-aware processing |

Marshal and unmarshal failures, including schema-validation failures and a missing part class, surface as `IOException` (medium confidence, one source: the 4.22.x source). Handle with `onException(java.io.IOException.class).handled(true).to("direct:xmlDeadLetter")`.

## Namespaces and encoding

- `namespacePrefix` is a `Map<String,String>` from namespace URI to prefix and replaces generated `ns2`, `ns3`. The page text names `namespacePrefixRef` in a Spring XML example while its options table says `namespacePrefix`; the integration test uses `setNamespacePrefix(Map.of("https://example.com/a", "test"))`.
- `encoding` has no default; the exchange property `Exchange.CHARSET_NAME` overrides it. The test uses `setEncoding("ISO-8859-1")` with `setFilterNonXmlChars(true)`. `filterNonXmlChars` (default `false`) only replaces invalid characters with a space; it is not a sanitiser, and `Exchange.FILTER_NON_XML_CHARS` takes precedence.

Sources: https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html ; https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbProducers.java

## Large XML

(medium confidence): the Split EIP page shows `streaming` defaulting to `false` ("all sub messages kept temporary in-memory"), `xtokenize` using a StAX parser and `tokenizeXML` splitting by child tag; the XPath engine loads the whole XML into memory ([Split EIP](https://camel.apache.org/components/4.22.x/eips/split-eip.html)). JAXB unmarshal builds the full object graph (source code). The JAXB-plus-split combination is not an official example, and `xtokenize` in native is (unverified).

```java
// Camel 4.22.x / CQ 3.40.x, representative
from("file:in?noop=true")
    .split().xtokenize("//order", 'i').streaming()
        .unmarshal("jaxbOrder")
        .to("direct:processOrder");
```
