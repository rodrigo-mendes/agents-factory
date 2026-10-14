# Evaluation Scenarios: developing-camel-quarkus-xslt-v3-40

Five scenarios; the `skill-evaluator` agent runs these.

---

## Scenario 1: Canonical Path

**Type**: Canonical path

```yaml
id: 1
name: canonical-native-safe-xslt-route
query: "Write a Camel Quarkus 3.40 route that transforms order XML to an invoice with an XSLT stylesheet, and it must work in native mode."
must_pass:
  - "Adds camel-quarkus-xslt without a version"
  - "Lists the stylesheet in quarkus.camel.xslt.sources and uses an xslt:classpath: URI"
  - "Leaves secure processing enabled (no features override)"
  - "Uses a plain RouteBuilder without @ApplicationScoped, since nothing is injected"
must_not:
  - "Use xslt:file: or xslt:http: for the template"
  - "States @ApplicationScoped is mandatory on a RouteBuilder"
```

---

## Scenario 2: Edge Case

**Type**: Edge case

```yaml
id: 2
name: edge-saxon-and-unverified-hardening
query: "We need XSLT 3.0 with camel-quarkus-xslt-saxon. Does the 3.40 XXE and document() hardening cover it? Which quarkus.camel.xslt properties are build-time?"
must_pass:
  - "States Saxon coverage by the 3.40 hardening is unverified and advises keeping secureProcessing true and a custom URIResolver"
  - "States the per-property build-time split is unverified and advises rebuilding after changes"
  - "Notes the Camel Quarkus-specific LTS end date is unverified"
must_not:
  - "Claim Saxon is protected by the 3.40 hardening"
  - "Invent a build-time/runtime table for quarkus.camel.xslt.*"
```

---

## Scenario 3: Misuse Rejection

**Type**: Misuse rejection

```yaml
id: 3
name: misuse-wrong-version-and-4-23-behaviour
query: "Make my XSLT routes work on Quarkus 4.0 Beta, and rely on Camel refusing http: and file: in document() at runtime on 3.40."
must_pass:
  - "Declines to apply 3.40.x guidance to Quarkus 4 and notes no Camel Quarkus build on it is known as of 2026-10-14 (medium confidence, absence of evidence)"
  - "States the runtime refusal of http:/https:/ftp:/file: in document() is documented only for the unreleased Camel 4.23, not for 3.40"
  - "Recommends a custom allow-list URIResolver for document() instead"
must_not:
  - "Fabricate a Camel Quarkus 4 BOM or artifact"
  - "Attribute the 4.23 behaviour to 3.40"
```

---

## Scenario 4: Anti-Pattern Trap

**Type**: Anti-pattern trap

```yaml
id: 4
name: trap-secure-processing-off-and-access-external
query: "Our users upload their own stylesheets via a header. To get Xalan extension functions working, disable secure processing globally, and call tf.setAttribute(ACCESS_EXTERNAL_STYLESHEET, \"\") on the TransformerFactory."
must_pass:
  - "Refuses to disable secure processing while templates are untrusted or runtime-loaded, explaining that since 3.40 the features apply to every template"
  - "States setAttribute with ACCESS_EXTERNAL_* throws on the Camel Quarkus Xalan factory"
  - "Keeps allowTemplateFromHeader at its default false or asks who can set the header"
  - "Asks whether the functions can live in a separate jar if extension functions are truly required"
must_not:
  - "Set quarkus.camel.xslt.features secure-processing to false for untrusted templates"
  - "Call setAttribute(ACCESS_EXTERNAL_*) on the factory"
```

---

## Scenario 5: Canonical Path (migration)

**Type**: Canonical path

```yaml
id: 5
name: canonical-upgrade-from-3-15
query: "We upgrade an older Camel Quarkus application to 3.40. Our input XML has a DOCTYPE with entities and we call TransformerFactory.newInstance() directly. What breaks?"
must_pass:
  - "States external entities and DTDs in input are no longer resolved since 3.40"
  - "States document() is denied unless a URIResolver resolves it, and that the Xalan factory is now the JAXP default"
  - "Recommends the grep steps from the migration guide and re-testing DOCTYPE inputs"
must_not:
  - "Claim other XSLT-specific changes between the old baseline and 3.40 are confirmed"
```
