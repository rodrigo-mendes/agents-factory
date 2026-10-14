# Integration Examples and Testing: Camel Quarkus File 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

Contents: [XSLT, JAXB, Bean](#file-with-xslt-jaxb-and-bean) · [Testing](#testing) · [Verification commands](#verification-commands-representative)

## File with XSLT, JAXB and Bean

Extensions: `camel-quarkus-xslt`, `camel-quarkus-jaxb`, `camel-quarkus-bean`.

```java
// Camel Quarkus 3.40.x
// application.properties (needed for native): quarkus.camel.xslt.sources = xslt/order.xsl
from("file:/data/in?antInclude=*.xml&readLock=changed")
    .to("xslt:xslt/order.xsl")                 // classpath: URI, required in native
    .unmarshal().jaxb("com.example.orders")
    .bean("orderService", "handle")            // CDI bean named "orderService" (@Named, see core skill)
    .marshal().jaxb("com.example.orders")
    .to("file:/data/out?tempPrefix=.tmp-&fileExist=Fail");
```

Facts (high confidence):
- XSLT, https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html: native supports only `classpath:` URIs; stylesheets in `quarkus.camel.xslt.sources` are compiled to translets at build time; `quarkus.camel.xslt.package-name` defaults to `org.apache.camel.quarkus.component.xslt.generated`; `<xsl:messaging>` and `XsltSaxonAggregationStrategy` are JVM-only. Which properties are build-time vs runtime is (unverified).
- XSLT 3.40.0 hardening: external entities and DTDs are no longer resolved; `document()` is denied without a URIResolver ([migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)).
- JAXB, https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html: in native, POJOs from a custom `ObjectFactory` without JAXB annotations need `@RegisterForReflection` or `quarkus.camel.native.reflection.include-patterns`.
- Bean, https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html: JVM and native since 0.1.0, no configuration.

## Testing

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html (high confidence unless tagged). The base-class package and the `doBeforeEach`/`adviceRoute` signatures are stated only in the skill `developing-camel-quarkus-junit-v3-40`; use that skill instead of copying them from here.

- `camel-quarkus-junit` (test scope) provides `CamelQuarkusTestSupport`, JVM-only.
- CamelContext lifecycle and route advice (AdviceWith): see the skill `developing-camel-quarkus-junit-v3-40`; do not copy them from here.
- `@QuarkusIntegrationTest` runs out of process; test it through the network or by observing the file system.
- NotifyBuilder on Camel Quarkus: (unverified) (not covered on the page).

```java
// Camel Quarkus 3.40.x: JVM test, replace the file input with direct: and mock the output.
// Base class and advice hook: see the skill developing-camel-quarkus-junit-v3-40 (imports resolve in the IDE).
@io.quarkus.test.junit.QuarkusTest
class FileIngestRouteTest extends CamelQuarkusTestSupport {
    // Placeholder: the advice hook (not shown) replaces the route's file: input with direct:in and its
    // output with mock:out, so the send below reaches the route; pattern and signatures in developing-camel-quarkus-junit-v3-40.

    @org.junit.jupiter.api.Test
    void routesFile() throws Exception {
        getMockEndpoint("mock:out").expectedMessageCount(1);
        template.sendBodyAndHeader("direct:in", "<a/>", org.apache.camel.Exchange.FILE_NAME, "a.xml");
        getMockEndpoint("mock:out").assertIsSatisfied();
    }
}
```

The official file integration test uses fixed `target/test-files/...` paths and `consumerTemplate.receiveBodyNoWait(...)` ([FileResource.java](https://raw.githubusercontent.com/apache/camel-quarkus/main/integration-tests/file/src/main/java/org/apache/camel/quarkus/component/file/it/FileResource.java), `main` branch, not the 3.40.x tag) (medium confidence).

## Verification commands (representative)

Adapt to your environment; the plugin coordinate form for `create` is (unverified).

```bash
mvn io.quarkus.platform:quarkus-maven-plugin:3.40.1:create -DprojectGroupId=org.acme -DprojectArtifactId=file-app \
  -Dextensions="org.apache.camel.quarkus:camel-quarkus-file"
# Expected: BUILD SUCCESS; pom lists camel-quarkus-file without a version
mvn test                       # Expected: Tests run: N, Failures: 0
mvn verify -Dnative            # Expected: *IT classes pass against the native binary
mkdir -p target/in && echo '<a/>' > target/in/a.xml && sleep 3 && ls target/in/.camel
# Expected: a.xml moved to .camel/ (default post-processing, when no move/delete/noop is set)
```
