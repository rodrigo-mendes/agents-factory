---
name: integrate-stripe-java
description: "Routes a closed Stripe Java integration requirement to the stripe-integrator executor agent. Use when a fully specified Stripe Java operation (PaymentIntent flow, webhook endpoint, subscription, idempotent calls) must be implemented in a target Java project using stripe-java 34.x."
argument-hint: "<requirement summary> <project-path> (e.g. 'implement PaymentIntent create with idempotency key path/to/project')"
context: fork
agent: stripe-integrator
disable-model-invocation: true
---

# Integrate Stripe Java

## Function

Routes a closed Stripe Java integration requirement to the `stripe-integrator` executor agent.
The agent loads the four knowledge skills listed below, generates code, and verifies compilation
and tests. It does not invent Stripe facts — every claim traces to an official source recorded
in a skill's `## Version Context` block.

## Pre-flight Checklist (supply before invoking)

The `stripe-integrator` agent is non-interactive. Provide all of the following or it will return
questions:

1. **Operation scope** — which Stripe operation(s): PaymentIntent create/confirm/capture/cancel,
   webhook handler, Customer create, Subscription create, or a combination.
2. **Target project path** — absolute or relative path to the Java project root.
3. **Error-handling expectations** — should errors propagate as exceptions, be mapped to HTTP
   status codes, or be swallowed with logging?
4. **Tests wanted** — yes / no (if yes, unit or integration).
5. **Maven or wrapper** — does the project use `./mvnw` or plain `mvn`?

## How the Agent Routes to the 4 Knowledge Skills

| Requirement involves | Skill loaded |
|---|---|
| StripeClient setup, idempotency keys, error handling, API-version | `developing-stripe-java-core-v34` (always loaded first) |
| PaymentIntent flows (create / confirm / capture / cancel) | `processing-stripe-payments-v34` |
| Webhook endpoints (signature verification, event dedup, async response) | `handling-stripe-webhooks-v34` |
| Customer, Subscription, Invoice lifecycle | `managing-stripe-subscriptions-v34` |
| Cross-cutting policies (idempotency on all POSTs, secret logging, version pinning) | [references/family-rules-v34.md](references/family-rules-v34.md) (R01–R07) |

All skills are under `packages/java/libs/stripe-java/.apm/skills/`.

## Coverage and Gaps

**Covered:** PaymentIntent lifecycle, webhook handling, Customer/Subscription/Invoice lifecycle,
idempotent retry patterns, StripeClient construction, API-version alignment, 33.x→34.x migration.

**Not covered:** Stripe Connect (marketplace), Terminal (in-person), Radar (fraud rules API), Link
(one-click checkout), Tax, Financial Connections, Identity. The agent will return a limitation
when any of these is needed.

## Usage Examples

```
/integrate-stripe-java "implement PaymentIntent create endpoint with UUID idempotency key and compile" ./my-java-api
/integrate-stripe-java "add webhook handler that verifies signature, dedupes on event ID, and returns 200 OK" ./payments-service
/integrate-stripe-java "create Customer and Subscription with monthly Price, include unit tests" ./billing-service
/integrate-stripe-java "migrate Stripe integration from 33.x to 34.x breaking changes" ./legacy-payments
```

## Evaluation Scenarios

See [./blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).
