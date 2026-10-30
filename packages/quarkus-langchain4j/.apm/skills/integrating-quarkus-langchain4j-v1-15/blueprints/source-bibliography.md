# Source bibliography

Back to [register](./unverified-and-risks.md) · [SKILL.md](../SKILL.md). All read 2026-10-28 with the WebFetch tool; coverage limits are L1 to L10 in the register. "Tag base" below is `https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/`.

| ID | URL | Used for |
|---|---|---|
| S1 | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-parent/1.15.0.CR1/quarkus-langchain4j-parent-1.15.0.CR1.pom | quarkus 3.40.0, langchain4j 1.21.0, wiremock 1.5.1 |
| S2 | https://github.com/quarkiverse/quarkus-langchain4j/releases/tag/1.15.0.CR1 | pre-release flag, changes |
| S3 | https://github.com/quarkiverse/quarkus-langchain4j/releases/tag/1.14.2 | 1.14.2 changes (security fix) |
| S4 | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-parent/1.14.2/quarkus-langchain4j-parent-1.14.2.pom | 1.14.2 on Quarkus 3.33.3.1, LangChain4j 1.20.2 |
| S5a | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-openai/maven-metadata.xml | versions, no 1.15.0 final |
| S5b | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-anthropic/maven-metadata.xml | versions |
| S5c | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-bedrock/maven-metadata.xml | versions, lastUpdated |
| S5d | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-bom/maven-metadata.xml | BOM exists at 1.15.0.CR1 |
| S6 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/index.html | docs version selector shows only dev; models page |
| S7 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/ai-services.html | `@RegisterAiService`, memory, tools |
| S8 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/openai-chat-model.html | dev defaults, mode, Responses API |
| S9 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/anthropic-chat-model.html | dev Anthropic table (superseded by S21, S22) |
| S10 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/bedrock-chat-model.html | Bedrock credentials quotes, key spellings |
| S11 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/guide-streamed-responses.html | Multi, non-blocking |
| S12 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/guide-fault-tolerance.html | `@Timeout` and `@Fallback` example, tools warning |
| S13 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/testing-model-mocking.html | WireMock approach |
| S14 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/testing.html | evaluation framework, WireMock pointer |
| S15 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/observability.html | metrics, spans, events |
| S16 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/security.html | secrets, logging, PII, injection |
| S17 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/function-calling.html | `@Tool` boundary |
| S18 | Tag base + model-providers/openai/openai-vanilla/runtime/src/main/java/io/quarkiverse/langchain4j/openai/runtime/config/LangChain4jOpenAiConfig.java | OpenAI top-level defaults |
| S19 | Tag base + model-providers/openai/openai-vanilla/runtime/src/main/java/io/quarkiverse/langchain4j/openai/runtime/config/ChatModelConfig.java | OpenAI model, temperature |
| S20 | Tag base + model-providers/openai/openai-vanilla/runtime/src/main/java/io/quarkiverse/langchain4j/openai/runtime/OpenAiRecorder.java | timeout fallback, maxRetries, dummy-key check |
| S21 | Tag base + model-providers/anthropic/runtime/src/main/java/io/quarkiverse/langchain4j/anthropic/runtime/config/LangChain4jAnthropicConfig.java | Anthropic top-level defaults |
| S22 | Tag base + model-providers/anthropic/runtime/src/main/java/io/quarkiverse/langchain4j/anthropic/runtime/config/ChatModelConfig.java | model, max-tokens, max-retries |
| S23 | Tag base + model-providers/anthropic/runtime/src/main/java/io/quarkiverse/langchain4j/anthropic/runtime/AnthropicRecorder.java | timeout fallback, `ModelAuthProvider` lookup |
| S24 | Tag base + core/runtime/src/main/java/io/quarkiverse/langchain4j/runtime/config/LangChain4jConfig.java | global keys |
| S25 | Tag base + core/runtime/src/main/java/io/quarkiverse/langchain4j/runtime/config/TracingConfig.java | tracing defaults |
| S26 | Tag base + core/runtime/src/main/java/io/quarkiverse/langchain4j/RegisterAiService.java | RequestScoped default, attributes |
| S27 | Tag base + model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/config/AwsConfig.java | region, credentials, retries, api-call-timeout |
| S28 | Tag base + model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/config/ChatModelConfig.java | model-id, temperature, max-tokens, top-p |
| S29 | Tag base + model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/config/HttpClientConfig.java | connect and read timeout, keep-alive |
| S30 | Tag base + model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/config/AwsClientConfig.java | log-requests, log-responses, log-body |
| S31 | Tag base + model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/BedrockRecorder.java | credentials, region, apiCallTimeout, retries |
| S32 | Tag base + model-providers/bedrock/runtime/pom.xml | HTTP client exclusions |
| S33 | Tag base + docs/modules/ROOT/pages/openai-chat-model.adoc | tag-pinned OpenAI mode, environment variable |
| S34 | Tag base + docs/modules/ROOT/pages/anthropic-chat-model.adoc | tag-pinned Anthropic prose |
| S35 | Tag base + docs/modules/ROOT/pages/ai-services.adoc | memory defaults, provider selection |
| S36 | https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.14.2/model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/config/ChatModelConfig.java ; https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.14.2/model-providers/openai/openai-vanilla/runtime/src/main/java/io/quarkiverse/langchain4j/openai/runtime/config/ChatModelConfig.java | 1.14.2 versus CR defaults |
| S37 | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html | REST API 29 s |
| S38 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html | HTTP API 30 s |
| S39 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html | response streaming REST yes, HTTP no |
| S40 | https://docs.aws.amazon.com/apigateway/latest/developerguide/response-transfer-mode-lambda.html | streaming output format |
| S41 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html | Node.js-only native streaming |
| S42 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html | 3 s default, 900 s maximum |
| S43 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html | Secrets Manager recommendation, role variables |
| S44 | https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html | Converse IAM actions |
| S45 | https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/credentials-chain.html | default credentials chain |
| S46 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java | buffered response |
| S47 | https://quarkus.io/version/3.40/guides/getting-started-testing | `@InjectMock` scope rule (partly read on 2026-10-28, L3) |
| S48 | https://docs.langchain4j.dev/integrations/frameworks/quarkus | native claim (indirect) |
| S49 | https://docs.langchain4j.dev/integrations/language-models/amazon-bedrock | Converse implication only |
| S50 | https://github.com/quarkiverse/quarkus-langchain4j/tree/1.15.0.CR1/model-providers/anthropic/runtime/src/main/java/io/quarkiverse/langchain4j/anthropic/runtime | `graalvm` package listing |

