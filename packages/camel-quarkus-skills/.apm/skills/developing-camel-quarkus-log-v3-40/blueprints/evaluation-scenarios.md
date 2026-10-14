# Evaluation Scenarios: developing-camel-quarkus-log-v3-40

Five scenarios covering the four types. The `skill-evaluator` agent runs these.

---

## Scenario 1: Canonical Path

**Type**: Canonical path

```yaml
id: 1
name: canonical-audit-logging-with-mdc
query: "Add audit logging to my Camel Quarkus 3.40 route, with the exchange id in every log line, and without leaking tokens."
must_pass:
  - "Adds camel-quarkus-log and camel-quarkus-mdc without versions"
  - "Sets quarkus.camel.mdc.enabled=true and renders %X{camel.exchangeId}"
  - "Uses a log: endpoint with logMask=true and selected show* options, not showAll"
  - "Uses a plain RouteBuilder without @ApplicationScoped, since nothing is injected"
  - "Does not claim logMask=true protects all PII: it masks only key-named values, URI passwords and PEM private keys"
must_not:
  - "Use camel.main.useMdcLogging"
  - "Enable showAll, showHeaders or showProperties"
  - "States @ApplicationScoped is mandatory on a RouteBuilder"
```

---

## Scenario 2: Edge Case

**Type**: Edge case

```yaml
id: 2
name: edge-unverified-claims
query: "Does the Log EIP support the JSONPath language, how much overhead does the log component add, and which quarkus.camel.mdc properties are build-time?"
must_pass:
  - "States the Log EIP language question is unverified (page says only Simple, yet logLanguage exists)"
  - "States there are no official performance numbers and gives only the qualitative notes"
  - "States which mdc properties are build-time is not confirmed and advises setting enabled in application.properties"
must_not:
  - "Invent a language list, a latency figure or a build-time property list"
  - "Assert a Camel Quarkus-specific end-of-support date"
```

---

## Scenario 3: Misuse Rejection

**Type**: Misuse rejection

```yaml
id: 3
name: misuse-quarkus-4-or-old-recipe
query: "Port this 3.15 recipe to Quarkus 4.0 Beta: camel.main.useMdcLogging=true and camel.main.mdcLoggingKeysPattern=myKey*."
must_pass:
  - "Declines to apply 3.40.x guidance to Quarkus 4 and notes no Camel Quarkus build on it is known as of 2026-10-14 (medium confidence, absence of evidence)"
  - "Replaces both properties with camel-quarkus-mdc and quarkus.camel.mdc.custom-exchange-properties"
  - "Points to the migration-guide blueprint"
must_not:
  - "Fabricate a Camel Quarkus 4 BOM or artifact"
  - "Keep the deprecated properties"
```

---

## Scenario 4: Anti-Pattern Trap

**Type**: Anti-pattern trap

```yaml
id: 4
name: trap-showall-and-runtime-trace
query: "For production debugging, log everything with .to(\"log:debug?showAll=true\") and set quarkus.log.category.\"org.apache.camel\".level=TRACE at runtime."
must_pass:
  - "Warns that showAll dumps headers and properties and may leak secrets, and proposes selected show* options with logMask=true"
  - "Says, tagged medium confidence, that quarkus.log.min-level (default DEBUG) is build-time and the category min-level must be lowered and rebuilt for TRACE"
  - "Asks whether a throughput or per-message view is needed"
must_not:
  - "Accept showAll in production without masking"
  - "Claim runtime TRACE works with the default min-level"
```

---

## Scenario 5: Edge Case, Medium-Confidence Handling

**Type**: Edge case

```yaml
id: 5
name: edge-global-logmask-and-stream-caching
query: "Is camel.main.logMask=true enough to mask everything, and can I switch stream caching off to save memory while logging bodies?"
must_pass:
  - "Tags camel.main.logMask support in Camel Quarkus as medium confidence and recommends logMask=true on sensitive URIs too"
  - "Tags the stream-caching claim as medium confidence, notes the default is true and that logging a stream body may leave it empty"
  - "Asks whether routes log stream-based bodies"
must_not:
  - "State the global setting is confirmed for every Camel Quarkus case"
  - "Present stream caching off as safe"
```
