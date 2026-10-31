# Reviewer checklist (I7)

Back to [SKILL.md](../SKILL.md). Used by the reviewer at I7 on a diff produced at I4 or I5, for Quarkus + Camel and Quarkus + AWS projects. The agent `quarkus-code-reviewer` (package quarkus-aws) consumes the same list. Quarkus facts apply to 3.40.x; each row names its source.

## Process items (do these first)

| # | Item | Pass when |
|---|---|---|
| P1 | **Checks against ADRs.** Read the project's architecture decision records (ADRs) that touch the changed code before reading the diff; their location is project-specific (page not recorded) | The diff contradicts no accepted ADR (client choice, tracing choice, scope policy, module boundaries). If an ADR would have to change, stop and raise a separate change |
| P2 | Scope of the change is a refactor | No new feature, no bug fix, no dependency or version change in the same diff |
| P3 | Baseline and result | The author reports a green suite before and after; the reviewer reruns it when feasible (representative command `./mvnw test`) |
| P4 | Tests moved with logic | Each extracted class has a focused test; moved tests still cover the old behaviour |

## Behaviour parity

| # | Check | Evidence source |
|---|---|---|
| B1 | Status codes unchanged | diff of `RestResponse.status(...)`, `Response.status(...)` and mapper methods |
| B2 | Exception types and messages unchanged where a mapper or test depends on them | diff of `throw` and `catch` blocks |
| B3 | Log texts and levels unchanged | diff of log strings |
| B4 | Side-effect order unchanged (validate, map, send, respond) | read the flow top to bottom |
| B5 | Public and package-private test hooks unchanged, or tests relocated | compile plus test run |

## Quarkus 3.40 checks

| # | Check | Source |
|---|---|---|
| Q1 | Every injected new class has a scope | [CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference) |
| Q2 | Moved beans kept `@Unremovable`, `@Named`, observers; `@Identifier`-only beans reached by name are kept unremovable (unverified, U2) | [CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference) |
| Q3 | No bean's scope changed; `@InjectMock` targets still normal-scoped (medium confidence, L1) | [testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing) |
| Q4 | No direct field reads on normal-scoped beans | [CDI guide](https://quarkus.io/version/3.40/guides/cdi) |
| Q5 | Resource methods keep blocking or `Uni` kind, `@Blocking` and `@NonBlocking` unchanged | [REST guide](https://quarkus.io/version/3.40/guides/rest) |
| Q6 | Constraint annotations still on the REST parameters | [validation guide](https://quarkus.io/version/3.40/guides/validation) |
| Q7 | `quarkus.lambda.handler` still equals the handler bean's CDI name | [AWS Lambda guide](https://quarkus.io/guides/aws-lambda) |
| Q8 | New module indexed (`beans.xml`, `jandex.idx` or `quarkus.index-dependency.*`) | [CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference) |
| Q9 | Build-time conditions (`@IfBuildProfile`, `@IfBuildProperty`) still on the same bean | [CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference) |
| Q10 | Moved mapper, init or startup logic keeps its scope of effect (medium confidence, M2 and M3) | [register](./unverified-and-risks.md#medium-confidence-items) M2, M3 |
| Q11 | Injection members package-private if native build (medium confidence, M1) | [register](./unverified-and-risks.md#medium-confidence-items) M1 |

## Structure and readability

| # | Check | Pass when |
|---|---|---|
| S1 | Entry classes (resource, Lambda handler) are thin | one flow call, boundary validation, response building |
| S2 | Methods read as short sequences of named steps | about 40 lines or fewer, at most 2 nesting levels (team convention) |
| S3 | No duplicated scaffolding left | retry, wrap and log blocks appear once |
| S4 | No speculative abstraction | every new interface has two implementations or a named seam |
| S5 | Handler class at the package root | not inside `web/`, `handler/`, `client/`, `transform/`, `obs/` |
| S6 | Constants named, values identical | diff of literals |

## Report format

```text
Verdict: APPROVE | REQUEST CHANGES
Findings (severity low | moderate | high; id from this list; file:line; one-line fix)
ADR check: checked <ADR ids or "none found">; contradictions: none | <list>
Tests: before green | after green | not run (reason)
```

High severity: B1 to B4, Q1 to Q9 failures, P1 contradiction, P2 (a feature, fix or version change mixed into the refactor). Moderate: S1, S4, S5, P3 (no green before/after report), P4 (extracted class without a focused test or moved tests that no longer cover the old behaviour), B5 (test hooks changed without relocating tests), Q10 (mapper or init scope of effect changed), Q11 (private injection members in a native build). Low: S2, S3, S6, naming.
