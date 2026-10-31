---
name: review-stripe-integration
description: "Routes a Stripe Java integration review request to the stripe-advisor read-only advisory agent. Use when reviewing or auditing an existing Stripe Java integration for correctness, security, version alignment, or 33.x→34.x migration gaps (e.g. 'review my webhook handler', 'check this PaymentIntent flow', 'audit billing code for 34.x breaking changes')."
argument-hint: "<scope or question> <project-path> (e.g. 'review webhook handler for signature verification order ./payments-service')"
context: fork
agent: stripe-advisor
disable-model-invocation: true
---

# Review Stripe Integration

## Function

Routes Stripe Java integration review requests to the `stripe-advisor` advisory agent. The agent
reads the four knowledge skills and the family rules, then audits the provided code against the
✅/🚫 patterns and the R01–R07 cross-cutting rules. It states no Stripe facts of its own.

## Pre-flight Checklist (supply before invoking)

The `stripe-advisor` agent is non-interactive. Provide:

1. **Project path** — where the Stripe-related Java files live.
2. **Review scope** — what to focus on: webhook handler, PaymentIntent flow, subscription billing,
   version migration, or all.
3. **Version context** — is the project currently on 33.x, 34.x, or unknown?

## How the Agent Routes to the 4 Knowledge Skills

| Review area | Skill consulted |
|---|---|
| StripeClient construction, idempotency key mechanics, error handling | `developing-stripe-java-core-v34` (always loaded first) |
| PaymentIntent create / confirm / capture / cancel patterns | `processing-stripe-payments-v34` |
| Webhook signature verification, event dedup, async response | `handling-stripe-webhooks-v34` |
| Customer, Subscription, Invoice lifecycle, billing cycle | `managing-stripe-subscriptions-v34` |
| Cross-cutting rules (R01–R07) | [family-rules-v34.md](../integrate-stripe-java/references/family-rules-v34.md) (shipped with `integrate-stripe-java`, same package) |

All skills are under `packages/java/libs/stripe-java/.apm/skills/`.

## Primary Review Checklist (Family Rules R01–R07)

The advisor always evaluates all seven rules:

| Rule | Policy |
|---|---|
| R01 | Idempotency key on every mutating POST |
| R02 | Webhook signature verified BEFORE any side effect |
| R03 | Webhook events deduped on `event.getId()`; 2xx returned before async processing |
| R04 | Stripe-Version pinned and aligned across SDK and webhook endpoint registration |
| R05 | No `Stripe.apiKey = ...` global assignment |
| R06 | No secret keys, `client_secret`, or card data in log statements |
| R07 | No ≤33.x patterns (see family rules for the full banned list) |

## What the Advisor Does NOT Do

- Write or edit any file
- State Stripe facts not in the loaded skills
- Cover Stripe Connect, Terminal, Radar, Tax, Financial Connections (no skills exist)

## Usage Examples

```
/review-stripe-integration "review webhook handler for R02 (signature-before-side-effects)" ./payments-api
/review-stripe-integration "audit PaymentIntent flow for idempotency and 34.x compliance" ./checkout-service
/review-stripe-integration "check subscription billing code for 33.x→34.x Invoice accessor breaking change" ./billing-service
/review-stripe-integration "full security review: secrets in logs, API key handling, webhook trust boundary" ./payments-platform
```

## Evaluation Scenarios

See [./blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).
