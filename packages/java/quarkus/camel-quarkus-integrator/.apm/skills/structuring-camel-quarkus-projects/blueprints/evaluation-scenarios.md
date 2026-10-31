# Evaluation Scenarios: structuring-camel-quarkus-projects

## Scenario 1 (canonical): where does a REST route class go

**Prompt**: "Create a route class that exposes the orders REST endpoint in this Camel Quarkus project." The project's `pom.xml` and source tree use base package `org.acme.billing`.

**Expected**:
- Resolves `org.acme.billing` from the project rather than using `com.company.project`.
- Places the class at `src/main/java/org/acme/billing/integration/routes/OrdersRestRoute.java` (or another `[Functionality]Route` name) in package `org.acme.billing.integration.routes`.
- Proposes the matching test `OrdersRestRouteTest.java` under `src/test/java/org/acme/billing/integration/routes/`.
- Does not state annotation or framework rules; defers them to the version-specific skills.

**Fail if**: it uses the placeholder package, puts the class in `model` or `services`, or names it without the `Route` suffix.

## Scenario 2 (edge): project with a different base package

**Prompt**: "Add a validation service." The existing tree is `src/main/java/es/example/hub/...` with `integration/routes` and `integration/services` already present, and no `pom.xml` is readable.

**Expected**:
- Infers `es.example.hub` from the existing tree, and states that it did so.
- Creates `ValidationService.java` in `es/example/hub/integration/services/`.
- Does not rename or move existing files.
- If no package could be determined, asks the user instead of guessing.

**Fail if**: it creates `com/company/project/...`, or proposes migrating the project to a new package without asking.

## Scenario 3 (misuse): restructure a non-Camel project

**Prompt**: "Reorganize my Spring Boot batch project into this layout." The project has no Camel or Quarkus dependency.

**Expected**:
- Says the skill covers Camel Quarkus integration projects and does not apply here.
- Does not move or rename files.
- At most, offers to apply the layout if the user confirms it should be used as a convention anyway (Ask First).

**Fail if**: it restructures the project, or invents Camel-specific justifications.

## Scenario 4 (guardrail): off-pattern test name

**Prompt**: "Add a test for FileProcessingRoute, call it FileRouteSpecTest."

**Expected**: flags that the convention is `[ClassName]Test`, proposes `FileProcessingRouteTest` in the same package as the route under `src/test/java`, and asks before using the requested name.

**Fail if**: it silently creates `FileRouteSpecTest`.
