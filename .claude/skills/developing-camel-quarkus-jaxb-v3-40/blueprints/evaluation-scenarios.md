# Evaluation Scenarios: developing-camel-quarkus-jaxb-v3-40

Five scenarios: canonical, edge, misuse, anti-pattern trap, and the special-case trap. The `skill-evaluator` agent runs these.

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-jaxb-roundtrip-with-xsd
query: "On Camel Quarkus 3.40, marshal a Person object to XML and unmarshal it back, validating against person.xsd."
must_pass:
  - "Adds camel-quarkus-jaxb without a version"
  - "Defines a named JaxbDataFormat with an explicit contextPath and sets prettyPrint explicitly"
  - "Uses schema=classpath:person.xsd and leaves accessExternalSchemaProtocols unset"
  - "Uses a plain RouteBuilder with no @ApplicationScoped, since nothing is injected"
must_not:
  - "states @ApplicationScoped is mandatory on a RouteBuilder"
  - "Adds com.sun.xml.bind dependencies as a requirement"
  - "Sets accessExternalSchemaProtocols=all"
```

---

## Scenario 2: Edge Case

**Type**: Unverified or contradictory territory the skill must handle gracefully

```yaml
id: 2
name: edge-unverified-defaults-and-setters
query: "What is the default of prettyPrint, which setter injects an external JAXBContext into JaxbDataFormat, and which Camel release added accessExternalSchemaProtocols?"
must_pass:
  - "States the prettyPrint default is contradictory on the 4.22.x page (table true, prose false) and advises setting it explicitly"
  - "States the setter name for an external JAXBContext is unverified and does not invent one"
  - "States the release that added accessExternalSchemaProtocols was not traced"
must_not:
  - "Invent a prettyPrint default, a setter name or a Camel release number"
  - "Assert a Camel Quarkus-specific end-of-support date"
```

---

## Scenario 3: Misuse Rejection

**Type**: Request outside this skill's scope

```yaml
id: 3
name: misuse-jacksonxml-on-quarkus-4
query: "Configure camel-quarkus-jacksonxml with Jackson 3 on Quarkus 4.0 Beta1 using this skill."
must_pass:
  - "States this skill covers camel-quarkus-jaxb on Camel Quarkus 3.40.x only"
  - "States jacksonxml options were not verified and that no Camel Quarkus build on Quarkus 4 is known as of 2026-10-14 (medium confidence, absence of evidence)"
  - "Offers JAXB on 3.40.x as the in-scope alternative, or points to a jacksonxml skill"
must_not:
  - "Fabricate a Camel Quarkus 4 BOM, artifact or jacksonxml option"
  - "Apply 3.40.x guidance to Quarkus 4 as if verified"
```

---

## Scenario 4: Anti-Pattern Trap

**Type**: Request with Never Do violations embedded

```yaml
id: 4
name: trap-unregistered-pojos-scope-and-junit5
query: "Our ObjectFactory creates plain PojoPerson classes without JAXB annotations. Build it native. Annotate the RouteBuilder with @ApplicationScoped just in case, and write tests with camel-quarkus-junit5."
must_pass:
  - "Registers PojoPerson with @RegisterForReflection or quarkus.camel.native.reflection.include-patterns, citing the extension page"
  - "Advises against @ApplicationScoped on a RouteBuilder that injects nothing"
  - "Recommends camel-quarkus-junit instead of camel-quarkus-junit5"
must_not:
  - "Leave the ObjectFactory POJOs unregistered"
  - "Keep camel-quarkus-junit5 as the test dependency"
```

---

## Scenario 5: Special-Case Trap (reflection on annotated classes)

**Type**: Request that tempts an overstated rule

```yaml
id: 5
name: edge-register-for-reflection-on-annotated-classes
query: "Is it wrong to put @RegisterForReflection on every @XmlRootElement class?"
must_pass:
  - "Says it is redundant but harmless, tagged medium confidence and inferred from Quarkus source code, not documented behaviour"
  - "Says registration is required for non-annotated ObjectFactory-created POJOs and cites the extension page"
must_not:
  - "Present it as a documented prohibition or as breaking the build"
  - "Say the extension page forbids it"
```
