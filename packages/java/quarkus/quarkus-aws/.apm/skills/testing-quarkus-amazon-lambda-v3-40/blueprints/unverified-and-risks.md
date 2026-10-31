# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 87%, a deep run using all 3 iterations, and 5 triangulated claims. Family facts verified by the orchestrator on 2026-10-28 keep the tags of the family facts file.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Resolved items](#resolved-items)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30; latest patch 3.40.1.1 (2026-10-19) (High; https://quarkus.io/releases). The 3.40 documentation is new and may still change.
- Quarkus 4.0.0 is "Upcoming" with no date on the releases page (High). Quarkus 4 and Quarkiverse 4.0.0.Beta* content is rejected for this skill.
- The Quarkiverse `dev` docs name Floci as the default Dev Services provider, the 3.23.x docs name LocalStack; this skill follows 3.23.x and the default may change with a later line.
- The `quarkus-amazon-services` 3.23.x line is paired with Quarkus 3.40 by inference (M7).

## Unverified items

8 unverified items (do not assert them).

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | Whether any code other than `DevServicesLambdaProcessor` reads `quarkus.lambda.dev-port` / `test-port` (only that processor and the config classes were read) | Use the `quarkus.lambda.mock-event-server.*` names; follow-up: grep devPort()/testPort() at tag 3.40.1.1 |
| U2 | Whether RestAssured's default port follows a non-default or random `mock-event-server.test-port` (the guide states it only for 8081) | Keep the default or ask (decision C4); follow-up: RestAssuredURLManager at tag 3.40.1.1 |
| U3 | Whether `@TestSecurity` applies to requests entering through the Lambda HTTP mock event server | Prefer claims in the event (decision C5) |
| U4 | Construction of the guide's `request(String)` helper (required `APIGatewayV2HTTPEvent` fields) and a REST-API (`AwsProxyRequest`) raw-event example; the guide shows neither | Do not invent the helper; ask for the event shape |
| U5 | Whether the HTTP Lambda test also starts the vertx-http server on `quarkus.http.test-port` (8081) next to the mock event server, and how the two share the port | Do not assert port sharing |
| U6 | Dev Services sharing default: the 3.23.x page lists `shared` default `true`, its isolation section says sharing is disabled in dev mode by default and always in test mode | Do not state a sharing default |
| U7 | Dev Services for amazon-services in `@QuarkusIntegrationTest` and native ITs (not mentioned on the page), and which credentials and region values are injected ("configured automatically" only) | Ask before relying on Dev Services in an IT |
| U8 | Absence of mock-event-server changes in the Quarkus 3.32 to 3.40 migration guides (not read) | Read the wiki migration guides before an upgrade |

## Irresolvable items

0 irresolvable items. Facts that documentation cannot resolve are listed once under unverified items.

## Medium-confidence items

13 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | Reconstructed `LambdaHandlerTest` code | The fetch tool returned a summary, not the verbatim block |
| M2 | Maven form of the guide's Gradle test dependencies | The guide gives no Maven snippet |
| M3 | `@QuarkusIntegrationTest` launches the jar, native executable or container, not `function.zip` | Inference from the testing guide; the Lambda guides do not name the artifact |
| M4 | "IT extends the `@QuarkusTest` class" pattern; ITs run in the `prod` profile and ignore test `application.properties` (Camel Quarkus family rule, not shipped with the skill) | Common pattern; the Lambda guides show no IT class |
| M5 | Illustrative code: event JSON test, Dev Services properties, native verify command (the error-path test is covered by M10) | Bodies are not from a page |
| M6 | `@TestSecurity` being HTTP-oriented | Inference from the examples on the security-testing page |
| M7 | `quarkus-amazon-services` 3.23.x paired with Quarkus patch 3.40.1.1 (family fact). Not part of M7: 3.23.0 is "built on Quarkus 3.40.0" (parent POM `quarkus.version`, High) | Inferred from a changelog dependency bump |
| M8 | The `System.getProperty` caution applied to the mock server port property | Applied by analogy to the `quarkus.http.test-port` change |
| M9 | Use of the `mock-event-server.*` names rests on source code at tag 3.40.1.1 (family fact): the short keys `quarkus.lambda.dev-port` / `test-port` exist and are not deprecated, but the start-up code reads only the `mock-event-server.*` names | Not a guide statement; the guide documents the `mock-event-server.*` names only. Files: MockEventServerConfig.java, DevServicesLambdaProcessor.java at tag 3.40.1.1 (S11, S12) |
| M10 | A handler error returns status 500 from the mock event server (and the illustrative error-path test); the server start is logged at debug level only; a closed server gives the caller 503; `setMaxWorkerExecuteTime(60)` is a worker limit, not a response timeout; the build step runs only in dev or test launch mode | Source file `MockEventServer.java` at tag 3.40.1.1 (S15) read through a summarising tool (L3); one tag, not two |
| M11 | With `LambdaClient` on the classpath ("legacy testing") the mock event server is not started | Source file `DevServicesLambdaProcessor.java` at tag 3.40.1.1 (S11) read through a summarising tool (L3) |
| M12 | Defaults of `quarkus.lambda-http.enable-security` (`false`), `map-cognito-to-roles` (`true`), `cognito-role-claim` (`cognito:groups`), `cognito-claim-matcher`, and of `quarkus.lambda.mock-event-server.enabled` (`true`) (family fact, rule 13) | Stated by the config reference, read 0 to 100,000 of 232,437 characters (L2); the guide only says to add `enable-security=true`; no verbatim quote recorded |
| M13 | Dev Services provider default `localstack` and its image `localstack/localstack:4.13` on the 3.23.x page | Page read through a summarising tool; no verbatim quote of the default row or image is recorded (family rule 13) |

