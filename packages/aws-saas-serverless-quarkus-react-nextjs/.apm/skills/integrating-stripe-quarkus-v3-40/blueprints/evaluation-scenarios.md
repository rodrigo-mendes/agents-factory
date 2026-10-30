# Evaluation Scenarios: integrating-stripe-quarkus-v3-40

Six scenarios, covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (DNS cache TTL conflict)](#scenario-2-edge-case-dns-cache-ttl-conflict)
- [Scenario 3: Misuse Rejection (Stripe API semantics request)](#scenario-3-misuse-rejection-stripe-api-semantics-request)
- [Scenario 4: Anti-Pattern Trap (request id as idempotency key)](#scenario-4-anti-pattern-trap-request-id-as-idempotency-key)
- [Scenario 5: Anti-Pattern Trap (tenant from metadata)](#scenario-5-anti-pattern-trap-tenant-from-metadata)
- [Scenario 6: Edge Case (native image request)](#scenario-6-edge-case-native-image-request)

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-webhook-on-quarkus-lambda-http
skills: ["integrating-stripe-quarkus-v3-40"]
query: "Add a Stripe webhook endpoint to my Quarkus 3.40 Lambda behind API Gateway HTTP API. It must verify the signature and not lose events."
must_pass:
  - "Takes the body as byte[] and verifies new String(body, UTF_8) with the 3-argument constructEvent"
  - "Reads Stripe-Signature with HttpHeaders.getHeaderString and explains that the HTTP handler splits header values on commas (medium confidence, M15), pointing to Ask First D9 for @RestHeader String and tagging its end-to-end failure as (unverified)"
  - "Sends the verified event to SQS before returning 2xx and returns non-2xx if the send fails"
  - "Dedupes on the evt_ id with a DynamoDB conditional put (attribute_not_exists) in the consumer and resolves the tenant from its own table"
  - "Reads the webhook secret from Secrets Manager or SSM and defers Stripe API semantics to the stripe-java skills by name"
must_not:
  - "Maps the body to a POJO or JsonNode before verification"
  - "Starts a background thread after returning 2xx"
  - "Advises a Body Mapping Template for this proxy integration"
```

---

## Scenario 2: Edge Case (DNS cache TTL conflict)

**Type**: Conflicting sources

```yaml
id: 2
name: edge-dns-ttl-snapstart
skills: ["integrating-stripe-quarkus-v3-40"]
query: "The Stripe README says set networkaddress.cache.ttl to 60. My function uses SnapStart. What value do I set?"
must_pass:
  - "Cites both statements: Stripe README says 60 seconds, AWS SnapStart guidance says avoid the Java DNS cache and set 0"
  - "Treats it as an Ask First item (D3), tags which value wins as (unverified), and asks the user which TTL to use, 60 or 0, without proposing a default"
  - "States that Lambda's managed DNS caching still applies"
must_not:
  - "Silently picks 60 or 0 without citing the other source"
  - "Recommends 0 (or 60) as the answer, for example because SnapStart is on, instead of asking"
```

---

## Scenario 3: Misuse Rejection (Stripe API semantics request)

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-subscription-proration
skills: ["integrating-stripe-quarkus-v3-40"]
query: "How do I create a Stripe subscription with proration and trial days using the Java SDK?"
must_pass:
  - "Says Stripe API semantics are out of scope and points to managing-stripe-subscriptions-v34 and processing-stripe-payments-v34 by name"
  - "Offers only the Lambda-specific parts: timeout budget, business idempotency key, tenant mapping"
must_not:
  - "Writes subscription or proration parameters"
  - "Edits or restates the stripe-java skills"
```

---

## Scenario 4: Anti-Pattern Trap (request id as idempotency key)

**Type**: Tempting shortcut

```yaml
id: 4
name: trap-request-id-idempotency-key
skills: ["integrating-stripe-quarkus-v3-40"]
query: "Use context.getAwsRequestId() as the Idempotency-Key for the PaymentIntent create so every call is unique."
must_pass:
  - "Rejects it: Stripe wants one key per operation, persisted and reused on every attempt; the claim that a client retry is a new invocation with a new request id is stated as an Ask First D10 note, not as fact"
  - "Proposes a key from tenant, operation and business id (for example an order id), up to 255 characters with no personal data"
  - "Tags the claim that a request-id key adds nothing over the SDK default as (medium confidence)"
must_not:
  - "Accepts the request id as the key"
  - "Generates a random key per attempt"
```

---

## Scenario 5: Anti-Pattern Trap (tenant from metadata)

**Type**: Tempting shortcut

```yaml
id: 5
name: trap-tenant-from-metadata
skills: ["integrating-stripe-quarkus-v3-40"]
query: "In the customer.subscription.updated handler, read tenant_id from the Customer metadata and activate that tenant's plan."
must_pass:
  - "Rejects granting from metadata alone as this skill's design (Ask First D10 recommendation A), and does not attribute it to family rule 6, which covers the path"
  - "Resolves the tenant from an own table keyed by Stripe Customer id and treats metadata as a reconciliation hint with an alert on mismatch"
  - "Returns an error for an unknown customer instead of falling back to metadata"
must_not:
  - "Calls grantPlan with the metadata value"
```

---

## Scenario 6: Edge Case (native image request)

**Type**: Decision the research does not settle

```yaml
id: 6
name: edge-native-image-stripe
skills: ["integrating-stripe-quarkus-v3-40"]
query: "Build this Stripe Lambda as a Quarkus native image, and also turn on SnapStart."
must_pass:
  - "Says SnapStart supports Java managed runtimes only, so native and SnapStart are mutually exclusive, and presents JVM + SnapStart versus native as an Ask First item, not a default"
  - "States that stripe-java documents no GraalVM support (medium confidence, absence of evidence) and maintainers marked it not planned (2026-06-18)"
  - "Warns that failures can be silent per a community report and requires native integration tests of every Stripe call path if native is chosen, tagging the completeness of any reflection workaround as (medium confidence)"
must_not:
  - "Recommends native as the default"
  - "Claims Stripe supports GraalVM"
```
