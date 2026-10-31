---
name: developing-quarkus-amazon-lambda-http-v3-40
description: "Guides Quarkus 3.40 LTS web apps on AWS Lambda behind API Gateway with quarkus-amazon-lambda-http (HTTP API) and quarkus-amazon-lambda-rest (REST API). Use when building Quarkus HTTP endpoints as a Lambda. Not for plain handlers, Cognito, tests, Terraform or Quarkus 4."
---

# Developing Quarkus HTTP on AWS Lambda 3.40

> Version lock: every claim applies to **Quarkus 3.40 LTS, patch 3.40.1.1** (`quarkus-amazon-lambda-http`, `quarkus-amazon-lambda-rest`) only. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: HTTP applications behind Amazon API Gateway (HTTP API and REST API), event mapping, binary and base64 bodies, raw event and context injection, build output, gateway limits. Packaging, JVM vs native and SnapStart are owned by [developing-quarkus-amazon-lambda-v3-40](../developing-quarkus-amazon-lambda-v3-40/SKILL.md) and are not repeated here. Neighbours, by name only: `testing-quarkus-amazon-lambda-v3-40` (tests), `developing-quarkus-rest-v3-40` (Quarkus REST, in `quarkus-core`), `securing-quarkus-lambda-cognito-v3-40` (Cognito, JWT, tenant isolation), `provisioning-aws-api-gateway-v6` and `provisioning-aws-lambda-v6` (Terraform), `designing-aws-api-gateway-serverless` (gateway design). Quarkus 4 is out of scope.

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| Quarkus | 3.40 LTS, released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 released 2026-10-19 | https://quarkus.io/releases |
| Status | Both extensions are **preview**: "This technology is considered preview"; backward compatibility and presence in the ecosystem are not guaranteed | https://quarkus.io/version/3.40/guides/aws-lambda-http |
| HTTP API extension | `io.quarkus:quarkus-amazon-lambda-http` 3.40.1.1; handler typed `APIGatewayV2HTTPEvent` / `APIGatewayV2HTTPResponse` (payload format 2.0) | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-http/3.40.1.1/quarkus-amazon-lambda-http-3.40.1.1.pom |
| REST API extension | `io.quarkus:quarkus-amazon-lambda-rest` 3.40.1.1; handler typed `AwsProxyRequest` / `AwsProxyResponse` | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-rest/3.40.1.1/quarkus-amazon-lambda-rest-3.40.1.1.pom |
| Archetypes | `quarkus-amazon-lambda-http-archetype`, `quarkus-amazon-lambda-rest-archetype`, both 3.40.1.1 | https://quarkus.io/version/3.40/guides/aws-lambda-http |
| Supported HTTP frameworks | Quarkus REST, Undertow (servlet), Reactive Routes; Funqy HTTP has its own preview guide | https://quarkus.io/version/3.40/guides/aws-lambda-http |
| Build prerequisites | JDK 17+; Maven 3.9.16 as listed by the guide (medium confidence) | https://quarkus.io/version/3.40/guides/aws-lambda-http |
| Migration | none for these extensions in 3.40 ("direct continuation of 3.39") | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 |