## Coverage limits

3 coverage limits (parts of pages not read, or read through summarisation).

| ID | Limit |
|---|---|
| L1 | https://quarkus.io/version/3.40/guides/getting-started-testing was read in two windows (0 to 100,000 and 100,000 to 108,105 of 108,105 characters); the page length differs from the 108,136 recorded in an earlier Camel Quarkus read, so the page may have changed slightly |
| L2 | https://quarkus.io/version/3.40/guides/all-config was read 0 to 100,000 of 232,437 characters; the `quarkus.lambda*` and `quarkus.lambda-http*` sections were inside the window |
| L3 | The fetch tool summarised pages and source files; identifiers and literals were quoted, other wording is a paraphrase by the tool |

## Resolved items

The open item U4 of the `developing-quarkus-amazon-lambda-v3-40` research (are `quarkus.lambda.dev-port` / `test-port` deprecated?) was resolved on 2026-10-28: they are not marked deprecated in the 3.40 reference or in source; they are a separate config root (`MockEventServerConfig`), and the start-up reads only `quarkus.lambda.mock-event-server.*`. Use those names. Sources: https://quarkus.io/version/3.40/guides/all-config ; source at tag 3.40.1.1.

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) reconstructed `LambdaHandlerTest` | always-do-patterns 1 | M1 |
| (medium confidence) Maven form of test dependencies | always-do-patterns 2 | M2 |
| (medium confidence) IT launches jar or native, not `function.zip` | always-do-patterns 4 | M3 |
| (medium confidence) IT `extends` pattern and `prod` profile | always-do-patterns 4; never-do F3 | M4 |
| (medium confidence) illustrative code and native verify flags | always-do-patterns 1; verification-loop | M5 |
| (medium confidence) handler error returns status 500 (incl. the error-path test) and the mock-server lifecycle steps 1, 3, 4, 5 | SKILL.md Quick Reference; always-do-patterns 1; mock-event-server | M10 |
| (medium confidence) `LambdaClient` on the classpath stops the mock event server | never-do F1 | M11 |
| (medium confidence) `lambda-http.*` security key defaults and `mock-event-server.enabled` default | SKILL.md Quick Reference; always-do-patterns 3; http-lambda-testing 2; evaluation-scenarios | M12 |
| (medium confidence) `@TestSecurity` HTTP-oriented | http-lambda-testing 2 | M6 |
| (medium confidence) 3.23.x pairing with patch 3.40.1.1 | SKILL.md Version Context; always-do-patterns 5; ask-first C2; migration-notes | M7 |
| (medium confidence) `System.getProperty` caution by analogy | mock-event-server; migration-notes | M8 |
| (medium confidence) short keys exist and are not deprecated; start-up reads `mock-event-server.*` only (derived from source) | SKILL.md Ask First (port row); always-do-patterns 3; ask-first C4; verification-loop (advisory grep); migration-notes | M9 |
| (unverified) other readers of `dev-port` / `test-port` | mock-event-server | U1 |
| (medium confidence) Dev Services provider default and image tag | SKILL.md Ask First and Quick Reference; ask-first C2 | M13 |
| (unverified) RestAssured follows a random or overridden port | SKILL.md Ask First; ask-first C4; mock-event-server | U2 |
| (unverified) `@TestSecurity` through the Lambda path | SKILL.md Ask First; ask-first C5; http-lambda-testing 2; evaluation-scenarios | U3 |
| (unverified) `request(String)` helper and REST-API raw event | http-lambda-testing 1; ask-first C5 | U4 |
| (unverified) vertx-http and mock server sharing port 8081 | http-lambda-testing 1 | U5 |
| (unverified) Dev Services sharing default | always-do-patterns 5 | U6 |
| (unverified) Dev Services in ITs, credentials and region | always-do-patterns 5; never-do F3; evaluation-scenarios | U7 |
| (unverified) no mock-event-server changes in 3.32 to 3.40 | migration-notes | U8 |
| (unverified) and (medium confidence) tags inside scenario expectations | evaluation-scenarios | U2, U3, U4, U7, M1, M2, M9, M10, M11, M12 |

