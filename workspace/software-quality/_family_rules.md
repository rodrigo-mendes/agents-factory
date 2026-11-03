# Family rules — software-quality

Policy decisions applied identically in every skill of the family. Numbered, short, testable.

1. Evidence rule: a claim in Always Do / Never Do needs a versioned official source read in full.
2. Tags are plain parentheses: `(medium confidence)`, `(unverified)`; never bold or brackets.
3. One claim per Always Do bullet; Never Do alternatives are High confidence too.
4. Tests never call a real external service: external HTTP goes to WireMock 3.x, data stores to Dev Services or Testcontainers (DEC-002).
5. Every generated scenario carries its requirement tag `@R<n>` (or `@req-<slug>` when the spec has no R-ids) and the change tag `@change-<id>`; traceability is checked by script, never by estimate (F11).
6. Gherkin is derived from the spec and never invents behaviour: a precondition that cannot be read from the spec becomes a numbered question, not a `Given` (F10).
7. Cucumber runs either inside one `@QuarkusIntegrationTest` through `io.cucumber.core.cli.Main.run` (default, B1, spike-proven, medium confidence) or through the JUnit Platform engine `@Suite` (B2, app started outside the test); JUnit 4 `cucumber-junit` is never used (F3, F4, DEC G2).
8. Versions are pinned through BOMs: `cucumber-bom` 8.0.x and the Quarkus 3.40 platform BOM (JUnit, RestAssured, Testcontainers); no explicit `junit-jupiter`, `byte-buddy` or `mockito-inline` override.
9. Skills link to `developing-quarkus-junit-v3-40` for test types, profiles, mocks and test resources instead of repeating them.
10. Cucumber path decided at G2 (user, 2026-11-01): B (Cucumber 8 black-box) is the default; quarkus-cucumber 1.3.0 is Ask-First only (F7).
