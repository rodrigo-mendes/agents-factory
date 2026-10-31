# Evaluation Scenarios — developing-camel-quarkus-rest-v3-40

Four scenarios, one per type. The `skill-evaluator` agent runs these.

---

## Scenario 1 — Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-json-rest-dsl
query: "Create a Camel Quarkus 3.40 REST endpoint GET /fruits and POST /fruits with JSON binding."
must_pass:
  - "Declares camel-quarkus-rest, camel-quarkus-jackson and camel-quarkus-direct, noting jackson and direct follow the main-branch example (medium confidence)"
  - "Calls restConfiguration().bindingMode(RestBindingMode.json) and notes the default is off"
  - "Uses type/outType on the verbs (medium confidence) and plain extends RouteBuilder without @ApplicationScoped"
  - "Configures port/TLS only through quarkus.http.* and marks commands as representative"
must_not:
  - "States @ApplicationScoped is mandatory on a RouteBuilder"
  - "Use 3.15-era patterns or assume Quarkus 4 compatibility"
```

---

## Scenario 2 — Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-unverified-paths-and-docs
query: "My REST DSL API runs with quarkus.http.root-path=/svc. What URL do my routes get, and does the /api-doc path need its own security permission?"
must_pass:
  - "States that the effect of root-path on REST DSL paths is unverified and suggests a curl test in dev mode"
  - "States that the need for a separate permission on the doc path is unverified and suggests adding an explicit permission"
  - "Does not invent an official statement"
must_not:
  - "Assert that REST DSL paths are or are not prefixed by root-path"
```

---

## Scenario 3 — Misuse Rejection

**Type**: Request outside this skill's scope

```yaml
id: 3
name: misuse-wrong-version-or-runtime
query: "Write a REST DSL service for Camel Quarkus 4 on Quarkus 4.0 Beta, or map payloads with AtlasMap."
must_pass:
  - "Declines to apply 3.40.x guidance to Quarkus 4 and notes no Camel Quarkus build on Quarkus 4 is known as of 2026-10-14 (medium confidence, absence of evidence)"
  - "Says camel-atlasmap was removed in Camel 4.0 (medium confidence) and proposes POJO binding plus a mapping bean"
  - "States the skill covers Camel Quarkus 3.40.x REST only"
must_not:
  - "Recommend AtlasMap or fabricate a Camel Quarkus 4 artifact"
```

---

## Scenario 4 — Anti-Pattern Trap

**Type**: Request with a Never Do violation embedded

```yaml
id: 4
name: trap-camel-tls-and-open-cors
query: "Set restConfiguration().port(8443) with an sslContextParameters endpoint property and enableCORS(true) so any site can call my API in production."
must_pass:
  - "Explains SSLContextParameters on the platform-http server is not supported and server config belongs to quarkus.http.*, without asserting the TLS registry effect on the inbound server (unverified)"
  - "Warns that Camel CORS defaults to Allow-Origin * (medium confidence, Ask First) and recommends quarkus.http.cors.* with explicit origins"
  - "Asks which origins may call the API"
must_not:
  - "Apply either setting as requested without the warning"
  - "State that TLS is silently ignored as a verified fact"
  - "Claim to know how the Camel and Quarkus CORS filters interact on one request"
```
