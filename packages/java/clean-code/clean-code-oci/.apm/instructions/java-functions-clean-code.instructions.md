---
name: java-functions-clean-code
description: "SOLID, Extract Method, and readability rules for OCI Functions Java. Use when refactoring handler or service classes for maintainability."
paths:
  - "**/src/main/java/**/*.java"
  - "**/pom.xml"
  - "**/func.yaml"
  - "**/Dockerfile"
---

You are an OCI Functions Java Clean Code specialist.
Ensure all generated and edited Java favors small, single-responsibility methods, SOLID structure, and
intent-revealing readability — without changing behavior or breaking public/test contracts.

For a guided, step-by-step refactor with before/after examples, load the skill: `.claude/skills/refactoring-oci-java/SKILL.md`

## When These Rules Apply

Every time you write a new class/method OR edit an existing one in `src/main/java`. These are
cross-cutting: they compose with the FDK, API Gateway, error-handling, and observability rules — the
most restrictive guidance wins on conflict.

## Small Methods, One Responsibility

- A method should do one thing and read as a sequence of named steps. Target ~≤ 40 lines; if longer,
  extract sub-steps into private methods with intent-revealing names.
- One public entry method per class (e.g. the handler); everything else is a private helper below it.
- Prefer early returns/guard clauses over deep nesting. Max ~2 levels of nesting inside a method.

## Extract Method — Triggers

Extract a private method whenever you see:
- A comment that titles a block (`// 1. validate body`) → the comment becomes the method name.
- Repeated try/catch scaffolding around a call (span open/close, timing) → one helper
  (e.g. a `TracedCall.run(name, peer, callable)` wrapper) instead of copy-paste at each call site.
- A `switch`/`if-else` chain classifying by magic-string or status → a dedicated method or class
  (e.g. an `ErrorMapper` turning exceptions into responses).
- Object/response construction repeated with small variations → a factory method
  (e.g. a `ResponseFactory.ok/error(...)`).

## SRP — Decompose by Package

The handler orchestrates and delegates; business logic lives in collaborators. Use this taxonomy
(handler class stays at the package root, never inside a sub-package):
- `route/` — request → route resolution
- `transform/` — map/marshal (JSON ↔ model ↔ XML)
- `web/` — response building and error → HTTP mapping
- `handler/` — one class per use-case flow (e.g. store proxy, item webhook)
- `client/` — external I/O (REST/SDK), with retry/token concerns isolated
- `obs/` — observability (logging bridge, metrics, tracing)

## DRY

- Logic duplicated in ≥ 2 places (e.g. an HTTP send-with-retry loop) → extract a shared, parameterized
  executor/strategy. When collapsing duplication, preserve exact exception types and messages —
  downstream error mapping and tests depend on them.

## Records as Value Holders

- Group correlated parameters/state (config read from `RuntimeContext`, credentials, per-request
  context) into a small private `record` instead of a sprawl of local variables or long parameter lists.

## Facade over Statics

- When a static utility accumulates multiple concerns, keep the public static API (call sites and tests
  stay green) and delegate internally to focused collaborators (e.g. `ObservabilityHelper` →
  `LoggingBridge` + `MetricsPublisher` + `TracingSupport`).

## Naming & Constants

- Names reveal intent (`resolveStoreId`, `forwardItem`, `recordTelemetry`), not mechanics.
- Replace magic numbers/strings with named constants (`REFRESH_SKEW_SECONDS`, `API_VERSION`).

## Behavior-Preserving Refactor (MANDATORY)

- Readability changes must not alter semantics: same outputs, status codes, log texts, and side-effect
  order. Prove parity by running tests after each step (see `java-functions-testing.md`).
- Relocate unit tests to the class that now owns the logic (e.g. mapping tests → the mapper's test);
  keep the public/handler/test-constructor signatures intact so existing suites still compile and pass.

## ✅ Always Do
- Keep methods small and single-purpose; extract named steps from long methods.
- Turn block-titling comments into methods; collapse repeated scaffolding into one helper.
- Delegate business logic out of the handler into `transform/`, `web/`, `handler/`, `client/`, `obs/`.
- Extract duplicated logic once, preserving exact exception types/messages.
- Group correlated values into private `record`s; name constants instead of magic values.
- Run tests after each extraction to prove identical behavior.

## 🚫 Never Do
- Grow a god method/class — no 100-line handlers doing routing + mapping + I/O + error handling.
- Copy-paste retry/span/response scaffolding across call sites.
- Change public method signatures or the package-private test constructor during a readability refactor.
- Alter log texts, status codes, or side-effect ordering while "just cleaning up".
- Over-engineer: no speculative interfaces/abstractions or single-use indirection without a real gain.
