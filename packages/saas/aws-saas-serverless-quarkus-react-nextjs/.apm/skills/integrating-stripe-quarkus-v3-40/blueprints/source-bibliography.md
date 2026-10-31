# Source bibliography

Back to [register](./unverified-and-risks.md) · [SKILL.md](../SKILL.md). Moved out of the register on 2026-10-28 to keep it under 160 lines; content unchanged.


All read 2026-10-28 with the WebFetch tool; see L1 to L6 for partial coverage.

| ID | URL | Used for |
|---|---|---|
| S1 | https://docs.stripe.com/webhooks | raw body, header, tolerance, 2xx, retries, dedupe, secret roll, IPs, destinations |
| S2 | https://docs.stripe.com/webhooks/event-notification-handlers?lang=java | Java example, exact UTF-8 body, processing flow (now "Manage webhook endpoints") |
| S3 | https://docs.stripe.com/keys-best-practices | secrets vault, restricted keys, rotation |
| S4 | https://docs.stripe.com/api/idempotent_requests | 255 characters, 24 hours, parameter comparison |
| S5 | https://docs.stripe.com/error-low-level?lang=java | zero retries, persisted keys, local identifier |
| S6 | https://docs.stripe.com/metadata | limits, events carry metadata, copy exceptions |
| S7 | https://docs.stripe.com/event-destinations/eventbridge | EventBridge destination limits |
| S8 | https://support.stripe.com/questions/webhooks-how-to-investigate-and-fix-timed-out | no numeric timeout (I1) |
| S9 | https://github.com/stripe/stripe-java/blob/v34.0.0/README.md | legacy pattern, timeout advice, DNS TTL |
| S10 | https://github.com/stripe/stripe-java/blob/master/README.md | Maven snippet, JDK list |
| S11 | https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/Stripe.java | default timeouts, legacy retries |
| S12 | https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/StripeClient.java | builder defaults, `constructEvent`, `withStripeContext` |
| S13 | https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/HttpClient.java | retry conditions, delays, jitter |
| S14 | https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/StripeRequest.java | automatic idempotency key |
| S15 | https://stripe.dev/stripe-java/com/stripe/StripeClient.StripeClientBuilder.html | builder setters |
| S16 | https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml | 34.x versions, release tag |
| S17 | https://github.com/stripe/stripe-java/issues/1905 | GraalVM "not planned" |
| S18 | https://github.com/stripe/stripe-java/issues/1199 | Quarkus native Gson failure |
| S19 | https://github.com/stripe/stripe-java/issues?q=graalvm | issue states |
| S20 | https://quarkus.io/version/3.40/guides/rest | body types, `HttpHeaders` |
| S21 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java | base64, UTF-8 copy, comma split |
| S22 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java | same body rule, `multiValueHeaders` |
| S23 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html | payload 2.0 headers |
| S24 | https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html | proxy maps the whole request |
| S25 | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-payload-encodings-workflow.html | REST content-type conversion |
| S26 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-best-practices.html | init, networking, DNS, dummy invocations |
| S27 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-security.html | snapshot encryption |
| S28 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html | freeze, background work, reuse |
| S29 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html | one request per environment |
| S30 | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html | conditional put |
| S31 | https://raw.githubusercontent.com/jakartaee/rest/main/jaxrs-api/src/main/java/jakarta/ws/rs/HeaderParam.java | first value for non-collection types |
| S32 | https://raw.githubusercontent.com/jakartaee/rest/main/jaxrs-api/src/main/java/jakarta/ws/rs/core/HttpHeaders.java | `getHeaderString` joins with "," |
| S33 | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html | REST API integration timeout 29 s, raisable for Regional and private APIs (read in full as S15 of `workspace/research_AWS_LambdaDebug_2026-10.md`) |
| S34 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html | HTTP API integration timeout 30 s maximum, not raisable (read in full as S14 of the same research) |
| S35 | https://github.com/stripe/stripe-java/releases ; https://raw.githubusercontent.com/stripe/stripe-java/refs/heads/master/CHANGELOG.md | release date and default API version, as cited by the neighbour skills (not re-fetched, M13) |
| S36 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html ; https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html ; https://stripe.dev/stripe-java/com/stripe/model/EventDataObjectDeserializer.html | pages cited by the neighbour skills for the config-source load, SQS at-least-once and empty `getObject()` claims (not re-fetched) |

Family facts (orchestrator-verified 2026-10-28): https://quarkus.io/releases ; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ ; https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html ; https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html ; https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html ; https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html ; https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html ; https://quarkus.io/version/3.40/guides/aws-lambda-http ; https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 ; https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom.

Internal sources (cited as internal, page not recorded; research ids in brackets): N1 `developing-stripe-java-core-v34` [I1]; N2 `handling-stripe-webhooks-v34` [I2]; N3 `developing-quarkus-arc-v3-40` [I3]; N4 U1 research on plain Lambda and SnapStart [I4]; N5 U2 research on HTTP mapping [I5]; N6 U4 research on DynamoDB [I6]; N7 U5 research on messaging and config sources [I7]; N8 D2 research on Lambda debugging [I8] (its API Gateway timeout facts are now cited to S33 and S34). Family rules 3, 5, 6, 7, 9 to 12 apply.
