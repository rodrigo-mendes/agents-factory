# Never-Do Patterns — stripe-java 34.0.0 (PAYMENTS)

Sources fetched 2026-10-14.

## 1. Using Removed `paymentMethodTypes` Parameter

`paymentMethodTypes` is **removed** from `PaymentIntentCreateParams`, `PaymentIntentConfirmParams`,
`PaymentIntentUpdateParams`, `SetupIntentCreateParams`, `SetupIntentUpdateParams`, and
`checkout.SessionCreateParams` in 34.0.0 — surfaces as a compile error.

```java
// WRONG — removed in 34.0.0; will not compile
PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
    .setAmount(2000L)
    .setCurrency("usd")
    .setPaymentMethodTypes(List.of("card"))  // ← compile error in 34.x
    .build();
// Source: https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md

// CORRECT — use automatic_payment_methods (recommended default)
PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
    .setAmount(2000L)
    .setCurrency("usd")
    .setAutomaticPaymentMethods(
        PaymentIntentCreateParams.AutomaticPaymentMethods.builder()
            .setEnabled(true)
            .build()
    )
    .build();
// Or: set allowed_payment_method_types / excluded_payment_method_types on the create/confirm params.
// Source: https://docs.stripe.com/api/payment_intents/create?lang=java
```

## 2. BLIK `setupFutureUsage` as a String Literal

In 34.0.0, `PaymentIntent.payment_method_options.blik.setupFutureUsage` and the corresponding
`PaymentIntentConfirmParams…blik.setupFutureUsage` changed from a string literal to an enum.

```java
// WRONG — string literal "none" no longer compiles in 34.x for BLIK options
// .setSetupFutureUsage("none")  ← type error in 34.x
// Source: https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md

// CORRECT — use the generated enum constant
// Exact enum class path: verify in 34.0.0 Javadoc — https://stripe.dev/stripe-java/
// Example form (verify constant name before use):
// .setSetupFutureUsage(BlikOptions.SetupFutureUsage.NONE)
```

## 3. Trusting a Client-Supplied Amount

```java
// WRONG — deriving amount from an untrusted client request
long amount = Long.parseLong(request.getParameter("amount")); // ← never trust client input
PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
    .setAmount(amount)
    .build();
// Source: https://docs.stripe.com/api/payment_intents/create?lang=java

// CORRECT — compute server-side from a trusted product/price catalog
long amount = priceService.getAmountInMinorUnits(productId, currency);
PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
    .setAmount(amount)
    .setCurrency(currency)
    .build();
```

## 4. Exposing `client_secret` Beyond the Checkout Session

```java
// WRONG — logging or broadcasting client_secret
log.info("Created PI: " + paymentIntent.getClientSecret()); // ← leaks the secret
System.out.println(paymentIntent.getClientSecret());         // ← leaks the secret
// Source: https://docs.stripe.com/api/payment_intents/confirm?lang=java

// CORRECT — send client_secret only to the specific client session over TLS
return Map.of("clientSecret", paymentIntent.getClientSecret());
// Scoped to one PaymentIntent; do not store, cache, or log it.
```

## 5. Using the Legacy Static `PaymentIntent.create(...)` API

The static style belongs to the pre-StripeClient model and is not shown in 34.x official samples.

```java
// WRONG — legacy static style; not recommended for 34.x new code
// PaymentIntent pi = PaymentIntent.create(params);

// CORRECT — use the StripeClient service graph
PaymentIntent pi = client.v1().paymentIntents().create(params);
// Source: https://docs.stripe.com/api/payment_intents/create?lang=java
```
