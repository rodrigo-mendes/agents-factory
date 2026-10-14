# Schema Validation and XML Security: Camel Quarkus JAXB 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

Contents: [Schema option](#schema-option) · [Default security behaviour](#default-security-behaviour) · [Opening protocols](#opening-protocols) · [Unmarshal-side parsing](#unmarshal-side-parsing) · [Related XSLT hardening](#related-xslt-hardening)

## Schema option

Documented (High, [data format page](https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html)): `schema` takes comma-separated `classpath:`, `file:` or `http:` locations. `schemaSeverityLevel` defaults to `0` (0 warning, 1 error, 2 fatal). The IT uses `setSchema("classpath:person.xsd")` with `setSchemaSeverityLevel(2)`.

The compiled schema is cached at startup (source code, [JaxbDataFormat.java](https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java)).

In native mode prefer `classpath:` and include the XSD in the image. Documentation covers `classpath:` only for build-time compiled XSLT ([xslt page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html)); the same constraint for the JAXB `schema` option is (medium confidence) (not documented), and the property name `quarkus.native.resources.includes` is (unverified).

## Default security behaviour

Source-code reading (medium confidence, branch-head source code: the URL points to the branch `camel-4.22.x`, not to a tag; not documentation): when `accessExternalSchemaProtocols` is unset (default `null`), the `SchemaFactory` sets `ACCESS_EXTERNAL_DTD` and `ACCESS_EXTERNAL_SCHEMA` to `""`, enables `FEATURE_SECURE_PROCESSING` and disallows DOCTYPE. Source: https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java

Documented rule (page): enable a protocol only if the XSDs import other files.

## Opening protocols

Decision order:
1. List the imported XSDs explicitly in `schema` (`classpath:order.xsd,classpath:common.xsd`). This is the research's recommendation, not a documented procedure.
2. Only if imports must resolve through another protocol, set `accessExternalSchemaProtocols`. Whether `all`, `file` and `http` are the accepted values is (unverified) (they follow `XMLConstants.ACCESS_EXTERNAL_SCHEMA` semantics by the research's reading).

```java
df.setSchema("classpath:order.xsd,classpath:common.xsd"); // preferred
// df.setAccessExternalSchemaProtocols("file");           // accepted values unverified
```

## Unmarshal-side parsing

The `XMLInputFactory` external-entity settings used when unmarshalling come from Camel's StAX type converter, not from `JaxbDataFormat`, and were **not verified**. For untrusted XML, do not assume entity resolution is disabled; ask the user before accepting input from outside the trust boundary.

## Related XSLT hardening

The 3.40.0 migration guide hardened the XSLT path: inputs are parsed with an `XMLReader` that "does not resolve external entities or load external DTDs", `document()` is denied unless a URIResolver resolves it, and `quarkus.camel.xslt.features` applies to every template ([migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)). It has no JAXB heading. That this affects code that marshals JAXB to a `Source` and transforms it yourself is the research's reading (medium confidence).
