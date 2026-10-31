---
name: integrating-quarkus-langchain4j-v1-15
description: "Integrates quarkus-langchain4j 1.15.0.CR1 (pre-release) into Quarkus 3.40 on AWS Lambda: AI services, OpenAI, Anthropic, Bedrock, timeouts, secrets, tests. Use when adding LLM calls to a Quarkus Lambda. Not for RAG, MCP, plain-Java LangChain4j or Quarkus 4."
---

# Integrating quarkus-langchain4j 1.15.0.CR1 in Quarkus 3.40 on AWS Lambda

> Version lock: every claim applies to **quarkus-langchain4j 1.15.0.CR1 on Quarkus 3.40 (LTS) inside AWS Lambda behind API Gateway** only. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> "Family rule N" means a rule of the factory's family rules file for this Quarkus-on-AWS team (not shipped with this skill); the rule text is stated inline at each use. Used here: 3 JVM/SnapStart vs native is an ADR; 4 `function.zip` + Terraform, no SAM/CDK; 5 secrets from Secrets Manager/SSM; 6 tenant from the token; 7 JSON logs with requestId/tenantId, no PII; 11 "default" means the documented default.
> Scope: `@RegisterAiService` with OpenAI, Anthropic and Amazon Bedrock chat models in a Quarkus Lambda: dependencies, configuration keys and their defaults, credentials, the API Gateway and Lambda time budget, retries, streaming behind API Gateway, SnapStart or native, tool boundary, tests without a real provider, metrics and tracing hooks. By name only (other packages): `integrating-quarkus-amazon-messaging-v3-40` (SQS, Secrets Manager config source), `developing-quarkus-amazon-lambda-http-v3-40` (HTTP mapping), `developing-langchain4j-core-v1-22` (plain-Java LangChain4j), `provisioning-aws-*-v6` (Terraform and IAM). Out of scope: RAG, vector and embedding stores, MCP, agent frameworks, Quarkus 4, Terraform.

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| quarkus-langchain4j | 1.15.0.CR1, a GitHub "Pre-release" (release block "released this 03 Oct", year not shown); Maven Central `lastUpdated` 2026-10-15 for the OpenAI, Anthropic and Bedrock artifacts | https://github.com/quarkiverse/quarkus-langchain4j/releases/tag/1.15.0.CR1 ; https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-bedrock/maven-metadata.xml |
| Platform pairing | Parent POM: `quarkus.version` 3.40.0, `langchain4j.version` 1.21.0; running it on Quarkus patch 3.40.1.1 is (medium confidence, M13) | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-parent/1.15.0.CR1/quarkus-langchain4j-parent-1.15.0.CR1.pom |
| Quarkus | 3.40 LTS, released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 (2026-10-19) | https://quarkus.io/releases |
| Lambda HTTP handler | Quarkus 3.40.1.1 `LambdaHttpHandler` (the `quarkus-amazon-lambda-http` extension) | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java |
| Documentation | docs.quarkiverse.io publishes only the `dev` version; tag-pinned sources win where they differ (see [config and contradictions](./blueprints/config-defaults-and-contradictions.md)) | https://docs.quarkiverse.io/quarkus-langchain4j/dev/index.html ; https://github.com/quarkiverse/quarkus-langchain4j/tree/1.15.0.CR1/docs/modules/ROOT/pages |

