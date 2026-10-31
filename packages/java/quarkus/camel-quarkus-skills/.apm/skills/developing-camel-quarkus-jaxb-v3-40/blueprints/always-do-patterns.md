# Always-Do Patterns: Camel Quarkus JAXB 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Each pattern rests on one High claim from a versioned official page; caveats that are medium or unverified are marked and listed in the [register](./unverified-and-risks.md).

Contents: [1 BOM](#1-extension-through-the-platform-bom) · [2 contextPath](#2-explicit-contextpath-on-a-named-data-format) · [3 native reflection](#3-register-objectfactory-created-pojos-in-native-mode) · [4 schema access](#4-keep-external-schema-access-closed-unless-imports-require-it)

## 1. Extension through the platform BOM

The extension page lists the coordinates `org.apache.camel.quarkus:camel-quarkus-jaxb`; the sample omits the version (version management is a core-skill topic, not sourced here).

```xml
<!-- Camel Quarkus 3.40.x -->
<dependency>
    <groupId>org.apache.camel.quarkus</groupId>
    <artifactId>camel-quarkus-jaxb</artifactId>
</dependency>
```

Do not add `com.sun.xml.bind:*` yourself: the 3.40.0 POM excludes it from `camel-jaxb` (source: [Maven Central](https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0)). Treating a manual add as harmful is (medium confidence), see [never-do patterns](./never-do-patterns.md#a-adding-comsunxmlbind-or-a-second-jaxb-runtime-medium-confidence).

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html

## 2. Explicit contextPath on a named data format

`contextPath` is the required option of the 4.22.x data format. Define one named bean per model and reference it by name in routes. The shape mirrors the 3.40.x integration test.

```java
// Camel Quarkus 3.40.x, mirrors integration-tests/jaxb JaxbProducers.java
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;
import jakarta.inject.Named;
import org.apache.camel.converter.jaxb.JaxbDataFormat;

@ApplicationScoped            // a producer holder bean, not a RouteBuilder
public class JaxbFormats {
    @Produces @Named("jaxbPerson")
    JaxbDataFormat jaxbPerson() {
        JaxbDataFormat df = new JaxbDataFormat();
        df.setContextPath(Person.class.getPackageName());
        df.setPrettyPrint(false);   // set explicitly: documented default is contradictory
        return df;
    }
}

// Routes: a plain RouteBuilder, referencing the bean by name (nothing injected)
public class PersonRoutes extends RouteBuilder {
    @Override public void configure() {
        from("direct:toXml").marshal("jaxbPerson");
        from("direct:fromXml").unmarshal("jaxbPerson");
        // inline alternative used by the IT:
        // from("direct:unmarshal").unmarshal().jaxb(Person.class.getPackageName());
    }
}
```

Caveats (not part of the Always Do claim):
- A package-based `contextPath` resolves only when the package has an `ObjectFactory` (`@XmlRegistry`) or a `jaxb.index` file. That is the Jakarta XML Binding rule and was **not fetched** (unverified).
- With `contextPathIsClassName=true` the value is a class name instead of a package ([data format page](https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html)).
- `@Named` is what the integration test uses; see the Ask First row "Bean name" in [SKILL.md](../SKILL.md).
- The context is built once in `doStart()` and cached per data format instance, so reuse named beans rather than many inline `.jaxb(...)` definitions (source code, [JaxbDataFormat.java](https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java)). That each inline definition creates its own context is (unverified).

Sources: https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html ; https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbProducers.java

## 3. Register ObjectFactory-created POJOs in native mode

If a custom `ObjectFactory` instantiates POJOs without JAXB annotations, the extension page says you "must register those POJO classes for reflection in order for them to be instantiated in native mode".

```java
// Camel Quarkus 3.40.x: POJO created by an ObjectFactory, no JAXB annotations
@io.quarkus.runtime.annotations.RegisterForReflection
public class PojoPerson { /* fields, getters, setters */ }
```

```properties
# Alternative (the artifact needs a Jandex index, per the native-mode guide)
quarkus.camel.native.reflection.include-patterns = com.acme.pojo.*
```

Classes annotated `@XmlRootElement`, `@XmlType` or `@XmlRegistry` and `jaxb.index` entries are registered by Quarkus at build time (source code, [JaxbProcessor](https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/deployment/src/main/java/io/quarkus/jaxb/deployment/JaxbProcessor.java)). Annotating those again is redundant and harmless: (medium confidence, inferred from source code, not documented behaviour). It is therefore not a Never Do rule. See [native mode](./native-mode-and-contexts.md).

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html

## 4. Keep external schema access closed unless imports require it

The `accessExternalSchemaProtocols` option description ties enabling a protocol to XSDs that import other files. Leave it unset otherwise, and use `schema` with `classpath:` locations.

```java
// Camel Quarkus 3.40.x, as in IT bean "jaxbDefault"
df.setSchema("classpath:person.xsd");
df.setSchemaSeverityLevel(2); // IT value: fail only on fatal errors; default 0 = warning level
```

What the unset default actually does (blocks `ACCESS_EXTERNAL_DTD` and `ACCESS_EXTERNAL_SCHEMA`, secure processing on, DOCTYPE disallowed) is read from the 4.22.x source, not from the page. See [schema validation and XML security](./schema-security.md). Accepted values when you do open it are (unverified).

Sources: https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html ; https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbProducers.java
