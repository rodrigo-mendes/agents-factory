# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 88%, a deep run using all 3 iterations, 5 triangulated claims and 0 irresolvable items. Family facts verified by the orchestrator on 2026-10-28 keep the tags of the family facts file. Register ids are U (unverified), I (irresolvable), M (medium confidence) and L (coverage limit) only.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

| Risk | Detail | Source |
|---|---|---|
| Preview status | Both extensions are marked preview in the 3.40 guide: "In preview, backward compatibility and presence in the ecosystem is not guaranteed". Re-read the guide on every upgrade (High; family fact) | https://quarkus.io/version/3.40/guides/aws-lambda-http |
| Quarkus line | 3.40 released 2026-09-30, LTS, community-maintained until 2027-09-30; patch 3.40.1.1 released 2026-10-19. The documentation is new and may still change | https://quarkus.io/releases |
| Quarkus 4 | 4.0.0 is "Upcoming" with no date; Quarkus 4 content is rejected for this skill | https://quarkus.io/releases |
| AWS runtimes | `provided` deprecated 2024-01-08 (create blocked 2024-02-08, update blocked 2027-08-31); `provided.al2023` deprecation 2029-06-30. Re-check the table before pinning a runtime | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html |

## Unverified items

13 unverified items (do not assert them).

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | Whether the Quarkus CORS filter (`quarkus.http.cors.*`) runs for Lambda-dispatched requests | Prefer gateway CORS for an HTTP API; ask (C3) |
| U2 | Which request content types an HTTP API delivers with `isBase64Encoded=true` | Do not list content types; test with the mock server and a deployment |
| U3 | Client-visible effect of binary media types `*/*` on REST responses the 3.40.1.1 handler sends as text (depends on U12) | Keep `*/*`; test on a deployed REST API |
| U4 | Mechanism behind `@Context` injection of `AwsProxyRequest` and `AwsProxyRequestContext` in the REST extension (producer class not fetched; the injection itself is in the guide) | Use the documented types only |
| U5 | Lambda function URL events with `quarkus-amazon-lambda-http` | Not documented; ask (C7) |
| U6 | ALB as a supported front end (only a `RequestSource.ALB` branch in the REST handler) | Not documented; ask (C7) |
| U7 | Status code the client receives when the gateway integration timeout fires before Lambda returns | Do not state a code; keep Lambda timeout below the gateway timeout (M6) |
| U8 | Lambda HTTP changes in the Quarkus 3.33 to 3.39 migration guides (only 3.40 read) | Read the wiki migration guides before an upgrade |
| U9 | Which HTTP frameworks the 3.40.1.1 archetypes include by default | Inspect the generated POM and keep one framework |
| U10 | Whether `quarkus.lambda-http.*` keys are build-time fixed (lock icon not visible to the tool) | Set them in `application.properties` at build time |
| U11 | Whether the `Globals.Api` block in the HTTP API SAM templates has any effect on an `HttpApi` event | Treat it as reference output only |
| U12 | REST response encoding, a guide vs source disagreement (cite both, pick neither). Guide: "the Quarkus extension forces a binary (base 64) encoding of all HTTP response messages" (https://quarkus.io/version/3.40/guides/aws-lambda-http). Source at tag 3.40.1.1: the REST `LambdaHttpHandler` sets Base64 encoding only when the `Content-Type` is not text (https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java; source read through summarisation, M10) | What a REST client receives for text responses with `*/*` is unknown (U3). Keep `*/*` (both sources require it); do not state "all responses are Base64" as fact; test with a deployed REST API (orchestrator or human follow-up) |
| U13 | Whether Quarkus resolves the Principal path `...claims.cognito:username` when the authorizer passes an access token (the Cognito claim fact itself is High: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html) | Identify users by `sub`; depth in `securing-quarkus-lambda-cognito-v3-40` |

## Irresolvable items

0 irresolvable items. Facts that documentation cannot resolve are listed once under unverified items.

## Medium-confidence items

11 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | Pairing native Quarkus with `provided.al2023` (family fact wording) | The guide does not name the runtime; the HTTP template and the AWS table support it. Evidence: `quarkus-amazon-lambda-http` 3.40.1.1 `sam.native.yaml` declares `Runtime: provided.al2023`; `quarkus-amazon-lambda-rest` 3.40.1.1 declares `Runtime: provided`. The skill relies only on those two High facts (templates and AWS runtime table) for [F4](./never-do-patterns.md#f4-copying-the-rest-native-runtime-provided-severity-high) and keeps the pairing as given |
| M2 | Method bodies and illustrative code (resources, test skeleton) | Class shapes come from the guide; bodies are not from a page |
| M3 | Effective inline payload ceiling of 6 MB (Lambda) below 10 MB (API Gateway), reduced further by Base64 overhead | Derived from two High numbers |
| M4 | Injecting `APIGatewayV2HTTPEvent` or `Context` in Reactive Routes or Undertow; Quarkus REST as the proposed framework | Inferred from `@RequestScoped` producers in source; the guide documents injection only for Quarkus REST |
| M5 | Statements the tool paraphrased rather than quoted (archetype `/hello` example, Maven 3.9.16 prerequisite) | Paraphrase, not a verbatim quote |
| M6 | Budgeting rule "Lambda timeout below gateway integration timeout" | Derived from two High numbers |
| M7 | Funqy HTTP on Lambda implies an HTTP API | It uses `quarkus-amazon-lambda-http`; its guide only says "API Gateway" |
| M8 | Consequence of comma-splitting for headers such as HTTP dates; `payloadFormatVersion` 2.0 requirement for `-http` | Derived from source plus the AWS page; the guide is silent |
| M9 | Defaults of the `quarkus.lambda-http.*` keys: `enable-security` `false`, `map-cognito-to-roles` `true`, `cognito-role-claim` `cognito:groups`, `cognito-claim-matcher`; `quarkus.lambda.mock-event-server.enabled` `true` (family fact: High for the guide text "add … enable-security=true" and for "unless map-cognito-to-roles=false", default values medium) | The defaults come from the config reference, read in 3 windows (L2); no verbatim quote recorded (rule 13) |
| M10 | Behaviour read from source files at tag 3.40.1.1: Base64 encoding of responses without `Content-Type` (`LambdaHttpHandler.java`), producers returning `null` for the other gateway's event (`AwsHttpContextProducers.java`), request rebuild from `rawPath` + `rawQueryString`; the whole per-request lifecycle in [request-and-response-mapping](./request-and-response-mapping.md) (500 on dispatch exception, 500 on a non-numeric `X-Forwarded-Port`, `Set-Cookie` to `cookies[]`, header splitting); that Quarkus REST binds `@QueryParam List<String>` from the rebuilt request | Source read through summarisation (L4); no verbatim quote recorded |
| M11 | Defaults of the Quarkus CORS filter: `quarkus.http.cors.enabled` `false`; origins have no default | The security-cors page coverage was not reported (L5) and no verbatim quote of the default rows is recorded (family rule 13) |

## Coverage limits

5 coverage limits (parts of pages not read, or read through summarisation).

| ID | Limit |
|---|---|
| L1 | The aws-lambda-http 3.40 guide was read in 7 fetch passes with a short-quote limit; quotes are fragments, the rest is tool paraphrase |
| L2 | The all-config page was read in 3 windows (232,437 characters); part of the first window was summarised; the keys were found only in characters 0 to 100,000 |
| L3 | The rest guide 3.40 was read to 100,000 of 167,085 characters |
| L4 | Source files at tag 3.40.1.1 were read through tool summarisation (code fragments quoted; SAM templates quoted line by line) |
| L5 | Coverage of the security-cors 3.40 page was not reported by the tool |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) CORS filter on Lambda | SKILL.md Ask First; ask-first-decisions C3; build-output config table | U1 |
| (unverified) content types delivered Base64 | ask-first-decisions C5; request-and-response-mapping | U2 |
| (unverified) client effect of `*/*` on text responses | never-do F3; request-and-response-mapping | U3 |
| (unverified) REST injection mechanism | always-do-patterns 3 | U4 |
| (unverified) Function URL | SKILL.md Ask First; ask-first-decisions C7 | U5 |
| (unverified) ALB front end | ask-first-decisions C7 | U6 |
| (unverified) status code on gateway timeout | ask-first-decisions C4 | U7 |
| (unverified) 3.33 to 3.39 changes | migration-notes | U8 |
| (unverified) archetype default frameworks | always-do-patterns 2 | U9 |
| (unverified) keys build-time fixed | build-output config table | U10 |
| (unverified) `Globals.Api` effect | build-output artifact contract | U11 |
| (unverified) guide vs source on REST response encoding | always-do-patterns 4; never-do F3; request-and-response-mapping | U12 |
| (unverified) Quarkus behaviour with a Cognito access token | SKILL.md Security | U13 |
| (medium confidence) native on `provided.al2023` pairing | never-do F4; build-output artifact contract; migration-notes matrix | M1 |
| (medium confidence) illustrative method bodies | always-do-patterns header and 8 | M2 |
| (medium confidence) effective payload ceiling | SKILL.md Ask First; ask-first-decisions C5 | M3 |
| (medium confidence) raw-event access outside Quarkus REST; Quarkus REST proposal | SKILL.md Ask First; always-do-patterns 3; ask-first-decisions C2 | M4 |
| (medium confidence) Maven 3.9.16 | SKILL.md Version Context; migration-notes matrix | M5 |
| (medium confidence) Lambda timeout below gateway timeout | SKILL.md Ask First; ask-first-decisions C4 | M6 |
| (medium confidence) Funqy HTTP implies HTTP API | ask-first-decisions C2 | M7 |
| (medium confidence) comma-split headers; payload format 2.0 proposal | SKILL.md Ask First; ask-first-decisions C6; request-and-response-mapping | M8 |
| (medium confidence) `lambda-http.*` defaults (`enable-security`, `map-cognito-to-roles`, `cognito-role-claim`, `cognito-claim-matcher`) and `mock-event-server.enabled` default `true` | SKILL.md Security and Quick Reference; always-do-patterns 5; never-do F6; build-output config table | M9 |
| (medium confidence) behaviour read from source files at tag | SKILL.md Ask First (C10) and Never Do; ask-first-decisions C4, C6, C7, C10; always-do-patterns 8; never-do F2, F5; request-and-response-mapping lifecycle | M10 |
| (medium confidence) CORS filter defaults | ask-first-decisions C3; build-output config table | M11 |
| (unverified) and (medium confidence) tags inside scenario expectations | evaluation-scenarios | U1, U3, U5, U6, U7, U12, U13, M1, M6, M9, M10 |

## Source Bibliography

All read 2026-10-28.

**Quarkus 3.40, registry and source at tag 3.40.1.1**

| # | URL | Coverage | Used for |
|---|---|---|---|
| S1 | https://quarkus.io/version/3.40/guides/aws-lambda-http | 7 passes (L1) | extensions, frameworks, preview, archetypes, build files, binary, injection, security, mock server, march |
| S2 | https://quarkus.io/version/3.40/guides/all-config | 3 windows (L2) | `quarkus.lambda-http.*`, mock-server keys, defaults |
| S3 | https://quarkus.io/version/3.40/guides/security-cors | not reported (L5) | `quarkus.http.cors.*` defaults |
| S4 | https://quarkus.io/version/3.40/guides/funqy-aws-lambda-http | short page, summary | Funqy HTTP with `quarkus-amazon-lambda-http` |
| S5 | https://quarkus.io/version/3.40/guides/rest | 0 to 100,000 of 167,085 (L3) | `quarkus-rest`, context objects |
| S6 | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 | full | no Lambda changes |
| S7, S8 | Maven Central POMs of `quarkus-amazon-lambda-http` and `quarkus-amazon-lambda-rest` 3.40.1.1 (https://repo1.maven.org/maven2/io/quarkus/) | full | name, description, dependencies |
| S9 to S14 | Source at tag 3.40.1.1: both `LambdaHttpHandler.java`, REST `AwsProxyRequest.java`, HTTP `AwsHttpContextProducers.java`, both `AmazonLambdaHttpProcessor.java` (https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/) | summarised (L4) | request and response mapping, producers, security build step |
| S15 to S18 | The four `sam.jvm.yaml` and `sam.native.yaml` templates at tag 3.40.1.1 | every line quoted | artifact contract, `provided.al2023`, `Runtime: provided` |

**AWS developer guides (current pages)**

| # | URL | Used for |
|---|---|---|
| S19 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html | payload 1.0 and 2.0, `payloadFormatVersion`, `rawPath` and API mapping |
| S20 | https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html | REST proxy input and output, CORS header, 502 on bad format |
| S21 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html | feature comparison |
| S22 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html | 30 s timeout, 10 MB, header size |
| S23 | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html | REST 29 s timeout, 10 MB, header sizes |
| S24 | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html | 6 MB payload, 1 MB headers, 900 s, concurrency |
| S25 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-cors.html | HTTP API CORS behaviour |
| S26 | https://docs.aws.amazon.com/apigateway/latest/developerguide/lambda-proxy-binary-media.html | binary media types, `Accept` header |
| S27 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html | `provided` deprecation, `provided.al2023`, `java21` |

**Family facts (orchestrator-verified)**: https://quarkus.io/releases ; https://quarkus.io/guides/aws-lambda ; https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html. Community sources: none used. Cross-unit research: the U1 plain-handler research (packaging, native, SnapStart).
