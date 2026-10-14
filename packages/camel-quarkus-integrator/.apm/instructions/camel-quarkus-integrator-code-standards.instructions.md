---
name: camel-quarkus-integrator-code-standards
description: "Camel Quarkus 3.40 route code standards: RouteBuilder scope, error handling, logging, testing. Use when editing route classes under integration/routes."
applyTo: "**/integration/routes/**/*.java"
---

# Camel Quarkus route standards (3.40)

Technical facts live in the skills; this rule only states what to check and where to look.
Skills are under `.claude/skills/`. Tags `(unverified)` / `(medium confidence)` in a skill apply here too.
Path-scoped rules load only when a matching file is read: this rule helps on existing layouts. The
new-project flow lives in the package README and the `camel-quarkus-integrator` agent.

## Always

- Route classes live where `structuring-camel-quarkus-projects` says (package, naming, tests).
- Give every route an explicit, unique route id (team convention).
- Rely on automatic RouteBuilder discovery. Add `@ApplicationScoped` only when the class uses
  `@Inject` or `@ConfigProperty` (`developing-camel-quarkus-core-v3-40`).
- Inject collaborators with CDI (`developing-quarkus-arc-v3-40`); for beans called from routes
  see `developing-camel-quarkus-bean-v3-40`.
- Declare error handling deliberately (`onException`, dead letter channel); the tradeoffs
  (`handled`, redelivery) are an Ask-First item in `developing-camel-quarkus-core-v3-40`.
- Log with the Log EIP or `log:`; mask data that may carry secrets or PII
  (`developing-camel-quarkus-log-v3-40`).
- Circuit breaking on outbound HTTP follows `developing-camel-quarkus-http-v3-40`.
- Test routes with `camel-quarkus-junit` and `@QuarkusTest`
  (`developing-camel-quarkus-junit-v3-40`, generic Quarkus testing in `developing-quarkus-junit-v3-40`).

## Ask first

- Error handling policy (should callers see the failure? is the flow async?).
- Retry / circuit breaker parameters.
- CamelContext lifecycle: need to control routes via the Camel API? Quarkus drives the lifecycle
  (core skill, Quick Reference Bootstrap) (medium confidence).
- Anything a loaded skill marks as an Ask-First decision.

## Never

- Add `@ApplicationScoped` to a RouteBuilder that injects nothing: boot-time cost only, no benefit.
- Use `camel-quarkus-resilience4j` (not in 3.40.x) or `camel-quarkus-junit5` / `junit5` imports:
  they do not resolve in 3.40; the skills name the replacements.
- Dump headers or bodies to logs without masking: they may carry secrets or PII.
- Write routes for messaging, databases, Quarkus security or e-mail from memory: no skill covers
  them, so any code would be unguided; flag it to the user.

## Verify

`./mvnw` (or `mvn` when the project has no wrapper): `clean compile`, then `test`. Health, metrics
and dev-UI paths are `(unverified)` in the skills; do not cite them as fact.