## Source Bibliography

All read 2026-10-28.

**Quarkus 3.40, source at tag and registry**

| # | URL | Coverage | Used for |
|---|---|---|---|
| S1 | https://quarkus.io/version/3.40/guides/aws-lambda | full per tool, 2 passes | mock server, ports, test example, IT and native, SAM local, Gradle test deps |
| S2 | https://quarkus.io/version/3.40/guides/aws-lambda-http | full per tool, 2 passes | HTTP test, `/_lambda_`, event classes, security keys, SAM `start-api`, `FORCE_USER_NAME` |
| S3 | https://quarkus.io/version/3.40/guides/all-config | 0 to 100,000 of 232,437 characters (L2) | `quarkus.lambda.*` and `quarkus.lambda-http.*` keys and defaults |
| S4 | https://quarkus.io/version/3.40/guides/getting-started-testing | two windows, full (L1) | `@QuarkusIntegrationTest`, injection limit, `prod` profile, failsafe, `@InjectMock` |
| S5 | https://quarkus.io/version/3.40/guides/security-testing | full per tool | `@TestSecurity`, `quarkus-test-security`, `@QuarkusTest` only |
| S6 | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 | searched for Lambda terms | removal of `quarkus-test-amazon-lambda` and `LambdaClient` |
| S7 | https://repo1.maven.org/maven2/io/quarkus/quarkus-test-amazon-lambda/maven-metadata.xml | full | latest 3.30.8 |
| S8 | https://repo1.maven.org/maven2/io/quarkus/quarkus-test-amazon-lambda/3.40.1.1/quarkus-test-amazon-lambda-3.40.1.1.pom | HTTP 404 | absence at 3.40.1.1 |
| S9 | https://repo1.maven.org/maven2/io/quarkus/quarkus-junit-mockito/3.40.1.1/quarkus-junit-mockito-3.40.1.1.pom | full | artifact name and dependencies |
| S10 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-http/3.40.1.1/quarkus-amazon-lambda-http-3.40.1.1.pom | full | dependencies (vertx-http, security, amazon-lambda) |
| S11 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-deployment/src/main/java/io/quarkus/amazon/lambda/deployment/DevServicesLambdaProcessor.java | full, summarised by the tool (L3) | start conditions, port property, legacy check |
| S12 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/MockEventServerConfig.java | full (L3) | `quarkus.lambda` prefix, port defaults, not deprecated |
| S15 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/event-server/src/main/java/io/quarkus/amazon/lambda/runtime/MockEventServer.java | full, summarised by the tool (L3) | routes, 500 on error |
| S16 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AmazonLambdaApi.java | full | `/_lambda_`, runtime API paths |
| S17 | https://github.com/quarkusio/quarkus/tree/3.40.1.1/test-framework | directory listing | no amazon-lambda test module at 3.40.1.1 |

**Quarkiverse**

| # | URL | Used for |
|---|---|---|
| S13 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html | Dev Services mechanism, providers, keys, defaults |
| S14 | https://docs.quarkiverse.io/quarkus-amazon-services/dev/dev-services.html | comparison only (Floci default on the dev line); not used for claims |

**Family facts (orchestrator-verified)**: https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom (3.23.0 built on Quarkus 3.40.0, High) ; https://quarkus.io/releases ; https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (junit rename) ; https://github.com/quarkiverse/quarkus-amazon-services/releases (3.23 and Quarkus 3.40, medium). Community sources: none used.
