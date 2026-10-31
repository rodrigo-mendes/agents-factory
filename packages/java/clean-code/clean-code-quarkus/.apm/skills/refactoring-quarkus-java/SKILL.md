---
name: refactoring-quarkus-java
description: "Guides behaviour-preserving refactoring of Quarkus 3.40 Java code (REST resources, CDI services, Lambda handlers, AWS client wrappers): Extract Method, DRY, records, package split. Use when cleaning up or reviewing code. Not for OCI Functions or Quarkus 4."
---

# Refactoring Quarkus Java (Quarkus 3.40 statements)

> Version lock: the refactoring method is not version-specific; every **Quarkus-specific** statement applies to **Quarkus 3.40.x** only. Research dates **2026-10-14** (ArC, REST, JUnit) and **2026-10-28** (AWS family facts).
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Used in the implementation cycle at I4 (clean code), I5 (behaviour-preserving refactor) and by the reviewer at I7, for Quarkus + Camel and Quarkus + AWS projects. Neighbours: `developing-quarkus-arc-v3-40`, `developing-quarkus-rest-v3-40`, `developing-quarkus-junit-v3-40`, the rule `quarkus-clean-code` (package `quarkus-core`), `quarkus-code-reviewer` (agent in package `quarkus-aws`).

## Version Context

| Item | Value | Source (fetched 2026-10-14 unless noted) |
|---|---|---|
| Quarkus | 3.40, released 2026-09-30, LTS, community-maintained until 2027-09-30 | https://quarkus.io/releases |
| ArC / CDI | Jakarta CDI 4.1 Lite; unused-bean removal default `all` | https://quarkus.io/version/3.40/guides/cdi-reference |
| Quarkus REST | threading follows the method signature; constraint failures on parameters give 400 | https://quarkus.io/version/3.40/guides/rest |
| AWS Lambda | `quarkus-amazon-lambda`; user handler chosen by `quarkus.lambda.handler` (fetched 2026-10-28) | https://quarkus.io/guides/aws-lambda |
| Test artifacts (medium confidence, L1) | `quarkus-junit`, `quarkus-junit-mockito` | https://quarkus.io/version/3.40/guides/getting-started-testing |
| Refactoring method | Extract Method, Extract Class, DRY, records, facade; team practice (unverified, U1); catalog pointer https://refactoring.com/catalog/ (unverified, no page read) | no page read |
| Java | Quarkus 3.40 minimum not recorded (unverified, U3); Camel Quarkus 3.40 supports 17 and 21 | https://camel.apache.org/releases/q-3.40.0/ |

