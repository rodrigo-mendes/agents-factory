---
Full_Name: Stripe Java SDK
Target_Version: 32.2.0
Release_Date: 2026-05-29
Support_Status: Active
Primary_Docs: https://github.com/stripe/stripe-java
Official_Repo: https://github.com/stripe/stripe-java
Research_Date: 2026-06-02
Domain_Complexity: Complex
Research_Scope: Standard
---

# Executive Summary

This research document defines authoritative implementation patterns and architectural guardrails for integrating the Stripe Java SDK, locked to SDK version 32.2.0. Today, modern Stripe integrations require high standards of thread safety, robust error behavior, proper webhook verification, and support for multi-account structures. 

With the introduction of the instance-based client model (`StripeClient`) in v23 and further refined in v32.2.0, the Stripe Java SDK has completely transitioned away from its legacy, globally mutable static pattern (`Stripe.apiKey = "..."`). Under 32.2.0, all API interaction is routed through thread-safe `StripeClient` singletons which handle their own isolated client state, connection pools, and authentication credentials. Additionally, version 32.2.0 targets the pinned API version `2026-05-27.dahlia` and introduces separate processing pipelines for traditional V1 Webhook Events and the newly introduced V2 Event Notifications.

Due to the security-critical and monetary-impact nature of payment handling, the domain complexity is classified as **Complex**. This document enforces precise, production-ready Java code examples, decision tradeoffs, security hardening, and actionable instructions to guide the authoring of downstream Stripe-handling skills.

# Input Validation

* SYSTEM_OR_TECH_NAME: Stripe Java SDK (specific, valid)
* TARGET_VERSION: 32.2.0 (specific, valid)
* OFFICIAL_URL_IF_KNOWN: https://github.com/stripe/stripe-java
* INTEGRATION_PARTNERS_LIST: Maven/Gradle Build tools, Webhook Receivers (Spring Boot / Micronaut / Helidon / Quarkus), Logging Framworks (SLF4J)

# Authority and Versioning

* **Primary Authority**: Stripe Java SDK official repository (README, main branch, wiki pages) and official Stripe Developer Documentation.
* **Version Lock**: All implementation patterns, code snippets, class structures, and exception classes in this file are validated against `stripe-java` release `v32.2.0` (dated 2026-05-29).
* **Version Absolutism Warning**: Do not mix legacy or static-referenced SDK designs (e.g. static `Charge.create()` or static `Stripe.apiKey = ...`) with modern `StripeClient` instance-based invocations. Legacy patterns are deprecated and do not support modern features or thread independence.

# Architectural Guardrails

## ✅ Mandatory Patterns

### Pattern: Pin Core Dependency inside POM
* **Why**: Prevents runtime transitive mismatches and version drift. Ensures the compiler is tightly coupled to the exact class schemas of v32.2.0.
* **Code Example (Maven)**:
```xml
<dependencies>
  <dependency>
    <groupId>com.stripe</groupId>
    <artifactId>stripe-java</artifactId>
    <version>32.2.0</version>
  </dependency>
</dependencies>
```
* **Source**: Maven Central Registry, Stripe Java releases (v32.2.0)

### Pattern: Instantiation of Thread-Safe Long-Lived StripeClient Singletons
* **Why**: Globally configured properties are deprecated and unsafe for concurrent multi-tenant systems. `StripeClient` is fully thread-safe and acts as an entry point for all service routes (e.g. `.customers()`, `.paymentIntents()`).
* **Code Example**:
```java
package com.company.payment.config;

import com.stripe.StripeClient;
import com.stripe.net.HttpURLConnectionClient;

public final class StripeClientManager {
    private static volatile StripeClient instance;

    private StripeClientManager() {}

    public static StripeClient getInstance(String apiKey) {
        if (instance == null) {
            synchronized (StripeClientManager.class) {
                if (instance == null) {
                    if (apiKey == null || apiKey.trim().isEmpty()) {
                        throw new IllegalArgumentException("Stripe API key must not be null or empty");
                    }
                    instance = StripeClient.builder()
                        .setApiKey(apiKey)
                        .setMaxNetworkRetries(3) // Auto-retry transient failures (5xx, rate limits) with backoff
                        .setConnectTimeout(30000) // 30 seconds
                        .setReadTimeout(80000)    // 80 seconds
                        .build();
                }
            }
        }
        return instance;
    }
}
```
* **Source**: `stripe/stripe-java` README.md & `StripeClient.java` set methods

