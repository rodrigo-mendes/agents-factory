# Always-Do Patterns — stripe-java 34.0.0 (BILLING)

Sources fetched 2026-10-14.

## 1. Customer Create

```java
StripeClient client = new StripeClient("<<YOUR_SECRET_KEY>>");

CustomerCreateParams params = CustomerCreateParams.builder()
    .setName("Jenny Rosen")             // max 256 chars
    .setEmail("jennyrosen@example.com") // max 512 chars
    .build();

Customer customer = client.v1().customers().create(params);
// Source: https://docs.stripe.com/api/customers/create?lang=java
```

- Builder entry point: `CustomerCreateParams.builder()` — confirmed.
- Setters confirmed: `setName(String)`, `setEmail(String)`.
- `email` max 512 chars; `name` max 256 chars (docs param table).

## 2. Subscription Create

`items` is required; max 20 items per subscription; max 500 subscriptions per customer.

```java
SubscriptionCreateParams params = SubscriptionCreateParams.builder()
    .setCustomer("cus_...")
    .addItem(
        SubscriptionCreateParams.Item.builder()
            .setPrice("price_...")
            .build()
    )
    .build();

Subscription subscription = client.v1().subscriptions().create(params);
// Source: https://docs.stripe.com/api/subscriptions/create?lang=java
```

Object graph prerequisite (from docs): Product (`POST /v1/products`) → Price (`POST /v1/prices`,
`recurring.interval=month`) → Customer → Subscription.

`latest_invoice` on the returned Subscription is a **string ID** by default and must be expanded
to retrieve the Invoice object. Use `.addExpand("latest_invoice")` on the create params if needed.

## 3. Invoice-to-Subscription Accessor Chain (34.x)

In 34.x `Invoice` has **no** `getSubscription()` method. The full accessor chain is:

```java
// Step 1: get the parent — "The parent that generated this invoice"
Invoice.Parent parent = invoice.getParent();
// Source: https://stripe.dev/stripe-java/com/stripe/model/Invoice.html

// Step 2: navigate to subscription details
Invoice.Parent.SubscriptionDetails subscriptionDetails = parent.getSubscriptionDetails();
// Source: https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html

// Step 3a: get subscription ID (string — always available on webhook payload)
String subscriptionId = subscriptionDetails.getSubscription();
// Returns String — "Get ID of expandable subscription object"
// Source: https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html

// Step 3b: get expanded subscription object (only non-null when explicitly expanded)
Subscription subscriptionObject = subscriptionDetails.getSubscriptionObject();
// Source: https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html
```

Additional accessors on `SubscriptionDetails`:
- `getSubscriptionProrationDate()` → `Long`
- `getMetadata()` → `Map<String,String>`

`Invoice.Parent` also exposes `getQuoteDetails()` → `Invoice.Parent.QuoteDetails` for
quote-originated invoices.

## 4. Guard on Parent Type

Always guard on `getType()` before reading subscription details because an invoice parent
may be `"quote_details"` for quote-originated invoices:

```java
// After the webhook unit has verified the signature and produced an Event:
Invoice invoice = (Invoice) event.getDataObjectDeserializer()
    .getObject()
    .orElseThrow();

String subscriptionId = null;
Invoice.Parent parent = invoice.getParent();
if (parent != null && "subscription_details".equals(parent.getType())) {
    subscriptionId = parent.getSubscriptionDetails().getSubscription();
}
// Source: https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html
// Confirmed enum values on getType(): "subscription_details" | "quote_details"
```

Webhook payloads are minimal/unexpanded (see §4 of the research). `getSubscription()` (ID string)
is the reliable read on webhook payloads. Use `getSubscriptionObject()` only when you explicitly
expanded the subscription on a direct API retrieve — it will be null in unexpanded webhook payloads.
