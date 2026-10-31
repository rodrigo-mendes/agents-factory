# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). langchain4j-open-ai 1.22.0, research date 2026-10-26. Generic `ChatModel`, handler and exception details live in the skill `developing-langchain4j-core-v1-22`.

## 1. Dependency

Source: https://docs.langchain4j.dev/get-started (fetched 2026-10-26).

```xml
<!-- LangChain4j 1.22.0 -->
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>dev.langchain4j</groupId>
      <artifactId>langchain4j-bom</artifactId>
      <version>1.22.0</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>

<dependencies>
  <dependency>
    <groupId>dev.langchain4j</groupId>
    <artifactId>langchain4j-open-ai</artifactId>   <!-- no <version>: the BOM manages it -->
  </dependency>
</dependencies>
```

The module brings `langchain4j-core` and `langchain4j-http-client` (compile scope) and `langchain4j-http-client-jdk` (runtime scope), so plain Java needs no extra HTTP dependency (https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/pom.xml).

## 2. Blocking model

Source: https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModel.java ; model ID checked against https://developers.openai.com/api/docs/models/all (2026-10-26).

```java
// langchain4j-open-ai 1.22.0
ChatModel model = OpenAiChatModel.builder()
        .apiKey(System.getenv("OPENAI_API_KEY"))
        .modelName("gpt-6-astra")        // string ID from the OpenAI catalog, never an enum constant
        .build();
String answer = model.chat("Hello");
```

The `gpt-6-astra` page lists `v1/chat/completions` (https://developers.openai.com/api/docs/models/gpt-6-astra). Build the model once and reuse it; it holds an HTTP client. Sharing one instance across threads is (unverified).

`modelName` has no build-time check in the constructor; a missing name surfaces later, at request time, and whether the module validates it before sending is (unverified). Always set it, as the docs list `api-key` and `model-name` as mandatory.

Optional scoping: `.organizationId(...)`, `.projectId(System.getenv("OPENAI_PROJECT_ID"))`.

## 3. Streaming model

Source: https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiStreamingChatModel.java

```java
// langchain4j-open-ai 1.22.0
StreamingChatModel streaming = OpenAiStreamingChatModel.builder()
        .apiKey(System.getenv("OPENAI_API_KEY"))
        .modelName("gpt-6-astra")
        .timeout(Duration.ofSeconds(120))
        .build();

CompletableFuture<ChatResponse> done = new CompletableFuture<>();
streaming.chat("Tell me a joke", new StreamingChatResponseHandler() {
    @Override public void onPartialResponse(String token) { System.out.print(token); }
    @Override public void onCompleteResponse(ChatResponse response) { done.complete(response); }
    @Override public void onError(Throwable error) { done.completeExceptionally(error); }
});
ChatResponse response = done.join();
```

The streaming builder has no `maxRetries`, so a failed stream is not retried (medium confidence). Failures reach `onError` as mapped LangChain4j exceptions; classify them as described in `developing-langchain4j-core-v1-22`. Thinking tokens go to `onPartialThinking` only when `returnThinking(true)` is set (see [options](./builder-options.md#openai-compatible-endpoints)).

## 4. Timeouts and retries

Source: OpenAiChatModel.java above; retry policy https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java

```java
// langchain4j-open-ai 1.22.0
OpenAiChatModel model = OpenAiChatModel.builder()
        .apiKey(System.getenv("OPENAI_API_KEY"))
        .modelName("gpt-6-astra")
        .timeout(Duration.ofSeconds(120))   // applies to connect AND read; defaults are 15 s and 60 s
        .maxRetries(2)                      // default 2, blocking model only
        .build();
```

`timeout(Duration)` is the only timeout setter; there is no separate read timeout on the builder. The blocking model retries up to `maxRetries` times with a 500 ms base delay, so total wait can reach `(maxRetries + 1) x timeout` plus delays. Whether 60 s is too short for long reasoning outputs is (unverified).

## 5. GPT-6 reasoning parameters

See [GPT-6 and reasoning-model rules](./gpt-6-and-reasoning.md) for the full examples: omit `temperature` and `topP` unless effort is `none`, and cap output with `maxCompletionTokens`.

## 6. Shared defaults

Source: https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatRequestParameters.java

```java
// langchain4j-open-ai 1.22.0
OpenAiChatModel model = OpenAiChatModel.builder()
        .apiKey(System.getenv("OPENAI_API_KEY"))
        .defaultRequestParameters(OpenAiChatRequestParameters.builder()
                .modelName("gpt-6-astra")
                .maxCompletionTokens(2000)
                .reasoningEffort("low")      // sent verbatim, no validation
                .build())
        .build();
```

The builder methods `modelName`, `maxCompletionTokens` and `reasoningEffort` on the parameters builder come partly from an inherited builder that was not seen directly (medium confidence). Per-request parameters override model defaults through `overrideWith` (the argument wins; see the core skill). `OpenAiChatRequestParameters` also adds `seed`, `user`, `store`, `metadata`, `serviceTier`, `logitBias`, `parallelToolCalls`, `promptCacheKey` and `customParameters`.

## 7. API key from the environment

Source: https://docs.langchain4j.dev/integrations/language-models/open-ai (the official sample reads `System.getenv("OPENAI_API_KEY")`).

```java
String apiKey = System.getenv("OPENAI_API_KEY");
if (apiKey == null || apiKey.isBlank()) {
    throw new IllegalStateException("OPENAI_API_KEY is not set");
}
OpenAiChatModel model = OpenAiChatModel.builder().apiKey(apiKey).modelName("gpt-6-astra").build();
```

Fail fast at startup instead of at the first call. A rejected key maps to `AuthenticationException` (401/403 mapping: core skill).
