# Always-Do Patterns — stripe-java 34.0.0 (CORE)

Sources fetched 2026-10-14.

## 1. StripeClient Instantiation

Use the constructor for a single key or the builder for global options. Both are documented.

```java
// Minimal — constructor
import com.stripe.StripeClient;
StripeClient client = new StripeClient("sk_test_...");
// Source: https://docs.stripe.com/get-started/development-environment?lang=java

// Builder — recommended for production (global options)
StripeClient client = StripeClient.builder()
    .setApiKey(System.getenv("STRIPE_SECRET_KEY"))
    .setMaxNetworkRetries(2)
    .setConnectTimeout(30 * 1000)  // milliseconds
    .setReadTimeout(80 * 1000)     // milliseconds
    .build();
// Source: https://docs.stripe.com/error-low-level?lang=java + README.md
```

Resource access is namespaced under `client.v1()`:

```java
// Source: https://docs.stripe.com/get-started/development-environment?lang=java
stripeClient.v1().products().create(params);
stripeClient.v1().customers().retrieve("cus_123", requestOptions);
```

## 2. Idempotency Keys

Pass `RequestOptions` as the last argument of every mutating POST call.

```java
import com.stripe.net.RequestOptions;
import java.util.UUID;

RequestOptions options = RequestOptions.builder()
    .setIdempotencyKey(UUID.randomUUID().toString()) // 36 chars — within 255-char limit
    .build();
// Sources: README.md + https://docs.stripe.com/api/idempotent_requests?lang=java
```

Rules (all high-confidence, two independent official pages):
- Max 255 characters ([docs.stripe.com/api/idempotent_requests?lang=java](https://docs.stripe.com/api/idempotent_requests?lang=java) + [docs.stripe.com/error-handling?lang=java](https://docs.stripe.com/error-handling?lang=java)).
- POST-only; no effect on GET/DELETE which are idempotent by definition.
- Stripe retains keys for at least 24 hours; reuse after pruning starts a new request.
- Reuse with different params raises `IdempotencyException`.
- Replayed responses carry `Idempotent-Replayed: true` header.

## 3. Error Handling

Catch `StripeException` or named subtypes. Use Javadoc casing, not docs.stripe.com prose casing.

```java
import com.stripe.exception.*;

try {
    // API call here
} catch (CardException e) {
    // Payment declined — surface e.getCode() and e.getMessage() to the user
} catch (InvalidRequestException e) {
    // Bad params — check e.getParam() and e.getDocUrl() before retrying
} catch (AuthenticationException e) {
    // Wrong API key
} catch (RateLimitException e) {
    // Back off and retry
} catch (ApiConnectionException e) {    // network error — NOT APIConnectionException
    // Transient; retry with backoff
} catch (ApiException e) {             // Stripe server error — NOT APIException
    // Rare; log e.getRequestId() for support
} catch (StripeException e) {
    // Catch-all: getStatusCode(), getCode(), getMessage(), getRequestId(), getStripeError()
    // Return types are medium confidence — taken from docs example, not Javadoc enumeration
}
// Source: https://docs.stripe.com/error-handling?lang=java
// Javadoc casing: https://stripe.dev/stripe-java/com/stripe/exception/package-summary.html
```

Full 13-class exception inventory is in the research file (section 4) including:
`IdempotencyException`, `PermissionException`, `SignatureVerificationException`,
`ApiKeyMissingException`, `EventDataObjectDeserializationException`, `TemporarySessionExpiredException`.
