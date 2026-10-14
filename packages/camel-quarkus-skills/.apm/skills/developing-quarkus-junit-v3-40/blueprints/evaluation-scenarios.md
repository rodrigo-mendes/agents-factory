# Evaluation Scenarios: developing-quarkus-junit-v3-40

Five scenarios covering the four types (canonical, edge, misuse, anti-pattern trap). Camel route-test scenarios live in `developing-camel-quarkus-junit-v3-40`. The `skill-evaluator` agent runs these.

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-rest-test-with-injectmock
query: "Write a @QuarkusTest for my Quarkus 3.40 GET /hello resource that mocks the @ApplicationScoped GreetingService, with the right Maven test dependencies."
must_pass:
  - "Adds quarkus-junit, rest-assured and quarkus-junit-mockito with test scope; does not use any -junit5 artifact"
  - "Uses @InjectMock on the @ApplicationScoped bean and a REST Assured call with a relative path (get(\"/hello\"))"
  - "Mentions the java.util.logging.manager Surefire property as part of the guide's setup"
must_not:
  - "Uses quarkus-junit5 or quarkus-junit5-mockito"
  - "Reads the port with System.getProperty"
  - "Writes Camel route-test code (it points to developing-camel-quarkus-junit-v3-40 if asked about Camel routes)"
```

---

## Scenario 2: Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-parallel-execution-and-jacoco-report-path
query: "Can I enable JUnit parallel execution for my @QuarkusTest suite, and where does JaCoCo write the HTML report in Quarkus 3.40?"
must_pass:
  - "States that no 3.40 page documents JUnit parallel execution with @QuarkusTest (unverified) and suggests running sequentially or parallelizing per module or fork"
  - "States the coverage page names both target/jacoco-report and target/jacoco-reports (unverified) and tells the user to set quarkus.jacoco.report-location explicitly"
  - "Gives the data-file default target/jacoco-quarkus.exec with its source"
must_not:
  - "Assert that parallel execution is supported or unsupported"
  - "Assert one report directory as the confirmed default"
```

---

## Scenario 3: Misuse Rejection

**Type**: Request outside this skill's scope

```yaml
id: 3
name: misuse-quarkus-4-and-old-artifact
query: "Set up tests for Quarkus 4.0 Beta1 and keep using quarkus-junit5 since it still works."
must_pass:
  - "Declines to apply 3.40 guidance to Quarkus 4 and notes Beta1 was published 2026-10-01 with the final release planned for the end of November"
  - "States quarkus-junit5 3.40.1 resolves only as a relocation POM, that the retention period is undocumented, and recommends quarkus-junit"
  - "States the skill covers Quarkus 3.40.x only"
must_not:
  - "Fabricate Quarkus 4 test artifacts or APIs"
  - "Recommend quarkus-junit5 for new 3.40 code"
```

---

## Scenario 4: Anti-Pattern Trap

**Type**: Request with a Never Do violation embedded

```yaml
id: 4
name: trap-injectmock-singleton-and-port-property
query: "Mock my @Singleton PriceService with @InjectMock and read the test port with System.getProperty(\"quarkus.http.test-port\"); also set quarkus.https.test-port=8444."
must_pass:
  - "Explains @InjectMock needs a normal-scoped bean, and offers @MockitoConfig(convertScopes = true), an @ApplicationScoped bean, or an @Alternative for startup beans"
  - "States system-property port lookups no longer work since 3.31 and offers the Quarkus config system, the injectable HttpServer, or quarkus.http.test-port with relative REST Assured paths; may list @TestHTTPResource or @TestHTTPEndpoint only as an option to confirm (medium confidence)"
  - "States quarkus.https.test-port was removed in 3.31; may offer quarkus.http.test-ssl-port as the replacement only with the tag (medium confidence, M10)"
must_not:
  - "Mock the @Singleton bean without convertScopes and without a warning"
  - "Keep the System.getProperty lookup or quarkus.https.test-port"
```

---

## Scenario 5: Anti-Pattern Trap (build file)

**Type**: Request with a Never Do violation embedded

```yaml
id: 5
name: trap-argline-and-main-test-injection
query: "My pom sets <argLine>-Xmx256m</argLine> for Surefire after upgrading from 3.15 to 3.40, and my @QuarkusMainTest injects a Repo with @InjectMock. Fix it."
must_pass:
  - "Includes @{argLine} in the argLine (e.g. first, as in the guide's example) and quotes the guide: that the property will automatically include the extra JVM parameters"
  - "States @QuarkusMainTest does not support CDI injection or @InjectMock and swaps the dependency through a @TestProfile"
  - "Replaces any -junit5 artifactIds with quarkus-junit and quarkus-junit-mockito"
must_not:
  - "Leave the argLine without @{argLine}"
  - "Keep @InjectMock in the @QuarkusMainTest"
```
