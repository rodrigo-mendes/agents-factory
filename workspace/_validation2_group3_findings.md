# Final validation, group 3 (reports were not written to disk by the validator; persisted by the orchestrator from its message). Skill folder = packages/camel-quarkus-skills/.apm/skills/<name>/

## developing-quarkus-junit-v3-40 (score 67)
HIGH
- H1 SKILL.md:74 Never Do test-port row: the ✅ alternative (@TestHTTPResource/@TestHTTPEndpoint) is medium (Ask First SKILL.md:60 and register M-3: two sources make different claims). Keep the ❌ (High, 3.31 wiki); make the ✅ a High item (e.g. REST Assured auto-configured base URL / relative paths); URL-injection options go to Ask First.
- H2 SKILL.md:50 Always Do 4 bundles four claims (normal-scope only; quarkus-junit-mockito requirement; @Singleton needs convertScopes; startup beans unaffected). Keep ONE claim, move the rest to blueprint/Ask First.
- H3 blueprints/integration-examples.md:19-21 and evaluation-scenarios.md:17: the sample overrides isUseAdviceWith() returning true and declares doBeforeEach(QuarkusTestContext ctx); the sibling skill makes isUseAdviceWith a Never Do (deprecated since 3.15.0) and the signature is QuarkusTestMethodContext. Scenario 1 must_pass requires "isUseAdviceWith returning true". Fix: delete the Camel route-test content (see rule 15), remove that must_pass item.
MEDIUM
- M1 SKILL.md:51 Always Do 5 mandates CamelQuarkusTestSupport (sibling offers plain @QuarkusTest as Ask First; QJ's own always-do-patterns never mentions the class): delete (rule 15).
- M2 SKILL.md:47 "never the -junit5 name" vs blueprint (resolves as a relocation POM, retention undocumented): reword to "prefer" and state it resolves.
- M3 Camel-specific content (Always Do 5, Never Do 6, integration-examples.md:11-41) duplicates the sibling: delete and link by name.
- M4 Never Do rows 3 and 4 (SKILL.md:73-74) cite only the unversioned 3.31 wiki (not orchestrator-verified): keep High only if the rule allows, otherwise tag medium and move to Ask First/blueprint; do not leave a medium claim in Never Do.
- M5 unverified-and-risks.md:81 says the testing guide was "read in full in two passes": it was read to 100k of 108,136 characters (rule 17).
LOW: mocking.md:14-15 no blank line before "## Examples"; SKILL.md:88 AOT/JDK 25+ row untagged; register ID scheme differs (rule 12); SKILL.md:19 BOM values from a partial read and untagged; Always Do 3 logging-manager claim phrased as "shows" but rule says "Always".

## developing-camel-quarkus-junit-v3-40 (score 71)
HIGH
- H1 SKILL.md:48 Always Do 3 has three claims (one shared context; isolate with @TestProfile; never stop/start/replace). Keep ONE ("the CamelContext is shared by the suite"); the last duplicates Never Do row 3.
- H2 blueprints/always-do-patterns.md:69-70 sample uses wildcard weaveByToUri("kafka:output-topic*") but SKILL.md:72, never-do-patterns.md:49-57 and scenario 1 must_not forbid wildcard weave. Use weaveById(...) (if the guide's own sample really uses a wildcard, soften Never Do 4 to its actual wording).
MEDIUM
- M1 SKILL.md:46-47 Always Do 2 says to extend CamelQuarkusTestSupport but Ask First (:57, medium) offers plain @QuarkusTest: make Always Do 2 claim only that the class and its package exist (package org.apache.camel.quarkus.test), move the choice out of Always Do.
- M2 unverified-and-risks.md:38 lists medium items as a run-on paragraph without IDs/count; mapping is by class only: add M1.. ids and a 1:1 tag mapping (rule 8, 12).
- M3 SKILL.md:84 Source column says "same source file": exact URL.
- M4 register lines 17 and 34 file the end date as I2 while SKILL.md:26 says unverified: rule 8.
- M5 SKILL.md:88 and native-testing.md:11 ("integration tests run in prod and ignore application.properties") and integration-examples.md:35 (@QuarkusTestResource global default) untagged: tag medium (rule 18).
- M6 SKILL.md:74 gives "subclass a plain @QuarkusTest class" as a High ✅ while SKILL.md:57 calls plain style medium: make the ✅ High or demote (rule 18).
LOW: always-do-patterns.md 106 lines with no TOC; SKILL.md:69-73 ✅ cells carry no inline source; never-do-patterns.md:20,49,62,91 "(severity: medium)" headings (rule 19); SKILL.md:49 Always Do 4 has two claims.

## developing-camel-quarkus-jaxb-v3-40 (score 87), no HIGH
- M1 never-do-patterns.md:25 "It is never mandatory on a RouteBuilder": reword to "not mandatory unless the route injects".
- M2 register :23 and :76 file the Camel Quarkus end date as I2: rule 8.
- M3 SKILL.md:47 Always Do 1 bundles two claims; "the version comes from quarkus-camel-bom" (always-do-patterns.md:9) has no source.
- M4 SKILL.md:65 and register U11 call Camel lookup of @Identifier beans unverified: rule 13 (High; only ArC removal is unverified).
- LOW: SKILL.md:9 does not link the mapping table; I3/M9 same fact in two classes; migration-guide.md:12 unsourced "(it does not use Java serialization)"; U1 mixes confidence classes ("medium in practice"); migration-guide.md:7 absence claim tagged "(High)"; SKILL.md:22 "none recorded" -> "page not recorded".

## developing-quarkus-arc-v3-40 (score 90), no HIGH
- M1 SKILL.md:46 Always Do 1 (classes without a bean-defining annotation are not beans) is stronger than always-do-patterns.md:16 (a class declaring producers/observers is treated as @Dependent): add the exception or narrow.
- M2 SKILL.md:75 Never Do 3 (only normal-scoped beans can be mocked) offers only "use a normal scope": add @MockitoConfig(convertScopes = true) to the ✅ cell (rule 14).
- M3 camel-integration.md:15 states untagged that Camel resolves @Identifier names: tag per rule 13 (High, cite the Camel Quarkus CDI page).
- LOW: register lines 16 and 18 repeat the Quarkus 3.40 release bullet; SKILL.md:48 Always Do 3 does not point to the Ask First row on @Identifier-only removal (U1); SKILL.md:50 Always Do 5 has two claims; SKILL.md:94 jandex plugin version numbers in Quick Reference go stale; Never Do 2's ✅ suits extension authors, not application code.

## developing-quarkus-rest-v3-40 (score 90), no HIGH
- M1 register :43 (also security-and-tls.md:68, camel-integration.md:62) files "does 3.40 TLS bridging affect the inbound platform-http server" as I2: rule 8 (unverified).
- M2 SKILL.md:47, :48, :50 Always Do 2, 3, 5 each carry two claims (IO-thread default plus "other signatures are blocking"; blocking-only plus Java 21+): one claim per bullet.
- M3 "pinning risk on Java 21-23" (SKILL.md:58, always-do-patterns.md:48) untagged and without an inline source.
- LOW: unverified IDs skip U2 and U5; Always Do 5 and Never Do 3 are High but L1/L3 were partly read: note limits there; always-do-patterns.md:19-23 server artifacts under heading "Client artifact"; camel-integration.md:35 .bean("orderService", ...) without showing the registration; SKILL.md:20 "Jackson 2.x" untagged.
