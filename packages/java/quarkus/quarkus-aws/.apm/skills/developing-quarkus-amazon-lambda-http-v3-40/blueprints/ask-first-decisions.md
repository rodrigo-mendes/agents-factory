# Ask-First Decisions

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Every decision here is put to the user; none has a default except where a proposal is marked.

## Contents

- [C1. HTTP API or REST API](#c1-http-api-or-rest-api)
- [C2. Which HTTP framework](#c2-which-http-framework)
- [C3. Where to handle CORS](#c3-where-to-handle-cors)
- [C4. Timeout budget](#c4-timeout-budget)
- [C5. Payload size and binary bodies](#c5-payload-size-and-binary-bodies)
- [C6. Payload format version and custom domains](#c6-payload-format-version-and-custom-domains)
- [C7. Function URL or ALB](#c7-function-url-or-alb)
- [C8. Identity mapping beyond defaults](#c8-identity-mapping-beyond-defaults)
- [C9. Native CPU target](#c9-native-cpu-target)
- [C10. Handler behaviour read from source](#c10-handler-behaviour-read-from-source)

## C1. HTTP API or REST API

This selects the extension. Source: [AWS comparison](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html), [HTTP API quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| HTTP API + `quarkus-amazon-lambda-http` | Price ("designed with minimal features so that they can be offered at a lower price"), native JWT authorizer, automatic deployments | No edge-optimized or private endpoints, no AWS WAF, no API keys or usage plans, no caching, no request validation, no gateway X-Ray tracing, no execution logs, no response streaming; integration timeout fixed at 30 s | Public regional API with Cognito or JWT and no API-management needs |
| REST API + `quarkus-amazon-lambda-rest` | API keys, per-client throttling, request validation, AWS WAF, private endpoints, caching, gateway X-Ray, resource policies | Higher price; binary media types must be `*/*`; no native JWT authorizer (Lambda authorizer instead) | Any REST-only feature is needed |

Ask: "Do you need API keys or usage plans, AWS WAF, private endpoints, caching, request validation or resource policies? If yes REST API, if not HTTP API."

## C2. Which HTTP framework

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Quarkus REST (`quarkus-rest`) | `@Context` injection of the raw event is documented only for it | page not recorded | Proposal for new JAX-RS APIs (`developing-quarkus-rest-v3-40`) |
| Reactive Routes | Lightweight Vert.x routes | Raw-event access not documented (medium confidence) | Very small route sets |
| Undertow (servlet) | Servlet portability; POM description "Allow applications written for a servlet container to run in AWS Lambda" | Raw-event access not documented (medium confidence) | Porting servlet code |
| Funqy HTTP | Function-style API | Separate preview guide; the gateway type is not stated (medium confidence that it implies an HTTP API) | Funqy codebases |

Funqy HTTP uses `quarkus-funqy-http` with `quarkus-amazon-lambda-http`; its guide says it "requires you to use AWS API Gateway" ([Funqy guide](https://quarkus.io/version/3.40/guides/funqy-aws-lambda-http)). Ask which framework; propose Quarkus REST (medium confidence) because the guide documents raw-event injection only for it. Source: [guide](https://quarkus.io/version/3.40/guides/aws-lambda-http).

## C3. Where to handle CORS

The Quarkus Lambda guide does not mention CORS. Source: [HTTP API CORS](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-cors.html), [Lambda proxy](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html), [Quarkus CORS](https://quarkus.io/version/3.40/guides/security-cors).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. HTTP API gateway CORS | Preflight answered by API Gateway "even if there isn't an OPTIONS route"; one place | "API Gateway ignores CORS headers returned from your backend integration"; with a `$default` route plus authorizer an unauthorized `OPTIONS /{proxy+}` route is needed | HTTP API |
| B. Quarkus filter (`quarkus.http.cors.enabled`, default `false`, origins have no default (medium confidence, M11), and "When not specified, CORS is not permitted") | Same config locally and deployed | Whether the filter runs for Lambda-dispatched requests is (unverified); ignored behind an HTTP API with CORS configured | REST API, or HTTP API without gateway CORS |
| C. Headers from code (REST API proxy: add `Access-Control-Allow-Origin` to the output `headers`) | Explicit | Hand-written; error responses must carry the headers too | REST API without B |

Ask: "Which gateway, and is gateway CORS already defined in `provisioning-aws-api-gateway-v6`?" Do not configure A and B for the same HTTP API: API Gateway ignores CORS headers returned from the backend integration when gateway CORS is configured ([AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-cors.html)).

## C4. Timeout budget

Facts: HTTP API integration timeout 30 s, not raisable. REST API Regional or private 50 ms to 29 s, raisable ("this might require a reduction in your Region-level throttle quota"); edge-optimized not raisable. Lambda timeout max 900 s. The generated templates use `Timeout: 15`. The 3.40.1.1 handlers wait on the response future without a timeout of their own (medium confidence, M10). Source: [HTTP quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html), [REST quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html), [Lambda limits](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. Lambda timeout below the gateway integration timeout (derived rule, medium confidence) | Lambda ends before the gateway gives up | Shorter work window | Proposal |
| B. REST Regional with a raised integration timeout | Longer synchronous calls | Lower Region-level throttle quota | Calls over 29 s |
| C. Move long work off the synchronous path | No gateway limit | Architecture change (out of scope) | Long-running work |

Ask the expected p99 latency. The status code a client sees when the gateway times out first is (unverified).

## C5. Payload size and binary bodies

Limits: API Gateway payload 10 MB (not increasable); Lambda synchronous "6 MB each for request and response"; Lambda "1 MB for the total combined size of request line and header values"; HTTP API headers 10240 bytes; REST API headers 20480 bytes (8000 for private). The effective inline ceiling (6 MB, reduced by Base64 overhead) is (medium confidence). Which request content types an HTTP API delivers Base64-encoded is (unverified). Source: [HTTP quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html), [Lambda limits](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html).

Options: A. inline binary within the 6 MB limit; B. presigned S3 URLs for large files (S3 client usage is outside this skill). Ask: "Maximum request and response size?" Above a few MB propose B.

## C6. Payload format version and custom domains

AWS requires `payloadFormatVersion` (`1.0` or `2.0`) when an integration is created through CLI, CloudFormation or SDK. The 3.40.1.1 HTTP handler reads the method from `requestContext.http.method` and throws `IllegalStateException` if it is missing, which a 1.0 payload lacks (medium confidence, M10). With a custom-domain API mapping, `rawPath` does not carry the mapping value; the HTTP handler builds the URI from `rawPath` (medium confidence, M10; [AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html)).

Proposal: `payloadFormatVersion = 2.0` for every integration of a `quarkus-amazon-lambda-http` function (medium confidence: the guide does not state it). Ask: "Is a custom-domain API mapping with a path planned?" If the prefix must be visible, B: REST API with `quarkus-amazon-lambda-rest`.

## C7. Function URL or ALB

The 3.40 guide documents API Gateway only. Function URL events with `quarkus-amazon-lambda-http` are (unverified). The REST handler contains a `RequestSource.ALB` branch (detected when `requestContext.elb` is non-null; medium confidence, M10), which is code, not a documented feature; ALB as a supported front end is (unverified). Ask before proposing either, and state that the guide covers API Gateway only.

## C8. Identity mapping beyond defaults

Built-in principals versus a custom `@ApplicationScoped` bean implementing `io.quarkus.amazon.lambda.http.LambdaIdentityProvider`. Depth, Cognito design and tenant isolation: `securing-quarkus-lambda-cognito-v3-40`. Ask: "Are the built-in principals (Cognito, IAM, Lambda authorizer) enough?" Source: [guide](https://quarkus.io/version/3.40/guides/aws-lambda-http).

## C9. Native CPU target

Ask only if native was chosen in the [U1 decision](../../developing-quarkus-amazon-lambda-v3-40/blueprints/ask-first-decisions.md#c1-jvm-snapstart-or-native). The guide: "AL2023 x86-64 binaries are built for the x86-64-v2 revision", "In Quarkus, the default value of quarkus.native.march is x86-64-v3", and "To maximize Lambda compatibility, you can set quarkus.native.march to x86-64-v2" ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). Ask: "Set `quarkus.native.march=x86-64-v2`?"

## C10. Handler behaviour read from source

Read from the source files at tag 3.40.1.1 (register M10), not from a documented page: `LambdaHttpHandler` Base64-encodes a response without `Content-Type` as binary (medium confidence), and `AwsHttpContextProducers` returns `null` when the injected event type belongs to the other gateway (medium confidence). Two practices rest on this source reading and are offered here, not as Always Do: (1) set an explicit `Content-Type` on every response, so the response is not encoded as binary by the missing-type rule ([pattern](./always-do-patterns.md#8-explicit-content-type)); (2) let Quarkus REST bind multi-value query parameters (`@QueryParam List<String>`) from the request the handler rebuilds from `rawPath` plus `rawQueryString`, instead of splitting the comma-combined string by hand (medium confidence, M10). Injecting the extension's own event type is documented by the guide and stays Always Do. Ask: "Do you want these two practices, and can a real deployment test confirm the response encoding?" Sources: [LambdaHttpHandler.java](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java), [AwsHttpContextProducers.java](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/AwsHttpContextProducers.java).
