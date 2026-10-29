---
name: quarkus-clean-code
description: "Clean code and behaviour-preserving refactor rules for Quarkus 3.40 Java (REST resources, CDI beans, Lambda handlers, AWS client wrappers). Use when writing, refactoring or reviewing Java in a Quarkus project, at implementation steps I4/I5 and review step I7."
paths:
  - "**/src/main/java/**/*.java"
  - "**/src/test/java/**/*.java"
---

# Quarkus clean code and refactor (3.40)

Technical facts live in the skill named below and its blueprints. This rule states what to check
and where to look; it does not duplicate skill bodies. Tags `(unverified)` and
`(medium confidence)` from the skill apply here too.

Activation: a glob cannot test file content, so the pattern covers Maven/Gradle main and test Java
sources only. Apply this rule **only in Quarkus projects** (the `pom.xml` or `build.gradle`
contains `io.quarkus`); otherwise ignore it.

OCI Functions projects: the `java-functions-clean-code` rule governs there, not this one. If both
load (for example a repo holding both kinds of module), the more restrictive guidance wins.
Quarkus 4 is out of scope.

## Skills

| Need | Skill |
|---|---|
| Method, guardrails, recipe, package taxonomy, reviewer checklist | `refactoring-quarkus-java` |
| Scopes, bean removal, `@InjectMock` limits | `developing-quarkus-arc-v3-40` |
| Resource thread model, validation placement | `developing-quarkus-rest-v3-40` |
| Test profiles and mocking | `developing-quarkus-junit-v3-40` |

Blueprints of `refactoring-quarkus-java`: `always-do-patterns`, `never-do-patterns`,
`refactor-recipe`, `package-taxonomy`, `before-after-examples`, `reviewer-checklist`,
`unverified-and-risks`.

## Always

- Get a green baseline first, map which tests name a bean, resource or constructor, then refactor one
  smell at a time and rerun the tests after each step (`refactor-recipe`).
- Preserve status codes, exception types and messages, log texts and side-effect order
  (`always-do-patterns`).
- Keep resources, Lambda handlers and the root handler class thin; delegate to collaborators
  (`package-taxonomy`).
- Give an extracted, injected collaborator a bean-defining scope; move `@Unremovable`, `@Named` and
  observers together with the bean (`always-do-patterns`).
- Keep a resource method's signature kind and keep constraint annotations on the REST parameter
  (`always-do-patterns`).
- Keep `quarkus.lambda.handler` equal to the handler bean's CDI name when renaming or moving it
  (`always-do-patterns`).
- At I7, review with the `reviewer-checklist` and its report format; read the project ADRs first.

## Ask First

- A new interface, a scope for a new bean, splitting into a module, constructor vs field injection,
  moving startup logic or exception mappers, low test coverage, relocating tests: take the question
  from the skill's Ask-First table, do not decide silently (`refactoring-quarkus-java`).
- Anything the skill tags `(unverified)` or `(medium confidence)`: state the tag when relying on it
  (`unverified-and-risks`).

## Never

- Change behaviour, scope, thread model or validation placement while "just cleaning up": open a
  separate task (`never-do-patterns`).
- Start refactoring with a red suite, or comment out failing tests.
- Add an abstraction with a single call site.
- Read a field of a normal-scoped bean from another bean; call a method instead (`never-do-patterns`).
- Rename or move the Lambda handler bean without updating `quarkus.lambda.handler`.
- Mix Quarkus 4 patterns into 3.40 code.

## Verify

- Run `./mvnw test` (or `mvn test`, or the Gradle equivalent) before and after each step.
- Grep the diff for removed `@Unremovable`, `@Named`, `@Valid` and changed `@ApplicationScoped` or
  `@Singleton`: review each match against `reviewer-checklist` Q1 to Q9.
- Grep for `quarkus.lambda.handler` and compare it with the `@Named` value of the handler class.
