# Evaluation Scenarios — managing-stripe-subscriptions-v34

Three or more scenarios required for a hybrid knowledge skill (canonical, edge, misuse).
Each scenario uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Create Customer and Subscription

```json
{
  "skills": ["managing-stripe-subscriptions-v34"],
  "query": "Show me how to create a Stripe customer and a monthly subscription for them in Java using stripe-java 34.",
  "success_criteria": {
    "must_pass": [
      "Uses client.v1().customers().create(CustomerCreateParams) for customer creation",
      "Uses client.v1().subscriptions().create(SubscriptionCreateParams) for subscription creation",
      "Calls addItem with SubscriptionCreateParams.Item.builder().setPrice(...) on the subscription params",
      "Does NOT use legacy static Customer.create() or Subscription.create() patterns"
    ],
    "must_not": [
      "Uses Customer.create(...) or Subscription.create(...) static methods",
      "Creates a subscription without any addItem call"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Retrieve Subscription ID from invoice.paid Webhook (34.x)

```json
{
  "skills": ["managing-stripe-subscriptions-v34"],
  "query": "In an invoice.paid webhook handler using stripe-java 34, how do I get the subscription ID from the Invoice object?",
  "success_criteria": {
    "must_pass": [
      "Uses invoice.getParent() to get Invoice.Parent",
      "Guards on parent.getType().equals(\"subscription_details\") before reading subscription details",
      "Calls getSubscriptionDetails().getSubscription() to get the String subscription ID",
      "Notes that webhook payloads are not auto-expanded so getSubscriptionObject() will be null",
      "Does NOT call invoice.getSubscription() which does not exist in 34.x"
    ],
    "must_not": [
      "Calls invoice.getSubscription() as a top-level method on Invoice",
      "Skips the getType() guard, which would NPE on quote-originated invoices"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: 33.x Invoice.getSubscription() Pattern

```json
{
  "skills": ["managing-stripe-subscriptions-v34"],
  "query": "I have code that calls invoice.getSubscription() from my 33.x integration. Does this still work in stripe-java 34?",
  "success_criteria": {
    "must_pass": [
      "Explicitly states that invoice.getSubscription() does NOT exist in stripe-java 34.x",
      "Identifies it as the 33.x pattern that is misinformation for 34.x targets",
      "Provides the correct 34.x chain: invoice.getParent().getSubscriptionDetails().getSubscription()",
      "Cites the Invoice Javadoc (stripe.dev) confirming absence of the method in 34.x"
    ],
    "must_not": [
      "Suggests that invoice.getSubscription() still works in 34.x",
      "Provides the 33.x accessor without flagging it as removed in 34.x"
    ]
  }
}
```

---

## Scenario 4 — Anti-pattern Trap: billingCycleAnchor Migration

```json
{
  "skills": ["managing-stripe-subscriptions-v34"],
  "query": "I'm migrating from stripe-java 33 to 34. My code uses SubscriptionUpdateParams.BillingCycleAnchor.NOW. Do I need to change anything?",
  "success_criteria": {
    "must_pass": [
      "Confirms that the billingCycleAnchor type on SubscriptionUpdateParams changed in 34.0.0",
      "States the change is from enum('now'|'unchanged') to billing_cycle_anchor_param",
      "Mentions that SubscriptionResumeParams and InvoiceCreatePreviewParams.subscription_details are also affected",
      "Notes that SubscriptionCreateParams.billing_cycle_anchor (timestamp) is unchanged",
      "Cites CHANGELOG 34.0.0 PR #2292 as the source"
    ],
    "must_not": [
      "Claims SubscriptionUpdateParams.BillingCycleAnchor.NOW still works unchanged in 34.x",
      "Applies the same breaking change to SubscriptionCreateParams (it is not affected)"
    ]
  }
}
```
