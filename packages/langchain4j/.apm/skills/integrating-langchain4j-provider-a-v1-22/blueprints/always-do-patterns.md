# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). langchain4j-anthropic 1.22.0, research date 2026-10-26. Generic `ChatModel` usage, handler and exceptions: see `developing-langchain4j-core-v1-22`.

## 1. Dependency: BOM and module

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
    <artifactId>langchain4j-anthropic</artifactId> <!-- no <version> -->
  </dependency>
</dependencies>
```

`langchain4j-core` and `langchain4j-http-client` arrive transitively in compile scope; `langchain4j-http-client-jdk` in runtime scope (https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-anthropic/pom.xml). `langchain4j-anthropic` is a stable 1.22.0 release (https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-anthropic/).

## 2. Blocking model

Source: https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java

```java
// langchain4j-anthropic 1.22.0
import dev.langchain4j.model.anthropic.AnthropicChatModel;
import dev.langchain4j.model.chat.ChatModel;
import java.time.Duration;

ChatModel model = AnthropicChatModel.builder()
        .apiKey(System.getenv("ANTHROPIC_API_KEY"))   // never a literal
        .modelName("claude-sonnet-5-5")               // string ID, current catalog
        .maxTokens(4096)                              // default is 1024
        .timeout(Duration.ofSeconds(60))              // no default in the model class
        .logRequests(false)
        .logResponses(false)
        .build();

String answer = model.chat("Summarize the BOM in one sentence.");
```

`modelName` is not checked at build time in either constructor; set it always (request-time validation is (unverified), see U1).

## 3. Streaming model

Source: https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicStreamingChatModel.java

```java
// langchain4j-anthropic 1.22.0
import dev.langchain4j.model.anthropic.AnthropicStreamingChatModel;
import dev.langchain4j.model.chat.StreamingChatModel;
import dev.langchain4j.model.chat.response.ChatResponse;
import dev.langchain4j.model.chat.response.StreamingChatResponseHandler;
import java.util.concurrent.CompletableFuture;

StreamingChatModel streaming = AnthropicStreamingChatModel.builder()
        .apiKey(System.getenv("ANTHROPIC_API_KEY"))
        .modelName("claude-haiku-5-5")
        .maxTokens(2048)
        .timeout(Duration.ofSeconds(60))
        .build();

CompletableFuture<ChatResponse> future = new CompletableFuture<>();
streaming.chat("Tell me a joke", new StreamingChatResponseHandler() {
    @Override public void onPartialResponse(String token) { System.out.print(token); }
    @Override public void onCompleteResponse(ChatResponse r) { future.complete(r); }
    @Override public void onError(Throwable t) { future.completeExceptionally(t); }
});
ChatResponse finalResponse = future.join();
```

The handler contract (abstract `onCompleteResponse` and `onError`, no-op partial callbacks) is in the core skill. The streaming model fails fast on a null handler and validates parameters before sending (read at tag 1.22.0).

## 4. Current Claude model IDs

Source: https://platform.claude.com/docs/en/about-claude/models/overview (fetched 2026-10-26).

| Model | API ID | Context | Max output | Default effort |
|---|---|---|---|---|
| Claude Fable 5.1 | `claude-fable-5-1` | 1M | 128K | high |
| Claude Opus 5.5 | `claude-opus-5-5` | 1M | 128K | medium |
| Claude Sonnet 5.5 | `claude-sonnet-5-5` | 1M | 128K | high |
| Claude Haiku 5.5 | `claude-haiku-5-5` | 1M | 128K | medium |

Legacy models remain available (Fable 5, Opus 5, Opus 4.8, 4.7, 4.6, 4.5, Sonnet 5, Sonnet 4.6, Haiku 4.5); their API ID strings were not collected (unverified), see U3.

## 5. API key

```java
String apiKey = System.getenv("ANTHROPIC_API_KEY");
if (apiKey == null || apiKey.isBlank()) {
    throw new IllegalStateException("ANTHROPIC_API_KEY is not set");
}
```

The `apiKey` builder option is documented at https://docs.langchain4j.dev/integrations/language-models/anthropic. The variable name is yours.

## 6. Errors

Catch the typed exceptions as shown in `developing-langchain4j-core-v1-22` (errors and retry). Anthropic-specific facts: the blocking `doChat` wraps the call in `withRetryMappingExceptions` using `maxRetries` (default 2); the streaming model does not retry (medium confidence).
