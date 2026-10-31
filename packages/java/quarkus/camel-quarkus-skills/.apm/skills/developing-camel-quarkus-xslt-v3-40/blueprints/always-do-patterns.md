# Always-Do Patterns: Camel Quarkus XSLT 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The patterns are high confidence for the claims stated in their Sources; section 1 also carries two caveats tagged (unverified) (build-time property split, archive inference), kept as caveats and not as patterns. Header hygiene, Saxon choice and extension functions are Ask First items: see [integration examples](./integration-examples.md) and [extension functions](./extension-functions.md).

## 1. Build-time template sources

Confidence: high for what the extension page states: listed sources are precompiled into Java classes (Xalan-J translets), and scheme-less entries are treated as `classpath:`. Which `quarkus.camel.xslt.*` properties are fixed at build time is not established (unverified): rebuild after changing them. Templates not listed in `sources` still run on JVM. That the `.xsl` files then need not be in the application archive is an inference (unverified).

```xml
<!-- Camel Quarkus 3.40.x: version managed by quarkus-camel-bom 3.40.x -->
<dependency>
  <groupId>org.apache.camel.quarkus</groupId>
  <artifactId>camel-quarkus-xslt</artifactId>
</dependency>
```

```properties
# src/main/resources/application.properties
quarkus.camel.xslt.sources = xslt/order-to-invoice.xsl
# optional; default org.apache.camel.quarkus.component.xslt.generated
# quarkus.camel.xslt.package-name = com.acme.xslt.generated
```

```java
// No @ApplicationScoped: nothing is injected here
public class XsltRoutes extends org.apache.camel.builder.RouteBuilder {
    @Override
    public void configure() {
        from("direct:transform").to("xslt:classpath:xslt/order-to-invoice.xsl");
    }
}
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html ; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html

## 2. Classpath templates in native mode

Confidence: high. Native mode supports `classpath:` only; `file:` and `http:` are JVM-only. `xsl:include` works natively when the including stylesheet is in `sources` and includes are classpath-relative. In the component `classpath` is the default `resourceUri` prefix.

```java
// Camel Quarkus 3.40.x: also listed in quarkus.camel.xslt.sources
.to("xslt:classpath:xslt/order-to-invoice.xsl")
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html ; https://camel.apache.org/components/4.22.x/xslt-component.html

## 3. Secure processing stays on

Confidence: high. Disabling `http://javax.xml.XMLConstants/feature/secure-processing` permits Xalan extension functions and logs a startup warning; the guide says to disable it only where every template the application transforms with is trusted. Since 3.40 the feature map also governs runtime-loaded templates. No configuration is needed: leave `quarkus.camel.xslt.features` unset.

```properties
# nothing to set
# quarkus.camel.xslt.features.* intentionally absent
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html ; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
