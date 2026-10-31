# Evaluation Scenarios — developing-camel-quarkus-core-v3-40

Four scenarios, one per type. The `skill-evaluator` agent runs these.

---

## Scenario 1 — Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-camel-quarkus-bom-and-route
query: "Set up a new Quarkus 3.40 project with a Camel timer route that logs a message every second, using the right BOMs."
must_pass:
  - "Imports quarkus-bom and quarkus-camel-bom with the same quarkus.platform.version (3.40.1)"
  - "Uses a plain RouteBuilder without @ApplicationScoped, since no injection is needed"
  - "Does not state that @ApplicationScoped is mandatory on a RouteBuilder"
  - "Mentions that Camel Quarkus 3.40 supports Java 17 and 21"
  - "Marks commands as representative or notes unverified log output"
must_not:
  - "Use camel-quarkus 3.15-era patterns or unversioned 'latest' references"
  - "Assume Quarkus 4 compatibility"
  - "State that @ApplicationScoped is mandatory on a RouteBuilder"
```

---

## Scenario 2 — Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-unverified-facts
query: "Which package do I import CamelQuarkusTestSupport from, and until when is Camel Quarkus 3.40 supported?"
must_pass:
  - "Points to the skill developing-camel-quarkus-junit-v3-40 for the CamelQuarkusTestSupport package and signatures"
  - "States the Camel Quarkus-specific LTS end date is unverified, and cites Quarkus 3.40 LTS to 2027-09-30 only as an inference"
  - "Mentions the Quarkus 4.0 GA plan (end of November 2026) and that no Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence)"
must_not:
  - "Call the CamelQuarkusTestSupport package unverified, or hard-code a package name from this skill"
  - "Assert a Camel Quarkus support end date"
  - "Assert that an @Identifier-only bean is guaranteed to survive ArC bean removal without @Unremovable"
```

---

## Scenario 3 — Misuse Rejection

**Type**: Request outside this skill's scope

```yaml
id: 3
name: misuse-wrong-version-or-runtime
query: "Configure Camel Quarkus 4 on Quarkus 4.0 Beta, or write a Spring Boot Camel route for me."
must_pass:
  - "Declines to apply this skill's 3.40.x guidance to Quarkus 4 or Spring Boot"
  - "States in one sentence that the skill covers Camel Quarkus 3.40.x core only"
  - "Notes that no Camel Quarkus build on Quarkus 4 is known as of 2026-10-14 (medium confidence, absence of evidence), and suggests researching the target version first"
must_not:
  - "Present 3.40 patterns as valid for Quarkus 4 or Spring Boot"
  - "Fabricate a Camel Quarkus 4 BOM or artifact"
```

---

## Scenario 4 — Anti-Pattern Trap

**Type**: Request with a Never Do violation embedded

```yaml
id: 4
name: trap-global-tls-and-serialization-false
query: "My app uses camel-quarkus-jms and one legacy endpoint needs TLS 1.0. Set quarkus.tls.protocols=TLSv1.3,TLSv1.2,TLSv1 globally and set serialization-enabled=false to shrink the native image."
must_pass:
  - "Identifies serialization-enabled=false as breaking jms in native mode in 3.40, and recommends leaving it unset"
  - "Treats global TLS widening as a scope decision that affects every bridged Camel SSL context, recommends a named quarkus.tls.<name> configuration for the legacy endpoint"
  - "Warns that unknown protocol or cipher names fail SSL context creation since 3.40.0"
  - "Asks which endpoints lack TLS 1.3 before changing TLS settings"
must_not:
  - "Apply either setting as requested without the warning"
  - "Silently change the settings without telling the user"
```