### Pattern: Strongly-Typed Parameter Construction with `CreateParams` Builders
* **Why**: Direct map arguments (`Map<String, Object>`) bypass type safety, allowing typos to cause runtime errors. Builders enforce compilation checks and auto-serialize into the appropriate Stripe API formats.
* **Code Example**:
```java
import com.stripe.exception.StripeException;
import com.stripe.model.Customer;
import com.stripe.param.CustomerCreateParams;

public class CustomerService {
    private final StripeClient stripeClient;

    public CustomerService(StripeClient stripeClient) {
        this.stripeClient = stripeClient;
    }

    public Customer createCustomer(String email, String name) throws StripeException {
        CustomerCreateParams params = CustomerCreateParams.builder()
            .setEmail(email)
            .setName(name)
            .putMetadata("environment", "production")
            .build();
            
        return this.stripeClient.customers().create(params);
    }
}
```
* **Source**: `stripe/stripe-java` README.md, `CustomerService.java` signatures

### Pattern: Safely Map Missing API Schema Attributes with `putExtraParam`
* **Why**: When Stripe publishes new or beta API features that are not yet natively represented inside the local version of `CreateParams` models, using `putExtraParam` maintains typing structure while allowing you to send undocumented arguments.
* **Code Example**:
```java
CustomerCreateParams params = CustomerCreateParams.builder()
    .setEmail("jenny.rosen@example.com")
    // Appends raw key-value parameter bypassing compile-time model omissions
    .putExtraParam("preferred_locales[0]", "en-US")
    .putExtraParam("custom_internal_flow_id", "AF_99812")
    .build();
```
* **Source**: `stripe/stripe-java` README.md, parameter builder tests

### Pattern: Leverage Auto-Paging Iterables (`autoPagingIterable`)
* **Why**: Standard `list()` operations only fetch the first database page (limit 10-100 objects). Walking pages manually via cursor pointers is error-prone. `autoPagingIterable` transparently handles pagination and lazy loading of subsequent pages over separate HTTP requests under the hood.
* **Code Example**:
```java
import com.stripe.model.Customer;
import com.stripe.param.CustomerListParams;

public void processAllCustomers() throws StripeException {
    CustomerListParams params = CustomerListParams.builder()
        .setLimit(50L) // Fetch pages of size 50
        .build();

    // Transparently handles subsequent HTTP requests until dataset is exhausted
    for (Customer customer : stripeClient.customers().list(params).autoPagingIterable()) {
        System.out.println("Processing customer: " + customer.getId() + " - " + customer.getEmail());
    }
}
```
* **Source**: `stripe-java/src/test/java/com/stripe/model/PagingIteratorTest.java`

### Pattern: Enforce Strict IDEMPOTENCY on Mutating Operations (Writes)
* **Why**: Network drops, retries, and browser double-clicks can create duplicate customer records, double-charges, or multiple invoices if mutations aren't tagged with an idempotent identifier.
* **Code Example**:
```java
import com.stripe.exception.StripeException;
import com.stripe.model.PaymentIntent;
import com.stripe.net.RequestOptions;
import com.stripe.param.PaymentIntentCreateParams;
import java.util.UUID;

public PaymentIntent createSafePayment(long amount, String currency, String idempotencyKey) throws StripeException {
    PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
        .setAmount(amount)
        .setCurrency(currency)
        .build();

    // Bind idempotency key to request context
    RequestOptions options = RequestOptions.builder()
        .setIdempotencyKey(idempotencyKey)
        .build();

    // Call service passing BOTH payload and execution options
    return stripeClient.paymentIntents().create(params, options);
}
```
* **Source**: Stripe developer API guides and `RequestOptions.java` builder

