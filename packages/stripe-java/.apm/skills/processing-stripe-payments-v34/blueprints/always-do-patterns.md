# Always-Do Patterns — stripe-java 34.0.0 (PAYMENTS)

Sources fetched 2026-10-14.

## 1. Service Accessor

All PaymentIntent operations go through `client.v1().paymentIntents()`. The `StripeClient` instance is constructed by the core/client unit (`developing-stripe-java-core-v34`) — consume it here, do not re-derive construction.

```java
// Inject or obtain a pre-configured StripeClient from the core unit.
// See developing-stripe-java-core-v34/blueprints/always-do-patterns.md#1-stripeclient-instantiation

import com.stripe.StripeClient;
import com.stripe.model.PaymentIntent;
import com.stripe.param.PaymentIntentCreateParams;
import com.stripe.param.PaymentIntentConfirmParams;
import com.stripe.param.PaymentIntentCaptureParams;
import com.stripe.param.PaymentIntentCancelParams;

// All four operations via the service graph:
// client.v1().paymentIntents().create(params)
// client.v1().paymentIntents().confirm(id, params)
// client.v1().paymentIntents().capture(id, params)
// client.v1().paymentIntents().cancel(id, params)
// Source: https://docs.stripe.com/api/payment_intents/create?lang=java
```

The legacy static `PaymentIntent.create(params)` belongs to the pre-StripeClient model; use the `client.v1()` service graph instead.

## 2. Amount in Minor Units

`amount` is a **required** `Long` in the smallest currency unit.
- `2000L` = $20.00 USD; `100L` = ¥100 (zero-decimal). Never pass a decimal (e.g. `20.00`).
- Minimum: $0.50 US equivalent. Maximum: 8 digits (`99999999`).
- Compute server-side — never use a client-supplied total.

```java
// HIGH confidence — from official Java sample
// Source: https://docs.stripe.com/api/payment_intents/create?lang=java
PaymentIntentCreateParams params =
  PaymentIntentCreateParams.builder()
    .setAmount(2000L)      // $20.00 USD — minor units
    .setCurrency("usd")   // lowercase ISO-4217
    .build();
```

Sources: [create](https://docs.stripe.com/api/payment_intents/create?lang=java), [currencies/zero-decimal](https://docs.stripe.com/currencies#zero-decimal).

## 3. Automatic Payment Methods (Recommended Default)

```java
// HIGH confidence — verbatim from official Java sample
// Source: https://docs.stripe.com/api/payment_intents/create?lang=java
PaymentIntentCreateParams params =
  PaymentIntentCreateParams.builder()
    .setAmount(2000L)
    .setCurrency("usd")
    .setAutomaticPaymentMethods(
      PaymentIntentCreateParams.AutomaticPaymentMethods.builder()
        .setEnabled(true)
        .build()
    )
    .build();

PaymentIntent paymentIntent = client.v1().paymentIntents().create(params);
// Send paymentIntent.getClientSecret() to the client SDK via TLS to complete payment.
// Do NOT log or expose client_secret beyond this checkout session.
```

- `automatic_payment_methods.enabled = true`: accepts Dashboard-enabled payment methods compatible with the intent.
- For `confirmation_method = automatic` (default), payment completes client-side via `client_secret` without a server re-confirm.

## 4. Confirm a PaymentIntent

```java
// HIGH confidence — verbatim from official Java sample
// Source: https://docs.stripe.com/api/payment_intents/confirm?lang=java
PaymentIntentConfirmParams params =
  PaymentIntentConfirmParams.builder()
    .setPaymentMethod("pm_card_visa")
    .setReturnUrl("https://www.example.com")
    .build();

PaymentIntent paymentIntent =
  client.v1().paymentIntents().confirm("pi_...", params);
```

Status transitions after confirm:
- Needs further auth → `requires_action` (inspect `next_action`).
- Payment failure → `requires_payment_method` (or `canceled` if the confirm limit is reached).
- Success → `succeeded`, or `requires_capture` when `capture_method = manual`.

## 5. Capture a PaymentIntent

```java
// HIGH confidence — verbatim from official Java sample
// Source: https://docs.stripe.com/api/payment_intents/capture?lang=java
PaymentIntentCaptureParams params = PaymentIntentCaptureParams.builder().build();
PaymentIntent paymentIntent =
  client.v1().paymentIntents().capture("pi_...", params);
```

- Capture is valid only when `status = requires_capture`.
- Optional `amount_to_capture`: must be ≤ original `amount`; defaults to full `amount_capturable`.
  Accessor: `.setAmountToCapture(...)` // (medium confidence — verify in 34.0.0 Javadoc)
- Optional `final_capture`: boolean, default `true`; `false` enables multicapture (availability-gated).
  Accessor: `.setFinalCapture(false)` // (medium confidence — verify in 34.0.0 Javadoc)
- Uncaptured intents auto-cancel after **7 days** by default.

## 6. Cancel a PaymentIntent

```java
// HIGH confidence — verbatim from official Java sample
// Source: https://docs.stripe.com/api/payment_intents/cancel?lang=java
PaymentIntentCancelParams params = PaymentIntentCancelParams.builder().build();
PaymentIntent paymentIntent =
  client.v1().paymentIntents().cancel("pi_...", params);
```

- Cancelable statuses: `requires_payment_method`, `requires_capture`, `requires_confirmation`,
  `requires_action`, `processing`.
- On cancel of `requires_capture`: remaining `amount_capturable` is automatically refunded.
- Optional `cancellation_reason` string values: `duplicate`, `fraudulent`,
  `requested_by_customer`, `abandoned`.

## 7. Idempotency Keys (Cross-Reference)

Apply `RequestOptions` with an idempotency key on every create/confirm/capture/cancel call.
The ≤255-char rule and `RequestOptions` mechanics are **owned by `developing-stripe-java-core-v34`** — do not re-derive them here.

```java
// See developing-stripe-java-core-v34/blueprints/always-do-patterns.md#2-idempotency-keys
// for the full RequestOptions + UUID pattern.
PaymentIntent pi = client.v1().paymentIntents().create(params, requestOptions);
```

Source (cross-ref only): [Idempotent requests](https://docs.stripe.com/api/idempotent_requests).
