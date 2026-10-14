# Never-Do Patterns — stripe-java 34.0.0 (BILLING)

Sources fetched 2026-10-14.

## 1. invoice.getSubscription() — 33.x Pattern Removed in 34.x

The ≤33.x top-level `Invoice.getSubscription()` does **not** exist in 34.x. Any code calling it
is misinformation for 34.x and will fail to compile against the 34.0.0 SDK.

```java
// WRONG — invoice.getSubscription() does NOT exist in stripe-java 34.x
String subscriptionId = invoice.getSubscription(); // compile error in 34.x
// Source confirming absence: https://stripe.dev/stripe-java/com/stripe/model/Invoice.html
// No method whose name contains "Subscription" is present in the Invoice Method Summary.

// CORRECT — use the 34.x parent accessor chain, guarded on type:
Invoice.Parent parent = invoice.getParent();
if (parent != null && "subscription_details".equals(parent.getType())) {
    String subscriptionId = parent.getSubscriptionDetails().getSubscription();
}
// Sources:
//   https://stripe.dev/stripe-java/com/stripe/model/Invoice.html
//   https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html
//   https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html
```

## 2. Subscription Create Without Items

```java
// WRONG — items is required; this will fail with a 400 InvalidRequestException
SubscriptionCreateParams params = SubscriptionCreateParams.builder()
    .setCustomer("cus_...")
    .build(); // missing addItem() → API error
// Source: https://docs.stripe.com/api/subscriptions/create?lang=java ("items" required)

// CORRECT — at least one item with a valid Price ID
SubscriptionCreateParams params = SubscriptionCreateParams.builder()
    .setCustomer("cus_...")
    .addItem(
        SubscriptionCreateParams.Item.builder()
            .setPrice("price_...")
            .build()
    )
    .build();
```

## 3. Old billingCycleAnchor Enum on Update / Resume / Invoice Preview

The `billingCycleAnchor` type changed in 34.0.0 for three param classes (CHANGELOG PR #2292).
The `now` / `unchanged` enum variants no longer exist on these classes.

```java
// WRONG — passing the 33.x enum literal to SubscriptionUpdateParams (type changed in 34.0.0)
SubscriptionUpdateParams params = SubscriptionUpdateParams.builder()
    .setBillingCycleAnchor(SubscriptionUpdateParams.BillingCycleAnchor.NOW) // removed in 34.x
    .build();
// Source: https://raw.githubusercontent.com/stripe/stripe-java/master/CHANGELOG.md (PR #2292)

// Affected param classes (must all migrate):
// - SubscriptionUpdateParams.billingCycleAnchor  → billing_cycle_anchor_param
// - SubscriptionResumeParams.billingCycleAnchor  → billing_cycle_anchor_param
// - InvoiceCreatePreviewParams.subscription_details.billingCycleAnchor → billing_cycle_anchor_param

// NOT affected (unchanged — still accepts a timestamp):
// - SubscriptionCreateParams.billing_cycle_anchor (future UTC timestamp)
// Source: https://docs.stripe.com/api/subscriptions/create?lang=java

// CORRECT — consult the 34.x Javadoc for the exact billing_cycle_anchor_param builder method
// and migrate update/resume/preview calls accordingly.
```

## 4. Expecting Auto-Expanded Objects in Webhook Payloads

```java
// WRONG — expecting getSubscriptionObject() to be non-null in a webhook payload
Invoice invoice = (Invoice) event.getDataObjectDeserializer().getObject().orElseThrow();
Subscription sub = invoice.getParent().getSubscriptionDetails().getSubscriptionObject();
// getSubscriptionObject() returns null in webhook payloads — webhooks are never auto-expanded.
// Source: https://docs.stripe.com/expand?lang=java — "webhooks are never auto-expanded"

// CORRECT — use the string ID from the webhook, then retrieve and expand if needed:
String subscriptionId = invoice.getParent().getSubscriptionDetails().getSubscription();

SubscriptionRetrieveParams retrieveParams = SubscriptionRetrieveParams.builder()
    .addExpand("latest_invoice")
    .build();
Subscription sub = client.v1().subscriptions().retrieve(subscriptionId, retrieveParams);
```
