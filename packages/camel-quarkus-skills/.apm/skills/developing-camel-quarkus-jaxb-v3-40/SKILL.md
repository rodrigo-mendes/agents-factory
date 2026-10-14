---
name: developing-camel-quarkus-jaxb-v3-40
description: "Guides camel-quarkus-jaxb 3.40.x (Camel 4.22): JAXB marshal/unmarshal, contextPath, native reflection, XSD validation. Use when routes convert Java objects to or from XML via JAXB. Not for Quarkus 4, other versions, or jacksonxml."
---

# Developing with Camel Quarkus JAXB 3.40.x

> Version lock: every claim applies to **Camel Quarkus 3.40.x** (Camel 4.22.x data format docs, Quarkus 3.40.x) only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; treat them as hypotheses. Each tag maps to a register id: [tag to register mapping](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Core topics (BOMs, CDI, route discovery, TLS) belong to the sibling skill `developing-camel-quarkus-core-v3-40`.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Camel Quarkus | 3.40.x; 3.40.0 released 2026-09-28, marked LTS | https://camel.apache.org/releases/ |
| Camel / Quarkus / GraalVM | 4.22.1 / 3.40.1 / 25.0.4.1 | https://camel.apache.org/camel-quarkus/latest/ |
| `camel-quarkus-jaxb` | JVM and native "since 1.0.0"; coordinates `org.apache.camel.quarkus:camel-quarkus-jaxb` | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html |
| Data format options | Camel 4.22.x `jaxb` data format | https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html |
| Java | 17 and 21 | https://camel.apache.org/releases/q-3.40.0/ |
| `quarkus-jaxb` underneath | Reached via `camel-quarkus-support-jaxb` (medium confidence, search summary) | https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-support-jaxb/3.40.0/jar |
| Jakarta XML Binding API version | (unverified), not read from the BOM | page not recorded |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01, GA is "planned for the end of November", Java 21 is the new base ([source](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)). No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence). Pin 3.40.x.
- `camel-quarkus-jaxb` has no Jackson dependency in its 3.40.0 POM (medium confidence, the research's reading of [Maven Central](https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0)); the Jackson 3 move affects `camel-quarkus-jacksonxml`, and the [Quarkus 4.0 migration guide](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0) lists no JAXB entries (medium confidence, absence of evidence).
- Quarkus 3.40 LTS is community-maintained until 2027-09-30 ([source](https://quarkus.io/releases)). The Camel Quarkus-specific end date is (unverified).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Native mode and JAXB contexts](./blueprints/native-mode-and-contexts.md)
- [Schema validation and XML security](./blueprints/schema-security.md)
- [Migration guide to 3.40](./blueprints/migration-guide.md)
- [Integration examples and testing](./blueprints/integration-examples.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Declare the extension as `org.apache.camel.quarkus:camel-quarkus-jaxb`.** The extension page lists these coordinates ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html)). See [patterns](./blueprints/always-do-patterns.md#1-extension-through-the-platform-bom).
- **Set `contextPath` on every `JaxbDataFormat`.** The 4.22.x page documents it as the required option ([data format page](https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html)). See [patterns](./blueprints/always-do-patterns.md#2-explicit-contextpath-on-a-named-data-format).
- **In native mode, register the POJOs that a custom `ObjectFactory` instantiates and that carry no JAXB annotations.** The page says you "must register those POJO classes for reflection", with `@RegisterForReflection` or `quarkus.camel.native.reflection.include-patterns` ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html), [native guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html)). See [patterns](./blueprints/always-do-patterns.md#3-register-objectfactory-created-pojos-in-native-mode).
- **Leave `accessExternalSchemaProtocols` unset unless the XSDs import other files.** The option description ties enabling a protocol to schemas that import other files ([data format page](https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html)). See [patterns](./blueprints/always-do-patterns.md#4-keep-external-schema-access-closed-unless-imports-require-it).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| `contextPath` as package vs class | Package (default) for XJC output with `ObjectFactory`; `contextPathIsClassName=true` for one hand-written root class. That a package needs an `ObjectFactory` or `jaxb.index` is the JAXB spec rule (unverified, not fetched) | "Are the classes XJC-generated or hand-written with a single root?" |
| Camel-built vs Quarkus `JAXBContext` | Camel builds its own context from `contextPath` (default) vs injecting one; the setter name is (unverified). `quarkus.jaxb.validate-jaxb-context=true` fails the build on a bad model | "Should a model error fail the build or the route start?" |
| Wrong-type bodies | Defaults pass non-JAXB bodies through; `mustBeJAXBElement=true` fails fast with `InvalidPayloadException` wrapped in `IOException` (medium confidence, source code) | "Is this a strict typed contract?" |
| Part or fragment output | Static `partClass`/`partNamespace` vs per-message headers vs `fragment=true` | "Is the part type fixed per route or decided per message?" |
| Schema location in native | `classpath:` resources only as a precaution (medium confidence: documented only for XSLT); the include property name is (unverified) | "Does the build run native, and are the XSDs on the classpath?" |
| Opening schema protocols | Explicit XSD list vs `accessExternalSchemaProtocols`; accepted values are (unverified) | "Do the XSDs really import other files, and from where?" |
| Large XML | Split with `xtokenize` + `streaming()` then unmarshal fragments (medium confidence; `xtokenize` in native (unverified)) vs whole-document unmarshal | "What is the maximum document size?" |
| `prettyPrint` | Page table says `true`, prose says `false` (unverified): set it explicitly | "Is human-readable output required?" |
| Error handling | `onException(IOException.class)` for marshal/unmarshal failures (medium confidence, single source) | "Which failures go to a dead-letter route?" |
| Bean name | `@Named` as in the 3.40.x integration test vs `@io.smallrye.common.annotation.Identifier` recommended by the [Quarkus CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference). The [Camel Quarkus CDI page](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html) documents `@Identifier` as an alternative to `@Named` for naming a bean (High). ArC removal of an `@Identifier`-only bean is (unverified): add `@Unremovable` | "Does the project already use `@Identifier` for Camel registry beans?" |
| JAXB vs jacksonxml | JAXB for XSD-driven contracts, validation, namespaces; `camel-quarkus-jacksonxml` for Jackson-annotated POJOs, exposed to the Jackson 3 move. Its options are (unverified) | "Is there an XSD contract, or are POJOs already Jackson-annotated?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Leave non-annotated POJOs that a custom `ObjectFactory` creates unregistered in native builds; the page says they "must" be registered ([source](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html)) | `@RegisterForReflection` on those classes, or `quarkus.camel.native.reflection.include-patterns` ([source](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html)) |
| Annotate a `RouteBuilder` with `@ApplicationScoped` when it injects nothing; it is needed only for `@Inject` and `@ConfigProperty` and adds boot time ([source](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)) | A plain `RouteBuilder`; add the scope only when it injects or reads config ([source](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)) |
| Use `camel-quarkus-junit5` in tests; it was renamed in 3.31 ([source](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html)) | `camel-quarkus-junit`, the only artifact in the 3.40 testing guide ([source](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)) |

Full ❌/✅ code and advisory items that are not Never Do rows: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `contextPath` | Required; package by default, class name when `contextPathIsClassName=true` (default `false`) | https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html |
| `ignoreJAXBElement` / `mustBeJAXBElement` / `objectFactory` | `true` / `false` / `true` | https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html |
| `schema` locations | Comma-separated `classpath:`, `file:` or `http:`; `schemaSeverityLevel` default `0` (0 warning, 1 error, 2 fatal) | https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html |
| `fragment` / `filterNonXmlChars` / `contentTypeHeader` | `false` / `false` / `true` | https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html |
| `prettyPrint` | Contradictory on the page (table `true`, prose `false`); (unverified), set explicitly | https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html |
| Part headers | `CamelJaxbPartClass`, `CamelJaxbPartNamespace` (`{namespaceUri}localPart`) | https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html |
| JAXBContext lifetime | Built once in `doStart()` and cached per data format; marshallers created per call (medium confidence, branch-head source code, not documented behaviour) | https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java |
| `quarkus.jaxb.validate-jaxb-context` / `exclude-classes` | `false` / no default; both `BUILD_AND_RUN_TIME_FIXED` (medium confidence, branch-head source code) | https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/runtime/src/main/java/io/quarkus/jaxb/runtime/JaxbConfig.java |
| Build-time class discovery | `@XmlRootElement`, `@XmlType`, `@XmlRegistry` and `jaxb.index` entries are registered by Quarkus (medium confidence, branch-head source code) | https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/deployment/src/main/java/io/quarkus/jaxb/deployment/JaxbProcessor.java |
| REST DSL XML binding | Uses JAXB when the extension is present (medium confidence, branch-head source code) | https://github.com/apache/camel-quarkus/blob/3.40.x/extensions/jaxb/runtime/src/main/java/org/apache/camel/quarkus/component/jaxb/JaxbRecorder.java |
| XSLT in native | `classpath:` resources only | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html |
| Representative commands | `./mvnw test`, `./mvnw verify -Dnative` | page not recorded |

## External Resources

All fetched 2026-10-14. camel.apache.org pages carry no page date and are the versioned 3.40.x / 4.22.x docs.

- JAXB extension: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html
- JAXB data format (4.22.x): https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html
- Native mode: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html
- CDI: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- Testing: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- 3.40.0 migration guide: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- Releases: https://camel.apache.org/releases/
- Quarkus LTS policy: https://quarkus.io/releases
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
