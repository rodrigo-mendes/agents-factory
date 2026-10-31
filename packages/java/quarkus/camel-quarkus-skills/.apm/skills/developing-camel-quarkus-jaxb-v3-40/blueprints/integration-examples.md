# Integration Examples and Testing: Camel Quarkus JAXB 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Code is representative unless marked as taken from the 3.40.x integration test.

Contents: [Model and routes](#model-and-routes) · [File plus bean plus XSLT](#file-plus-bean-plus-xslt) · [JAXB vs jacksonxml](#jaxb-vs-jacksonxml) · [REST DSL binding](#rest-dsl-binding) · [Testing](#testing) · [Verification commands](#verification-commands)

## Model and routes

```java
// Camel Quarkus 3.40.x
@XmlRootElement(name = "person", namespace = "https://example.com/a")
@XmlAccessorType(XmlAccessType.FIELD)
public class Person { String firstName; String lastName; }

// src/main/resources/com/acme/model/jaxb.index (when there is no ObjectFactory), one class name per line:
//   Person

public class PersonRoutes extends RouteBuilder {   // plain RouteBuilder, nothing injected
    @Override public void configure() {
        onException(java.io.IOException.class).handled(true).to("direct:xmlError");
        from("direct:toXml").marshal("jaxbPerson");    // bean from JaxbFormats
        from("direct:fromXml").unmarshal("jaxbPerson");
    }
}
```

The `JaxbFormats` producer is in [always-do patterns](./always-do-patterns.md#2-explicit-contextpath-on-a-named-data-format). The `jaxb.index` resolution rule is (unverified) (JAXB spec, not fetched).

## File plus bean plus XSLT

```java
// Camel Quarkus 3.40.x, representative
from("file:inbox?include=.*\\.xml")
    .unmarshal("jaxbPerson")                    // XML -> Person
    .bean(PersonService.class, "enrich")        // camel-quarkus-bean
    .marshal("jaxbPerson")                      // Person -> XML
    .to("xslt:classpath:xsl/person-to-v2.xsl")  // must be listed in quarkus.camel.xslt.sources for native
    .to("file:outbox");
```

```properties
# camel-quarkus-xslt 3.40.x (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html)
quarkus.camel.xslt.sources = xsl/person-to-v2.xsl
# quarkus.camel.xslt.package-name default: org.apache.camel.quarkus.component.xslt.generated
```

Read-lock, post-processing and charset choices for the `file:` consumer belong to the sibling file skill.

## JAXB vs jacksonxml

`camel-quarkus-jacksonxml` (JVM and native since 1.0.0) uses Jackson's XmlMapper ([page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jacksonxml.html)). Default recommendation (research's judgement): JAXB for XSD-driven contracts, schema validation and namespaces; jacksonxml when POJOs are already Jackson-annotated. Jackson XML is the extension exposed to the Quarkus 4 / Jackson 3 move. Its options were not fetched (the 4.22.x jacksonXml page returned 404): (unverified).

## REST DSL binding

Camel Quarkus registers a `JaxbRestBindingJaxbDataFormatFactory` context plugin at STATIC_INIT, so REST DSL XML binding uses JAXB when the extension is present (source code: [JaxbRecorder](https://github.com/apache/camel-quarkus/blob/3.40.x/extensions/jaxb/runtime/src/main/java/org/apache/camel/quarkus/component/jaxb/JaxbRecorder.java), [JaxbProcessor](https://github.com/apache/camel-quarkus/blob/3.40.x/extensions/jaxb/deployment/src/main/java/org/apache/camel/quarkus/component/jaxb/deployment/JaxbProcessor.java)).

## Testing

(medium confidence): the shape follows the 3.40.x integration test (`JaxbResource` and `JaxbRoute`, driven through REST resources and `direct:` endpoints, [tree](https://github.com/apache/camel-quarkus/tree/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it)). Use the `camel-quarkus-junit` artifact, the only one in the [testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html).

```java
// Camel Quarkus 3.40.x, representative
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

The sample above injects `ProducerTemplate`, so it runs in JVM mode only. For the native image, write a separate HTTP-only `@QuarkusIntegrationTest` (REST Assured against REST resources that call the routes); the shape is in skill `developing-camel-quarkus-junit-v3-40`. The IT defines named data formats (the research text says 10, but its list names 12 items: default, schema, fragment, namespacePrefix, encoding with `filterNonXmlChars`, `mustBeJAXBElement=false`, `partClass`, ignoreElement, `jaxbProviderProperties`, custom XmlStreamWriter, `objectFactory=false`, `noNamespaceSchemaLocation`) and is the best reference: https://github.com/apache/camel-quarkus/tree/3.40.x/integration-tests/jaxb

## Verification commands

Representative, output not verified (page not recorded):

```bash
./mvnw quarkus:add-extension -Dextensions=org.apache.camel.quarkus:camel-quarkus-jaxb
# Expected: dependency added without <version>
./mvnw test
# Expected: JVM tests green
./mvnw verify -Dnative
# Expected: native IT passes; missing reflection shows up as unmarshal failures
# Optional build-time model check: quarkus.jaxb.validate-jaxb-context=true -> DeploymentException on a bad model
```