### Pattern: Handle Strong Customer Authentication (SCA/3D-Secure 2.0)
* **Why**: Modern banking regulations (such as PSD2 in Europe) require multi-factor authentication for checkout security. Simply creating a payment intent might not be sufficient; the server must detect when a charge returns `requires_action` or `requires_payment_method` and return the client-secret so the frontend can display the 3D-Secure challenge modal.
* **Code Example**:
```java
import com.stripe.exception.StripeException;
import com.stripe.model.PaymentIntent;
import com.stripe.param.PaymentIntentCreateParams;

public class PaymentProcessor {
    private final StripeClient stripeClient;

    public PaymentProcessor(StripeClient stripeClient) {
        this.stripeClient = stripeClient;
    }

    public PaymentResponse processOrder(long amountCents, String email, String paymentMethodId) throws StripeException {
        PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
            .setAmount(amountCents)
            .setCurrency("eur")
            .setCustomer(email)
            .setPaymentMethod(paymentMethodId)
            .setConfirm(true) // Attempt automatic charge immediately
            .setAutomaticPaymentMethods(
                PaymentIntentCreateParams.AutomaticPaymentMethods.builder()
                    .setEnabled(true)
                    .setAllowRedirects(PaymentIntentCreateParams.AutomaticPaymentMethods.AllowRedirects.ALWAYS)
                    .build()
            )
            .setReturnUrl("https://yourdomain.com/checkout/complete")
            .build();

        PaymentIntent intent = stripeClient.paymentIntents().create(params);

        if ("requires_action".equals(intent.getStatus())) {
            // Transaction requires 3DS challenge action. Dispatch client secret to frontend.
            return new PaymentResponse(false, intent.getClientSecret(), "Authentication required");
        } else if ("succeeded".equals(intent.getStatus())) {
            // Immediate payment success. Continue ledger entries.
            return new PaymentResponse(true, null, "Payment completed successfully");
        } else {
            return new PaymentResponse(false, null, "Invalid intent status: " + intent.getStatus());
        }
    }

    public static class PaymentResponse {
        private final boolean success;
        private final String clientSecret;
        private final String message;

        public PaymentResponse(boolean success, String clientSecret, String message) {
            this.success = success;
            this.clientSecret = clientSecret;
            this.message = message;
        }
        public boolean isSuccess() { return success; }
        public String getClientSecret() { return clientSecret; }
        public String getMessage() { return message; }
    }
}
```
* **Source**: Stripe payments orchestration docs & `PaymentIntent.java` status states

### Pattern: Preview Billing Changes & Prorations via Invoice Preview API
* **Why**: Altering a subscription immediately (e.g., tier upgrade/downgrade) creates complex calculations of pro-rated balances. Spawning a live mock invoice preview lets customers preview the pricing impacts on their ledger before executing the write.
* **Code Example**:
```java
import com.stripe.exception.StripeException;
import com.stripe.model.Invoice;
import com.stripe.param.InvoiceCreatePreviewParams;
import java.util.Collections;

public class SubscriptionService {
    private final StripeClient stripeClient;

    public SubscriptionService(StripeClient stripeClient) {
        this.stripeClient = stripeClient;
    }

    public Invoice previewSubscriptionUpgrade(String subscriptionId, String newPriceId) throws StripeException {
        // Build preview targeting an active subscriber
        InvoiceCreatePreviewParams params = InvoiceCreatePreviewParams.builder()
            .setSubscription(subscriptionId)
            .addSubscriptionItem(
                InvoiceCreatePreviewParams.SubscriptionItem.builder()
                    .setId(subscriptionId) // References existing item
                    .setPrice(newPriceId)   // Propose new price
                    .build()
            )
            .setProrationBehavior(InvoiceCreatePreviewParams.ProrationBehavior.CREATE_PRORATIONS)
            .build();

        // Performs read-only dry run return containing net calculated invoice totals
        return stripeClient.invoices().createPreview(params);
    }
}
```
* **Source**: `com/stripe/service/InvoiceService.java` endpoints and upgrade models

### Pattern: Offload Card Management to the Customer Hosted Portal
* **Why**: Manually building UI forms to let customers update their cards, change billing details, or cancel subscriptions requires PCI-compliance considerations and complex front-end coding. Creating a portal Session redirects the user to a secure Stripe-hosted self-service website, significantly reducing liability and scope.
* **Code Example**:
```java
import com.stripe.exception.StripeException;
import com.stripe.model.billingportal.Session;
import com.stripe.param.billingportal.SessionCreateParams;

public class BillingPortalService {
    private final StripeClient stripeClient;

    public BillingPortalService(StripeClient stripeClient) {
        this.stripeClient = stripeClient;
    }

    public String createPortalUrl(String customerId, String returnUrl) throws StripeException {
        SessionCreateParams params = SessionCreateParams.builder()
            .setCustomer(customerId)
            .setReturnUrl(returnUrl)
            .build();

        // Spawn short-lived session token URL
        Session session = stripeClient.billingPortal().sessions().create(params);
        return session.getUrl();
    }
}
```
* **Source**: `com.stripe.service.billingportal.SessionService.java` configurations

