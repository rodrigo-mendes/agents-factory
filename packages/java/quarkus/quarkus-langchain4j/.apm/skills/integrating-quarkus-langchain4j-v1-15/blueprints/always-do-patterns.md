# Always-do patterns

Back to [SKILL.md](../SKILL.md). Research date 2026-10-28. Source ids (S1, S31, ...) resolve in the [source bibliography](./source-bibliography.md). Code is illustrative and was not compiled (medium confidence, M16).

## Contents

- [1 Pin the line with the BOM](#1-pin-the-line-with-the-bom)
- [2 Bedrock on the Lambda role](#2-bedrock-on-the-lambda-role)
- [3 API keys stay out of config](#3-api-keys-stay-out-of-config)
- [4 Explicit model and timeouts](#4-explicit-model-and-timeouts)
- [5 Timeout below the gateway limit](#5-timeout-below-the-gateway-limit)
- [6 Blocking resource method](#6-blocking-resource-method)
- [7 Default scope and tracing defaults](#7-default-scope-and-tracing-defaults)
- [8 Tests without a real provider](#8-tests-without-a-real-provider)

## 1 Pin the line with the BOM

The parent POM of 1.15.0.CR1 sets `quarkus.version` 3.40.0, `langchain4j.version` 1.21.0 and `quarkus-wiremock.version` 1.5.1 [S1]. A `quarkus-langchain4j-bom` artifact exists at 1.15.0.CR1 [S5d]. The plain-Java skill family uses LangChain4j 1.22.0; do not import that version here (Ask First D9).

```xml
<!-- Quarkus 3.40 + quarkus-langchain4j 1.15.0.CR1 (pre-release) -->
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>io.quarkiverse.langchain4j</groupId>
      <artifactId>quarkus-langchain4j-bom</artifactId>
      <version>1.15.0.CR1</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>
<dependencies>
  <!-- only the providers this function uses -->
  <dependency><groupId>io.quarkiverse.langchain4j</groupId><artifactId>quarkus-langchain4j-bedrock</artifactId></dependency>
  <!-- quarkus-langchain4j-openai / quarkus-langchain4j-anthropic -->
  <dependency><groupId>io.quarkus</groupId><artifactId>quarkus-smallrye-fault-tolerance</artifactId></dependency>
</dependencies>
```

`quarkus-smallrye-fault-tolerance` provides `@Timeout` [S12]. Whether the BOM manages every `dev.langchain4j:*` artifact was not read (unverified, U1). Bedrock: the extension excludes `netty-nio-client`, `url-connection-client` and `apache-client` from `langchain4j-bedrock` [S32][S31]; that this makes an extra client artifact unnecessary, and that its own factory is Vert.x-based, are (medium confidence, M9).

## 2 Bedrock on the Lambda role

The recorder sets a credentials provider only `if (credentialsProvider.isPresent())` and the region only `if (region.isPresent())` [S31]. The documented defaults are "default aws credentials provider chain" and "default aws region provider chain" [S27]. The AWS SDK chain checks the environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN`, then container credentials [S45]. Lambda sets those variables "obtained from the function's execution role" and sets `AWS_REGION` [S43]. Under SnapStart the runtime uses container credentials (`AWS_CONTAINER_CREDENTIALS_FULL_URI`; https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html). The `dev` page says "The extension uses the AWS SDK default credentials provider chain." [S10].

```properties
# Quarkus 3.40 + quarkus-langchain4j-bedrock 1.15.0.CR1: Lambda role, no key, no region
# no quarkus.langchain4j.bedrock.aws.credentials-provider, no quarkus.langchain4j.bedrock.aws.region
quarkus.langchain4j.bedrock.chat-model.model-id=<chosen model or inference-profile id>
```

The role needs the two Bedrock actions: Ask First D5 holds the action list and the unverified resource ARN forms (IAM itself is written by `provisioning-aws-*-v6`).

## 3 API keys stay out of config

OpenAI and Anthropic keys default to the literal `dummy`; an unset key fails with `SRCFG00014 ... is required` when the base URL is the default [S20][S23]. Lambda guidance and the extension agree: Secrets Manager instead of environment variables [S43], and "Never embed API keys, or other credentials directly in your source code, prompts, or user-controlled inputs." [S16]. Family rule 5 applies (secrets come from Secrets Manager or SSM). The properties file therefore holds no `api-key` line for these providers; the mechanism that delivers the key is Ask First D3.

```properties
# application.properties: nothing for api-key. Never: quarkus.langchain4j.openai.api-key=sk-...
quarkus.langchain4j.openai.chat-model.model-name=<chosen model>
```

## 4 Explicit model and timeouts

Defaults differ between layers, so set them. Anthropic: code default `claude-3-haiku-20240307` [S22] versus tag docs "latest available Claude model" [S34] (C2). Bedrock `model-id` has a documentation default only, with no `@WithDefault` (unverified, U5) [S28]. The timeout fallback is `Duration.ofSeconds(10)` for OpenAI and Anthropic [S20][S23]. Bedrock `aws.api-call-timeout` is documented as `13s` while the recorder falls back to 10 s (medium confidence, M14; C3) [S27][S31]. The whole table is in [config defaults](./config-defaults-and-contradictions.md).

```properties
# quarkus-langchain4j 1.15.0.CR1: example values for a REST API route (29 s), not defaults
quarkus.langchain4j.openai.chat-model.model-name=<chosen OpenAI model>
quarkus.langchain4j.openai.timeout=20s
quarkus.langchain4j.anthropic.chat-model.model-name=<chosen Claude model>
quarkus.langchain4j.anthropic.chat-model.max-tokens=1024
quarkus.langchain4j.anthropic.timeout=20s
quarkus.langchain4j.bedrock.chat-model.model-id=<chosen model or inference-profile id>
quarkus.langchain4j.bedrock.client.timeout=20s
quarkus.langchain4j.bedrock.aws.api-call-timeout=24s
quarkus.langchain4j.bedrock.aws.max-retries=1
```

`openai.timeout` and `anthropic.timeout` come from the tag config interfaces [S18][S21]; the Bedrock key spellings from the `dev` config table and the tag interfaces [S10][S27][S29]. The values above are design choices (medium confidence, M1).

## 5 Timeout below the gateway limit

Limits: REST API "50 milliseconds - 29 seconds for all integration types" [S37]; HTTP API "Maximum integration timeout | 30 seconds | No" [S38]; Lambda default 3 s, maximum 900 s [S42]. The fault-tolerance deprecation javadoc says "Using the fault tolerance mechanisms built in Langchain4j is not recommended. If possible, use MicroProfile Fault Tolerance instead." [S22]. The guide's example is `@Timeout(value = 60, unit = ChronoUnit.SECONDS)` [S12]; that 60 s is the guide's example, not a default.

```java
// Quarkus 3.40 + quarkus-langchain4j 1.15.0.CR1 + quarkus-smallrye-fault-tolerance
@RegisterAiService
public interface SupportAssistant {
    @Timeout(value = 25, unit = ChronoUnit.SECONDS)   // below the 29 s REST API limit
    String answer(@UserMessage String question);
}
```

Rule of thumb (medium confidence, M1): provider `timeout` times attempts stays below `@Timeout`, `@Timeout` stays below the gateway limit minus Quarkus and Lambda overhead, and the Lambda timeout is at least the gateway limit. A `@Fallback` default method on the interface follows the guide's pattern, but its exact signature is (medium confidence, M3).

## 6 Blocking resource method

The `quarkus-amazon-lambda-http` 3.40.1.1 handler allocates `new ByteArrayOutputStream(BUFFER_SIZE)`, checks `msg instanceof LastHttpContent`, calls `responseBuilder.setBody(baos.toString(StandardCharsets.UTF_8))` and blocks on `handler.getFuture().get()` [S46]. HTTP APIs have no response streaming [S39]; Lambda streams natively "on Node.js managed runtimes" [S41]. A streamed answer therefore reaches the client as one buffered response.

```java
// Quarkus 3.40 (quarkus-amazon-lambda-http) + quarkus-langchain4j 1.15.0.CR1
@Path("/assist")
public class AssistResource {
    @Inject SupportAssistant assistant;

    @POST @Consumes(MediaType.TEXT_PLAIN) @Produces(MediaType.TEXT_PLAIN)
    public String assist(String question) { return assistant.answer(question); }
}
```

## 7 Default scope and tracing defaults

`@RegisterAiService` beans are `@RequestScoped` by default and "If you need to change the scope, simply annotate the class with a CDI scope." [S26]. Memory defaults: "`MessageWindowChatMemory` with 10-message window", "Memory is request-scoped by default" [S35]. `TracingConfig` has `@WithDefault("false")` on `includePrompt`, `includeCompletion`, `includeToolArguments`, `includeToolResult` [S25]; `log-requests` and `log-responses` have documentation default `false` [S24]. Family rule 7: JSON logs with `requestId` and `tenantId`, no PII.

```properties
# explicit = the documented defaults, in the production profile
quarkus.langchain4j.tracing.include-prompt=false
quarkus.langchain4j.tracing.include-completion=false
quarkus.langchain4j.log-requests=false
quarkus.langchain4j.log-responses=false
```

## 8 Tests without a real provider

`@InjectMock` works for any normal CDI scoped bean through `quarkus-junit-mockito` [S47], and the AI service is `@RequestScoped` [S26]. The WireMock guide starts a server "as a Dev Service in dev and test mode"; it "does not automatically redirect model calls", so `base-url` is overridden, and "No internal Quarkus LangChain4j testing modules are required" [S13]. The OpenAI dummy-key check applies only with the default base URL [S20]. `quarkus-test-amazon-lambda` was removed in Quarkus 3.31; Lambda-level tests use `quarkus-junit` with RestAssured against the mock event server (https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31).

```java
// Quarkus 3.40 + quarkus-junit-mockito + quarkus-langchain4j 1.15.0.CR1
@QuarkusTest
class AssistResourceTest {
    @InjectMock SupportAssistant assistant;

    @Test void answers() {
        Mockito.when(assistant.answer("hi")).thenReturn("hello");
        given().contentType("text/plain").body("hi").post("/assist")
               .then().statusCode(200).body(is("hello"));
    }
}
```

```properties
%test.quarkus.langchain4j.openai.base-url=http://localhost:${quarkus.wiremock.devservices.port}/v1
%test.quarkus.langchain4j.openai.api-key=test-key
```

The guide covers OpenAI Chat Completions only. HTTP-level stubs for Bedrock or Anthropic are not documented (unverified, U9); mock the AI service there.
