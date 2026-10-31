# Unverified Claims and Risks — stripe-java 34.0.0 (WEBHOOKS)

Research date 2026-10-14. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **34.x is the current stable major** as of 2026-10-14; the SDK moves fast (GitHub Releases shows
  alpha/beta pre-releases for 34.1.0 as of research date). Re-verify when starting a new project
  or after 30 days. Source: https://github.com/stripe/stripe-java/releases (checked 2026-10-14).
- **33.x is superseded** (last: 33.4.2, 2026-09-09). All 33.x webhook patterns are treated as
  misinformation for a 34.x target. Do not apply 33.x guidance to 34.x code.
- `2026-09-30.endive` is pinned by default in 34.0.0; future 34.x minor releases may change this
  default. Audit pinned-version assumptions whenever upgrading minor releases.
- The `StripeEventNotificationHandler` Javadoc page is >219 KB; only the visible portion was
  confirmed. Additional methods may exist beyond the truncation point.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Exact superclass and constructor list of `com.stripe.exception.EventDataObjectDeserializationException` | (unverified) — class confirmed to exist and carry `getRawJson()`; dedicated exception Javadoc page not fully enumerated; superclass not individually confirmed |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | Full method list of `StripeEventNotificationHandler` beyond `handle`, `getRegisteredEventTypes`, `preHandle`, and the `onV1…/onV2…` fluent registrar families | (medium confidence) — Javadoc page >219 KB; confirmed methods are visible; additional methods past the truncation point were not enumerated |
| M2 | Exact signature of `StripeEventNotificationHandler.withoutVerification(StripeClient, EventNotificationFallbackCallback)` static factory | (medium confidence) — referenced in the class description but below the Javadoc truncation point; exact parameter order not confirmed |

## Coverage Limits

| Tag | Item | Status |
|---|---|---|
| L1 | Maven Central publish timestamp for 34.0.0 | (coverage limit) — existence corroborated via GitHub Releases + docs.stripe.com; direct Maven Central versions page did not load fully 2026-10-14 |
| L2 | `docs.stripe.com/events/how-events-work` — automatic retry window (3-day claim) | (coverage limit) — referenced via the event-notification-handlers page; not independently re-fetched 2026-10-14 |
| L3 | `docs.stripe.com/ips` — Stripe IP ranges for allowlisting | (coverage limit) — referenced via the event-notification-handlers page; not independently re-fetched 2026-10-14 |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) — class exists but superclass/constructors not enumerated | always-do-patterns.md §5, SKILL.md Quick Reference row for unsafe deserialization | U1 |
| (medium confidence) — full method list past Javadoc truncation | always-do-patterns.md §6, SKILL.md Quick Reference handler rows | M1 |
| (medium confidence) — static withoutVerification factory signature | always-do-patterns.md §6 | M2 |

## Source Bibliography

All sources are official (stripe.com / docs.stripe.com / github.com/stripe / stripe.dev / Maven Central / Sonatype).
Checked **2026-10-14**.

