# Integration Examples and Testing: Camel Quarkus XSLT 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Component options: https://camel.apache.org/components/4.22.x/xslt-component.html. Samples omit `@ApplicationScoped` because nothing is injected (needed only for `@Inject`/`@ConfigProperty`: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html).

## Full lifecycle

```properties
quarkus.camel.xslt.sources = xslt/order-to-invoice.xsl
```

```java
public class XsltRoutes extends org.apache.camel.builder.RouteBuilder {
    @Override
    public void configure() {
        from("direct:transform")
            .removeHeaders("*", "currency")   // headers -> <xsl:param> (medium confidence hygiene)
            .to("xslt:classpath:xslt/order-to-invoice.xsl?transformerCacheSize=4&output=bytes");
    }
}
```

## With camel-quarkus-file

`output=file` streams to a `File` named by the `CamelXsltFileName` header. The parent directory must exist, otherwise a runtime exception occurs. Native support for file output is unverified.

```java
from("file:inbox?include=.*\\.xml")
    .setHeader("CamelXsltFileName", simple("outbox/${file:onlyname.noext}.out.xml"))
    .to("xslt:classpath:xslt/t.xsl?output=file&deleteOutputFile=false");
```

Read-lock and post-processing options for the consumer belong to the sibling file skill and are not covered by this research.

## With camel-quarkus-jaxb and camel-quarkus-bean

- jaxb: marshal a POJO with `.marshal().jaxb()` then call `.to("xslt:...")`. JAXB-specific 3.40 details are (unverified).
- bean: `resourceUri` supports `bean:myBean.myMethod` and `ref:` (registry lookup) per the component page. Native support for these is (unverified).

## Error handling

The default `ErrorListener` stores errors as exchange properties. For Saxon these are `Exchange.XSLT_ERROR`, `XSLT_FATAL_ERROR` and `XSLT_WARNING` (medium confidence; https://camel.apache.org/components/4.22.x/xslt-saxon-component.html). `failOnNullBody=true` by default; `xsl:message` output goes to `xsltMessageLogger` (https://camel.apache.org/components/4.22.x/xslt-component.html). Which exception type wraps a failed transformation is (unverified); check it before writing an `onException` clause.

## Testing (pattern from the core skill; no XSLT-specific guidance on the extension page)

No XSLT-specific testing guidance exists on the extension page (medium confidence).

```java
@QuarkusTest
class XsltRouteTest {
    @Inject ProducerTemplate template;

    @Test
    void transforms() {
        String out = template.requestBodyAndHeader("direct:transform",
            "<order><total>10</total></order>", "currency", "EUR", String.class);
        assertTrue(out.contains("EUR"));
    }
}
```

Run `@QuarkusIntegrationTest` in native too: classpath and translet problems show only there. Examples repository: https://github.com/apache/camel-quarkus-examples; an XSLT-specific example was not located (unverified).
