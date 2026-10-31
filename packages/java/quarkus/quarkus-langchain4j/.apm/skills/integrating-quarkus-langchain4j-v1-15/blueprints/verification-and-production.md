# Verification and production readiness

Back to [SKILL.md](../SKILL.md). Research date 2026-10-28. Source ids resolve in the [source bibliography](./source-bibliography.md). Commands and code are representative and were not run (medium confidence, M16); adapt paths to your project.

## Contents

- [Verification Loop](#verification-loop)
- [Mocking at the model HTTP level](#mocking-at-the-model-http-level)
- [Production readiness](#production-readiness)

## Verification Loop

```bash
# 1. Versions: the extension line and LangChain4j
./mvnw -q dependency:tree -Dincludes=io.quarkiverse.langchain4j,dev.langchain4j
# Expected: io.quarkiverse.langchain4j:* at 1.15.0.CR1 and dev.langchain4j:* at 1.21.0 only

# 2. No keys in configuration
grep -nE "api-key=|AKIA|sk-" src/main/resources/application.properties
# Expected: no match (a %test. placeholder such as test-key is the only allowed api-key line)

# 3. Logging and prompt tracing off outside the dev profile
grep -nE "log-requests=true|log-responses=true|include-prompt=true|include-completion=true" src/main/resources/application.properties
# Expected: no match except on lines starting with %dev.

# 4. Timeouts below the gateway limit
grep -rnE "@Timeout\(value = ([3-9][0-9]|[0-9]{3,})" src/main/java
# Expected: no match on API Gateway routes (29 s REST API, 30 s HTTP API)

# 5. No streaming return type on a gateway route
grep -rnE "Multi<String>|SERVER_SENT_EVENTS" src/main/java
# Expected: no match in resource classes behind API Gateway

# 6. Tests make no outbound model call
./mvnw verify
# Expected: BUILD SUCCESS, no connection to api.openai.com, api.anthropic.com or bedrock-runtime

# 7. Package
./mvnw package
# Expected: target/function.zip (family rule 4: function.zip plus Terraform via provisioning-aws-*-v6, no SAM or CDK)
```

Check 4 matches `@Timeout` annotations that carry a literal value of 30 or more in seconds; a `unit` other than seconds needs a manual read.

## Mocking at the model HTTP level

Pattern from the WireMock guide [S13]; the guide covers OpenAI Chat Completions only and says "Other HTTP model providers can use the same approach, but need mappings that match their own URLs and response formats." [S13].

```java
// Quarkus 3.40 + quarkus-wiremock 1.5.1 + quarkus-langchain4j-openai 1.15.0.CR1
// %test.quarkus.langchain4j.openai.base-url=http://localhost:${quarkus.wiremock.devservices.port}/v1
// %test.quarkus.langchain4j.openai.api-key=test-key
// %test.quarkus.langchain4j.openai.chat-model.model-name=gpt-4o-mini
@QuarkusTest
class ModelContractTest {
    @Inject ChatModel model;
    @ConnectWireMock WireMock wiremock;   // annotation name (medium confidence, M15)

    @Test void callsChatCompletions() {
        assertEquals("Hello from WireMock!", model.chat("Hello"));
        wiremock.verifyThat(1, postRequestedFor(urlPathEqualTo("/v1/chat/completions")));
    }
}
```

- The test dependencies are `quarkus-wiremock` and `quarkus-wiremock-test` at 1.5.1, the version in the parent POM [S1][S13], plus `quarkus-junit-mockito`.
- For Bedrock, an HTTP-level equivalent would use `quarkus.langchain4j.bedrock.aws.endpoint-override` [S27] with Converse-shaped stubs; this is not documented (unverified, U9). The documented safe default for Bedrock is `@InjectMock` of the AI service.
- No Dev Services for OpenAI, Anthropic or Bedrock were found on the pages read (unverified, U9).
- `enable-integration=false` "Set to `false` to disable all requests." [S8] (dev docs, verbatim); the key exists at the tag [S18][S21].

## Production readiness

- **Performance.** Model latency dominates and the library does not bound it, so bound it (pattern 5). Init cost of provider clients and secret fetches is unquantified (unverified, U7). Bedrock keep-alive is on by default [S29]. Streaming gives no time-to-first-byte gain on Lambda (pattern 6).
- **Scalability.** One request per Lambda environment at a time (medium confidence, M19). Vendor rate limits are per account or key and were not read here. Long generations: Ask First D4 option C.
- **Metrics.** With `quarkus-micrometer` the extension publishes `langchain4j.aiservices.timed`, `langchain4j.aiservices.counted` and `gen_ai.client.token.usage` [S15]. There is no Quarkiverse CloudWatch Micrometer registry (https://repo1.maven.org/maven2/io/quarkiverse/micrometer/registry/), so the export path is the metrics unit's decision. Keep dimensions bounded (family rule 7: no PII in logs or dimensions); a tenant id as a metric tag needs an ADR.
- **Traces.** With `quarkus-opentelemetry` spans are named `langchain4j.aiservices.$interface_name.$method_name` [S15]. X-Ray SDK versus OpenTelemetry is an ADR because the X-Ray SDK is in maintenance mode since 2026-02-25 (https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html).
- **Events.** `AiServiceStartedEvent`, `AiServiceCompletedEvent`, `AiServiceErrorEvent` are correlated by `event.invocationContext().invocationId()`; "The Quarkus-specific auditing features have been deprecated and removed." [S15]. Log the invocation id and `requestId` or `tenantId` (family rule 7: JSON logs with requestId/tenantId, no PII), never prompt text.
- **Errors.** Map provider failures and `@Timeout` to a controlled 5xx body. An uncaught function error makes API Gateway answer 502 and it does not retry (https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html).
- **Security.** Bedrock role only with least-privilege resources (Ask First D5). Keys from Secrets Manager or SSM (Ask First D3). Prompt-injection hygiene: "Clearly separate instructions from user-provided data in your prompts." [S16]. The tenant id comes from the token, never from the prompt or path (family rule 6: tenant from the token). `@RolesAllowed` on tool methods is enforced [S17]. Keep the AI service at its default scope (Ask First D8).
- **Cost.** `gen_ai.client.estimated_cost` exists "when a `CostEstimator` bean is available" [S15].
