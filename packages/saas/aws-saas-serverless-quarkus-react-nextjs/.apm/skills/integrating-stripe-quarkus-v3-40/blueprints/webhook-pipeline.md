# Webhook Pipeline Blueprint

Back to [SKILL.md](../SKILL.md). stripe-java 34.0.0, Quarkus 3.40.1.1 (`quarkus-amazon-lambda-http` or `-rest`), Quarkiverse amazon-services 3.23.0. Fetched 2026-10-28. The assembled example was not compiled or run (medium confidence); method names follow the `client.v1().<resource>().create(params, options)` pattern of the internal skill `developing-stripe-java-core-v34`, and the exact parameter classes belong to `processing-stripe-payments-v34` and `managing-stripe-subscriptions-v34`.

## Contents

- [Lifecycle](#lifecycle)
- [Dependencies](#dependencies)
- [Webhook resource](#webhook-resource)
- [SQS consumer with dedupe](#sqs-consumer-with-dedupe)
- [Tenant mapping](#tenant-mapping)

## Lifecycle

```text
Init or SnapStart snapshot: Secrets Manager config source loads stripe.api-key + stripe.webhook-secret once
  -> @Singleton StripeClient built with explicit timeouts; no Stripe network call (D4)
Invoke (API path):  tenant from token (securing-quarkus-lambda-cognito-v3-40) -> mapping table -> stripe.v1()...create(params, RequestOptions(key))
Invoke (webhook):   byte[] body + getHeaderString -> constructEvent -> SQS send -> 2xx
Invoke (SQS worker): conditional put evt_ id -> process -> mark processed
```

## Dependencies

```xml
<!-- Quarkus 3.40.1.1 platform BOM + Quarkiverse 3.23.0 BOM assumed; versions per the owning skills -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-amazon-lambda-http</artifactId></dependency>
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest</artifactId></dependency>
<dependency><groupId>io.quarkiverse.amazonservices</groupId><artifactId>quarkus-amazon-secretsmanager</artifactId></dependency>
<dependency><groupId>io.quarkiverse.amazonservices</groupId><artifactId>quarkus-amazon-sqs</artifactId></dependency>
<dependency><groupId>io.quarkiverse.amazonservices</groupId><artifactId>quarkus-amazon-dynamodb</artifactId></dependency>
<dependency><groupId>com.stripe</groupId><artifactId>stripe-java</artifactId><version>34.0.0</version></dependency>
<!-- SQS and DynamoDB need an explicit HTTP client artifact (Ask First in the messaging and data skills) -->
```

Pin `34.0.0` explicitly: Maven `<release>` points at a pre-release ([Maven metadata](https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml), contradiction C4).

## Webhook resource

```java
@Path("/stripe/webhook")
public class StripeWebhookResource {

    @Inject StripeClient stripe;
    @Inject SqsClient sqs;
    @ConfigProperty(name = "stripe.webhook-secret") String webhookSecret;
    @ConfigProperty(name = "billing.stripe-events-queue-url") String queueUrl;

    @POST
    public Response receive(byte[] body, @Context HttpHeaders headers) {
        String payload = new String(body, StandardCharsets.UTF_8);
        String sig = headers.getHeaderString("Stripe-Signature");     // re-joins the split values
        final Event event;
        try {
            event = stripe.constructEvent(payload, sig, webhookSecret);  // 3-argument form
        } catch (SignatureVerificationException e) {
            return Response.status(400).build();                       // Stripe's examples answer 400
        }
        sqs.sendMessage(b -> b.queueUrl(queueUrl).messageBody(payload)  // or the event id only (D6)
                .messageAttributes(Map.of("eventId", MessageAttributeValue.builder()
                        .dataType("String").stringValue(event.getId()).build())));
        return Response.ok().build();    // an SQS exception propagates -> 5xx -> Stripe retries
    }
}
```

Notes: the response has no body, so the base64-on-non-text-content-type response rule of the HTTP skill does not matter here. The exception type `constructEvent` throws for a non-JSON body is not stated on the pages read (unverified). Stripe's examples return 400 on a bad signature ([webhooks](https://docs.stripe.com/webhooks)). A webhook endpoint whose API version differs from the SDK pin leaves `getObject()` empty (medium confidence, M13: neighbour skill `handling-stripe-webhooks-v34`, which cites the [EventDataObjectDeserializer Javadoc](https://stripe.dev/stripe-java/com/stripe/model/EventDataObjectDeserializer.html); not re-fetched here).

## SQS consumer with dedupe

Mirrors Stripe's `mark_as_processing` / `mark_as_processed` recovery flow ([manage webhook endpoints](https://docs.stripe.com/webhooks/event-notification-handlers?lang=java)): skip already-processed events and return 200. The `claim` method is in [always-do patterns](./always-do-patterns.md#7-event-id-dedupe).

```java
void onMessage(String eventId, String payload) {
    if (!claim(eventId, ttlEpochSeconds)) return;          // duplicate: skip, let SQS delete the message
    try {
        process(payload);                                   // tenant lookup first (below)
        markProcessed(eventId);                             // status PROCESSING -> PROCESSED
    } catch (RuntimeException e) {
        releaseClaim(eventId);                              // or let a lease expire, so a redelivery retries
        throw e;
    }
}
```

For dual Event objects Stripe says to "use the ID of the object in data.object along with the event.type" ([webhooks](https://docs.stripe.com/webhooks)). Cap the consumer with reserved concurrency to protect Stripe rate limits (429 means back off, [error handling](https://docs.stripe.com/error-low-level?lang=java)); the sizing is an inference (medium confidence).

## Tenant mapping

```java
// API path: tenantId comes from the verified token, never from the body
CustomerCreateParams p = CustomerCreateParams.builder()
        .putMetadata("tenant_id", tenantId)        // key <= 40 chars, value <= 500 chars, nothing sensitive
        .build();
Customer c = stripe.v1().customers().create(p,
        RequestOptions.builder().setIdempotencyKey("t:" + tenantId + ":customer").build()); // one Customer per tenant
tenantMapping.put(tenantId, c.getId());            // DynamoDB, both directions (data skill owns the table)

// Consumer: resolve the tenant from OUR table using the customer id carried by the object
String tenant = tenantMapping.findTenantByStripeCustomer(stripeCustomerId).orElseThrow();
```

The `putMetadata` builder name is (medium confidence). Metadata is not copied automatically to related objects except listed one-time snapshots (PaymentIntent to Charge, Subscription to Invoice `parent.subscription_details.metadata`); Stripe recommends a local identifier in metadata "so you can match an object received through a webhook to your local records" ([metadata](https://docs.stripe.com/metadata), [error handling](https://docs.stripe.com/error-low-level?lang=java)).