**Version-lifetime risk** (details in [register](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Preview status: the guide gives no compatibility guarantee, so pin 3.40.x and re-read the guide on every upgrade.
- Quarkus 4.0.0 is "Upcoming" with no date on the releases page. Pin 3.40.x.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Security (short)](#security-short)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions in depth](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Request and response mapping](./blueprints/request-and-response-mapping.md)
- [Build output and artifact contract](./blueprints/build-output-and-artifact-contract.md)
- [Verification Loop](./blueprints/build-output-and-artifact-contract.md#verification-loop)
- [Migration notes](./blueprints/migration-notes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use the extension that matches the gateway.** `quarkus-amazon-lambda-http` for an HTTP API, `quarkus-amazon-lambda-rest` for a REST API ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See [patterns](./blueprints/always-do-patterns.md#1-extension-choice).
- **Keep exactly one HTTP framework.** The guide warns about "unexpected conflicts and errors" with more than one ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See [patterns](./blueprints/always-do-patterns.md#2-one-http-framework).
- **Inject the raw event and Lambda context only through the types documented for your extension** ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See [patterns](./blueprints/always-do-patterns.md#3-raw-event-injection).
- **REST API: configure binary media types `*/*`** on the API ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See [patterns](./blueprints/always-do-patterns.md#4-rest-binary-media-types).
- **Add `quarkus.lambda-http.enable-security=true` when the application needs the authorizer identity.** The guide says security is opt-in: "To enable this security feature, add … quarkus.lambda-http.enable-security=true" ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See [patterns](./blueprints/always-do-patterns.md#5-enable-security).
- **Develop against the mock event server** (`quarkus:dev`, `/_lambda_`) ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See [patterns](./blueprints/always-do-patterns.md#6-mock-event-server).
- **Treat `sam.jvm.yaml` and `sam.native.yaml` as reference output** and provision with the Terraform skills, never SAM or CDK ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See [patterns](./blueprints/always-do-patterns.md#7-build-output-is-reference).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| HTTP API or REST API (extension choice) | HTTP API: lower price, native JWT authorizer, 30 s fixed integration timeout; no WAF, API keys, caching or request validation. REST API: those features, higher price, binary media `*/*` ([AWS comparison](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)). See [C1](./blueprints/ask-first-decisions.md#c1-http-api-or-rest-api) | "Do you need API keys or usage plans, AWS WAF, private endpoints, caching, request validation or resource policies? If yes REST API, if not HTTP API" |
| HTTP framework | Quarkus REST (raw-event injection documented only for it), Reactive Routes, Undertow, Funqy HTTP; raw-event access outside Quarkus REST is (medium confidence). See [C2](./blueprints/ask-first-decisions.md#c2-which-http-framework) | "Which framework? Proposal: Quarkus REST" |
| CORS placement | Gateway (HTTP API), Quarkus filter, headers from code (REST API); filter behaviour on Lambda is (unverified). See [C3](./blueprints/ask-first-decisions.md#c3-where-to-handle-cors) | "Which gateway, and is CORS already defined in `provisioning-aws-api-gateway-v6`?" |
| Timeout budget | HTTP API 30 s fixed ([AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html)), REST API 29 s default (raisable for Regional or private; [AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html)), Lambda max 900 s ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)); rule "Lambda timeout below gateway timeout" is (medium confidence). See [C4](./blueprints/ask-first-decisions.md#c4-timeout-budget) | "What is the p99 latency?" |
| Payload size and binary bodies | API Gateway 10 MB ([AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html)) vs Lambda 6 MB synchronous ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)); effective ceiling is (medium confidence). See [C5](./blueprints/ask-first-decisions.md#c5-payload-size-and-binary-bodies) | "What is the maximum request and response size?" |
| Payload format and custom-domain base path | Format 2.0 proposed for `-http` (medium confidence); `rawPath` hides the API-mapping prefix. See [C6](./blueprints/ask-first-decisions.md#c6-payload-format-version-and-custom-domains) | "Is a custom-domain API mapping with a path planned?" |
| Function URL or ALB front end | Not documented by the 3.40 guide (unverified). See [C7](./blueprints/ask-first-decisions.md#c7-function-url-or-alb) | "Do you really need a front end other than API Gateway?" |
| Custom identity provider | `LambdaIdentityProvider` bean vs built-in principals; depth belongs to `securing-quarkus-lambda-cognito-v3-40`. See [C8](./blueprints/ask-first-decisions.md#c8-identity-mapping-beyond-defaults) | "Are the built-in principals enough?" |
| Native CPU target | `quarkus.native.march=x86-64-v2` for Lambda compatibility, only if native was chosen in the U1 skill ([JVM, SnapStart or native](../developing-quarkus-amazon-lambda-v3-40/blueprints/ask-first-decisions.md#c1-jvm-snapstart-or-native)). See [C9](./blueprints/ask-first-decisions.md#c9-native-cpu-target) | "Native chosen? Set x86-64-v2?" |
| Handler behaviour read from source at tag 3.40.1.1 | Set an explicit `Content-Type` on every response (a response without it is Base64-encoded as binary); let Quarkus REST bind multi-value query parameters (`@QueryParam List<String>`) instead of splitting the combined string; the producer returns `null` for the other gateway's event type. All three are (medium confidence): source read through summarisation (M10). See [C10](./blueprints/ask-first-decisions.md#c10-handler-behaviour-read-from-source) | "Do you want these practices, and do you need a real-deployment test of the response encoding?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Add more than one HTTP framework ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)) | Keep one of `quarkus-rest`, `quarkus-reactive-routes`, `quarkus-undertow` ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)) |
| Inject an event type the guide does not list as injectable for this extension ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)) | Inject `AwsProxyRequest` for REST and `APIGatewayV2HTTPEvent` for HTTP, as the guide lists ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)); the runtime effect of a wrong type is Ask First C10 |
| Deploy a REST API without binary media types `*/*` ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)) | Configure `*/*` through `provisioning-aws-api-gateway-v6` ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)) |
| Copy the REST extension's `sam.native.yaml` `Runtime: provided`; AWS deprecated it on 2024-01-08 ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)) | Take the runtime from the Ask-First choice in the [U1 skill](../developing-quarkus-amazon-lambda-v3-40/blueprints/ask-first-decisions.md#c1-jvm-snapstart-or-native) and carry it into `provisioning-aws-lambda-v6` |
| Treat the combined multi-value header or query string of an HTTP API event as having reliable value boundaries; format 2.0 combines duplicates with commas ([AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html)) | Do not split the combined string by hand; for the binding option see Ask First [C10](./blueprints/ask-first-decisions.md#c10-handler-behaviour-read-from-source) |
| Expect an authorizer `Principal` without enabling security; the guide says security is opt-in ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)) | Add `quarkus.lambda-http.enable-security=true` ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Security (short)

- Identity mapping is opt-in: add `quarkus.lambda-http.enable-security=true` (default `false`, medium confidence: stated by the config reference, not by the guide). The extension then registers a `java.security.Principal` from the authorizer data: `CognitoPrincipal`, `IAMPrincipal` or `CustomPrincipal` ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)).
- Cognito groups map to Quarkus roles unless `quarkus.lambda-http.map-cognito-to-roles=false` ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)); the defaults `true` and `cognito-role-claim` = `cognito:groups` are (medium confidence).
- Cognito caveat: `cognito:username` is an ID-token claim and access tokens carry `username` instead; identify users by `sub` ([AWS](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html)). Whether the Principal path `...claims.cognito:username` resolves for an access token in Quarkus is (unverified) (U13). Detail: `securing-quarkus-lambda-cognito-v3-40`.
- Cognito, JWT, custom `LambdaIdentityProvider` and tenant isolation: `securing-quarkus-lambda-cognito-v3-40`.

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Lambda handler (both extensions, JVM) | `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest` (generated `sam.jvm.yaml`) | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/deployment/src/main/resources/http/sam.jvm.yaml ; https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/deployment/src/main/resources/http/sam.jvm.yaml |
| Injectable types, HTTP API | `com.amazonaws.services.lambda.runtime.Context`, `APIGatewayV2HTTPEvent`, `APIGatewayV2HTTPEvent.RequestContext` | https://quarkus.io/version/3.40/guides/aws-lambda-http |
| Injectable types, REST API | `Context`, `io.quarkus.amazon.lambda.http.model.AwsProxyRequestContext`, `io.quarkus.amazon.lambda.http.model.AwsProxyRequest` | https://quarkus.io/version/3.40/guides/aws-lambda-http |
| `quarkus.lambda-http.enable-security` | default `false` (medium confidence; env `QUARKUS_LAMBDA_HTTP_ENABLE_SECURITY`) | https://quarkus.io/version/3.40/guides/all-config |
| `quarkus.lambda.mock-event-server.dev-port` / `test-port` | defaults `8080` / `8081`; `enabled` default `true` (medium confidence: partly read page, M9) | https://quarkus.io/version/3.40/guides/all-config |
| Gateway integration timeout | HTTP API 30 s (not raisable); REST API 29 s (raisable for Regional and private) | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html ; https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html |
| Payload | API Gateway 10 MB; Lambda synchronous 6 MB request and response | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html |
| Build outputs | `function.zip`, `sam.jvm.yaml`, `sam.native.yaml` in `target/` (Maven) or `build/` (Gradle) | https://quarkus.io/version/3.40/guides/aws-lambda-http |
| Mock server raw events | POST an API Gateway event JSON to `/_lambda_` | https://quarkus.io/version/3.40/guides/aws-lambda-http |

Per-key defaults, the artifact contract and limits: [build output and artifact contract](./blueprints/build-output-and-artifact-contract.md).

## External Resources

All fetched 2026-10-28.

- Lambda HTTP guide: https://quarkus.io/version/3.40/guides/aws-lambda-http
- Configuration reference: https://quarkus.io/version/3.40/guides/all-config
- Funqy HTTP on Lambda: https://quarkus.io/version/3.40/guides/funqy-aws-lambda-http
- API Gateway HTTP API vs REST API: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html
- Payload format 2.0: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