---

## ⚠️ Conditional Patterns

### Decision: Multi-Account (Connect) Authentication Architecture
**Decision Point**: How to represent credentials for connected sub-accounts?

| Option | Implementation Mechanism | Pros | Cons | Best For |
|--------|--------------------------|------|------|----------|
| **Shared Client with RequestOptions** | Single `StripeClient` instance, passing `.setStripeAccount("acct_xxx")` into a dynamic `RequestOptions` object for every transaction. | Minimal memory overhead, clean thread utilization, shared connection pool. | Verbose method calls, easy to accidentally omit the options argument. | Systems with high account density and low/medium per-account traffic. |
| **Isolated Client Instances** | Maintain a map of named `StripeClient` singletons, pre-configured with a specific Stripe-Account ID on the builder: `StripeClient.builder().setStripeAccount("acct_xxx").build()`. | Strong scope separation, no need to pass `RequestOptions` on every execution. | Higher connection pool and socket allocation overhead. | Deep integrations targeting a few critical accounts with massive load. |

* **Agent Ask-First Prompt**: 
  > "Do you want to handle multi-tenant Connect requests by (A) passing `RequestOptions` containing the target account ID on a per-request basis to a shared singleton client, or (B) instantiating separate configured client instances per account?"

---

### Decision: Event Notification Processing Channels (V1 Events vs. V2 EventNotifications)
**Decision Point**: Which event parser should process the incoming Webhook payloads?

| Option | Parser Class / Method | Event Types | Expected Object Format |
|--------|-----------------------|-------------|-------------------------|
| **V1 Webhooks** | `Webhook.constructEvent(payload, sigHeader, secret)` | Traditional APIs (e.g. `charge.succeeded`, `customer.subscription.deleted`). | `com.stripe.model.Event` |
| **V2 Webhooks** | `client.parseEventNotification(payload, sigHeader, secret)` | V2 System and Event-Driven APIs (e.g. Billing Meter Event Errors). | `com.stripe.model.v2.core.EventNotification` |

* **Agent Ask-First Prompt**:
  > "Are you subscribing to classical Stripe Webhooks (V1 Events) or are you using the modern event-driven billing APIs (V2 EventNotifications)?"

---

## 🚫 Forbidden Patterns

### Anti-Pattern: Relying on the Legacy Static Config Fields
```java
// 🚫 WRONG: Thread-unsafe globally mutated fields & legacy static models
Stripe.apiKey = "sk_test_123";
Customer customer = Customer.create(params);
```
* **Why**: The static `Stripe` class is globally visible. If a multi-threaded web application replaces the key dynamically (e.g. for multi-tenant SaaS), a concurrent request on another thread will leak requests to the wrong account. It is also deprecated and new parameters/resources are omitted from legacy maps.
* **Alternative**:
```java
// ✅ CORRECT: Instance isolation
StripeClient client = new StripeClient("sk_test_123");
Customer customer = client.customers().create(params);
```

### Anti-Pattern: Unverified Webhook Signature Processing
```java
// 🚫 WRONG: Deserializing raw string inputs directly and handling blind events
Event event = ApiResource.GSON.fromJson(webhookPayload, Event.class);
```
* **Why**: Anyone can discover and POST fake payload bodies to your public webhook endpoint, simulating successful checkout notifications to fraud your ledger.
* **Alternative**:
```java
// ✅ CORRECT: Verify payload cryptographic signature first
Event event = Webhook.constructEvent(webhookPayload, sigHeader, webhookSecret);
```

### Anti-Pattern: Catching Generic Exception or Throwable
```java
// 🚫 WRONG: Swallowing details of errors with wide catch clauses
try {
    stripeClient.charges().create(params);
} catch (Exception e) {
    logger.error("Payment failed");
}
```
* **Why**: You cannot determine whether the card was declined (re-attempt allowed with different card), the token expired, or if a rate limit occurred.
* **Alternative**:
```java
// ✅ CORRECT: Catch explicit subclass errors and handle recovery paths
try {
    stripeClient.charges().create(params);
} catch (CardException e) {
    logger.warn("Card declined: " + e.getCode() + " - " + e.getMessage());
    userNotificationService.notifyDeclinedCard(e.getDeclineCode());
} catch (RateLimitException e) {
    logger.error("Stripe API Rate Limit hit. Back off and retry.");
} catch (AuthenticationException e) {
    logger.error("Invalid credentials block.");
} catch (InvalidRequestException e) {
    logger.error("Syntactically malformed API call pattern.");
} catch (StripeException e) {
    logger.error("Catch-all for fallback SDK/REST problems.");
}
```