**Version-lifetime risk** (as of 2026-10-28; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; Java 21 becomes the base ([source](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)). Do not apply Quarkus 4 patterns here; re-check this skill when 4.0 is final.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Method (team practice)](#method-team-practice-unverified-u1-not-a-quarkus-fact-outside-the-three-tiers)
- [Quick Reference](#quick-reference)
- [Verification Loop](#verification-loop)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Safe-refactor recipe](./blueprints/refactor-recipe.md)
- [Package taxonomy and thin entry points](./blueprints/package-taxonomy.md)
- [Before / after examples](./blueprints/before-after-examples.md)
- [Reviewer checklist (I7)](./blueprints/reviewer-checklist.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

The tiers below hold only Quarkus 3.40 facts, each with a source URL. The general refactoring method (register U1) is team practice and sits in its own block after Never Do.

### ✅ Always Do

1. **Give an extracted collaborator that is injected a bean-defining scope.** Discovery runs in annotated mode, so a class without one is not a bean ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). See [patterns](./blueprints/always-do-patterns.md#scope-for-an-extracted-collaborator).
2. **Move `@Unremovable`, `@Named` and observer methods together with the bean.** These are the unremovable roots; the default is `remove-unused-beans=all` ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). See [patterns](./blueprints/always-do-patterns.md#markers-travel-with-a-moved-bean).
3. **Keep a resource method's signature kind.** The thread follows the signature: `Uni`/`Multi`/`CompletionStage`/`Publisher` run on the IO thread, other types are blocking ([REST guide](https://quarkus.io/version/3.40/guides/rest)). See [patterns](./blueprints/always-do-patterns.md#resource-signature-keeps-its-thread-model).
4. **Keep constraint annotations on the REST parameter.** Parameter violations return 400; service-method violations give 5xx unless `ConstraintViolationException` is mapped ([validation guide](https://quarkus.io/version/3.40/guides/validation)). See [patterns](./blueprints/always-do-patterns.md#validation-stays-on-the-resource-parameter).
5. **Keep `quarkus.lambda.handler` equal to the handler bean's CDI name.** The user handler is selected by that property ([AWS Lambda guide](https://quarkus.io/guides/aws-lambda)). See [patterns](./blueprints/always-do-patterns.md#lambda-handler-name-stays-in-sync).
6. **Index a bean archive when moving classes into another module.** A dependency is scanned only with `beans.xml`, `META-INF/jandex.idx` or `quarkus.index-dependency.<name>.*` ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). See [patterns](./blueprints/always-do-patterns.md#index-a-new-module).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| New interface | Only with a second implementation or a test seam. A normal-scoped class bean can be mocked with `@InjectMock` without an interface (medium confidence, M5) | "Is there a second implementation, or a seam that `@InjectMock` cannot give?" |
| Splitting a module | New module needs indexing (Always Do 6) and may change which tests see the beans | "Is a separate module worth the indexing and test relocation?" |
| Scope of a new bean | the CDI guide recommends `@ApplicationScoped` (lazy, mockable); `@Singleton` has no proxy and is not mockable by default (medium confidence, L1; [ArC skill](../developing-quarkus-arc-v3-40/SKILL.md)) | "Must the bean be mocked in tests?" |
| Moved bean qualified only with `@Identifier` | Whether ArC removes it is (unverified, U2); default: keep or add `@Unremovable` | "Is it injected by type anywhere, or only looked up by name?" |
| Private injection members (medium confidence, M1) | Package-private members avoid reflection registration in native builds | "Is the app built as a native executable?" |
| Constructor vs field injection (medium confidence, M4) | No page read states a preference; the REST guide's statement that resources may use either rests on a partly read guide (REST skill register, M11); follow the codebase | "Does the team already have a convention?" |
| Moving init or startup logic (medium confidence, M2) | Normal-scoped beans are created on the first proxy call; `@Startup` or `StartupEvent` makes creation eager | "Must the logic run before the first call?" |
| Moving `@ServerExceptionMapper` (medium confidence, M3) | A mapper inside a resource class applies only to that class; a global mapper lives outside | "Should the mapper stay class-local?" |
| Scope change and mocking (medium confidence, L1) | `@InjectMock` works only on normal-scoped beans; a `@Singleton` needs `@MockitoConfig(convertScopes = true)` ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)) | "Is the bean mocked in tests, and may its scope change?" |
| Records as value holders | Needs a Java level that supports records; the Quarkus 3.40 minimum is (unverified, U3) | "Which JDK does the build use?" |
| Low test coverage | Add characterization tests first, or proceed with smaller steps | "Add tests before refactoring?" |
| Relocating tests | Move a test with the logic it covers; shared tests need confirmation | "May I move or edit these test files?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Read a field of a normal-scoped bean from another bean after extracting; the client proxy delegates only method calls ([CDI guide](https://quarkus.io/version/3.40/guides/cdi)) | Call a method on the bean ([CDI guide](https://quarkus.io/version/3.40/guides/cdi)) |
| Move `@Valid` or constraint annotations from the resource parameter into a service method ([validation guide](https://quarkus.io/version/3.40/guides/validation)) | Validate at the resource parameter, then delegate |
| Flip a resource method between blocking and `Uni` return types while "cleaning up" ([REST guide](https://quarkus.io/version/3.40/guides/rest)) | Keep the return kind; changing the thread model is a separate task |
| Drop `@Unremovable`, `@Named` or an observer when moving a bean ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)) | Move the markers with the bean |
| Rename or move the Lambda handler bean without updating `quarkus.lambda.handler` ([AWS Lambda guide](https://quarkus.io/guides/aws-lambda)) | Change class name, CDI name and property in one step |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

### Method (team practice, unverified U1; not a Quarkus fact, outside the three tiers)

General refactoring method stated as team practice (register U1, "no page read"); the Fowler catalog https://refactoring.com/catalog/ is only a pointer (unverified). The Quarkus-specific rule file is `quarkus-clean-code` (package `quarkus-core`). Follow the method, but do not present it as a Quarkus claim.

1. Get a green baseline before editing; never start with a red suite or comment out failing tests (fix or skip with a reason). See [patterns](./blueprints/always-do-patterns.md#green-baseline).
2. Map test coupling first: which tests name a bean type, a resource class or a constructor. See [patterns](./blueprints/always-do-patterns.md#test-coupling).
3. Refactor one smell at a time and rerun the tests after every step. See [patterns](./blueprints/always-do-patterns.md#one-smell-at-a-time).
4. Preserve exact exception types and messages, log texts, status codes and side-effect order; open a separate task for any fix. See [recipe](./blueprints/refactor-recipe.md#dry-with-exception-parity).
5. Keep resources, Lambda handlers and the root handler class thin; delegate to collaborators. See [taxonomy](./blueprints/package-taxonomy.md).
6. Do not change a bean's scope during a refactor; make it a separate task (mock-scope details: Ask First row "Scope change and mocking").
7. Do not add an abstraction with one call site; extract a plain class and add an interface when a second implementation appears.

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Method size / nesting (team convention) | about 40 lines or fewer; at most 2 nesting levels; early returns | team practice, U1 (not a Quarkus fact) |
| `quarkus.arc.remove-unused-beans` | `all` default; also `none`/`false`, `fwk`/`framework` | https://quarkus.io/version/3.40/guides/cdi-reference |
| Unremovable roots | `@Unremovable`, `quarkus.arc.unremovable-types`, `UnremovableBeanBuildItem`, `@Named` beans, beans with an observer method | https://quarkus.io/version/3.40/guides/cdi-reference |
| Unqualified injection point / unannotated producer scope | `@Default` / `@Dependent` | https://quarkus.io/version/3.40/guides/cdi |
| `@IfBuildProfile`, `@IfBuildProperty` | evaluated at build time; move them with the bean | https://quarkus.io/version/3.40/guides/cdi-reference |
| Qualifier | prefer `@io.smallrye.common.annotation.Identifier` to `@Named` | https://quarkus.io/version/3.40/guides/cdi-reference |
| `@InjectMock` (medium confidence, L1) | needs `quarkus-junit-mockito`; normal-scoped beans only | https://quarkus.io/version/3.40/guides/getting-started-testing |
| Lambda handler | `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest`; user handler via `quarkus.lambda.handler` | https://quarkus.io/guides/aws-lambda |
| ArC dev endpoints | `/q/arc/removed-beans` and siblings, dev mode (unverified, U4) | page not recorded |

## Verification Loop

After every extraction step, before the next one:

1. Compile and run the full suite (representative command `./mvnw test`); the exit code must stay 0, as in the baseline.
2. Diff status codes, exception types and messages, log texts and side-effect order against the original (reviewer checklist B1 to B4).
3. Check the Quarkus items that tests may not catch: every injected new class has a scope (Q1), moved markers are still on the bean (Q2), `quarkus.lambda.handler` equals the handler's CDI name (Q7), a new module is indexed (Q8). Walk the [reviewer checklist](./blueprints/reviewer-checklist.md).
4. In dev mode the ArC removed-beans endpoint can show a bean that was dropped (path is (unverified, U4); confirm in the running dev UI).
5. If any check fails, revert the last step instead of fixing forward.

## External Resources

All fetched 2026-10-14 unless noted. quarkus.io/version/3.40 pages document the current stable LTS.

- CDI reference: https://quarkus.io/version/3.40/guides/cdi-reference
- CDI introduction: https://quarkus.io/version/3.40/guides/cdi
- REST guide: https://quarkus.io/version/3.40/guides/rest
- Validation guide: https://quarkus.io/version/3.40/guides/validation
- Testing guide: https://quarkus.io/version/3.40/guides/getting-started-testing
- AWS Lambda guide (fetched 2026-10-28): https://quarkus.io/guides/aws-lambda
- Sibling skills in this package: [ArC](../developing-quarkus-arc-v3-40/SKILL.md), [REST](../developing-quarkus-rest-v3-40/SKILL.md), [JUnit](../developing-quarkus-junit-v3-40/SKILL.md)
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