**Version-lifetime risk** (as of 2026-10-28; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- 1.15.0.CR1 is a pre-release and there is no 1.15.0 final on Maven Central (https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-openai/maven-metadata.xml). The stable 1.14.2 is built on Quarkus 3.33.3.1 and LangChain4j 1.20.2 (https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-parent/1.14.2/quarkus-langchain4j-parent-1.14.2.pom), so it does not fit Quarkus 3.40. 2.0.0.Beta1 is the Quarkus 4 line (medium confidence, absence of evidence, I4) and is rejected here. Adoption is Ask First [D1](./blueprints/ask-first-decisions.md#d1-adopt-a-pre-release), which states the pre-release caveat.
- Re-check trigger: when 1.15.0 final appears in the metadata above, re-run the defaults check (C1 to C4) on its tag and re-scope this skill if its Quarkus version is not 3.40.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions in depth](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Config defaults and contradictions](./blueprints/config-defaults-and-contradictions.md)
- [Verification Loop](./blueprints/verification-and-production.md#verification-loop)
- [Production readiness](./blueprints/verification-and-production.md#production-readiness)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Source bibliography](./blueprints/source-bibliography.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Import `quarkus-langchain4j-bom` 1.15.0.CR1 and add one extension per provider you use.** The BOM exists at that version ([BOM metadata](https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-bom/maven-metadata.xml)). See [patterns](./blueprints/always-do-patterns.md#1-pin-the-line-with-the-bom).
- **Run Bedrock on the Lambda execution role and configure no credentials.** The recorder sets a credentials provider only `if (credentialsProvider.isPresent())`, so otherwise the AWS SDK default chain applies ([BedrockRecorder](https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/BedrockRecorder.java)). See [patterns](./blueprints/always-do-patterns.md#2-bedrock-on-the-lambda-role).
- **Keep OpenAI and Anthropic API keys in Secrets Manager or SSM, never in properties, code or Lambda environment variables.** AWS: "we recommend that you use AWS Secrets Manager instead of environment variables to store ... API keys" ([Lambda environment variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)). How the key reaches the extension is Ask First D3. See [patterns](./blueprints/always-do-patterns.md#3-api-keys-stay-out-of-config).
- **Set the model id or name explicitly for every provider.** Anthropic's code default is `claude-3-haiku-20240307` ([ChatModelConfig](https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/model-providers/anthropic/runtime/src/main/java/io/quarkiverse/langchain4j/anthropic/runtime/config/ChatModelConfig.java)). See [patterns](./blueprints/always-do-patterns.md#4-explicit-model-and-timeouts).
- **Set the provider timeouts explicitly.** The OpenAI recorder falls back to `Duration.ofSeconds(10)` ([OpenAiRecorder](https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/model-providers/openai/openai-vanilla/runtime/src/main/java/io/quarkiverse/langchain4j/openai/runtime/OpenAiRecorder.java)). See [patterns](./blueprints/always-do-patterns.md#4-explicit-model-and-timeouts).
- **Put `@Timeout` on each AI service method, below the API Gateway integration timeout.** A REST API allows "50 milliseconds - 29 seconds for all integration types" ([REST API quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html)); the HTTP API limit is in the Quick Reference. See [patterns](./blueprints/always-do-patterns.md#5-timeout-below-the-gateway-limit).
- **Return `String` or a POJO from AI service methods behind API Gateway, not `Multi<String>`.** With `quarkus-amazon-lambda-http` the 3.40.1.1 handler writes chunks to a `ByteArrayOutputStream` and completes on `LastHttpContent` ([LambdaHttpHandler](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java)). See [patterns](./blueprints/always-do-patterns.md#6-blocking-resource-method).
- **Leave the AI service at its default scope.** The javadoc says "The resulting CDI bean is {@link jakarta.enterprise.context.RequestScoped} by default" ([RegisterAiService](https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/core/runtime/src/main/java/io/quarkiverse/langchain4j/RegisterAiService.java)). See [patterns](./blueprints/always-do-patterns.md#7-default-scope-and-tracing-defaults).
- **Leave prompt and completion tracing at its off default.** `TracingConfig` has `@WithDefault("false")` on `includePrompt` and `includeCompletion` ([TracingConfig](https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/core/runtime/src/main/java/io/quarkiverse/langchain4j/runtime/config/TracingConfig.java)). See [patterns](./blueprints/always-do-patterns.md#7-default-scope-and-tracing-defaults).
- **Test the AI service with `@InjectMock`.** "By default, the `@InjectMock` annotation can be used for any normal CDI scoped bean" ([Quarkus testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)). See [patterns](./blueprints/always-do-patterns.md#8-tests-without-a-real-provider).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| D1 Adopt a pre-release | A: 1.15.0.CR1 now, flagged. B: wait for 1.15.0 final. See [D1](./blueprints/ask-first-decisions.md#d1-adopt-a-pre-release) | "Is a pre-release acceptable in this function, and who re-runs the defaults check when 1.15.0 final ships?" |
| D2 Providers per function | One provider per function, or several named models. The names `anthropic` and `bedrock` in `chat-model.provider` are (medium confidence, M8). See [D2](./blueprints/ask-first-decisions.md#d2-providers-per-function) | "Which provider or providers does each function call?" |
| D3 Key loading mechanism | Secrets Manager config source mapped onto `quarkus.langchain4j.*.api-key`, or a `ModelAuthProvider` bean; the config-source timing is (unverified, U2). See [D3](./blueprints/ask-first-decisions.md#d3-api-key-loading-mechanism) | "Must keys rotate without a redeploy?" |
| D4 Time budget split | Single attempt, `@Retry` with short attempts, or an async SQS path; the budget formula is (medium confidence, M1). See [D4](./blueprints/ask-first-decisions.md#d4-time-and-retry-budget) | "Which gateway type, Lambda timeout, p99 model latency and output length?" |
| D5 Bedrock model id and IAM | Plain model id or inference profile; the IAM resource ARN forms are (unverified, U4) and the Converse mapping of the two actions is (medium confidence, M2). See [D5](./blueprints/ask-first-decisions.md#d5-bedrock-model-id-and-iam) | "Which model, and is cross-Region routing allowed?" |
| D6 JVM + SnapStart or native | Always an ADR (family rule 3: JVM/SnapStart vs native is an ADR). Native support of the providers is (unverified, U6); HTTP clients after a restore are (unverified, U7). See [D6](./blueprints/ask-first-decisions.md#d6-jvm--snapstart-or-native) | "Is there an ADR for the runtime choice?" |
| D7 OpenAI API mode | Chat Completions (tag default) or Responses (build-time); the mode key declaration was not located (medium confidence, absence of evidence, I2). See [D7](./blueprints/ask-first-decisions.md#d7-openai-api-mode) | "Does the chosen model exist only on the Responses API?" |
| D8 Scope and memory in multi-tenant functions | An application-wide scope would share one memory window across requests (medium confidence, M11); in-JVM memory is not durable on Lambda (medium confidence, M6). See [D8](./blueprints/ask-first-decisions.md#d8-ai-service-scope-and-chat-memory) | "Is conversation memory needed across requests, and where is it stored per tenant?" |
| D9 LangChain4j version override | Overriding `dev.langchain4j` to the plain-Java family's 1.22.0 is (unverified, U1). See [D9](./blueprints/ask-first-decisions.md#d9-langchain4j-version-override) | "Why must LangChain4j differ from 1.21.0?" |
| D10 Streaming on a REST API or Function URL | The REST extension handler buffering is (medium confidence, M4); the response-streaming output format is (unverified, U3). See [D10](./blueprints/ask-first-decisions.md#d10-streaming-and-tools) | "Is incremental delivery a hard requirement?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Put an OpenAI or Anthropic key in `application.properties`, source or a Lambda environment variable; the extension says "Never embed API keys, or other credentials directly in your source code" ([security](https://docs.quarkiverse.io/quarkus-langchain4j/dev/security.html)) | Keep it in Secrets Manager or SSM (Ask First D3 for the mechanism) |
| Configure static AWS credentials for Bedrock; the page says "Do not configure AWS credentials in `application.properties`." ([Bedrock](https://docs.quarkiverse.io/quarkus-langchain4j/dev/bedrock-chat-model.html)) | Leave `credentials-provider` unset so the Lambda role applies |
| Expose a `Multi<String>` or SSE AI endpoint through an HTTP API with `quarkus-amazon-lambda-http` and expect incremental delivery; the 3.40.1.1 handler completes the response on `LastHttpContent` ([LambdaHttpHandler](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java)) | Return the whole answer as `String` (pattern 6); the REST extension is Ask First D10 |
| Copy the guide's 60 s `@Timeout` onto an API Gateway route; the guide's value is an example ([fault tolerance](https://docs.quarkiverse.io/quarkus-langchain4j/dev/guide-fault-tolerance.html)) and the gateway limit is 29 s or 30 s | Set a value below the gateway limit (pattern 5) |
| Turn on `log-requests` or `tracing.include-prompt` in production; the extension says "Avoid logging full prompts and responses unless absolutely necessary for auditing." ([security](https://docs.quarkiverse.io/quarkus-langchain4j/dev/security.html)) | Keep both off, enable them under `%dev.` only |
| Call a real provider from tests; WireMock runs "without calling a real model" ([testing](https://docs.quarkiverse.io/quarkus-langchain4j/dev/testing-model-mocking.html)) | Mock the AI service, or for OpenAI set `base-url` to WireMock; other providers: U9 |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| OpenAI `timeout` | doc default `10s`; the recorder falls back to `Duration.ofSeconds(10)` | https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/model-providers/openai/openai-vanilla/runtime/src/main/java/io/quarkiverse/langchain4j/openai/runtime/OpenAiRecorder.java |
| Anthropic `timeout` | doc default `10s`; the recorder falls back to `Duration.ofSeconds(10)` | https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/model-providers/anthropic/runtime/src/main/java/io/quarkiverse/langchain4j/anthropic/runtime/AnthropicRecorder.java |
| OpenAI and Anthropic `max-retries` | `1`, "exactly one attempt, with retrying disabled"; deprecated in favour of MicroProfile Fault Tolerance | https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/model-providers/openai/openai-vanilla/runtime/src/main/java/io/quarkiverse/langchain4j/openai/runtime/config/LangChain4jOpenAiConfig.java ; https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/model-providers/anthropic/runtime/src/main/java/io/quarkiverse/langchain4j/anthropic/runtime/config/ChatModelConfig.java |
| Bedrock `aws.max-retries` | doc default `3` | https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/config/AwsConfig.java |
| Bedrock `aws.api-call-timeout` | doc default `13s`, recorder fallback `Duration.ofSeconds(10)` (medium confidence, M14; C3, set it explicitly) | same AwsConfig.java ; https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/BedrockRecorder.java |
| Bedrock `client.timeout`, `client.connect-timeout` | doc defaults `10s`, `3s` | https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/config/HttpClientConfig.java |
| Anthropic `chat-model.max-tokens` | `1024` | https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/model-providers/anthropic/runtime/src/main/java/io/quarkiverse/langchain4j/anthropic/runtime/config/ChatModelConfig.java |
| Default chat memory | `MessageWindowChatMemory`, 10-message window, request-scoped | https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/docs/modules/ROOT/pages/ai-services.adoc |
| `tracing.include-tool-arguments`, `include-tool-result` | `false` | https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/core/runtime/src/main/java/io/quarkiverse/langchain4j/runtime/config/TracingConfig.java |
| API Gateway integration timeout | REST API 29 s (Regional and private APIs can be raised, edge-optimized not); HTTP API 30 s, not raisable | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html ; https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html |
| Lambda timeout | default 3 s, maximum 900 s | https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html |
| API Gateway to Lambda errors | function error or bad response gives 502, Lambda API rejection gives 500, no retry | https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html |
| Response streaming | REST API yes, HTTP API no | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html |
| Bedrock IAM actions | `bedrock:InvokeModel` for `Converse`, `bedrock:InvokeModelWithResponseStream` for `ConverseStream` | https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html |

## External Resources

All fetched 2026-10-28.

- quarkus-langchain4j docs (dev): https://docs.quarkiverse.io/quarkus-langchain4j/dev/index.html
- Release 1.15.0.CR1: https://github.com/quarkiverse/quarkus-langchain4j/releases/tag/1.15.0.CR1
- Tag-pinned docs sources: https://github.com/quarkiverse/quarkus-langchain4j/tree/1.15.0.CR1/docs/modules/ROOT/pages
- Quarkus 3.40 testing guide: https://quarkus.io/version/3.40/guides/getting-started-testing
- API Gateway quotas: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html (REST) ; https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html (HTTP API)
- Lambda timeout and environment variables: https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html ; https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html
- Full bibliography: [source bibliography](./blueprints/source-bibliography.md)
