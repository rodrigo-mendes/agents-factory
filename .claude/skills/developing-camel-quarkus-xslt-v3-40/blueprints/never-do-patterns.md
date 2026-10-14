# Never-Do Patterns: Camel Quarkus XSLT 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

Contents: [1 file/http in native](#1-file-and-http-templates-in-native-mode) · [2 secure processing off](#2-disabling-secure-processing-for-untrusted-templates) · [3 factory attributes](#3-external-access-attributes-on-the-factory) · [4 DTD expansion](#4-relying-on-dtd-or-external-entity-expansion) · [5 raw headers](#5-raw-external-headers-feeding-document-medium-confidence-inferred-risk) · [6 unescaped colon](#6-unescaped-colon-in-the-features-key-unverified)

Items 1-4 are high confidence and appear in SKILL.md. Item 5 is medium confidence and item 6 is unverified; both are advisory only.

## 1. File and http templates in native mode

Severity: high. Only `classpath:` works natively; the endpoint fails in the native executable.

```java
// ❌ WRONG: JVM-only
to("xslt:file:/opt/xslt/transform.xsl")
// ✅ CORRECT: also listed in quarkus.camel.xslt.sources
to("xslt:classpath:xslt/transform.xsl")
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html

## 2. Disabling secure processing for untrusted templates

Severity: high. Since 3.40 `quarkus.camel.xslt.features` applies to every template, including runtime-loaded ones. Disabling secure processing enables Xalan extension functions (arbitrary Java calls from a stylesheet).

```properties
# ❌ WRONG when any template may be untrusted
quarkus.camel.xslt.features."http\://javax.xml.XMLConstants/feature/secure-processing"=false
# ✅ CORRECT: leave quarkus.camel.xslt.features unset
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html ; https://camel.apache.org/components/4.22.x/xslt-component.html (`allowTemplateFromHeader` default `false`)

## 3. External-access attributes on the factory

Severity: moderate. `setAttribute` throws for `ACCESS_EXTERNAL_DTD` and `ACCESS_EXTERNAL_STYLESHEET` on the Camel Quarkus Xalan factory, and the extension enforces the restrictions itself. The reason, that Xalan-J 2.7.x predates JAXP 1.5, is not stated on the page (unverified).

```java
// ❌ WRONG: throws on Camel Quarkus 3.40
TransformerFactory tf = TransformerFactory.newInstance();
tf.setAttribute(XMLConstants.ACCESS_EXTERNAL_STYLESHEET, "");
// ✅ CORRECT: defaults already block; supply a resolver for document()
TransformerFactory tf = TransformerFactory.newInstance();
tf.setURIResolver(allowListResolver);
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html ; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html

## 4. Relying on DTD or external-entity expansion

Severity: moderate. Since 3.40, external entities and external DTDs in input documents are not resolved. Entity references may stay unexpanded or fail.

```text
❌ WRONG: input with <!DOCTYPE x SYSTEM "http://host/x.dtd"> expecting expansion
✅ CORRECT: pass a SAXSource with a deliberately configured XMLReader
   (passed through unchanged) only for trusted input
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html

## 5. Raw external headers feeding document() (medium confidence, inferred risk)

All headers and variables become XSLT parameters by default (4.22.x component page). A parameter fed to `document()` lets the sender steer resource reads; that risk is spelled out only on the 4.23 docs page (not the target version), so it is advisory here. Do not claim 4.23 runtime refusals apply to 3.40.

```java
// ❌ WRONG: every header becomes a parameter
from("platform-http:/x").to("xslt:classpath:lookup.xsl");
// ✅ CORRECT
from("platform-http:/x").removeHeaders("*", "customerId").to("xslt:classpath:lookup.xsl");
```

```xml
<xsl:param name="customerId"/>
```

Sources: https://camel.apache.org/components/4.22.x/xslt-component.html ; https://camel.apache.org/components/next/xslt-component.html (contrast only)

## 6. Unescaped colon in the features key (unverified)

The 3.40 docs show the escaped form `"http\://..."`. Whether the unescaped form (used by older research) parses correctly is (unverified).

```properties
# ❌ WRONG (may not apply)
quarkus.camel.xslt.features."http://javax.xml.XMLConstants/feature/secure-processing"=true
# ✅ CORRECT form, if a feature must be set at all (keeps secure processing on, see item 2)
quarkus.camel.xslt.features."http\://javax.xml.XMLConstants/feature/secure-processing"=true
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html (the page example uses the escaped key to disable secure processing; do not copy that value, see item 2)
