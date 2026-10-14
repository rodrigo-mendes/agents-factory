# Evaluation Scenarios — developing-stripe-java-core-v34

Three or more scenarios required for a hybrid knowledge skill (canonical, edge, misuse).
Each scenario uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Create StripeClient and make an idempotent POST call

```json
{
  "skills": ["developing-stripe-java-core-v34"],
  "query": "Show me how to create a StripeClient and make an idempotent API call in Java using stripe-java 34.",
  "success_criteria": {
    "must_pass": [
      "Uses the StripeClient constructor or builder",
      "Creates RequestOptions with setIdempotencyKey using UUID.randomUUID().toString()",
      "Keeps the idempotency key within the 255-character limit",
      "Accesses resources via the client.v1() namespace",
      "Catches StripeException or a named subtype",
      "Uses the correct Javadoc casing ApiException"
    ],
    "must_not": [
      "Uses the Stripe.apiKey global assignment",
      "Uses the casing APIException or APIConnectionException"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Configuring retries and timeouts

```json
{
  "skills": ["developing-stripe-java-core-v34"],
  "query": "How do I configure automatic retries and custom timeouts for StripeClient in stripe-java 34?",
  "success_criteria": {
    "must_pass": [
      "States that StripeClient defaults to 0 retries and does not inherit legacy global retry settings",
      "Shows setMaxNetworkRetries(n) on StripeClient.builder()",
      "Shows setConnectTimeout and setReadTimeout with millisecond units",
      "Mentions that the SDK auto-generates idempotency keys for retries"
    ],
    "must_not": [
      "Claims retries are enabled by default"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Deprecated global Stripe.apiKey pattern

```json
{
  "skills": ["developing-stripe-java-core-v34"],
  "query": "Is it fine to do Stripe.apiKey = 'sk_test_...' in a new stripe-java 34 project?",
  "success_criteria": {
    "must_pass": [
      "Explicitly rejects the Stripe.apiKey global assignment as the pre-v23 deprecated pattern",
      "Provides the StripeClient constructor or builder as the correct alternative",
      "Notes that removal-vs-deprecation of the field in 34.0.0 is (unverified)"
    ],
    "must_not": [
      "Silently permits the global assignment pattern",
      "Asserts the field is definitely removed or definitely retained without the unverified hedge"
    ]
  }
}
```

---

## Scenario 4 — Anti-pattern Trap: Wrong exception class names from docs

```json
{
  "skills": ["developing-stripe-java-core-v34"],
  "query": "Write a try-catch for APIException and APIConnectionException from the Stripe SDK.",
  "success_criteria": {
    "must_pass": [
      "Corrects the class names to ApiException and ApiConnectionException (Javadoc casing)",
      "Explains that docs.stripe.com prose renders the names incorrectly",
      "Cites stripe.dev/stripe-java Javadoc as authoritative for class casing"
    ],
    "must_not": [
      "Emits code using APIException or APIConnectionException outside a WRONG-annotated block"
    ]
  }
}
```