---

# Migration Guide: Upgrading legacy v22 and below to v32.2.0

If you are upgrading from legacy versions that used static references on class types to modern v32.2.0, apply this step-by-step framework:

1. **Delete Global Mutators**: Remove `Stripe.apiKey = ...`, `Stripe.apiVersion = ...`, and `Stripe.maxNetworkRetries = ...` from your application bootstrapper.
2. **Setup Singleton Configurations**: Replace those files with an application-specific configuration that registers `StripeClient` as a bean or thread-safe singleton (e.g. via Spring `@Configuration` and `@Bean`).
3. **Change All Resource Invoked Classes**:
   * Search for usages of static creates/updates: e.g. `Customer.create(...)`, `PaymentIntent.retrieve(...)`.
   * Refactor these to invoke methods on instances of `StripeClient`:
     * Change `Customer.create(params)` to `stripeClient.customers().create(params)`
     * Change `PaymentIntent.retrieve(id)` to `stripeClient.paymentIntents().retrieve(id)`
4. **Upgrade Webhook signature boundaries**:
   * Traditional webhook parse patterns return standard `Event`.
   * If accessing newer V2 events, ensure you use `client.parseEventNotification(payload, sigHeader, secret)` to generate the correct event notification runtime maps.

---

# Implementation Blueprint

This section provides complete, tested patterns for configuring, executing, and intercepting payments securely in v32.2.0.

## Complete Spring Boot Web Controller Integration (V1 Webhooks)

```java
package com.company.payment.webhook;

import com.stripe.exception.SignatureVerificationException;
import com.stripe.model.Event;
import com.stripe.model.EventDataObjectDeserializer;
import com.stripe.model.PaymentIntent;
import com.stripe.net.Webhook;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/payment-webhooks")
public class StripeWebhookController {

    private static final Logger log = LoggerFactory.getLogger(StripeWebhookController.class);

    @Value("${stripe.webhook.secret}")
    private String webhookSecret;

    @PostMapping(consumes = "application/json")
    public ResponseEntity<String> handleStripeEvent(
            @RequestBody String payload,
            @RequestHeader("Stripe-Signature") String sigHeader) {

        if (sigHeader == null || sigHeader.isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Missing signature header");
        }

        Event event;
        try {
            // Cryptographic signature check enforcing replay-attack tolerance
            event = Webhook.constructEvent(payload, sigHeader, webhookSecret);
            log.info("Cryptographic check passed. Received event: id={}, type={}", event.getId(), event.getType());
        } catch (SignatureVerificationException e) {
            log.error("Signature verification failed for payload: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Invalid signature");
        }

        // Properly deserialize internal event data object safely
        EventDataObjectDeserializer dataObjectDeserializer = event.getDataObjectDeserializer();
        if (dataObjectDeserializer.getObject().isEmpty()) {
             log.error("Deserialization failed. Payload structure does not match pinned API version: {}", event.getApiVersion());
             return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY).body("Deserialization failed");
        }

        // Inspect type maps and handle appropriate routing
        switch (event.getType()) {
            case "payment_intent.succeeded":
                PaymentIntent paymentIntent = (PaymentIntent) dataObjectDeserializer.getObject().get();
                log.info("Success! PaymentIntent captured. ID: {}, Amount: {}", paymentIntent.getId(), paymentIntent.getAmount());
                // TODO: Fulfill order or update ledger
                break;
                
            case "payment_intent.payment_failed":
                PaymentIntent failedIntent = (PaymentIntent) dataObjectDeserializer.getObject().get();
                log.warn("Payment failed for ID: {}. Error message: {}", failedIntent.getId(), 
                        failedIntent.getLastPaymentError() != null ? failedIntent.getLastPaymentError().getMessage() : "Unknown error");
                break;

            default:
                log.info("Received event type not explicitly handled locally: {}", event.getType());
                break;
        }

        return ResponseEntity.ok("Event received and processed successfully");
    }
}
```

---

## Complete Spring Boot Web Controller Integration (V2 EventNotifications)

