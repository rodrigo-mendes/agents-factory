# stripe-java

APM package for Stripe Java SDK (`com.stripe:stripe-java`) integrations — version **34.x**.

Contains four hybrid knowledge skills, two agents (executor + advisor), one instructions file
covering Java source and Maven POM files, and a family rules seed for cross-cutting policies.

---

## Skills

| Skill | Scope |
|---|---|
| `developing-stripe-java-core-v34` | StripeClient, API-version pinning, idempotency keys, error handling, retries/timeouts — stripe-java 34.0.0 |
| `processing-stripe-payments-v34` | PaymentIntent create / confirm / capture / cancel, automatic payment methods, amounts in minor units |
| `handling-stripe-webhooks-v34` | Signature verification, raw-body handling, event deserialization, dedup, async response, thin-event handler |
| `managing-stripe-subscriptions-v34` | Customers, Prices, Subscriptions, Invoice lifecycle, 33→34 billing migration |

All skills target stripe-java **34.0.0** (current stable, research date 2026-10-14).
≤33.x patterns are treated as superseded. See each skill's "33 to 34 Migration" section.

---

## Agents

| Agent | Role | Tools |
|---|---|---|
| `stripe-integrator` | Non-interactive executor — implements a closed Stripe Java integration (PaymentIntent, webhook, subscription), verifies with `mvn compile`/`mvn test` | Read, Grep, Glob, Edit, Write, Bash |
| `stripe-advisor` | Read-only advisor — reviews and audits a Stripe Java integration against the four skills and the R01–R07 family rules | Read, Grep, Glob |

---

## Instructions

| File | Scope |
|---|---|
| `stripe-java-code-standards.instructions.md` | Java source files (`**/*.java`) and Maven POMs (`**/pom.xml`) — R01–R07 family rules enforcement |

---

## Family Rules Seed

`workspace/stripe-java/_family_rules_v34.md` — 7 numbered testable policies spanning ≥2 skills:

| Rule | Policy |
|---|---|
| R01 | Idempotency key on every mutating POST |
| R02 | Verify webhook signature BEFORE any side effect |
| R03 | Dedupe webhook events on `event.getId()`; return 2xx before async processing |
| R04 | Pin and align Stripe-Version across SDK and webhook endpoint |
| R05 | Never use `Stripe.apiKey` global |
| R06 | Never log secret keys, `client_secret`, or card data |
| R07 | Treat ≤33.x patterns as superseded |

---

## Example Usage

### Run the integrator agent

```
/integrate-stripe-java "implement PaymentIntent create POST endpoint with UUID idempotency key, compile and unit test" ./my-java-api
/integrate-stripe-java "add webhook handler: verify signature first, dedupe on event ID, return 200 OK" ./payments-service
/integrate-stripe-java "create Customer and monthly Subscription, include tests" ./billing-service
/integrate-stripe-java "migrate stripe-java 33.x billing code to 34.x — fix Invoice accessor breaking change" ./legacy-payments
```

### Run the advisor agent

```
/review-stripe-integration "review webhook handler for R02 compliance" ./payments-api
/review-stripe-integration "audit PaymentIntent flow for idempotency and 34.x compliance" ./checkout-service
/review-stripe-integration "check subscription billing code for 33.x→34.x Invoice accessor breaking change" ./billing-service
/review-stripe-integration "full security review: secrets in logs, API key handling, webhook trust boundary" ./payments-platform
```

### Load a skill directly (knowledge mode)

Claude auto-invokes the knowledge skills when the trigger is matched:
- "How do I set up StripeClient in Java 34.x?" → `developing-stripe-java-core-v34`
- "What are the breaking changes in stripe-java 34.0.0 for payments?" → `processing-stripe-payments-v34`
- "How do I verify a Stripe webhook signature in Java?" → `handling-stripe-webhooks-v34`
- "How do I traverse the Invoice→Subscription chain in 34.x?" → `managing-stripe-subscriptions-v34`

---

## Out of Scope

No skills exist for: Stripe Connect (marketplace/multi-party), Terminal (in-person payments),
Radar (fraud rules API), Link (one-click checkout), Tax, Financial Connections, Identity.
Both agents return a limitation when these areas are requested.
