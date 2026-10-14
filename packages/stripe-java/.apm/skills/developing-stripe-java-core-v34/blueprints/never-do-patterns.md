# Never-Do Patterns — stripe-java 34.0.0 (CORE)

Sources fetched 2026-10-14.

## 1. Global Stripe.apiKey Assignment

The pre-v23 global static approach is not documented for new code in 34.0.0.
Whether `Stripe.apiKey` is removed or merely deprecated is (unverified) — not
individually confirmed against the 34.0.0 Javadoc. Treat it as off-limits for new code.

```java
// WRONG — pre-v23 global pattern; README does not document it for new code
Stripe.apiKey = "sk_test_...";
// Source: https://github.com/stripe/stripe-java/blob/master/README.md (checked 2026-10-14)

// CORRECT — constructor or builder
StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));
// or
StripeClient client = StripeClient.builder()
    .setApiKey(System.getenv("STRIPE_SECRET_KEY"))
    .build();
```

## 2. Idempotency Key Exceeding 255 Characters

```java
// WRONG — composite key that could silently exceed 255 chars
String key = "order-" + orderId + "-" + userId + "-" + System.currentTimeMillis() + "-extra";

// CORRECT — UUID v4 is always 36 chars, well within the limit
String key = UUID.randomUUID().toString();
// Source: https://docs.stripe.com/api/idempotent_requests?lang=java
```

## 3. Wrong Exception Class Names

docs.stripe.com prose renders `ApiException` as `APIException` and `ApiConnectionException`
as `APIConnectionException`. The Javadoc is authoritative.

```java
// WRONG — docs.stripe.com prose names; will not compile against 34.0.0 classes
} catch (APIException e) { }
} catch (APIConnectionException e) { }

// CORRECT — Javadoc names for stripe-java 34.0.0
} catch (ApiException e) { }           // Stripe server-side error
} catch (ApiConnectionException e) { } // Network error
// Source: https://stripe.dev/stripe-java/com/stripe/exception/package-summary.html
```

## 4. Stripe-Version Override Without Testing SDK Compatibility

```java
// WRONG — overriding the default API version without verifying deserialization
RequestOptions opts = RequestOptions.builder()
    .<stripeVersionSetter_VERIFY_IN_JAVADOC>("2024-09-30.acacia") // METHOD NAME UNVERIFIED (M1) — confirm the real 34.0.0 setter in the Javadoc; older-version shapes differ
    .build();
// Risk: response/param shapes for the older version may not match 34.x SDK models,
// causing silent deserialization errors or missing fields.

// CORRECT — rely on SDK default (2026-09-30.endive) unless you have verified alignment
RequestOptions opts = RequestOptions.builder()
    .setIdempotencyKey(UUID.randomUUID().toString())
    .build();
```
