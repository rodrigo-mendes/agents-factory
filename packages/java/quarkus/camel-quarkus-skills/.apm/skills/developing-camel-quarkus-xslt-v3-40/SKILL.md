---
name: developing-camel-quarkus-xslt-v3-40
description: "Guides Camel Quarkus 3.40.x XSLT (Camel 4.22): camel-quarkus-xslt and xslt-saxon, build-time templates, native mode, 3.40 hardening. Use when routes transform XML with xslt:. Not for Quarkus 4, other versions or XQuery/XPath."
---

# Developing with Camel Quarkus XSLT 3.40.x

> Version lock: every claim applies to **Camel Quarkus 3.40.x** (Camel 4.22.x component docs) only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; treat them as hypotheses.
> Core topics (BOMs, CDI, route discovery, testing basics) belong to the sibling skill `developing-camel-quarkus-core-v3-40`.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Camel Quarkus | 3.40.0 released 2026-09-28, marked LTS (no LTS-until date given) | https://camel.apache.org/releases/ |
| Platform versions | Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1 | https://camel.apache.org/camel-quarkus/latest/ |
| Java | 17 and 21 | https://camel.apache.org/releases/q-3.40.0/ |
| Camel component docs | 4.22.x | https://camel.apache.org/components/4.22.x/xslt-component.html |
| `camel-quarkus-xslt` | JVM and native since 0.4.0; Xalan-J patch version (unverified) | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html |
| `camel-quarkus-xslt-saxon` | JVM since 1.1.0, native since 3.2.0 (medium confidence, `latest` alias) | https://camel.apache.org/camel-quarkus/latest/reference/extensions/xslt-saxon.html |
| 3.40 XSLT hardening | Documented for the `xslt` extension; Saxon coverage (unverified) | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November" and Java 21 is the new base ([source](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)). No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence). Jackson 3 on Quarkus 4 was not verified for this skill (unverified).
- Quarkus 3.40 (released 2026-09-30, LTS) is community-maintained until 2027-09-30 ([source](https://quarkus.io/releases)). The Camel Quarkus-specific end date is (unverified): not resolvable from documentation.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Security hardening in 3.40](./blueprints/security-hardening-3-40.md)
- [Native mode](./blueprints/native-mode.md)
- [Extension functions](./blueprints/extension-functions.md)
- [Migration guide 3.15 to 3.40](./blueprints/migration-guide.md)
- [Integration examples and testing](./blueprints/integration-examples.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **List templates in `quarkus.camel.xslt.sources`.** The sources listed there are precompiled ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html)). See [patterns](./blueprints/always-do-patterns.md#1-build-time-template-sources).
- **Write scheme-less `sources` entries only for classpath templates.** A scheme-less entry is treated as `classpath:` ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html)). See [patterns](./blueprints/always-do-patterns.md#1-build-time-template-sources).
- **Use `classpath:` template URIs for anything that must run natively.** Only `classpath:` works in native mode; `file:` and `http:` are JVM-only ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html)). See [patterns](./blueprints/always-do-patterns.md#2-classpath-templates-in-native-mode).
- **Leave `quarkus.camel.xslt.features` unset so secure processing stays on.** Disabling secure processing permits Xalan extension functions ([3.40.0 migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)). See [patterns](./blueprints/always-do-patterns.md#3-secure-processing-stays-on).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Disabling secure processing | Logs a startup warning; the guide says to disable only if every template is trusted ([3.40.0 migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)) | "Is every template the application transforms with trusted?" |
| Build-time property split (unverified) | Which `quarkus.camel.xslt.*` properties are fixed at build time is not established; templates not listed in `sources` still run on JVM | "Which properties will change between deployments? Rebuild after changing them." |
| Header hygiene (medium confidence) | All headers and variables become XSLT parameters ([component](https://camel.apache.org/components/4.22.x/xslt-component.html)); `removeHeaders("*", "param")` before `xslt:` limits that. The explicit untrusted-sender warning is only on the 4.23 docs page | "Can an external caller set headers on this route, and does any stylesheet use a parameter in `document()`?" |
| Xalan (`xslt`) vs Saxon (`xslt-saxon`) (medium confidence) | `xslt`: build-time translets, hardening documented. `xslt-saxon`: XSLT 3.0 features such as `useJsonBody`, hardening coverage (unverified), `XsltSaxonAggregationStrategy` JVM-only | "Do the stylesheets need XSLT 2.0/3.0 or JSON input? If not, use `camel-quarkus-xslt`." |
| Xalan extension functions | Disabling secure processing permits them ([3.40.0 migration guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)); the other setup conditions, a separate jar and reflection registration, are (medium confidence); see [extension functions](./blueprints/extension-functions.md) | "Are all stylesheets trusted, and can the functions live in a separate jar?" |
| Dynamic templates (`allowTemplateFromHeader`, `CamelXsltResourceUri`, `CamelXsltStylesheet`) | Default `false` ([component](https://camel.apache.org/components/4.22.x/xslt-component.html)); `true` loads templates at runtime (not precompiled, native behaviour: medium confidence) | "Can any external party set the template header?" |
| `document()` access (medium confidence) | Routes resolve through the component's resolver; direct `TransformerFactory` code is denied unless it sets a `URIResolver` | "Which hosts or schemes must `document()` reach?" |
| Output format | `string` (default), `bytes`, `DOM`, `file` (needs `CamelXsltFileName`, parent directories must exist; native file output (unverified)) | "What payload size and downstream type?" |
| Caching | `contentCache=true`, `transformerCacheSize=0` defaults; raise the cache for hot endpoints | "What throughput is expected?" |
| `bean:` / `ref:` template URIs | Supported by the component; native support (unverified) | "Is native mode required for this route?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Use `xslt:file:` or `xslt:http:` templates in a native build ([source](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html)) | `xslt:classpath:...` and list it in `quarkus.camel.xslt.sources` |
| Disable secure processing while any template is untrusted or runtime-loaded; since 3.40 the features apply to every template ([source](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)) | Leave `quarkus.camel.xslt.features` unset |
| Call `setAttribute` with `ACCESS_EXTERNAL_DTD` or `ACCESS_EXTERNAL_STYLESHEET` on the Camel Quarkus Xalan factory; it throws ([source](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html)) | Rely on the built-in restrictions; call `setURIResolver(...)` for `document()` |
| Expect DTD or external-entity expansion in input XML; since 3.40 they are not resolved ([source](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)) | Pass a `SAXSource` with a configured `XMLReader` (passed through unchanged) for trusted input ([source](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `quarkus.camel.xslt.sources` | `List of string`, no default; scheme-less = `classpath:` | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html |
| `quarkus.camel.xslt.package-name` | `org.apache.camel.quarkus.component.xslt.generated` | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html |
| Build-time vs runtime per property | (unverified); rebuild after changing any `quarkus.camel.xslt.*` property | page not recorded |
| `output` | `string` | https://camel.apache.org/components/4.22.x/xslt-component.html |
| `contentCache` / `transformerCacheSize` | `true` / `0` | https://camel.apache.org/components/4.22.x/xslt-component.html |
| `xpathTotalOpLimit` | `10000` per TransformerFactory instance | https://camel.apache.org/components/4.22.x/xslt-component.html |
| `failOnNullBody` / `allowTemplateFromHeader` | `true` / `false` | https://camel.apache.org/components/4.22.x/xslt-component.html |
| Saxon `useJsonBody` / `allowStAX` / `secureProcessing` | `false` / `true` / `true` (medium confidence) | https://camel.apache.org/components/4.22.x/xslt-saxon-component.html |
| Saxon error properties | `Exchange.XSLT_ERROR`, `XSLT_FATAL_ERROR`, `XSLT_WARNING` (medium confidence) | https://camel.apache.org/components/4.22.x/xslt-saxon-component.html |
| Xalan factory as JAXP default | since 3.40.0; affects `TransformerFactory.newInstance()` app-wide (incl. Tika, XML Security) | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |
| Representative commands | `./mvnw clean verify`, `./mvnw verify -Dnative` (log output: unverified) | page not recorded |

## External Resources

All fetched 2026-10-14. camel.apache.org pages carry no page date and are the current stable 3.40.x / 4.22.x docs.

- XSLT extension: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html
- 3.40.0 migration guide: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- XSLT component (4.22.x): https://camel.apache.org/components/4.22.x/xslt-component.html
- XSLT Saxon component (4.22.x): https://camel.apache.org/components/4.22.x/xslt-saxon-component.html
- Releases: https://camel.apache.org/releases/
- Docs index (platform versions): https://camel.apache.org/camel-quarkus/latest/
- Quarkus LTS policy: https://quarkus.io/releases
- Quarkus 4 Beta1: https://quarkus.io/blog/quarkus-4-0-0-beta1-released/
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