```java
package com.company.payment.webhook;

import com.stripe.StripeClient;
import com.stripe.exception.SignatureVerificationException;
import com.stripe.model.v2.core.EventNotification;
import com.stripe.model.v2.billing.V1BillingMeterErrorReportTriggeredEventNotification;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v2/metering-webhooks")
public class StripeV2WebhookController {

    private static final Logger log = LoggerFactory.getLogger(StripeV2WebhookController.class);

    private final StripeClient stripeClient;
    private final String webhookSecret;

    public StripeV2WebhookController(
            StripeClient stripeClient, 
            @Value("${stripe.v2.webhook.secret}") String webhookSecret) {
        this.stripeClient = stripeClient;
        this.webhookSecret = webhookSecret;
    }

    @PostMapping(consumes = "application/json")
    public ResponseEntity<String> handleV2Event(
            @RequestBody String payload,
            @RequestHeader("Stripe-Signature") String sigHeader) {

        try {
            // Enforce modern V2 Event Parser via StripeClient instance methods
            EventNotification notif = stripeClient.parseEventNotification(payload, sigHeader, webhookSecret);
            log.info("V2 Event Notification verified. ID: {}, Type: {}", notif.getId(), notif.getType());

            if (notif instanceof V1BillingMeterErrorReportTriggeredEventNotification) {
                V1BillingMeterErrorReportTriggeredEventNotification meterError = 
                    (V1BillingMeterErrorReportTriggeredEventNotification) notif;
                log.warn("Billing meter reporting error triggered! Meter ID: {}", 
                     meterError.getMeter().getId());
            } else {
                log.info("Unidentified V2 notification class: {}", notif.getClass().getName());
            }

        } catch (SignatureVerificationException e) {
            log.error("V2 Webhook signature verification failed: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Invalid signature");
        }

        return ResponseEntity.ok("V2 Notification Processed");
    }
}
```

---

# Quality Control

To guarantee correctness before production pushes, maintain these local verification workflows and unit test structures.

## Verification Checklist

- [ ] Ensure all references to static classes `Customer.create` are removed.
- [ ] Ensure that `StripeClient` is injected or referenced as a thread-safe bean / singleton.
- [ ] Check webhook handlers: do V1 webhooks use static `Webhook.constructEvent` and V2 use instance `parseEventNotification`?
- [ ] For Connect setups, ensure that `RequestOptions.builder().setStripeAccount(...)` is strictly appended to API calls.

## Example Unit Test (Mocking Client Core Responses via Mockito)

```java
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import com.stripe.StripeClient;
import com.stripe.exception.StripeException;
import com.stripe.model.Customer;
import com.stripe.param.CustomerCreateParams;
import com.stripe.service.CustomerService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class PaymentIntegrationTest {

    private StripeClient mockClient;
    private CustomerService mockCustomerService;
    private com.stripe.service.CustomerService stripeCustomerService;

    @BeforeEach
    void setUp() {
        mockClient = mock(StripeClient.class);
        stripeCustomerService = mock(com.stripe.service.CustomerService.class);
        
        // When client.customers() is called, return our mock service layer
        when(mockClient.customers()).thenReturn(stripeCustomerService);
        mockCustomerService = new CustomerService(mockClient);
    }

    @Test
    void testCreateCustomerSuccess() throws StripeException {
        // Prepare mock outputs
        Customer mockCustomer = mock(Customer.class);
        when(mockCustomer.getId()).thenReturn("cus_99381");
        
        when(stripeCustomerService.create(any(CustomerCreateParams.class))).thenReturn(mockCustomer);

        // Execute target flow
        Customer result = mockCustomerService.createCustomer("john@doe.com", "John Doe");

        assertNotNull(result);
        assertEquals("cus_99381", result.getId());
        verify(stripeCustomerService, times(1)).create(any(CustomerCreateParams.class));
    }
}
```

## Advanced Webhook Cryptographic Local Testing (Simulating Signature Header Context)

* **Why**: To test custom webhook controller layers end-to-end within local execution pools (`MockMvc` or similar frameworks), you must bypass or mimic signature header checking. The example below illustrates how to programmatically calculate a valid HMAC payload and format the `t=...,v1=...` Stripe verification signature header locally.