1. **GitHub — stripe/stripe-java Releases**
   https://github.com/stripe/stripe-java/releases
   Used for: v34.0.0 "Latest" status (published 2026-10-01), pre-release list, last 33.x stable 33.4.2,
   v33.4.2 non-empty webhook secret validation (#2286).

2. **GitHub — stripe/stripe-java CHANGELOG.md**
   https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md
   (raw: https://raw.githubusercontent.com/stripe/stripe-java/master/CHANGELOG.md)
   Used for: pinned API version `2026-09-30.endive`, #2294 account-scoping fix for event-notification-handler
   callback clients, #2288 singleton related objects, #2292 webhook-endpoint params + `snapshotEvent`,
   new `V1…EventNotification` classes, `STRIPE_SUPPRESS_NOTICES`.

3. **GitHub (raw) — Webhook.java @ tag v34.0.0**
   https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/Webhook.java
   Used for: exact `DEFAULT_TOLERANCE = 300;` source line, 3/4/5-arg `constructEvent` overload delegation,
   `Signature.verifyHeader(...)` throw conditions for `SignatureVerificationException`.

4. **Javadoc (stripe.dev) — com.stripe.net.Webhook**
   https://stripe.dev/stripe-java/com/stripe/net/Webhook.html
   Used for: `constructEvent` overloads (3/4/5-arg incl. Clock), `DEFAULT_TOLERANCE` field,
   `constructEventWithoutVerification`, `maybeExtractFromCloudProviderEnvelope`,
   nested `Webhook.Signature` / `Webhook.Util`.

5. **Javadoc (stripe.dev) — com.stripe.StripeClient**
   https://stripe.dev/stripe-java/com/stripe/StripeClient.html
   Used for: instance `constructEvent` (3/4-arg, no Clock overload), `constructEventWithoutVerification`,
   `parseEventNotification` (3/4-arg), `parseEventNotificationWithoutVerification`,
   `notificationHandler`, `notificationHandlerWithoutVerification`.

6. **Javadoc (stripe.dev) — com.stripe.model.Event**
   https://stripe.dev/stripe-java/com/stripe/model/Event.html
   Used for: `getId()` (`evt_…`), `getType()`, `getApiVersion()`, `getData()`, `getDataObjectDeserializer()`.

7. **Javadoc (stripe.dev) — com.stripe.model.EventDataObjectDeserializer**
   https://stripe.dev/stripe-java/com/stripe/model/EventDataObjectDeserializer.html
   Used for: `getObject()` → `Optional<StripeObject>` (empty on API-version mismatch, the #1 footgun),
   `deserializeUnsafe()` → `StripeObject` throws `EventDataObjectDeserializationException`,
   `deserializeUnsafeWith(CompatibilityTransformer)` throws `JsonParseException`, `getRawJson()`,
   API-version-mismatch guidance and fix.

8. **Javadoc (stripe.dev) — com.stripe.StripeEventNotificationHandler**
   https://stripe.dev/stripe-java/com/stripe/StripeEventNotificationHandler.html
   Used for: constructor `(String webhookSecret, StripeClient client, EventNotificationFallbackCallback)`,
   `handle(String, String)` (verifying), `getRegisteredEventTypes()`, `onV1…/onV2…` fluent registrars,
   `withoutVerification(...)` reference in class description.
   Note: page is >219 KB; only the visible portion was confirmed.

9. **Javadoc (stripe.dev) — com.stripe package summary**
   https://stripe.dev/stripe-java/com/stripe/package-summary.html
   Used for: class inventory confirming `StripeEventNotificationHandler`,
   `StripeEventNotificationHandlerWithoutVerification`, `EventNotificationCallback`,
   `EventNotificationFallbackCallback`; absence of a class literally named `EventNotificationHandler`.

10. **Docs — Event notification handlers (Java)**
    https://docs.stripe.com/webhooks/event-notification-handlers?lang=java
    Used for: handler construction via `client.notificationHandler(...)`, typed callbacks `onV1…`,
    `preHandle` dedup pattern, `.handle(body, sig)`, fallback callback shape, SDK Java GA table
    (`v33.4.0`), error-handling-to-HTTP mapping, best practices (dedup, 2xx, async, raw body),
    signature-error troubleshooting, `stripeClient.constructEvent(requestBody, signature, endpointSecret)`
    official Java snippet.
    NOTE: this page carried the injected `stripe agent setup` CTA; no claim is derived from that section.

11. **Docs — Webhooks overview (Java)**
    https://docs.stripe.com/webhooks?lang=java
    Used for: endpoint setup, event delivery model, EventBridge/Event Grid alternatives.
    NOTE: same injected CTA observed and ignored.

12. **Maven Central (Sonatype) — com.stripe:stripe-java versions**
    https://central.sonatype.com/artifact/com.stripe/stripe-java/versions
    Used for: artifact coordinate corroboration only. (L1: full versions page did not load; existence
    corroborated via sources 1 and docs.)

13. **Maven Central (repo1) — maven-metadata.xml**
    https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml
    Used for: confirming stable target is `34.0.0` (`<latest>` = `34.1.0-beta.1` is NOT the stable target;
    `maven-metadata.xml <latest>` tracks the newest upload, not newest stable).