## Pages cited inline from family facts (not re-fetched for this skill)

| ID | URL | Used for |
|---|---|---|
| F1 | https://quarkus.io/releases | Quarkus 3.40 LTS dates, 3.40.1.1, 4.0.0 "Upcoming" |
| F2 | https://quarkus.io/version/3.40/guides/aws-lambda-http | `quarkus-amazon-lambda-http` and `-rest` are preview |
| F3 | https://github.com/quarkiverse/quarkus-langchain4j/tree/1.15.0.CR1/docs/modules/ROOT/pages | tag-pinned documentation sources |
| F4 | https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html | API Gateway to Lambda errors (502, 500, no retry) |
| F5 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html | SnapStart supports Java managed runtimes only |
| F6 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html | SnapStart activation |
| F7 | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 | `quarkus-test-amazon-lambda` removal in 3.31 |
| F8 | https://repo1.maven.org/maven2/io/quarkiverse/micrometer/registry/ | no Quarkiverse CloudWatch Micrometer registry |
| F9 | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html | X-Ray SDK maintenance mode |

## Internal sources (cited, not re-verified here)

| ID | Source | Used for |
|---|---|---|
| N1 | the research behind skill `integrating-quarkus-amazon-messaging-v3-40` (Quarkus 3.40): Secrets Manager and SSM config sources | defaults off, loaded once at startup |
| N2 | the family research on Stripe in a Quarkus Lambda: SnapStart and secrets | secrets in the snapshot, rotation needs a new version |
| N3 | the family research on Lambda HTTP: HTTP API feature limits | no response streaming on HTTP APIs |

Family facts and rules (rows verified by the orchestrator 2026-10-28) are cited by name where used: Quarkus 3.40 LTS dates, SnapStart, `quarkus-test-amazon-lambda` removal in 3.31, no Quarkiverse CloudWatch Micrometer registry, X-Ray SDK maintenance mode, API Gateway to Lambda errors.

## Not available or failed (2026-10-28)

- Not found (404): the tag-pinned `bedrock-chat-model.adoc`, `bedrock.adoc` and `amazon-bedrock.adoc` under `docs/modules/ROOT/pages/` (I1); the tag `nav.adoc` lists no Bedrock entry.
- Timed out: https://github.com/quarkiverse/quarkus-langchain4j/compare/1.14.2...1.15.0.CR1 (I3).
- The Lambda runtime environment-variable anchor page returned only a title; superseded by S43.
- `conversation-inference-call.html` reported "moved"; superseded by S44.
- A WebSearch for native-image support returned only secondary sources (conference talks, a vendor tutorial); none was used as evidence.