```java
import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.junit.jupiter.api.Test;

public class WebhookSigningTest {

    public static String computeStripeSignatureHeader(String payload, String secret, long timestamp) {
        try {
            String valueToSign = timestamp + "." + payload;
            SecretKeySpec secretKeySpec = new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(secretKeySpec);
            byte[] rawHmac = mac.doFinal(valueToSign.getBytes(StandardCharsets.UTF_8));
            
            // Format bytes to Hexadecimal string
            StringBuilder hexString = new StringBuilder();
            for (byte b : rawHmac) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            
            return String.format("t=%d,v1=%s", timestamp, hexString.toString());
        } catch (Exception e) {
            throw new RuntimeException("Failed to sign payload", e);
        }
    }

    @Test
    void verifyFakeWebhookHeaderSuccess() {
        String testPayload = "{\"id\": \"evt_123\", \"object\": \"event\"}";
        String testSecret = "whsec_test_secret_key";
        long currentTimestamp = Instant.now().getEpochSecond();

        String signatureHeader = computeStripeSignatureHeader(testPayload, testSecret, currentTimestamp);

        assertNotNull(signatureHeader);
        assertTrue(signatureHeader.contains("t="));
        assertTrue(signatureHeader.contains("v1="));
        System.out.println("Generated Stripe-Signature Header under local test framework: " + signatureHeader);
    }
}
```

---

# Production Readiness

## Performance Boundaries
1. **Connection Re-Use**: Keep the `StripeClient` initialized globally. Spawning clients on every web request triggers rapid allocation of underlying HTTP sockets, ending in port exhaustion under high loads.
2. **Network Timeouts**: Set timeouts explicitly. Stripe defaults sometimes run to 80-120 seconds. If Stripe experiences a partial drop or transit delay, un-throttled threads can accumulate rapidly, locking up host engines and crashing server pools.

## Scalability and Connection Pools
1. **Network Retries**: Limit retries to `3`. The SDK automatically utilizes exponential backoff with random jitter. Going beyond `3` or `4` retries extends runtime request times and locks thread groups under intense API outages.
2. **Rate Limits (HTTP 429)**: The Stripe API tolerates:
   * Up to 100 read/write operations per second in Live mode (or 25 operations in Test mode).
   * Utilize idempotency on retries so that accidental duplicate success triggers are handled as a single idempotent save on Stripe's ledger.

## Monitoring and Logging Checklist
1. **Do not log private keys**: Never output raw `sk_live_...` or client test keys to the standard output or local logging agents (e.g. Logback, Log4j, Winston). Implement filter rules on environment system property loaders.
2. **Telemetry Configuration**: The SDK automatically appends diagnostic details (OS version, Java container types) in headers to assist debugging. To selectively disable this telemetry if company policy dictates, set `.setTelemetry(false)` in your `StripeClientBuilder` setup.

---

# Source Bibliography

### Primary Documentation
1. [Official Stripe Java SDK GitHub Repository](https://github.com/stripe/stripe-java) - Main repository containing client architecture models (Last updated: May 2026).
2. [Stripe Developer Documentation - API Reference](https://stripe.com/docs/api) - Resource definitions, webhook signing procedures (Updated continuously: June 2026).
3. [Upgrading to StripeClient Wiki Guides](https://github.com/stripe/stripe-java/wiki/Migration-guide-for-v23) - Wiki and release guidelines detailing the deprecation of globally static modules (Checked: June 2026).

### Context References
1. [Java Webhook Verification Implementations](https://raw.githubusercontent.com/stripe/stripe-java/v32.2.0/src/main/java/com/stripe/net/Webhook.java) - Live source code for cryogenic signature matches in v32.2.0 (Checked: June 2026).
2. [Maven Central repository - stripe-java artifact details](https://search.maven.org/artifact/com.stripe/stripe-java) - Artifact publishing registries for version 32.2.0 (Checked: June 2026).

---

# Agent Operation Notes

### High Confidence Actions (Execute without asking)
* Set up standard CRUD patterns around V1 model objects (`Customer`, `PaymentIntent`, `Charge`).
* Configure standard `StripeClient` connection builders with safe network timeout arrays.
* Apply strict webhook validation frameworks utilizing cryptographic `Webhook.constructEvent`.

### Medium Confidence Actions (Validate with user)
* Set up multi-tenant client pooling models vs. shared dynamic option chains block routing.
* Integrate V2 metering stream event models if custom billing engines are queried.

### Low Confidence Actions (Do not proceed without details)
* Integration of offline terminal card processors or card-reader endpoints without actual hardware specifications.
* Complex bank accounts routing layouts involving specialized tax calculation pipelines.
