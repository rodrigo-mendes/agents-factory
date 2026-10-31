# Migration Notes

Back to [SKILL.md](../SKILL.md). Fetched 2026-10-28. SDK-level breaking changes are owned by `developing-stripe-java-core-v34` and `handling-stripe-webhooks-v34`; this page lists only what changes this integration.

## Changes relevant to this integration

- stripe-java 34.0.0 pins API version `2026-09-30.endive`; a webhook endpoint whose API version differs leaves `getObject()` empty (medium confidence, M13: neighbour skill `handling-stripe-webhooks-v34`, which cites the [EventDataObjectDeserializer Javadoc](https://stripe.dev/stripe-java/com/stripe/model/EventDataObjectDeserializer.html); not re-fetched here). Snapshot destinations select an API version at creation ([webhooks](https://docs.stripe.com/webhooks)).
- Pre-releases 34.1.0-alpha.1 to alpha.4 and beta.1 exist; Maven `<release>` is `34.1.0-beta.1` (lastUpdated 2026-10-21) ([Maven metadata](https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml)). Pin `34.0.0` (contradiction C4).
- Stripe's docs now recommend the Thin payload for new destinations; existing snapshot code keeps working ([webhooks](https://docs.stripe.com/webhooks)).
- Quarkus side: `quarkus.snapstart.enable` is deprecated since 3.26, use `quarkus.snapstart.enabled` ([all-config](https://quarkus.io/version/3.40/guides/all-config)); `quarkus-amazon-lambda-http` and `-rest` remain preview.

## Upgrade steps

1. Pin `com.stripe:stripe-java:34.0.0` explicitly, no version ranges.
2. Replace any `Stripe.apiKey = ...` with the producer ([pattern 1](./always-do-patterns.md#1-stripeclient-producer)).
3. Replace `@RestHeader String` signature parameters (Ask First D9) with `HttpHeaders.getHeaderString` ([pattern 5](./always-do-patterns.md#5-signature-header)) and POJO webhook bodies with `byte[]` ([pattern 4](./always-do-patterns.md#4-raw-body-as-bytes)).
4. Set explicit timeouts and retries (Ask First [D1](./ask-first-decisions.md#d1-timeout-and-retry-values)).
5. Move secrets to the Secrets Manager config source; publish a new SnapStart version after a rotation (medium confidence); see [D4](./ask-first-decisions.md#d4-secrets-and-snapstart).

## Compatibility

| Dependency | Minimum | Maximum | Note |
|---|---|---|---|
| stripe-java | 34.0.0 | 34.x stable | 35.x needs a new skill |
| Java | 17 (Quarkiverse source and target) | 25 | Lambda `java17.al2023`, `java21`, `java25` runtimes |
| Quarkus | 3.40.1.1 | 3.40.x | Quarkus 4 rejected |
| Quarkiverse amazon-services | 3.23.0 | 3.23.x | pairing with patch 3.40.1.1 is (medium confidence) |
| GraalVM native | not supported by Stripe (medium confidence, absence of evidence) | not supported by Stripe (medium confidence, absence of evidence) | Ask First [D2](./ask-first-decisions.md#d2-jvm--snapstart-or-native) |

Sources: [Lambda runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html), [Quarkiverse parent POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom), [releases](https://quarkus.io/releases).
