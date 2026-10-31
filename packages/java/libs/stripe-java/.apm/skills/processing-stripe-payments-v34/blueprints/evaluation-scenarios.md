# Evaluation Scenarios — processing-stripe-payments-v34

Three or more scenarios required for a hybrid knowledge skill (canonical, edge, misuse).
Each scenario uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Create a PaymentIntent with automatic payment methods

```json
{
  "skills": ["processing-stripe-payments-v34"],
  "query": "Show me how to create a PaymentIntent in Java using stripe-java 34 with automatic payment methods.",
  "success_criteria": {
    "must_pass": [
      "Uses client.v1().paymentIntents().create(params) service accessor",
      "Sets amount as a Long in minor units (e.g. 2000L for $20.00)",
      "Sets currency as a lowercase ISO-4217 string",
      "Uses AutomaticPaymentMethods.builder().setEnabled(true)",
      "Mentions returning client_secret to the client SDK for payment completion",
      "Mentions sending an idempotency key or cross-references developing-stripe-java-core-v34"
    ],
    "must_not": [
      "Uses legacy static PaymentIntent.create(...) style",
      "Derives amount from an untrusted client-supplied value",
      "Uses setPaymentMethodTypes which was removed in 34.0.0"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Manual capture flow with expiry risk

```json
{
  "skills": ["processing-stripe-payments-v34"],
  "query": "How do I implement a separate authorization and capture flow with stripe-java 34?",
  "success_criteria": {
    "must_pass": [
      "Identifies capture_method = manual as the key parameter to enable separate auth/capture",
      "States that uncaptured intents auto-cancel after 7 days by default",
      "Shows client.v1().paymentIntents().capture(id, params) for the capture step",
      "Recommends planning a capture job before the 7-day auto-cancel window",
      "Tags .setCaptureMethod(...) as medium confidence requiring Javadoc verification"
    ],
    "must_not": [
      "Presents .setCaptureMethod(...) as a plainly callable high-confidence accessor without a verification note",
      "Omits the 7-day auto-cancel risk"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Using removed `paymentMethodTypes`

```json
{
  "skills": ["processing-stripe-payments-v34"],
  "query": "Can I use setPaymentMethodTypes(List.of(\"card\")) on PaymentIntentCreateParams in stripe-java 34?",
  "success_criteria": {
    "must_pass": [
      "Explicitly rejects setPaymentMethodTypes as removed in 34.0.0",
      "Cites the stripe-java CHANGELOG as the authoritative source",
      "States this causes a compile error in 34.x",
      "Provides the correct alternative: automatic_payment_methods or allowed_payment_method_types"
    ],
    "must_not": [
      "Suggests setPaymentMethodTypes as a valid option in stripe-java 34.x",
      "Fails to mention the compile-time error consequence"
    ]
  }
}
```

---

## Scenario 4 — Anti-pattern Trap: Presenting medium-confidence accessors as high-confidence

```json
{
  "skills": ["processing-stripe-payments-v34"],
  "query": "Write code to create a PaymentIntent with confirm=true, customer set, and capture_method=manual in stripe-java 34.",
  "success_criteria": {
    "must_pass": [
      "Tags .setConfirm(true), .setCustomer(...), and .setCaptureMethod(...) as medium confidence",
      "Includes a comment or note instructing verification against the 34.0.0 Javadoc before use",
      "Shows .setAmount(2000L) and .setCurrency(\"usd\") as high-confidence verified accessors",
      "References stripe.dev/stripe-java/ as the verification target for accessor names"
    ],
    "must_not": [
      "Presents .setConfirm(true), .setCustomer(...), or .setCaptureMethod(...) as plainly callable code without a medium-confidence verification note"
    ]
  }
}
```
